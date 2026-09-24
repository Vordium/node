# Agent permissions — chain 101101, genesis `2c1c0679`

_Generated from the running node binary `0e49718d` (source commit `b68649651`, citations are `path:line` in that source) and the live chain at spec 9 (2026-09-24T15:30:27Z). Machine-readable twin: `agents` in https://rpc.vordium.com/network-spec.json._

## Status on the live chain today

- The agent **policy gate is OFF**: chain-param key 235 reads 0 (it enforces only when the value is 1; `crates/vordium-consensus/src/vordcore_state.rs:5512`).
- So `RegisterAgent`, `SetAgentPolicy` and `SetAgentMarketLimit` are accepted, stored and readable, but **nothing enforces them yet**.
- Orders signed by a session key go through the **legacy caps gate** instead (`crates/vordium-consensus/src/vordcore_state.rs:5419`). The genesis seeded default caps {"allowed_order_types": 3, "max_input_per_trade_usdc_6dec": "1000000000", "max_leverage": 5, "max_total_position_18dec": "10000000000000000000000"}. Their effect today: every session-key order is refused ('agent mode OFF') until the owner signs SetAgentMode; and genesis max_leverage 5 is compared against the order's leverage IN BPS, so any order at ≥ 1x (10000 bps) is refused ('agent leverage over cap') unless the owner sets explicit caps (`crates/vordium-consensus/src/vordcore_state.rs:5478`, `crates/vordium-consensus/src/vordcore_state.rs:1133`).
- Turning the policy gate on is `SetChainParam{key 235, value 1}` — a release direction: a 2-of-3 owner envelope with the T0a delay.
- An agent key signs as a **session key** of its owner: the chain recognises the owner key or one of the owner's live session keys, nothing else. `RegisterAgent` does not by itself let a key sign; the owner must also create a session for it.
- Every agent op is accepted at public `POST /submit` (body ≤ 8192 bytes, `crates/vordium-consensus/src/admin_submit.rs:83`). A `202` means the op entered the mempool, **not** that it applied. Every apply-path refusal is a silent no-op, and the only way to see it is that `GET /agents/…` does not change.

## Who signs what

| op | # | EIP-712 domain | signer | intake |
|---|---|---|---|---|
| RegisterAgent | 117 | VordCore | owner only (signature must recover to `owner`) | public POST /submit |
| RevokeAgent | 118 | VordCore | owner only | public POST /submit |
| SetAgentPolicy | 119 | VordCore | apply path: owner for a first policy or any loosening (+ cooldown); owner OR the agent key for a pure tightening. Intake and gossip admit an OWNER signature only, so an agent-signed tightening never reaches the apply path. | public POST /submit |
| SetAgentMarketLimit | 120 | VordCore | owner only | public POST /submit |
| SetAgentCaps | 18 | VordCore | owner only | session API POST /agent/caps — not exposed publicly |
| SetAgentMode | 19 | VordCore | owner only | session API POST /agent/mode — not exposed publicly |
| SessionCreate | 9 | VordexSession | owner (the struct names the session key; the owner is the recovered signer) | public POST /session/create |
| SessionRevoke | 10 | VordexSession | owner | public POST /session/revoke |

### RegisterAgent  (VordCoreOp #117, apply `crates/vordium-consensus/src/vordcore_state.rs:5728`)

EIP-712 type (VordCore domain, `crates/vordium-consensus/src/eip712_ops.rs:312`):

