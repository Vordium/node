# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `8f3414f5d39a95b8`
| artefact | name | sha256 |
|---|---|---|
| node binary | `8f3414f5d39a95b8` (also served as `vordium-8f3414f5d39a95b8`) | `8f3414f5d39a95b8491f6feea5d19bcaa3d641963af419551380ac1a77b15fc8` |
| signed manifest | `SHA256SUMS.8f3414f5d39a95b8` + `SHA256SUMS.8f3414f5d39a95b8.asc` | `ec23d96f2fd9a341e41706521ccc303d1d96c40b2de0629a6b11077e047b9641` (manifest file) |
| visor | `vordium-visor` (unchanged; listed in the release manifest) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

What this release changes now (node-local behaviour only):
- **Block sync finishes every batch.** A node that catches up by block sync, or replays its own blocks at boot, now
  finishes each synced batch exactly as the certified path does: the batch's oracle prices, its commit operations
  (bridge credits, matches, liquidations, auto-deleveraging, funding), then TP/SL, TWAP and spot. Before, such a node
  left each synced batch's oracle (and any synced funding settlement) unapplied and logged `state_root divergence` until
  it reconciled. Peers now send each batch's commit operations with the blocks; a peer on an earlier release does not,
  and the node then finishes that batch as before and counts it in the `batches_boundary_unknown` log field.

**Changes that activate at a height — not active.** This release also carries rule changes that take effect only from
the height set by `[consensus] aa2007_activation_height`. That height has not been chosen: do **not** add the key (an
earlier release refuses a `node.toml` that carries it). Without the key this release agrees with `1205b19080d08893`
block for block, and a node can roll back to `1205b19080d08893` at any height. The height, and the changes it
activates, will be published in a later signed release index and described here.

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

The signed `SHA256SUMS.8f3414f5d39a95b8` lists the node binary under its manifest name `8f3414f5d39a95b8` and the visor
`vordium-visor` (`eb743997e563f1bc`). The signed node binary carries the genesis sha256 compiled in and refuses any
other genesis, so the genesis is pinned transitively. The release index `releases.json` (+ `releases.json.asc`, same
release key C5EB4728F660369CE519D834B48FB4B71EFD48AE) at `binaries.vordium.com/Mainnet/` and `rpc.vordium.com/` names
`1205b19080d08893` as current until its update for this release is signed; both releases run on the network today.

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `1205b19080d08893` | `SHA256SUMS.1205b19080d08893` + `.asc` | superseded by `8f3414f5d39a95b8`. Same consensus rules and activation heights while `aa2007_activation_height` is unset; a node may roll back to it at any height until that key is set, but its block sync leaves synced batches unfinished (it logs `state_root divergence` after a catch-up, then reconciles). |
| `0e49718dc0147cfd` | `SHA256SUMS.0e49718dc0147cfd` + `.asc` | superseded by `1205b19080d08893`. Same consensus rules and activation heights; a node may roll back to it at any height, but it has the earlier batch pacing and none of the intake changes of `1205b19080d08893`. |
| `bddf26dbac2bfb0a` | `SHA256SUMS.bddf26dbac2bfb0a` + `.asc` | superseded by `0e49718dc0147cfd`. Same consensus rules and activation heights; a node may roll back to it at any height, but it has no proposal persistence and no batch-membership routes. |
| `22f590437dec5b67` | `SHA256SUMS.22f590437dec5b67` + `.asc` | superseded by `bddf26dbac2bfb0a`. It does not implement the rules active from block 845000 and must not be run at or past that height. |
| `fa2af621c5c64bb9` (launch) | `SHA256SUMS` + `SHA256SUMS.asc` (frozen: the plain name is the launch manifest and never lists a later release) | superseded. It does not implement the rules active from block 625000 and must not be run at or past that height. |

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

