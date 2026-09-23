# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `22f590437dec5b67`
| artefact | name | sha256 |
|---|---|---|
| node binary | `22f590437dec5b67` (also served as `vordium-22f590437dec5b67`) | `22f590437dec5b678d929b6a282cdcd5a1d358c4b6c7375c6482c0d94846ee5a` |
| signed manifest | `SHA256SUMS.22f590437dec5b67` + `SHA256SUMS.22f590437dec5b67.asc` | `f224a660c7b7505f834e4d905636b0673f8e98b7ff2bef149267f4146730332d` (manifest file) |
| visor | `vordium-visor` (unchanged) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

**Activation height: `aa1998_activation_height = 625000`** — every node's `config/node.toml` `[consensus]`
must carry exactly this value (it is in `config/node.toml.template`). The rules it gates — a one-year lock on
owner-seeded validator seats and airdrop tranches funded from the Airdrop bucket with the claim window latched on
the armed emission anchor — apply only to operations executed at or after block 625000. The release also fixes a
full-fleet restart and makes committed sessions report `confirmed: true` on every node (node-local, no height).

The signed `SHA256SUMS.22f590437dec5b67` covers the node binary under its manifest name `22f590437dec5b67`; the
signed node binary in turn carries the genesis sha256 compiled in and refuses any other genesis, so the genesis is
pinned transitively. The visor's hash is published here and in `releases.json` (unsigned — see the honest limit in
`SECURITY.md`).

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `fa2af621c5c64bb9` (launch) | `SHA256SUMS` + `SHA256SUMS.asc` | superseded by `22f590437dec5b67`. It does not implement the rules active from block 625000 and must not be run at or past that height. |

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

