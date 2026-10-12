# Agent permissions — mainnet (chain 101101, genesis `2c1c0679`)

An **agent** is a key that trades for an account (its **owner**) within limits the owner signs. This page describes
how agents are registered, what they can and cannot sign, and how their limits are checked. The machine-readable
twin is the `agents` section of <https://rpc.vordium.com/network-spec.json>.

## The essentials

- **An agent key signs as a session key of its owner.** The chain recognises the owner's key or one of the owner's
  live session keys. Registering an agent does not by itself let the key sign: the owner also creates a session for it
  (`SessionCreate`).
- **Every agent needs a live registration.** Every action signed by an agent key — place, modify and cancel orders,
  TWAP place and cancel, each TWAP child, TP/SL, vault orders — is refused once block time ≥ the registration's
  `expires_ms` (`agent: registration not live`). A registration with `expires_ms` 0 is expired. Renew by registering
  the same agent again with a higher nonce and a later `expires_ms`; there is no maximum.
- **Agents never withdraw.** A withdrawal applies only if its EIP-712 `Withdraw` signature recovers to the owner
  (owner, destination, amount, nonce). Session keys are never consulted. No public route accepts a VORD transfer.
- **The owner is never gated.** Orders the owner signs never pass through any agent check.
- **`202` means accepted into the mempool, not applied.** A refusal on the apply path is a silent no-op; read the agent
  back (`GET /agents/<owner>/<agent>`) to see whether it changed.

## Which limits apply

Two checks exist:

- the **capability gate** — per owner: `SetAgentMode` (0 off, 1 reduce-only, 2 active) and `SetAgentCaps`
  (max leverage, allowed order types, max input per trade, max total position);
- the **policy engine** — per (owner, agent): a signed `SetAgentPolicyV1` policy, per-market limits
  (`SetAgentMarketLimit`) and a daily risk record.

On mainnet today session-key orders go through the **capability gate**. Policies and market limits are accepted,
stored and readable, and apply when the policy engine is in force. Agent actions can also be paused network-wide; while
paused, new agent actions are refused and cancels still pass.

Capability gate refusals: `agent mode OFF` · `agent REDUCE_ONLY: order must reduce position` · `agent mode invalid` ·
`agent caps unset` · `agent order type not allowed` · `agent leverage over cap` · `agent input over cap` ·
`agent position over cap`.

`SetAgentCaps.maxLeverage` is compared with the order's leverage **in basis points** (10000 = 1x), and the default caps
carry 5. Set explicit caps before an agent places orders.

## Ops

All agent ops below use the **VordCore** EIP-712 domain; the session ops use the **VordexSession** domain. Both domains
are bound to this network's genesis (`salt = keccak256(tag ‖ genesis sha256)`). Signatures are 65 bytes r‖s‖v over the
EIP-712 digest. Agent ops are submitted to the public intake `POST https://rpc.vordium.com/submit` (body ≤ 8192 bytes).

| op | # | signer | EIP-712 type |
|---|---|---|---|
| RegisterAgentV2 | 129 | owner | `RegisterAgentV2(address owner,address agent,string name,string mandate,uint64 expiresMs,uint64 nonce)` |
| SetAgentName | 130 | owner | `SetAgentName(address owner,address agent,string name,uint64 nonce)` |
| RevokeAgent | 118 | owner | `RevokeAgent(address owner,address agent,uint64 nonce)` |
| SetAgentPolicyV1 | 132 | owner; the agent key may sign a pure tightening | `SetAgentPolicyV1(address owner,address agent,uint32 capsBitmask,uint8 sideMode,uint128 maxTotalExposure6dec,uint32 maxLeverageBps,uint128 dailyLossLimit6dec,uint128 dailyFeeCap6dec,uint32 opsPerWindow,uint32 opsWindowMs,uint32 activeFromMsOfDay,uint32 activeToMsOfDay,uint32 oracleBandBps,bool lockAutoClear,uint64 expiresMs,bool enabled,uint64 nonce)` |
| SetAgentMarketLimit | 120 | owner | `SetAgentMarketLimit(address owner,address agent,uint32 pair,bool allowed,uint128 maxOrder18dec,uint128 maxPosition18dec,uint32 maxLeverageBps,uint64 nonce)` |
| ClearAgentLock | 133 | owner | `ClearAgentLock(address owner,address agent,uint64 lockSinceMs,uint64 nonce)` |
| SetAgentCaps | 18 | owner | `SetAgentCaps(address owner,uint64 maxLeverage,uint32 allowedOrderTypes,uint128 maxInputPerTrade,uint128 maxTotalPosition)` |
| SetAgentMode | 19 | owner | `SetAgentMode(address owner,uint8 mode)` |
| SessionCreate | 9 | owner (recovered signer) | `SessionCreate(address sessionKey,uint256 expiresAt,uint256 nonce)` — `POST /session/create` |
| SessionRevoke | 10 | owner | `SessionRevoke(address owner,uint256 nonce)` — `POST /session/revoke` |

