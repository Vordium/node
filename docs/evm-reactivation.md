# EVM reactivation — how it would be switched on, and what is not ready

_Generated from the running node binary `db6d34f8` and the live chain at spec 19 (2026-09-26T21:59:03Z). Machine-readable twin: `evm.reactivation` in https://rpc.vordium.com/network-spec.json. Nothing described here has been changed._

## State today

- `evmIsLive` = false, `evmLive` = false, `executionEnabled` = true.
- `executionEnabled: true` is the genesis capability; on its own it does nothing — batches and EvmBridgeDeposit return early while evm_live is false.
- The EVM state is part of the state root: evm_exec_state is a named subtree of the authoritative Merkle root (empty until something executes).
- `eth_getCode` returns `0x` for an address with no committed code because eth_getCode reads committed evm_exec_state only; the genesis `alloc` is never loaded (only evm_execution_enabled is read) and switching EVM execution on does not load it (genesis `alloc` read sites: 0).
- `EvmBridgeDeposit` is accepted at public `POST /submit`; while the EVM is not live it is a silent no-op (no funds move, nonce unused).

## The switch

- A global trading pause also halts the EVM.
- Not an activation height, not a genesis parameter, and not a new binary: the op exists in the running binary.

## Preconditions

| id | status | basis | evidence |
|---|---|---|---|
| determinism-across-7 | **not-demonstrated** | record | no multi-validator EVM execution run on record |
| evm-output-in-state-root | **met-structurally** | source | evm_exec_state is committed under the authoritative root; empty today |
| parent-hash-semantics | **not-ethereum-compatible** | live-probe | batch 891699: 7 blocks, 9 null heights, 1 distinct parentHash; consecutive blocks linked: false |
| gas-model | **partial** | live-probe | EIP-1559 base fee unified with native transfers; eth_feeHistory(4) returned 1 bucket(s) |
| public-rpc-write-acceptance | **refused** | live-probe | eth_sendRawTransaction on the public EVM lane; the lane answers an allow-list of read methods, and a write needs evm_live AND a node-operator switch that is off by default (writes are disabled on the public RPC) |
| precompile-080b | **met** | source | every read precompile, 0x…080B included, answers eth_call through one table: a result or a precompile error |
| external-review | **none-on-record** | record | the only audit report in the tree is the upstream reth assessment, not Vordium's EVM |

A library that walks the chain by `parentHash`, recomputes a header hash, or asks `eth_feeHistory` for more than one block will not behave as on Ethereum. Check ethers, viem, Foundry and Hardhat against those behaviours before the switch.

_Generated from node binary `db6d34f8`; network-spec v19._
