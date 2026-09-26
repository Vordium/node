# Agent permissions — chain 101101, genesis `2c1c0679`

_Generated from the running node binary `db6d34f8` and the live chain at spec 19 (2026-09-26T21:59:03Z). Machine-readable twin: `agents` in https://rpc.vordium.com/network-spec.json._

## Status on the live chain today

- The agent **policy gate is OFF**: chain-param key 235 reads 0 (it enforces only when the value is 1).
- So `RegisterAgent`, `SetAgentPolicy` and `SetAgentMarketLimit` are accepted, stored and readable, but **nothing enforces them yet**.
- Orders signed by a session key go through the **legacy caps gate** instead. The genesis seeded default caps {"allowed_order_types": 3, "max_input_per_trade_usdc_6dec": "1000000000", "max_leverage": 5, "max_total_position_18dec": "10000000000000000000000"}. Their effect today: every session-key order is refused ('agent mode OFF') until the owner signs SetAgentMode; and genesis max_leverage 5 is compared against the order's leverage IN BPS, so any order at ≥ 1x (10000 bps) is refused ('agent leverage over cap') unless the owner sets explicit caps.
- An agent key signs as a **session key** of its owner: the chain recognises the owner key or one of the owner's live session keys, nothing else. `RegisterAgent` does not by itself let a key sign; the owner must also create a session for it.
- Every agent op is accepted at public `POST /submit` (body ≤ 8192 bytes). A `202` means the op entered the mempool, **not** that it applied. Every apply-path refusal is a silent no-op, and the only way to see it is that `GET /agents/…` does not change.

## Who signs what

| op | # | EIP-712 domain | signer | intake |
|---|---|---|---|---|
| RegisterAgent | 117 | VordCore | owner only (signature must recover to `owner`) | public POST /submit |
| RevokeAgent | 118 | VordCore | owner only | public POST /submit |
| SetAgentPolicy | 119 | VordCore | apply path: owner for a first policy or any loosening (+ cooldown); owner OR the agent key for a pure tightening. Intake and gossip admit an OWNER signature only, so an agent-signed tightening never reaches the apply path. | public POST /submit |
| SetAgentMarketLimit | 120 | VordCore | owner only | public POST /submit |
| SetAgentCaps | 18 | VordCore | owner only | the node's agent-settings intake — not publicly reachable |
| SetAgentMode | 19 | VordCore | owner only | the node's agent-settings intake — not publicly reachable |
| SessionCreate | 9 | VordexSession | owner (the struct names the session key; the owner is the recovered signer) | public POST /session/create |
| SessionRevoke | 10 | VordexSession | owner | public POST /session/revoke |

### RegisterAgent (VordCoreOp #117)

EIP-712 type (VordCore domain):

```
RegisterAgent(address owner,address agent,string mandate,uint64 expiresMs,uint64 nonce)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account the agent acts for; must be the signer | — |
| `agent` | `Address` | — | the agent key's address (one owner per ACTIVE agent) | — |
| `mandate` | `String` | — | public free-text description; the only text field | — |
| `expires_ms` | `u64` | UNIX milliseconds (block timestamp clock) | record expiry — stored and served, not enforced | not enforced — any value is accepted and stored |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid |

- firstRegistrationAnyNonce: no stored record ⇒ no nonce comparison

### RevokeAgent (VordCoreOp #118)

EIP-712 type (VordCore domain):

```
RevokeAgent(address owner,address agent,uint64 nonce)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account | — |
| `agent` | `Address` | — | the agent to revoke | — |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid |


### SetAgentPolicy (VordCoreOp #119)

EIP-712 type (VordCore domain):

