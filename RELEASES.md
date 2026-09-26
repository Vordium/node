# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `db6d34f81ae52174`
| artefact | name | sha256 |
|---|---|---|
| node binary | `db6d34f81ae52174` (also served as `vordium-db6d34f81ae52174`) | `db6d34f81ae52174b6731619d00e96c6cd4d3a8a44b95403c57079b242ea9415` |
| signed manifest | `SHA256SUMS.db6d34f81ae52174` + `SHA256SUMS.db6d34f81ae52174.asc` | `a906a8e46538c9703c8cf740f5fdabce9d35d3a5258103a88b6c8a1072c554ab` (manifest file) |
| visor | `vordium-visor` (unchanged; listed in the release manifest) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

What this release changes now (node-local only — never what a batch contains or how a vote is decided):
- **Owner-operation digests on `/block/{n}/ops`.** Each owner-operation envelope carries `op_digest` — the digest the
  owners signed, which is also the key of the operation in the timelock queue — with `inner_op_bytes` and `inner_hash`.
  Execute and cancel operations carry `op_digest_hex`, so a queued operation, its execution and its cancellation link up.
- **Compressed block store.** The block store's main column family is LZ4-compressed for newly written files (it was
  uncompressed), as is the trading-records store. Older files are rewritten compressed as compaction reaches them. Earlier
  releases read the compressed files.
- **`/orders/{addr}` reads committed state.** It lists the account's resting orders as the chain holds them, with the
  signed `client_nonce`, the exact 8-decimal price, leverage, reduce-only / post-only, time in force, reserved margin,
  agent and TWAP id. Stop orders held by the node are still listed (`is_stop`, `confirmed:false`).

**Roll B activates at block 28300000.** This release sets `[consensus] aa2007_activation_height = 28300000` (the rules ship
in every release since `8f3414f5d39a95b8`; this is the release that sets the height). From block 28300000:
- every EIP-191 admin message carries `Genesis: <genesis sha256>` as its third line, and raw-tag digests bind the genesis;
  a message signed the old way is refused from that height (there is no overlap window);
- clients must not sign a direct message within 3,000 blocks below the height;
- the rest of the Roll B rule set applies.
The height is published in the signed `releases.json` (activation key `aa2007_activation_height`). Wallets, the SDK and
tools read it from there.

**Activation heights.** Every node's `config/node.toml` `[consensus]` must carry exactly these values (all three are in
`config/node.toml.template`):
- `aa1998_activation_height = 625000` (from release `22f590437dec5b67`): a one-year lock on owner-seeded validator
  seats, and airdrop tranches funded from the Airdrop bucket with the claim window latched on the armed emission
  anchor.
- `aa2001_activation_height = 845000` (from release `bddf26dbac2bfb0a`): the timelock seal fix. From block 845000 a
  per-operation timelock override must name the operation's real tier (the stricter tier for an operation whose tier
  depends on direction), operations 100 (ConfigureTimelock) and 101 (SealTimelocks) carry no per-operation override,
  and a queued owner operation whose tier has changed since it was queued must wait its new tier's delay before it can
  execute.
- `aa2007_activation_height = 28300000` (set by this release): Roll B, above. A node without it, or with another value,
  diverges at 28300000. A release older than `8f3414f5d39a95b8` refuses a `node.toml` that carries it.

**Rolling back.** Before block 28300000 a node may roll back to `ef49928485806dee` with or without the key. At or after
it, the only rollback is `ef49928485806dee` with the key kept; never remove the key, and never run a release older than
`8f3414f5d39a95b8`.

The signed `SHA256SUMS.db6d34f81ae52174` lists the node binary under its manifest name `db6d34f81ae52174` and the visor `vordium-visor`
(`eb743997e563f1bc`). The signed node binary carries the genesis sha256 compiled in and refuses any other genesis, so the
genesis is pinned transitively. The release index `releases.json` (+ `releases.json.asc`, same release key
C5EB4728F660369CE519D834B48FB4B71EFD48AE) at `binaries.vordium.com/Mainnet/` and `rpc.vordium.com/` names `db6d34f81ae52174` as
current, `ef49928485806dee` as its rollback, and the three activation heights above.

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `ef49928485806dee` | `SHA256SUMS.ef49928485806dee` + `.asc` | superseded by `db6d34f81ae52174`. Carries the same Roll B rules behind the same key: before block 28300000 a node may roll back to it with or without the key; at or after it, only with the key kept. It serves no owner-operation digests on `/block/{n}/ops`, `/orders/{addr}` is its node-local book, and its block store's main column family writes uncompressed (it reads compressed files). |
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

