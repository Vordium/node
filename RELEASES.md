# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `0e49718dc0147cfd`
| artefact | name | sha256 |
|---|---|---|
| node binary | `0e49718dc0147cfd` (also served as `vordium-0e49718dc0147cfd`) | `0e49718dc0147cfd1e8e9f0322f93636fd31da2d3052ea79a849526d53931d0b` |
| signed manifest | `SHA256SUMS.0e49718dc0147cfd` + `SHA256SUMS.0e49718dc0147cfd.asc` | `82e7cc7117eb4dc167e41c82a5ce92daaa33a4e9099bb589cddb482305994510` (manifest file) |
| visor | `vordium-visor` (unchanged) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

What this release adds (node-local behaviour only):
- **Proposal persistence.** A validator records each slot proposal it signs in `data/chain/last_slot_proposals.json`,
  durably, before it broadcasts it. After a restart it re-sends the identical proposal or abstains, so a restarted
  leader never proposes different content for the same slot. Treat the file like `last_signed.json`: never delete it
  on a running validator.
- **Finalized batch membership.** `GET /batch/{n}` and `GET /batches?from_height=&to_height=` (batch heights, at most
  1000 per call) on the node's HTTP port list each committed batch's member blocks — hashes in the order the finalized
  batch certificate lists them, with their heights. A batch that is not committed yet answers 404.

**No new activation height and no consensus rule change.** This release agrees with `bddf26dbac2bfb0a` block for block,
and a node can roll back to `bddf26dbac2bfb0a` at any height (no state or block-store format change).

**Activation heights** — unchanged. Every node's `config/node.toml` `[consensus]` must carry exactly these values (both
are in `config/node.toml.template`):
- `aa1998_activation_height = 625000` (from release `22f590437dec5b67`): a one-year lock on owner-seeded validator
  seats, and airdrop tranches funded from the Airdrop bucket with the claim window latched on the armed emission
  anchor.
- `aa2001_activation_height = 845000` (from release `bddf26dbac2bfb0a`): the timelock seal fix. From block 845000 a
  per-operation timelock override must name the operation's real tier (the stricter tier for an operation whose tier
  depends on direction), operations 100 (ConfigureTimelock) and 101 (SealTimelocks) carry no per-operation override,
  and a queued owner operation whose tier has changed since it was queued must wait its new tier's delay before it can
  execute.

The signed `SHA256SUMS.0e49718dc0147cfd` covers the node binary under its manifest name `0e49718dc0147cfd`; the
signed node binary in turn carries the genesis sha256 compiled in and refuses any other genesis, so the genesis is
pinned transitively. The visor's hash is published here and in `releases.json` (unsigned — see the honest limit in
`SECURITY.md`).

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `bddf26dbac2bfb0a` | `SHA256SUMS.bddf26dbac2bfb0a` + `.asc` | superseded by `0e49718dc0147cfd`. Same consensus rules and activation heights; a node may roll back to it at any height, but it has no proposal persistence and no batch-membership routes. |
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