```
RegisterAgent(address owner,address agent,string mandate,uint64 expiresMs,uint64 nonce)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account the agent acts for; must be the signer | — | `crates/vordium-consensus/src/vordcore_op.rs:4715` |
| `agent` | `Address` | — | the agent key's address (one owner per ACTIVE agent) | — | `crates/vordium-consensus/src/vordcore_op.rs:4716` |
| `mandate` | `String` | — | public free-text description; the only text field | — | `crates/vordium-consensus/src/vordcore_op.rs:4717` |
| `expires_ms` | `u64` | UNIX milliseconds (block timestamp clock) | record expiry — stored and served, not enforced | not enforced — any value is accepted and stored | `crates/vordium-consensus/src/vordcore_op.rs:4718` |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid | `crates/vordium-consensus/src/vordcore_op.rs:4719` |

- oneOwnerPerAgent: `crates/vordium-consensus/src/vordcore_state.rs:5732`
- nonce: `crates/vordium-consensus/src/vordcore_state.rs:5736`
- firstRegistrationAnyNonce: no stored record ⇒ no nonce comparison (same line)

### RevokeAgent  (VordCoreOp #118, apply `crates/vordium-consensus/src/vordcore_state.rs:5746`)

EIP-712 type (VordCore domain, `crates/vordium-consensus/src/eip712_ops.rs:321`):

```
RevokeAgent(address owner,address agent,uint64 nonce)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account | — | `crates/vordium-consensus/src/vordcore_op.rs:4731` |
| `agent` | `Address` | — | the agent to revoke | — | `crates/vordium-consensus/src/vordcore_op.rs:4732` |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid | `crates/vordium-consensus/src/vordcore_op.rs:4733` |

- nonce: `crates/vordium-consensus/src/vordcore_state.rs:5750`
- effect: `crates/vordium-consensus/src/vordcore_state.rs:5751`
- disablesPolicy: `crates/vordium-consensus/src/vordcore_state.rs:5755`

### SetAgentPolicy  (VordCoreOp #119, apply `crates/vordium-consensus/src/vordcore_state.rs:5789`)

EIP-712 type (VordCore domain, `crates/vordium-consensus/src/eip712_ops.rs:336`):

```
SetAgentPolicy(address owner,address agent,uint32 capsBitmask,uint8 sideMode,uint128 maxTotalNotional6dec,uint32 maxLeverageOverallBps,uint128 dailyLossLimit6dec,uint32 drawdownBps,uint128 feeCapWindow6dec,uint64 opsPerWindow,uint64 windowLenMs,uint32 activeFromMsOfDay,uint32 activeToMsOfDay,uint64 expiresMs,bool enabled,uint64 nonce)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account | — | `crates/vordium-consensus/src/vordcore_op.rs:4746` |
| `agent` | `Address` | — | the agent this policy governs | — | `crates/vordium-consensus/src/vordcore_op.rs:4747` |
| `caps_bitmask` | `u32` | — | which op kinds the agent may sign (capability bits below) | OR of capabilityBits | `crates/vordium-consensus/src/vordcore_op.rs:4748` |
| `side_mode` | `u8` | — | 0 both sides, 1 reduce-only | 0 = both sides, 1 = reduce-only (any other value behaves as 0 — only 1 is tested) | `crates/vordium-consensus/src/vordcore_op.rs:4749` |
| `max_total_notional_6dec` | `u128` | USDC, 6 decimals | cap on the agent's open gross notional at mark + the new order (not applied to reducing orders) | 0 = dimension off (no cap) | `crates/vordium-consensus/src/vordcore_op.rs:4750` |
| `max_leverage_overall_bps` | `u32` | basis points (10000 = 1x / 100 %) | per-order leverage cap across all markets | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4751` |
| `daily_loss_limit_6dec` | `u128` | USDC, 6 decimals | window loss (realised + unrealised at mark) that trips the agent | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4752` |
| `drawdown_bps` | `u32` | basis points (10000 = 1x / 100 %) | drop below the window's equity high-water mark that trips the agent | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4753` |
| `fee_cap_window_6dec` | `u128` | USDC, 6 decimals | fees the agent may pay per window before placements stop | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4754` |
| `ops_per_window` | `u64` | — | placements allowed per window | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4755` |
| `window_len_ms` | `u64` | UNIX milliseconds (block timestamp clock) | length of the accounting window | 0 = 86,400,000 ms (24 h) | `crates/vordium-consensus/src/vordcore_op.rs:4756` |
| `active_from_ms_of_day` | `u32` | milliseconds since 00:00 UTC | start of the daily trading window (UTC) | from = to = 0 ⇒ always active; from = to ≠ 0 ⇒ never active | `crates/vordium-consensus/src/vordcore_op.rs:4757` |
| `active_to_ms_of_day` | `u32` | milliseconds since 00:00 UTC | end of the daily trading window (UTC, exclusive; wraps past midnight when from > to) | see active_from_ms_of_day | `crates/vordium-consensus/src/vordcore_op.rs:4758` |
| `expires_ms` | `u64` | UNIX milliseconds (block timestamp clock) | policy expiry (block time) | no 0-means-never: the gate refuses when block time ≥ expires_ms, so 0 = already expired | `crates/vordium-consensus/src/vordcore_op.rs:4759` |
| `enabled` | `bool` | — | false = the gate refuses everything for this agent | — | `crates/vordium-consensus/src/vordcore_op.rs:4760` |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid | `crates/vordium-consensus/src/vordcore_op.rs:4761` |

