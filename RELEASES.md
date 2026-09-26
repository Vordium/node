# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `ef49928485806dee`
| artefact | name | sha256 |
|---|---|---|
| node binary | `ef49928485806dee` (also served as `vordium-ef49928485806dee`) | `ef49928485806dee7b7acb93db1af48feaa3d784adf6945ae95785f46fc1d72a` |
| signed manifest | `SHA256SUMS.ef49928485806dee` + `SHA256SUMS.ef49928485806dee.asc` | `4d9649474d472d4858ac171ac30774ade269af0b8d76be1addff8ba1f809ddbf` (manifest file) |
| visor | `vordium-visor` (unchanged; listed in the release manifest) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

What this release changes now (node-local only — new reads and when a block is built, never what a batch contains or how
a vote is decided):
- **Trading records.** After every committed block and every batch the node derives records from committed state —
  an order placed (with the order id the chain assigned, beside the signed client nonce), an order updated or closed
  (filled / cancelled / expired, with the reason), each fill (both sides' order ids, the fee paid and where its rate
  comes from, the taker's realised PnL), funding payments, liquidations, TWAP placed / progress / ended, agent events —
  into the node's own store (not chain state), kept for the node's block retention. Reads: `GET /block/{n}/events`,
  `/events/range`, `/events/account/{addr}`, `/events/agent/{addr}`, `/events/coverage`; `/twaps/{addr}` reads
  committed state. Every answer carries its coverage; a node that restored a snapshot lists the skipped heights as a gap.
- **`/funding/{pair}`** reads the committed funding schedule (next settlement = the last one + 1 hour; the rate is for
  one 1-hour interval). **`/status`** carries `withdrawal_fee_usdc_6dec` and `withdrawal_min_gross_usdc_6dec`.
- **Block building waits for a finished batch.** A slot leader no longer builds a new block while the previous batch is
  still being applied, and first finishes a batch it received block by block, so the parent root it stamps is final
  (before this, a node could log one `state_root divergence` at such a batch and then reconcile).

**Changes that activate at a height — not active.** As in `0796cc84877b96fe`, this release carries rule changes that take effect only
from the height set by `[consensus] aa2007_activation_height`. That height has not been chosen: do **not** add the key
(an earlier release refuses a `node.toml` that carries it). Without the key this release agrees with `0796cc84877b96fe` block for
block, and a node can roll back to `0796cc84877b96fe` at any height. The height, and the changes it activates, will be published in a
later signed release index and described here.

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

The signed `SHA256SUMS.ef49928485806dee` lists the node binary under its manifest name `ef49928485806dee` and the visor `vordium-visor`
(`eb743997e563f1bc`). The signed node binary carries the genesis sha256 compiled in and refuses any other genesis, so the
genesis is pinned transitively. The release index `releases.json` (+ `releases.json.asc`, same release key
C5EB4728F660369CE519D834B48FB4B71EFD48AE) at `binaries.vordium.com/Mainnet/` and `rpc.vordium.com/` names `ef49928485806dee` as
current and `0796cc84877b96fe` as its rollback.

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `0796cc84877b96fe` | `SHA256SUMS.0796cc84877b96fe` + `.asc` | superseded by `ef49928485806dee`. Same consensus rules and activation heights while `aa2007_activation_height` is unset; a node may roll back to it at any height until that key is set, but it serves no trading records, its `/funding/{pair}` answers a rolling next time, and a leader can stamp a parent root before the batch is finished (one `state_root divergence` line, then it reconciles). |
| `8f3414f5d39a95b8` | `SHA256SUMS.8f3414f5d39a95b8` + `.asc` | superseded by `0796cc84877b96fe`. Same consensus rules and activation heights while `aa2007_activation_height` is unset; a node may roll back to it at any height until that key is set, but its vote check can refuse an honest batch proposal after the node falls behind (one lost vote; the batch still finalizes). |
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

