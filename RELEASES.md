# Releases

The chain a node joins is identified by its **genesis sha256**, never by chain id alone
(chain id 101101 is reused across relaunches). `genesis_sha256` is the discriminator every
consumer keys on — the node's `/status`, `seeds.json`, `releases.json`, and the visor's
`genesis.sha256` check.

Current network genesis: `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`

## Current release
| artefact | name | sha256 |
|---|---|---|
| node binary | `fa2af621c5c64bb9` (also served as `vordium-fa2af621c5c64bb9`) | `fa2af621c5c64bb9ecf09c1fbbc851b61a1eb8140a9dc3bcfcc6379af3207421` |
| visor | `vordium-visor` | `eb743997e563f1bc772ca2ec9518613cfb6c2e64f0c1046b72531d9a64634ed7` |
| genesis | `genesis.json` | `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f` |

The signed `SHA256SUMS` for this release covers the node binary under its manifest name `fa2af621c5c64bb9`; the signed
node binary in turn carries the genesis sha256 compiled in and refuses any other genesis, so the
genesis is pinned transitively. The visor's hash is published here and in `releases.json`
(unsigned — see the honest limit in `SECURITY.md`).

The signed manifest `SHA256SUMS` (+ `SHA256SUMS.asc`) and the binaries are served from
`binaries.vordium.com`. The machine-readable index is `releases.json` there.

## How a release is cut
1. Build the node + visor in the pinned build image; record their sha256.
2. Write `SHA256SUMS` (node, visor, genesis).
3. The keyholder signs `SHA256SUMS` **offline** with the release key → `SHA256SUMS.asc`.
   The private signing key is never on a build box or a validator.
4. Publish `<sha16>` (+ the `vordium-<sha16>` alias), `vordium-visor`, `SHA256SUMS`, `SHA256SUMS.asc`,
   `releases.json` (+ `.asc`) to `binaries.vordium.com`; tag this repo.

## How you verify a release
```
./vordium-visor pub_key.asc SHA256SUMS SHA256SUMS.asc \
    <sha16> <sha16> genesis.json genesis.sha256
```
Exit 0 = accept, 1 = refuse (read the `REFUSE[...]` line), 2 = usage.

