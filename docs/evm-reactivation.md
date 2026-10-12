# EVM — status and compatibility (mainnet, chain 101101)

Vordium's trading engine runs natively in consensus. The EVM execution layer is **not live** on mainnet: EVM
transactions are not executed and contracts cannot be deployed. The machine-readable twin is the `evm` section of
<https://rpc.vordium.com/network-spec.json>.

## What works today

- **A read-only EVM lane:** `https://rpc.vordium.com/evmrpc` answers standard JSON-RPC read methods (`eth_chainId`
  returns `0x18aed`, blocks, balances, logs and the like). An unsupported method answers JSON-RPC error `-32601`.
- **Writes are refused:** `eth_sendRawTransaction` answers `-32003` with *"transaction rejected: EVM transactions are not
  accepted on Vordium; use the app or the SDK"*. Trade, deposit and withdraw through the app or the SDK.
- **Two balance views:** on `/evmrpc` a balance is the EVM mirror (bridged VORD); on `https://rpc.vordium.com` it is
  native VORD.
- **Contract code reads as empty:** `eth_getCode` returns `0x` for every address, and `eth_call` against an address
  returns `0x`.
- `EvmBridgeDeposit` is accepted at the public intake (`POST https://rpc.vordium.com/submit`, signed by the depositor);
  while the EVM is not live it changes nothing (no funds move, the nonce is not used).

## Compatibility notes for EVM tooling

If you point ethers, viem, Foundry or Hardhat at the read lane, expect these differences from Ethereum:

- **`parentHash` does not link consecutive blocks.** A batch commits several blocks together and they report the same
  parent; some heights in a batch have no block (`null`). Do not walk the chain by `parentHash` or recompute header
  hashes.
- **`eth_feeHistory` returns a single bucket**, whatever block count you ask for.
- **Fees:** the base fee follows EIP-1559 and is shared with native transfers; trading ops pay no gas.

When the EVM goes live, the network spec and this page will say so.