```
SetAgentPolicy(address owner,address agent,uint32 capsBitmask,uint8 sideMode,uint128 maxTotalNotional6dec,uint32 maxLeverageOverallBps,uint128 dailyLossLimit6dec,uint32 drawdownBps,uint128 feeCapWindow6dec,uint64 opsPerWindow,uint64 windowLenMs,uint32 activeFromMsOfDay,uint32 activeToMsOfDay,uint64 expiresMs,bool enabled,uint64 nonce)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account | — |
| `agent` | `Address` | — | the agent this policy governs | — |
| `caps_bitmask` | `u32` | — | which op kinds the agent may sign (capability bits below) | OR of capabilityBits |
| `side_mode` | `u8` | — | 0 both sides, 1 reduce-only | 0 = both sides, 1 = reduce-only (any other value behaves as 0 — only 1 is tested) |
| `max_total_notional_6dec` | `u128` | USDC, 6 decimals | cap on the agent's open gross notional at mark + the new order (not applied to reducing orders) | 0 = dimension off (no cap) |
| `max_leverage_overall_bps` | `u32` | basis points (10000 = 1x / 100 %) | per-order leverage cap across all markets | 0 = off |
| `daily_loss_limit_6dec` | `u128` | USDC, 6 decimals | window loss (realised + unrealised at mark) that trips the agent | 0 = off |
| `drawdown_bps` | `u32` | basis points (10000 = 1x / 100 %) | drop below the window's equity high-water mark that trips the agent | 0 = off |
| `fee_cap_window_6dec` | `u128` | USDC, 6 decimals | fees the agent may pay per window before placements stop | 0 = off |
| `ops_per_window` | `u64` | — | placements allowed per window | 0 = off |
| `window_len_ms` | `u64` | UNIX milliseconds (block timestamp clock) | length of the accounting window | 0 = 86,400,000 ms (24 h) |
| `active_from_ms_of_day` | `u32` | milliseconds since 00:00 UTC | start of the daily trading window (UTC) | from = to = 0 ⇒ always active; from = to ≠ 0 ⇒ never active |
| `active_to_ms_of_day` | `u32` | milliseconds since 00:00 UTC | end of the daily trading window (UTC, exclusive; wraps past midnight when from > to) | see active_from_ms_of_day |
| `expires_ms` | `u64` | UNIX milliseconds (block timestamp clock) | policy expiry (block time) | no 0-means-never: the gate refuses when block time ≥ expires_ms, so 0 = already expired |
| `enabled` | `bool` | — | false = the gate refuses everything for this agent | — |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid |

- raiseCooldownMs: 3600000

### SetAgentMarketLimit (VordCoreOp #120)

EIP-712 type (VordCore domain):

```
SetAgentMarketLimit(address owner,address agent,uint32 pair,bool allowed,uint128 maxOrder18dec,uint128 maxPosition18dec,uint32 maxLeverageBps,uint64 nonce)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account | — |
| `agent` | `Address` | — | the agent | — |
| `pair` | `u32` | — | market id | — |
| `allowed` | `bool` | — | false = explicit deny for this market | false on a present row = explicit deny |
| `max_order_18dec` | `u128` | base-asset size, 18 decimals | max size of one order in this market | 0 = off |
| `max_position_18dec` | `u128` | base-asset size, 18 decimals | max |net position| after the order in this market | 0 = off |
| `max_leverage_bps` | `u32` | basis points (10000 = 1x / 100 %) | leverage cap in this market | 0 = off (per market) |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid |

- noRemovalPath: no remove/retain/clear on agent_market_limit anywhere in the crate — once any row exists the (owner,agent) is in allowlist mode for good
- noRemovalEvidence: grep 'agent_market_limit.(remove|retain|clear)' → 0

### SetAgentCaps (VordCoreOp #18)

EIP-712 type (VordCore domain):

```
SetAgentCaps(address owner,uint64 maxLeverage,uint32 allowedOrderTypes,uint128 maxInputPerTrade,uint128 maxTotalPosition)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account (legacy caps are per OWNER, not per agent) | — |
| `max_leverage` | `u64` | bps as compared by the gate (field name says x) | compared against the order's leverage IN BPS (so 5 means 0.0005x, not 5x) | compared against leverage in bps |
| `allowed_order_types` | `u32` | — | bitmask of order types: bit 0 market, bit 1 limit | — |
| `max_input_per_trade` | `u128` | USDC, 6 decimals | max margin per order (USDC, 6 decimals; notional ÷ leverage) | — |
| `max_total_position` | `u128` | base-asset size, 18 decimals | max |net position| after the order (18 decimals) | — |

- noNonce: the op and its EIP-712 type carry no nonce

### SetAgentMode (VordCoreOp #19)

EIP-712 type (VordCore domain):

```
SetAgentMode(address owner,uint8 mode)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account | — |
| `mode` | `u8` | — | 0 OFF (default), 1 REDUCE_ONLY, 2 ACTIVE; > 2 refused | default when never set: 0 (OFF) |

- noNonce: no nonce

### SessionCreate (VordCoreOp #9)

EIP-712 type (VordexSession domain):

