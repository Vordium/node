# Vordium node

Everything a validator operator needs to verify and run a Vordium node: the public release key, the signed release
index, the signed checksums for each release, the config templates and the systemd units. Text and config only —
no binaries, no source, no private keys.

## Choose your network

| network | chain id | folder | release channel |
|---|---|---|---|
| **Mainnet** | `101101` (0x18aed) | [`mainnet/`](mainnet/) | <https://binaries.vordium.com/mainnet> |
| **Testnet** | `101102` (0x18aee) | [`testnet/`](testnet/) | <https://binaries.vordium.com/testnet> |

Each folder has the same layout:

| path | what it is |
|---|---|
| `README.md` | the operator guide for that network |
| `config/` | config templates (paths and ports only — never keys) |
| `ops/` | systemd unit and the visor drop-in that verifies every start |
| `genesis.sha256` | the network's identity: the sha256 of its genesis file |
| `releases.json` + `.asc` | the signed release index (`current` is the release to run, each release names its rollback) |
| `SHA256SUMS.<id>` + `.asc` | the signed checksums of the current release and its rollback |

Binaries are served only from the release channel (`binaries.vordium.com`); the signed text files here are a mirror
you can check against it.

## Before anything else

- **One release key signs everything:** [`pub_key.asc`](pub_key.asc), fingerprint
  `C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE` (ed25519). If your copy shows another fingerprint, stop.
- **A network is identified by its genesis sha256, never by its chain id alone.**
- **Two keys:** a cold operator key that never touches the node box, and a hot validator key generated on the box.
  See [`SECURITY.md`](SECURITY.md).

Run a validator: <https://vordium.com/run-a-validator>

Reference: [`docs/agents.md`](docs/agents.md) (agent permissions) · [`docs/evm-reactivation.md`](docs/evm-reactivation.md)
(EVM status and compatibility) · [`vectors/`](vectors/) (signing test vectors).

Report security issues privately to security@vordium.com.