- requiresActiveRecord: `crates/vordium-consensus/src/vordcore_state.rs:5793`
- nonce: `crates/vordium-consensus/src/vordcore_state.rs:5794`
- loosenedWhen: `crates/vordium-consensus/src/vordcore_state.rs:5770`
- raiseCooldownMs: 3600000 (`crates/vordium-consensus/src/vordcore_state.rs:5765`)
- firstRaiseExempt: `crates/vordium-consensus/src/vordcore_state.rs:5800`
- agentMayTightenAtApply: `crates/vordium-consensus/src/vordcore_state.rs:5804`
- intakeOwnerOnly: `crates/vordium-consensus/src/admin_submit.rs:1429`
- gossipOwnerOnly: `crates/vordium-consensus/src/vordcore_state.rs:4618`

### SetAgentMarketLimit  (VordCoreOp #120, apply `crates/vordium-consensus/src/vordcore_state.rs:5820`)

EIP-712 type (VordCore domain, `crates/vordium-consensus/src/eip712_ops.rs:354`):

```
SetAgentMarketLimit(address owner,address agent,uint32 pair,bool allowed,uint128 maxOrder18dec,uint128 maxPosition18dec,uint32 maxLeverageBps,uint64 nonce)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account | — | `crates/vordium-consensus/src/vordcore_op.rs:4778` |
| `agent` | `Address` | — | the agent | — | `crates/vordium-consensus/src/vordcore_op.rs:4779` |
| `pair` | `u32` | — | market id | — | `crates/vordium-consensus/src/vordcore_op.rs:4780` |
| `allowed` | `bool` | — | false = explicit deny for this market | false on a present row = explicit deny | `crates/vordium-consensus/src/vordcore_op.rs:4781` |
| `max_order_18dec` | `u128` | base-asset size, 18 decimals | max size of one order in this market | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4782` |
| `max_position_18dec` | `u128` | base-asset size, 18 decimals | max |net position| after the order in this market | 0 = off | `crates/vordium-consensus/src/vordcore_op.rs:4783` |
| `max_leverage_bps` | `u32` | basis points (10000 = 1x / 100 %) | leverage cap in this market | 0 = off (per market) | `crates/vordium-consensus/src/vordcore_op.rs:4784` |
| `nonce` | `u64` | — | replay guard for (owner, agent) | strictly greater than the stored last_nonce (shared per (owner, agent) by all four L1/L2 ops); no jump cap; a UNIX-ms timestamp is valid | `crates/vordium-consensus/src/vordcore_op.rs:4785` |

- nonce: `crates/vordium-consensus/src/vordcore_state.rs:5825`
- noRemovalPath: no remove/retain/clear on agent_market_limit anywhere in the crate — once any row exists the (owner,agent) is in allowlist mode for good
- noRemovalEvidence: grep 'agent_market_limit.(remove|retain|clear)' → 0

### SetAgentCaps  (VordCoreOp #18, apply `crates/vordium-consensus/src/vordcore_state.rs:9478`)