```
SessionCreate(address sessionKey,uint256 expiresAt,uint256 nonce)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account; recovered from the signature (not in the signed struct) | — |
| `session_key` | `Address` | — | the key being authorised — this is how an agent key gets to sign | — |
| `expires_at` | `u64` | UNIX seconds | UNIX SECONDS; at most now + the session horizon | must be ≤ block time + the session horizon; a past value makes the session inert |
| `nonce` | `u64` | — | per-owner session nonce; 0 refused | 0 is refused; otherwise strictly greater than the owner's stored session nonce |

- maxExpirySecs: 7776000

### SessionRevoke (VordCoreOp #10)

EIP-712 type (VordexSession domain):

```
SessionRevoke(address owner,uint256 nonce)
```

| field | type | units | meaning | zero / default |
|---|---|---|---|---|
| `owner` | `Address` | — | the account (revokes the owner's sessions) | — |
| `nonce` | `u64` | — | per-owner session nonce | strictly greater than the owner's stored session nonce |


## Capability bits (`caps_bitmask`)

| bit | value | name | lets the agent key sign |
|---|---|---|---|
| 0 | 1 | place | PlaceOrder that is not reduce-only (policy gate) |
| 1 | 2 | cancel | CancelOrder, CancelTwap |
| 2 | 4 | modify | ModifyOrder (also re-checked against the policy limits) |
| 3 | 8 | tpsl | SetTpSl |
| 4 | 16 | close | reduce-only PlaceOrder |

There is **no withdraw bit**. Where each capability is checked:

- `CancelOrder` → AGENT_CAP_CANCEL via the agent op check
- `ModifyOrder` → AGENT_CAP_MODIFY via the agent op check
- `VordTransfer` → 0 via the agent op check
- `CancelTwap` → AGENT_CAP_CANCEL via the agent op check
- `SetTpsl` → AGENT_CAP_TPSL via the agent op check
- `ModifyOrder` → AGENT_CAP_MODIFY via the agent policy check
- `PlaceOrder` → AGENT_CAP_PLACE (AGENT_CAP_CLOSE when reduce_only) via the agent policy check

Session-signed ops that run **no agent check at all**, even with the gate on: `PlaceTwap`, `VlpDeposit`, `VlpWithdraw`, `Stake`, `Unstake`, `ClaimStakingRewards`, `CreateVault`, `VaultDeposit`, `VaultWithdraw`, `VaultClose`, `VaultPlaceOrder`, `VaultCancelOrder`. `PlaceTwap` matters most: a TWAP's children are placed as system orders and skip the policy gate.

## Can an agent withdraw or move funds?

- **Withdraw: never.** A withdrawal applies only if the EIP-712 `Withdraw` signature recovers to the OWNER over owner, destination, amount and nonce; session keys are not consulted in any switch state.
- **VORD transfer:** none — no public route accepts a VordTransfer; the only other entry is validator-to-validator gossip, which is not publicly reachable. On the apply path, refused for a session key only while the policy gate is ON (capability 0 is never granted); with the gate OFF the apply path accepts a session-key signature on VordTransfer. The policy gate is OFF today.
- Session keys can also sign VLP deposit/withdraw, stake/unstake/claim and vault create/deposit/withdraw/close/order ops (the list above). Withdrawals and claims among them pay the owner's own balance (never a third address); a deposit moves the owner's funds into a pool or a vault, where the vault LEADER trades them — and a leader's session key can place and cancel that vault's orders with no agent check. The vault registry is shut today (control key 253).

## Expiry

- policy: SetAgentPolicy.expires_ms — enforced by the policy gate (block time); no maximum
- record: RegisterAgent.expires_ms — stored and served, NOT enforced; status 'expired' is never assigned
- session: SessionCreate.expires_at (seconds) — max now + the compiled session horizon (or chain-param 241)
- atExpiry: policy gate refuses with 'agent: policy expired'; an expired session key does not verify
- The clock is the block timestamp (milliseconds; seconds for sessions), identical on every validator. No maximum bounds a policy's or a record's `expires_ms`.

## Nonces

- RegisterAgent, RevokeAgent, SetAgentPolicy and SetAgentMarketLimit share ONE counter per (owner, agent): `AgentRecord.last_nonce`. Each op needs `nonce > last_nonce`; the first registration accepts any nonce. There is no jump cap, so a UNIX-millisecond timestamp is a valid nonce. Revoke keeps the record, so the counter survives it.
- SetAgentCaps and SetAgentMode carry **no nonce** in their signed type.
- SessionCreate / SessionRevoke use the owner's session nonce (a separate counter). A create at nonce 0 is refused.

## Name / label

No name/label field on chain; `mandate` is public free text bounded only by the 8 KiB intake body. The registry's `status` is `active`, `revoked` or `expired`; `expired` is never assigned today.

## How the limits are enforced (policy gate order, when ON)

The agent policy check runs for orders; the agent op check runs for cancel/modify/TP-SL/transfer. Owner-signed and system ops are never gated. In order, the order gate refuses with:

1. `agent: no policy (deny by default)`
1. `agent: policy disabled`
1. `agent: policy expired`
1. `agent: capability not granted`
1. `agent: tripped (reduce-only rest of window)`
1. `agent: reduce-only side mode`
1. `agent: outside active window`
1. `agent: market not allowed`
1. `agent: max order (market)`
1. `agent: max position (market)`
1. `agent: max leverage (market)`
1. `agent: pair not in allowlist`
1. `agent: max leverage (overall)`
1. `agent: max total notional`
1. `agent: ops-per-window`
1. `agent: fee cap window`
1. `agent: daily loss limit → tripped`
1. `agent: drawdown breaker → tripped`

- The market allowlist applies only once a market row exists for the (owner, agent); from then on an unlisted pair is refused, and **no op deletes a row**, so allowlist mode is permanent for that pair of keys.
- A trip (daily loss or drawdown) makes the agent reduce-only until the window rolls. The window defaults to 86400000 ms when 0.
- Loosening any policy dimension is owner-only and waits 3600000 ms after the previous raise (the first raise is exempt). The apply path would also accept an AGENT-signed tightening, but intake and gossip admit only the owner's own signature, so that path is unreachable today.

Legacy caps gate refusals (governing today):

- `agent mode OFF`
- `agent REDUCE_ONLY: order must reduce position`
- `agent mode invalid`
- `agent caps unset`
- `agent order type not allowed`
- `agent leverage over cap`
- `agent input over cap`
- `agent position over cap`

## Reading an agent

- `GET https://rpc.vordium.com/agents/<owner>` — every agent of the owner: agent, status, mandate, expires_ms, has_policy.
- `GET https://rpc.vordium.com/agents/<owner>/<agent>` — status, mandate, created_ms, expires_ms, policy, market_limits, accounting (committed state; `found:false` when unknown).
- A revoked agent is returned with `status: "revoked"` and its policy `enabled: false`. Nothing is ever deleted.
- **Missing:** there is no public read of the legacy caps (`SetAgentCaps`) or mode (`SetAgentMode`).

