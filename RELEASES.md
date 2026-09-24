# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `bddf26dbac2bfb0a`
| artefact | name | sha256 |
|---|---|---|
| node binary | `bddf26dbac2bfb0a` (also served as `vordium-bddf26dbac2bfb0a`) | `bddf26dbac2bfb0a037693ed242d2ec0e13f126dbd6f0e9d0fff369e86234884` |
| signed manifest | `SHA256SUMS.bddf26dbac2bfb0a` + `SHA256SUMS.bddf26dbac2bfb0a.asc` | `bb7dfb8ab69b00b92e216c2b97bdbcd63f4126494b77db1ee16e257559440805` (manifest file) |
| visor | `vordium-visor` (unchanged) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

**Activation heights** — every node's `config/node.toml` `[consensus]` must carry exactly these values (both are in
`config/node.toml.template`):
- `aa1998_activation_height = 625000` (from release `22f590437dec5b67`): a one-year lock on owner-seeded validator
  seats, and airdrop tranches funded from the Airdrop bucket with the claim window latched on the armed emission
  anchor.
- `aa2001_activation_height = 845000` (this release): the timelock seal fix. From block 845000 a per-operation
  timelock override must name the operation's real tier (the stricter tier for an operation whose tier depends on
  direction), operations 100 (ConfigureTimelock) and 101 (SealTimelocks) carry no per-operation override, and a
  queued owner operation whose tier has changed since it was queued must wait its new tier's delay before it can
  execute. These rules apply only to operations executed at or after block 845000; below it the release behaves
  exactly like `22f590437dec5b67`.

The signed `SHA256SUMS.bddf26dbac2bfb0a` covers the node binary under its manifest name `bddf26dbac2bfb0a`; the
signed node binary in turn carries the genesis sha256 compiled in and refuses any other genesis, so the genesis is
pinned transitively. The visor's hash is published here and in `releases.json` (unsigned — see the honest limit in
`SECURITY.md`).

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `22f590437dec5b67` | `SHA256SUMS.22f590437dec5b67` + `.asc` | superseded by `bddf26dbac2bfb0a`. It does not implement the rules active from block 845000 and must not be run at or past that height. |
| `fa2af621c5c64bb9` (launch) | `SHA256SUMS` + `SHA256SUMS.asc` | superseded. It does not implement the rules active from block 625000 and must not be run at or past that height. |

The signed manifests and the binaries are served from `binaries.vordium.com`. The machine-readable index is
`releases.json` there.

## Signing vectors
| file | what | sha256 |
|---|---|---|
| `vectors/agent-ops-vectors-2c1c0679.json` | EIP-712 vectors for the four agent operations (RegisterAgent, RevokeAgent, SetAgentPolicy, SetAgentMarketLimit) on genesis `2c1c0679`: domain + salt rule, type strings/hashes, inputs, struct hashes, digests, and signed cases with the expected result (accepted / rejected). Keys in the file are PUBLIC TEST KEYS only. | `9b25f2456fdb83b669e8d4a72148149a124c9fb18c92353464def4d450be7665` |

The canonical digests are the node's own pinned test vectors; a client implementation must reproduce every digest
byte-for-byte before it signs anything for this network.

## How a release is cut
1. Build the node + visor in the pinned build image; record their sha256.
2. Write the release's manifest `SHA256SUMS.<sha16>`.
3. The keyholder signs it **offline** with the release key → `SHA256SUMS.<sha16>.asc`.
   The private signing key is never on a build box or a validator.
4. Publish `<sha16>` (+ the `vordium-<sha16>` alias), `SHA256SUMS.<sha16>` + `.asc`,
   `releases.json` (+ `.asc`) to `binaries.vordium.com`; tag this repo.

## How you verify a release
```
./vordium-visor pub_key.asc SHA256SUMS.<sha16> SHA256SUMS.<sha16>.asc \
    <sha16> <sha16> genesis.json genesis.sha256
```
Exit 0 = accept, 1 = refuse (read the `REFUSE[...]` line), 2 = usage.

