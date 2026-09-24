# EVM reactivation — how it would be switched on, and what is not ready

_Generated from the running node binary `0e49718d` (source commit `b68649651`) and the live chain at spec 9 (2026-09-24T15:30:27Z). Machine-readable twin: `evm.reactivation` in https://rpc.vordium.com/network-spec.json. Nothing described here has been changed._

## State today

- `evmIsLive` = false, `evmLive` = false, `executionEnabled` = true, SetEvmLive nonce = 0.
- `executionEnabled: true` is the genesis capability; on its own it does nothing — batches and EvmBridgeDeposit return early while evm_live is false (`crates/vordium-consensus/src/vordcore_apply_engine.rs:501`, `crates/vordium-consensus/src/vordcore_state.rs:12008`).
- The EVM state is part of the state root: evm_exec_state is a named subtree of the authoritative Merkle root (empty until something executes).
- `eth_getCode` returns `0x` for the old contracts because eth_getCode reads committed evm_exec_state only; the genesis `alloc` is never loaded (only evm_execution_enabled is read) and SetEvmLive does not load it (`crates/vordium-evm/src/rpc.rs:835`, `crates/vordium-consensus/src/genesis_loader.rs:574`; genesis `alloc` read sites: 0). **Switching the EVM on would not bring those contracts back.**
- `EvmBridgeDeposit` is accepted at public `POST /submit`; while the EVM is not live it is a silent no-op (no funds move, nonce unused) (`crates/vordium-consensus/src/vordcore_state.rs:12008`).

## The switch

- **Mechanism:** owner op SetEvmLive (VordCoreOp #88), private intake /admin/dex/submit; flips state.evm_live.
- **Authority:** 2 distinct signatures of the compiled 3-owner set, direct (not an OwnerOp envelope) (`crates/vordium-consensus/src/vordcore_state.rs:12074`); the genesis capability must be on (`crates/vordium-consensus/src/vordcore_state.rs:12056`).
- **Tier / notice:** `immediate` — it applies in the block it lands in: no delay, so 0 days' notice (from the node's own prepare_owner_op answer, published in `authority.opTiers`).
- **Reversible:** true — the same op with live=false and a higher nonce (`crates/vordium-consensus/src/vordcore_state.rs:12077`). A global trading pause also halts the EVM.
- **Nonce:** strictly greater than the stored nonce (any gap allowed) (`crates/vordium-consensus/src/vordcore_state.rs:12059`).
- **Signed text:** `{h}\nChain: {c}\nAction: Set EVM Live\nLive: {l}\nNonce: {n}` (`crates/vordium-consensus/src/vordcore_op.rs:2990`). Binds genesis: false. The signed text carries chain id + nonce only, not the genesis — a 2-of-3 signature made on an earlier chain with the same chain id and a nonce above the current one would verify here.
- Not an activation height, not a genesis parameter, and not a new binary: the op exists in the running binary.

## Preconditions

| id | status | basis | evidence |
|---|---|---|---|
| determinism-across-7 | **not-demonstrated** | record | no multi-validator EVM execution run on record; the one prior flip (earlier chain, 2026-09-20) executed 0 EVM transactions |
| evm-output-in-state-root | **met-structurally** | source | evm_exec_state is committed under the authoritative root; empty today |
| parent-hash-semantics | **not-ethereum-compatible** | live-probe | batch 110493: 7 blocks, 9 null heights, 1 distinct parentHash; consecutive blocks linked: false |
| gas-model | **partial** | live-probe | EIP-1559 base fee unified with native transfers; eth_feeHistory(4) returned 1 bucket(s) |
| public-rpc-write-acceptance | **refused** | live-probe | eth_sendRawTransaction on the public EVM lane; the lane has no method filter, so writes open the moment evm_live flips — `crates/vordium-evm/src/rpc.rs:930` |
| precompile-080b | **defect** | source | eth_call to 0x…080B hits `_ => unreachable!()` (index 11 not handled) — the connection task panics — `crates/vordium-evm/src/rpc.rs:1138` |
| external-review | **none-on-record** | record | the only audit report in the tree is the upstream reth assessment, not Vordium's EVM |

A library that walks the chain by `parentHash`, recomputes a header hash, or asks `eth_feeHistory` for more than one block will not behave as on Ethereum. Check ethers, viem, Foundry and Hardhat against those behaviours before the switch.

_Rendered by scripts/aa2005-render-docs.py from source commit `b68649651`; spec v9._
