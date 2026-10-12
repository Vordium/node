# Security model

## The one rule
A validator runs nothing it has not verified against a key published before the binary
existed. `vordium-visor` enforces this at every start; it is the trust root, not a
convenience. Its pinned release fingerprint is compiled in:
`C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE` (ed25519, expires 2028-09-11).

The visor refuses to continue unless all four hold, at **every** start:
1. the node binary's hash is in the release's signed `SHA256SUMS.<id>`, under the name the manifest uses;
2. `SHA256SUMS.<id>.asc` is a good signature **by the pinned key and no other** (a good signature
   from a different key is the attack, and is refused by fingerprint — not accepted);
3. `genesis.json` (delivered privately to admitted validators) matches the published `genesis.sha256`;
4. `pub_key.asc` carries the pinned fingerprint (checked first; nothing else means anything
   without it).

Each release manifest `SHA256SUMS.<id>` also lists the visor binary itself, signed by the same key. Check the
manifest's signature and the visor's hash by hand once, before you install the visor.

Honest limit: once installed, nothing re-checks the visor itself. An attacker who is already
root on your box can replace it. The visor raises the cost of a swapped *release*; it
is not a defense against a compromised host. Protect root access accordingly.

## Two-key model
- **Operator key (cold, offline).** Registers and bonds the validator. Moves
  value. Never on the node box, never in a config file.
- **Validator hot key (on the box).** Signs blocks/votes via the local signer. Holds no funds,
  cannot move the bond. Compromise → jail + rotate, not loss of stake.

No private key of any kind belongs in this repository, a config file, or an env file. Configs
reference key *files* you place with `0600` permissions; the release ships only the public key.

## Reproducibility
Releases are built in a pinned, content-addressed container image and are **reproducible
internally** — the same source in that image rebuilds the same bytes, which is how the release
hashes in each `SHA256SUMS.<id>` are produced and cross-checked before signing. Public build-from-source
reproducibility is not offered for this closed-binary distribution; your trust rests on the
signature over the manifest and the pinned key, which the visor checks for you. Verify, don't
trust the download.

## Addresses
No host address of any validator is published in this repository. An admitted validator receives its peer list with
its acceptance, and the validator p2p port answers seated validators only.

## Reporting
Report vulnerabilities **privately** to security@vordium.com — never in a public issue, pull request, forum or chat.

**We fix first.** A report stays private while the fix is built, signed and rolled out to the validators. **Details are
published after the fix is live**, together with the release that carries it (see each network's `releases.json`). We acknowledge a report
as soon as we have read it and tell you when the fix is live.