EIP-712 type (VordCore domain, `crates/vordium-consensus/src/eip712_ops.rs:288`):

```
SetAgentCaps(address owner,uint64 maxLeverage,uint32 allowedOrderTypes,uint128 maxInputPerTrade,uint128 maxTotalPosition)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account (legacy caps are per OWNER, not per agent) | — | `crates/vordium-consensus/src/vordcore_op.rs:1726` |
| `max_leverage` | `u64` | bps as compared by the gate (field name says x) | compared against the order's leverage IN BPS (so 5 means 0.0005x, not 5x) | compared against leverage in bps | `crates/vordium-consensus/src/vordcore_op.rs:1727` |
| `allowed_order_types` | `u32` | — | bitmask of order types: bit 0 market, bit 1 limit | — | `crates/vordium-consensus/src/vordcore_op.rs:1728` |
| `max_input_per_trade` | `u128` | USDC, 6 decimals | max margin per order (USDC, 6 decimals; notional ÷ leverage) | — | `crates/vordium-consensus/src/vordcore_op.rs:1729` |
| `max_total_position` | `u128` | base-asset size, 18 decimals | max |net position| after the order (18 decimals) | — | `crates/vordium-consensus/src/vordcore_op.rs:1730` |

- noNonce: the op and its EIP-712 type carry no nonce — a signed body can be re-submitted and re-applied
- intake: `bin/vordium/src/bft.rs:1340`

### SetAgentMode  (VordCoreOp #19, apply `crates/vordium-consensus/src/vordcore_state.rs:9501`)

EIP-712 type (VordCore domain, `crates/vordium-consensus/src/eip712_ops.rs:303`):

```
SetAgentMode(address owner,uint8 mode)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account | — | `crates/vordium-consensus/src/vordcore_op.rs:1747` |
| `mode` | `u8` | — | 0 OFF (default), 1 REDUCE_ONLY, 2 ACTIVE; > 2 refused | default when never set: 0 (OFF) | `crates/vordium-consensus/src/vordcore_op.rs:1748` |

- noNonce: no nonce — replayable
- intake: `bin/vordium/src/bft.rs:1403`

### SessionCreate  (VordCoreOp #9, apply `crates/vordium-consensus/src/vordcore_state.rs:6880`)

EIP-712 type (VordexSession domain, `crates/vordium-consensus/src/session.rs:355`):