## Refusals you can see

- `202` {"success":true,"status":"submitted","intaken":bool} — accepted into the mempool, NOT applied
- `400` {"error":"invalid body","details":…}
- `403` {"error":"bad_signature"|"malformed_signature"|"not_public"}
- `413` {"error":"payload exceeds 8KiB"}
- `429` {"error":"mempool full"}

## Example vectors (throwaway keys — never fund them)

Keys are `sha256(label)` for the labels `vordium-public-test-key:agent-ops:owner` (owner `0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551`) and `vordium-public-test-key:agent-ops:agent` (agent `0x705b803E72B85900854704C9917bA11FFD24d3c6`). Domains are bound to the genesis: VordCore `0x8590981a62e73d4fe04427a68536a1a63f3acb4765e41116859ab126c20099a2` salt, VordexSession `0xf330ba59148d525b0270023bba26e37f3897e9d497970b34facb4da84c4b1935` salt; the salt is `keccak256(tag ‖ 32 raw genesis bytes)`. Signatures are 65 bytes r‖s‖v over the raw EIP-712 digest.

The node has no read-only path that verifies these ops, so each vector was checked against the node's own pinned unit-test digests: both domain separators and all six VordCore types match their pins, every signature recovers to its signer, and the four already published in `vectors/agent-ops-vectors-2c1c0679.json` re-derive byte-for-byte.