Units: `*6dec` = USDC with 6 decimals; `*18dec` = base-asset size with 18 decimals; `*Bps` = basis points
(10000 = 100 % or 1x); `*Ms` = milliseconds of block time; `*MsOfDay` = milliseconds since 00:00 UTC (the window wraps
past midnight when from > to; from = to = 0 means always active). In a policy or a market limit, 0 switches a limit off.

### Agent names

`name` is 3–32 bytes of ASCII letters, digits, space, `-`, `_` and `.`, in canonical form, with at least one letter or
digit, and must not contain a reserved word. The full rule and the order of its refusals are in the spec
(`agents.nameRule`, `agents.reservedWords`). `mandate` is public free text.

### Capability bits (`capsBitmask`)

| bit | value | name | lets the agent key sign |
|---|---|---|---|
| 0 | 1 | place | a PlaceOrder that is not reduce-only |
| 1 | 2 | cancel | CancelOrder, CancelTwap |
| 2 | 4 | modify | ModifyOrder (re-checked against the limits) |
| 3 | 8 | tpsl | SetTpSl |
| 4 | 16 | close | a reduce-only PlaceOrder |
| 5 | 32 | vault | vault orders |

A policy carrying any bit outside 63 is refused. There is no withdraw bit.

## Nonces and timing

- RegisterAgentV2, SetAgentName, RevokeAgent, SetAgentPolicyV1, SetAgentMarketLimit and ClearAgentLock share one
  counter per (owner, agent): each needs a `nonce` greater than the last one used (a UNIX millisecond timestamp is a
  common choice). The first registration needs any nonce above 0. An agent-signed policy tightening uses the agent's
  own counter.
- SetAgentCaps and SetAgentMode carry no nonce.
- Sessions use the owner's own session counter; nonce 0 is refused. `expiresAt` is in **seconds** and at most
  90 days ahead of block time.
- **Loosening is rate-limited:** a policy or market-limit change that loosens any limit applies only one hour after the
  previous loosening for that agent (the first policy is not a loosening). Tightening is never delayed.
- A **market limit row cannot be removed**: once any row exists for an (owner, agent), unlisted markets are refused for
  that agent.

## When the policy engine is in force

The agent acts only while block time is before the earlier of the policy's and the registration's `expires_ms`; a
policy whose `expiresMs` is not later than block time is refused. Reaching the daily loss limit locks the agent to
reduce-only: the lock clears at the next UTC day when the policy sets `lockAutoClear`, otherwise when the owner signs
`ClearAgentLock`. Refusals you can see in the agent's activity: `agent: no v1 policy (deny by default)`,
`agent: policy disabled`, `agent: policy expired`, `agent: capability not granted`, `agent: reduce-only (locked or side
mode)`, `agent: outside active window`, `agent: market not allowlisted`, `agent: max order (market)`,
`agent: max position (market)`, `agent: max leverage (market)`, `agent: max leverage (overall)`,
`agent: max total exposure`, `agent: ops-per-window`, `agent: daily fee cap`, `agent: daily loss limit`,
`agent: price outside oracle band`, `agent: oracle stale`, `agent: not this agent's order`,
`agent: not this agent's TWAP`.

## Reading an agent

- `GET https://rpc.vordium.com/agents/<owner>` — every agent of the owner.
- `GET https://rpc.vordium.com/agents/<owner>/<agent>` — status, name, mandate, `expires_ms`, `policy_v1`, `risk_v1`,
  market limits, `last_raise_ms` / `next_raise_ms` (committed state; `found:false` when unknown). Large amounts are JSON
  numbers that may exceed 2^53 — parse them as big integers.
- Decide "expired" from `expires_ms` (0, or ≤ block time), not from `status`: a record with `expires_ms` 0 reads
  `active` there although the chain treats it as expired.
- A revoked agent is returned with `status: "revoked"`; nothing is ever deleted.

## Intake responses

| code | body |
|---|---|
| `202` | `{"success":true,"status":"submitted","intaken":bool}` — in the mempool, not yet applied |
| `400` | `{"error":"invalid body","details":…}` |
| `403` | `{"error":"bad_signature"|"malformed_signature"|"not_public"}` |
| `413` | `{"error":"payload exceeds 8KiB"}` |
| `429` | `{"error":"mempool full"}` |