```
SessionCreate(address sessionKey,uint256 expiresAt,uint256 nonce)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account; recovered from the signature (not in the signed struct) | — | `crates/vordium-consensus/src/vordcore_op.rs:1143` |
| `session_key` | `Address` | — | the key being authorised — this is how an agent key gets to sign | — | `crates/vordium-consensus/src/vordcore_op.rs:1144` |
| `expires_at` | `u64` | UNIX seconds | UNIX SECONDS; at most now + the session horizon | must be ≤ block time + the session horizon; a past value makes the session inert | `crates/vordium-consensus/src/vordcore_op.rs:1146` |
| `nonce` | `u64` | — | per-owner session nonce; 0 refused | 0 is refused; otherwise strictly greater than the owner's stored session nonce | `crates/vordium-consensus/src/vordcore_op.rs:1147` |

- maxExpirySecs: 7776000 (`crates/vordium-consensus/src/vordcore_state.rs:141`)
- expiryCheck: `crates/vordium-consensus/src/vordcore_state.rs:6903`
- nonceZeroRefused: `crates/vordium-consensus/src/vordcore_state.rs:6914`
- nonce: `crates/vordium-consensus/src/vordcore_state.rs:6920`
- intake: `bin/vordium/src/bft.rs:1209`

### SessionRevoke  (VordCoreOp #10, apply `crates/vordium-consensus/src/vordcore_state.rs:6939`)

EIP-712 type (VordexSession domain, `crates/vordium-consensus/src/session.rs:452`):

```
SessionRevoke(address owner,uint256 nonce)
```

| field | type | units | meaning | zero / default | declared |
|---|---|---|---|---|---|
| `owner` | `Address` | — | the account (revokes the owner's sessions) | — | `crates/vordium-consensus/src/vordcore_op.rs:1153` |
| `nonce` | `u64` | — | per-owner session nonce | strictly greater than the owner's stored session nonce | `crates/vordium-consensus/src/vordcore_op.rs:1154` |

- intake: `bin/vordium/src/bft.rs:1294`

## Capability bits (`caps_bitmask`)

| bit | value | name | lets the agent key sign | declared |
|---|---|---|---|---|
| 0 | 1 | place | PlaceOrder that is not reduce-only (policy gate) | `crates/vordium-consensus/src/vordcore_state.rs:5503` |
| 1 | 2 | cancel | CancelOrder, CancelTwap | `crates/vordium-consensus/src/vordcore_state.rs:5504` |
| 2 | 4 | modify | ModifyOrder (also re-checked against the policy limits) | `crates/vordium-consensus/src/vordcore_state.rs:5505` |
| 3 | 8 | tpsl | SetTpSl | `crates/vordium-consensus/src/vordcore_state.rs:5506` |
| 4 | 16 | close | reduce-only PlaceOrder | `crates/vordium-consensus/src/vordcore_state.rs:5507` |

There is **no withdraw bit** (`crates/vordium-consensus/src/vordcore_state.rs:5502`). Where each capability is checked:

- `apply_cancel_order` → AGENT_CAP_CANCEL via `agent_op_authorized` (`crates/vordium-consensus/src/vordcore_state.rs:6312`)
- `apply_modify_order` → AGENT_CAP_MODIFY via `agent_op_authorized` (`crates/vordium-consensus/src/vordcore_state.rs:6402`)
- `apply_vord_transfer` → 0 via `agent_op_authorized` (`crates/vordium-consensus/src/vordcore_state.rs:6992`)
- `apply_cancel_twap` → AGENT_CAP_CANCEL via `agent_op_authorized` (`crates/vordium-consensus/src/vordcore_state.rs:7907`)
- `apply_set_tpsl` → AGENT_CAP_TPSL via `agent_op_authorized` (`crates/vordium-consensus/src/vordcore_state.rs:9100`)
- `apply_modify_order` → AGENT_CAP_MODIFY via `agent_policy_gate` (`crates/vordium-consensus/src/vordcore_state.rs:6411`)
- `apply_place_order` → AGENT_CAP_PLACE (AGENT_CAP_CLOSE when reduce_only) via `agent_policy_gate` (`crates/vordium-consensus/src/vordcore_state.rs:5982`)

Session-signed ops that run **no agent check at all**, even with the gate on: `apply_place_twap`, `apply_vlp_deposit`, `apply_vlp_withdraw`, `apply_stake`, `apply_unstake`, `apply_claim_staking_rewards`, `apply_create_vault`, `apply_vault_deposit`, `apply_vault_withdraw`, `apply_vault_close`, `apply_vault_place_order`, `apply_vault_cancel_order`. `apply_place_twap` matters most: a TWAP's children are placed as system orders and skip the policy gate.

## Can an agent withdraw or move funds?

- **Withdraw: never.** A withdrawal applies only if the EIP-712 `Withdraw` signature recovers to the OWNER over owner, destination, amount and nonce; session keys are not consulted in any switch state (`crates/vordium-consensus/src/vordcore_state.rs:6589`).
- **VORD transfer:** none — no route in bin/vordium builds a VordTransfer and AdminSubmitBody has no VordTransfer variant; the only other entry is validator gossip on the mesh-only /admin/query. On the apply path, refused for a session key only while the policy gate is ON (capability 0 is never granted); with the gate OFF the apply path accepts a session-key signature on VordTransfer (`crates/vordium-consensus/src/vordcore_state.rs:6987`, `crates/vordium-consensus/src/vordcore_state.rs:6992`, `crates/vordium-consensus/src/vordcore_state.rs:5707`). The policy gate is OFF today.
- Session keys can also sign VLP deposit/withdraw, stake/unstake/claim and vault create/deposit/withdraw/close/order ops (the list above). Withdrawals and claims among them pay the owner's own balance (never a third address); a deposit moves the owner's funds into a pool or a vault, where the vault LEADER trades them — and a leader's session key can place and cancel that vault's orders with no agent check. The vault registry is shut today (control key 253).

## Expiry

- policy: SetAgentPolicy.expires_ms — enforced by the policy gate (block time); no maximum
- record: RegisterAgent.expires_ms — stored and served, NOT enforced; status 'expired' is never assigned
- session: SessionCreate.expires_at (seconds) — max now + MAX_SESSION_EXPIRY_HORIZON_SECS (or chain-param 241)
- atExpiry: policy gate refuses with 'agent: policy expired'; an expired session key no longer verifies
- evidence for the record: AgentRecord.expires_ms has no read site in the apply path and status 2 ('expired') is never assigned (grep 'status = 2|status: 2' in crates/vordium-consensus/src/vordcore_state.rs → 0); policy check `crates/vordium-consensus/src/vordcore_state.rs:5598`.
- The clock is the block timestamp (milliseconds; seconds for sessions), identical on every validator. No maximum bounds a policy's or a record's `expires_ms`.

## Nonces

- RegisterAgent, RevokeAgent, SetAgentPolicy and SetAgentMarketLimit share ONE counter per (owner, agent): `AgentRecord.last_nonce`. Each op needs `nonce > last_nonce`; the first registration accepts any nonce. There is no jump cap, so a UNIX-millisecond timestamp is a valid nonce. Revoke keeps the record, so the counter survives it.
- SetAgentCaps and SetAgentMode carry **no nonce**: a signed body can be re-submitted and applies again.
- SessionCreate / SessionRevoke use the owner's session nonce (a separate counter). A create at nonce 0 is refused.

## Name / label

No name/label field on chain; `mandate` is public free text bounded only by the 8 KiB intake body. The registry's `status` is `active`, `revoked` or `expired`; `expired` is never assigned today.

## How the limits are enforced (policy gate order, when ON)

`agent_policy_gate` (`crates/vordium-consensus/src/vordcore_state.rs:5577`) runs for orders; `agent_op_authorized` (`crates/vordium-consensus/src/vordcore_state.rs:5692`) runs for cancel/modify/TP-SL/transfer. Owner-signed and system ops are never gated. In order, the order gate refuses with:

1. `agent: no policy (deny by default)` — `crates/vordium-consensus/src/vordcore_state.rs:5703`
1. `agent: policy disabled` — `crates/vordium-consensus/src/vordcore_state.rs:5705`
1. `agent: policy expired` — `crates/vordium-consensus/src/vordcore_state.rs:5706`
1. `agent: capability not granted` — `crates/vordium-consensus/src/vordcore_state.rs:5707`
1. `agent: tripped (reduce-only rest of window)` — `crates/vordium-consensus/src/vordcore_state.rs:5615`
1. `agent: reduce-only side mode` — `crates/vordium-consensus/src/vordcore_state.rs:5617`
1. `agent: outside active window` — `crates/vordium-consensus/src/vordcore_state.rs:5712`
1. `agent: market not allowed` — `crates/vordium-consensus/src/vordcore_state.rs:5631`
1. `agent: max order (market)` — `crates/vordium-consensus/src/vordcore_state.rs:5632`
1. `agent: max position (market)` — `crates/vordium-consensus/src/vordcore_state.rs:5633`
1. `agent: max leverage (market)` — `crates/vordium-consensus/src/vordcore_state.rs:5634`
1. `agent: pair not in allowlist` — `crates/vordium-consensus/src/vordcore_state.rs:5636`
1. `agent: max leverage (overall)` — `crates/vordium-consensus/src/vordcore_state.rs:5640`
1. `agent: max total notional` — `crates/vordium-consensus/src/vordcore_state.rs:5643`
1. `agent: ops-per-window` — `crates/vordium-consensus/src/vordcore_state.rs:5648`
1. `agent: fee cap window` — `crates/vordium-consensus/src/vordcore_state.rs:5652`
1. `agent: daily loss limit → tripped` — `crates/vordium-consensus/src/vordcore_state.rs:5661`
1. `agent: drawdown breaker → tripped` — `crates/vordium-consensus/src/vordcore_state.rs:5673`

- The market allowlist applies only once a market row exists for the (owner, agent); from then on an unlisted pair is refused (`crates/vordium-consensus/src/vordcore_state.rs:5636`), and **no op deletes a row**, so allowlist mode is permanent for that pair of keys.
- A trip (daily loss or drawdown) makes the agent reduce-only until the window rolls (`crates/vordium-consensus/src/vordcore_state.rs:5615`). The window defaults to 86400000 ms when 0 (`crates/vordium-consensus/src/vordcore_state.rs:5604`).
- Loosening any policy dimension is owner-only and waits 3600000 ms after the previous raise (the first raise is exempt). The apply path would also accept an AGENT-signed tightening, but intake and gossip admit owner signatures only, so that path is unreachable today.

Legacy caps gate refusals (governing today):

- `agent mode OFF` — `crates/vordium-consensus/src/vordcore_state.rs:1118`
- `agent REDUCE_ONLY: order must reduce position` — `crates/vordium-consensus/src/vordcore_state.rs:1121`
- `agent mode invalid` — `crates/vordium-consensus/src/vordcore_state.rs:1125`
- `agent caps unset` — `crates/vordium-consensus/src/vordcore_state.rs:1128`
- `agent order type not allowed` — `crates/vordium-consensus/src/vordcore_state.rs:1131`
- `agent leverage over cap` — `crates/vordium-consensus/src/vordcore_state.rs:1134`
- `agent input over cap` — `crates/vordium-consensus/src/vordcore_state.rs:1137`
- `agent position over cap` — `crates/vordium-consensus/src/vordcore_state.rs:1140`

## Reading an agent

- `GET https://rpc.vordium.com/agents/<owner>` — every agent of the owner: agent, status, mandate, expires_ms, has_policy.
- `GET https://rpc.vordium.com/agents/<owner>/<agent>` — status, mandate, created_ms, expires_ms, policy, market_limits, accounting (committed state; `found:false` when unknown; served at `bin/rpc-api/src/main.rs:621`).
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