| op | message | digest | signature (owner key) | accepted? |
|---|---|---|---|---|
| RegisterAgent | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","mandate":"mm","expiresMs":"1","nonce":"7"}` | `0x478e7c8229636b5d5762c5ba9c5fe38756169d8dce313f84b15a1fb55b1df486` | `0xefaa424900a3f9546a00e78ef95d3ea2fd874736992259073c948c47aed0902425310551151ec09d471fdd7c792c1720eb0f2650b731f9fe854d1affb64880681b` | yes, if nonce > stored |
| RevokeAgent | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","nonce":"7"}` | `0xf76493bc40d05b92747aa469b59770053724fe434d872bf815ae65f56d1ac5a0` | `0xc41df46134bc84dd8b790ac3ca2fdd5262173765feacb17e71afdc44363d28d803d0299a9bb4b942a9dc0e01330140b65db7a3fdcc3e1c30f46ae03adbe3cdc41b` | yes, if registered and nonce > stored |
| SetAgentPolicy | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","capsBitmask":"3","sideMode":"0","maxTotalNotional6dec":"1000000","maxLeverageOverallBps":"50000","dailyLossLimit6dec":"500000","drawdownBps":"1000","feeCapWindow6dec":"100000","opsPerWindow":"100","windowLenMs":"86400000","activeFromMsOfDay":"0","activeToMsOfDay":"0","expiresMs":"9999999999","enabled":true,"nonce":"7"}` | `0xc6eee8986bb9e0d062ad37b353d10d3da8a0f9a76c4b866b57c6ddaa7ea3458e` | `0x214dfe712da2cd4e3cb2ad3e67f520d8d4c81c667a45e74465e27955dd1cafa12d29c0f831140cce171d4d7c9945098fe842031823b95b2e73db5ca64ee5dda51c` | yes, owner-signed |
| SetAgentMarketLimit | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","pair":"1","allowed":true,"maxOrder18dec":"1000000000000000000","maxPosition18dec":"2000000000000000000","maxLeverageBps":"50000","nonce":"7"}` | `0x003410b2c080b32bbc47b7b92759fbd8eb0c240df3c86e954cd7785fc9536117` | `0x0f0d31d419bf6e60e216a7a607078aaa6b5b700cc043c206dd82610e9d9f53f706a853ddbaa30177717cc06f0ff0edbc3208587b86ce86e0bb4121f6d0709b301c` | yes, if registered and active |
| SetAgentCaps | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","maxLeverage":"10","allowedOrderTypes":"3","maxInputPerTrade":"100000000","maxTotalPosition":"1000000000"}` | `0x0d84d19f43104cfa18f464e5267dd551aa9463c9cf907893e132f18aa2bfdc70` | `0x4200147b7e57dcc7b0d064c1367f3d009a73e29e1c9ea025d95747ffc30113723c4b9730e28f9237afccaeec9f016fbac3a8cafb9a39baae0fb2b6f1568a638a1c` | yes (no nonce) |
| SetAgentMode | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","mode":"2"}` | `0xf46facaa1fee6192f44ab6f118e2548adb99c43898ef8dd9de07148afd7261c0` | `0x78a6305323da37f7dab42389a5337c217cf2dbbf1f28c729a6a9f02c0a23950978e18f5080fd1fb8190f44db30c71c5c623f56098fcbe9f7ac3c3335b384be841c` | yes (no nonce) |
| SessionCreate | `{"sessionKey":"0x705b803E72B85900854704C9917bA11FFD24d3c6","expiresAt":"1790000000","nonce":"1"}` | `0xf7af226eb60e3d80479e185cedda9d61dcfddd81432d17c94923a81cac92f47f` | `0x2acf0101519d745ceffe5467d1bd7fe3d9f1f186c71b810abfdf4eca64a34738498b7877eac250b6226971d43b69a970a3376b18b13e66f45a03b079d2fef1e91c` | yes, if expiresAt within the horizon and nonce > stored |
| SessionRevoke | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","nonce":"2"}` | `0x73d4e57f57ef21acf06bd8bce875029a174d078a9a65cb89fc086e9bca1e682c` | `0xc203f1460da0ac4debd660142d81daa0588285847ef3577de16b0c0955db9b4e49cfe66bdff3a61556e7668b85881355d04ae00c6518edb0f90ca754824879121c` | yes, if nonce > stored |

The same digests signed by the agent key recover to the agent address and are refused for every op above (for SetAgentPolicy: refused at intake and gossip, which admit only the owner's own signature). The SessionCreate vector's `expiresAt` illustrates the encoding only: a real create needs block time < expiresAt ≤ block time + 7776000 s.


_Generated from node binary `db6d34f8`; network-spec v19._
