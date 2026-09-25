# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release — `1205b19080d08893`
| artefact | name | sha256 |
|---|---|---|
| node binary | `1205b19080d08893` (also served as `vordium-1205b19080d08893`) | `1205b19080d088930c6574540b622a3f78c9cb9c8ba3d3cf6f8b80addbdbf50c` |
| signed manifest | `SHA256SUMS.1205b19080d08893` + `SHA256SUMS.1205b19080d08893.asc` | `0e586d2817658eeb56f849468f79aa9acd717568cd247e192186bdd95eca96a0` (manifest file) |
| visor | `vordium-visor` (unchanged; now listed in the release manifest) | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` (unchanged) | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

What this release changes (node-local behaviour only):
- **Batch pacing.** The batch coordinator waits only for each leader's first slot (the slots that can arrive), and the
  pacemaker records success when the batch certificate commits, so a batch no longer closes on the slot timeout.
- **Owner-only operations.** A session key may not move funds. `VordTransfer`, `WithdrawalRequest`, `VlpDeposit`,
  `VlpWithdraw`, `Stake`, `Unstake`, `CreateVault`, `VaultDeposit`, `VaultWithdraw`, `VaultClose`, `AirdropClaim`,
  `VestingClaim` and `ClaimReferralEarnings` must be signed by the owner's own key; a session-key signature is refused
  at intake with `this op must be signed by its owner — a session key may not move funds`.
- **Referral claims.** `POST /referral/claim` refuses (403) a claim the referrer did not sign, before it reaches the pool.
- **Public submit.** `RegisterValidator` is no longer accepted on the public `POST /submit`.
- **Pause routes.** `/admin/pause` and `/admin/unpause` are retired (410). `EmergencyPause`/`EmergencyUnpause` and the
  system-only kinds (`MatchOrder`, `LiquidationEvent`, `AdlExecution`, `FundingSettlement`, `SpotMatch`) are never
  pooled or admitted from gossip.
- **EVM JSON-RPC (`:9100`).** A read allow-list; `eth_getLogs` needs `fromBlock` and spans at most 10,000 blocks; a batch
  request carries at most 50 calls; `eth_call` to `0x…080B` answers an error instead of failing the request.
- **HTTP intake.** A request body cap, requests split across writes, and `Expect: 100-continue` are handled.

**No new activation height and no consensus rule change.** This release agrees with `0e49718dc0147cfd` block for block,
and a node can roll back to `0e49718dc0147cfd` at any height (no state or block-store format change).

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

The signed `SHA256SUMS.1205b19080d08893` lists the node binary under its manifest name `1205b19080d08893` and the visor
`vordium-visor` (`eb743997e563f1bc`). The signed node binary carries the genesis sha256 compiled in and refuses any
other genesis, so the genesis is pinned transitively. The release index `releases.json` is signed as well:
`releases.json.asc` (same release key C5EB4728F660369CE519D834B48FB4B71EFD48AE), at `binaries.vordium.com/Mainnet/` and
`rpc.vordium.com/`.

## Previous releases
| release | signed manifest | status |
|---|---|---|
| `0e49718dc0147cfd` | `SHA256SUMS.0e49718dc0147cfd` + `.asc` | superseded by `1205b19080d08893`. Same consensus rules and activation heights; a node may roll back to it at any height, but it has the earlier batch pacing and none of the intake changes above. |
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