| op | message | digest | owner signature | accepted? |
|---|---|---|---|---|
| RegisterAgent | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","mandate":"mm","expiresMs":"1","nonce":"7"}` | `0x478e7c8229636b5d5762c5ba9c5fe38756169d8dce313f84b15a1fb55b1df486` | `0xefaa424900a3f9546a00e78ef95d3ea2fd874736992259073c948c47aed0902425310551151ec09d471fdd7c792c1720eb0f2650b731f9fe854d1affb64880681b` | yes, if nonce > stored |
| RevokeAgent | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","nonce":"7"}` | `0xf76493bc40d05b92747aa469b59770053724fe434d872bf815ae65f56d1ac5a0` | `0xc41df46134bc84dd8b790ac3ca2fdd5262173765feacb17e71afdc44363d28d803d0299a9bb4b942a9dc0e01330140b65db7a3fdcc3e1c30f46ae03adbe3cdc41b` | yes, if registered and nonce > stored |
| SetAgentPolicy | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","capsBitmask":"3","sideMode":"0","maxTotalNotional6dec":"1000000","maxLeverageOverallBps":"50000","dailyLossLimit6dec":"500000","drawdownBps":"1000","feeCapWindow6dec":"100000","opsPerWindow":"100","windowLenMs":"86400000","activeFromMsOfDay":"0","activeToMsOfDay":"0","expiresMs":"9999999999","enabled":true,"nonce":"7"}` | `0xc6eee8986bb9e0d062ad37b353d10d3da8a0f9a76c4b866b57c6ddaa7ea3458e` | `0x214dfe712da2cd4e3cb2ad3e67f520d8d4c81c667a45e74465e27955dd1cafa12d29c0f831140cce171d4d7c9945098fe842031823b95b2e73db5ca64ee5dda51c` | yes, owner-signed |
| SetAgentMarketLimit | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","agent":"0x705b803E72B85900854704C9917bA11FFD24d3c6","pair":"1","allowed":true,"maxOrder18dec":"1000000000000000000","maxPosition18dec":"2000000000000000000","maxLeverageBps":"50000","nonce":"7"}` | `0x003410b2c080b32bbc47b7b92759fbd8eb0c240df3c86e954cd7785fc9536117` | `0x0f0d31d419bf6e60e216a7a607078aaa6b5b700cc043c206dd82610e9d9f53f706a853ddbaa30177717cc06f0ff0edbc3208587b86ce86e0bb4121f6d0709b301c` | yes, if registered and active |
| SetAgentCaps | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","maxLeverage":"10","allowedOrderTypes":"3","maxInputPerTrade":"100000000","maxTotalPosition":"1000000000"}` | `0x0d84d19f43104cfa18f464e5267dd551aa9463c9cf907893e132f18aa2bfdc70` | `0x4200147b7e57dcc7b0d064c1367f3d009a73e29e1c9ea025d95747ffc30113723c4b9730e28f9237afccaeec9f016fbac3a8cafb9a39baae0fb2b6f1568a638a1c` | yes (no nonce — replayable) |
| SetAgentMode | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","mode":"2"}` | `0xf46facaa1fee6192f44ab6f118e2548adb99c43898ef8dd9de07148afd7261c0` | `0x78a6305323da37f7dab42389a5337c217cf2dbbf1f28c729a6a9f02c0a23950978e18f5080fd1fb8190f44db30c71c5c623f56098fcbe9f7ac3c3335b384be841c` | yes (no nonce — replayable) |
| SessionCreate | `{"sessionKey":"0x705b803E72B85900854704C9917bA11FFD24d3c6","expiresAt":"1790000000","nonce":"1"}` | `0xf7af226eb60e3d80479e185cedda9d61dcfddd81432d17c94923a81cac92f47f` | `0x2acf0101519d745ceffe5467d1bd7fe3d9f1f186c71b810abfdf4eca64a34738498b7877eac250b6226971d43b69a970a3376b18b13e66f45a03b079d2fef1e91c` | yes, if expiresAt within the horizon and nonce > stored |
| SessionRevoke | `{"owner":"0x6e7f9Fc6CAAFA3A5Ebfd9f27c13C559afefEF551","nonce":"2"}` | `0x73d4e57f57ef21acf06bd8bce875029a174d078a9a65cb89fc086e9bca1e682c` | `0xc203f1460da0ac4debd660142d81daa0588285847ef3577de16b0c0955db9b4e49cfe66bdff3a61556e7668b85881355d04ae00c6518edb0f90ca754824879121c` | yes, if nonce > stored |

The same digests signed by the agent key recover to the agent address and are refused for every op above (for SetAgentPolicy: refused at intake and gossip, which admit owner signatures only). The SessionCreate vector's `expiresAt` illustrates the encoding only: a real create needs block time < expiresAt ≤ block time + 7776000 s.

## Known gaps (not changed)

- The policy gate is off, so registered policies and market limits are not enforced.
- The genesis default caps compare `max_leverage` 5 against leverage in bps, so every session-key order at 1x or more is refused while the legacy gate governs.
- SetAgentCaps and SetAgentMode have no nonce: a captured signed body can be replayed to restore an older mode or caps.
- `RegisterAgent.expires_ms` is not enforced and `expired` is never set.
- PlaceTwap and the vault/VLP/staking ops accept session keys with no agent check.
- The legacy caps and mode cannot be read publicly, and cannot be set through the public host.
- A market allowlist, once created, cannot be removed.

_Rendered by scripts/aa2005-render-docs.py from source commit `b68649651`; spec v9._
