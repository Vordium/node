# Security model

## The one rule
A validator runs nothing it has not verified against a key published before the binary
existed. `vordium-visor` enforces this at every start; it is the trust root, not a
convenience. Its pinned release fingerprint is compiled in:
`C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE` (ed25519, expires 2028-09-11).

The visor refuses to continue unless all four hold, at **every** start:
1. the node binary's hash is in the signed `SHA256SUMS`, under the name the manifest uses;
2. `SHA256SUMS.asc` is a good signature **by the pinned key and no other** (a good signature
   from a different key is the attack, and is refused by fingerprint — not accepted);
3. `genesis.json` matches `genesis.sha256`;
4. `pub_key.asc` carries the pinned fingerprint (checked first; nothing else means anything
   without it).

The visor binary has its own signed manifest, `SHA256SUMS.vordium-visor-eb743997e563f1bc` + `.asc`
(same release key). Check it by hand before you install the visor:
`gpg --verify SHA256SUMS.vordium-visor-eb743997e563f1bc.asc && sha256sum -c SHA256SUMS.vordium-visor-eb743997e563f1bc`.
From the next release on, each release manifest `SHA256SUMS.<sha16>` lists the visor too.

Honest limit: once installed, nothing re-checks the visor itself. An attacker who is already
root on your box can replace it. The visor raises the cost of a swapped *release*; it
is not a defense against a compromised host. Protect root access accordingly.

## Two-key model
- **Operator key (cold, offline).** Registers/bonds the validator and signs governance. Moves
  value. Never on the node box, never in a config file.
- **Validator hot key (on the box).** Signs blocks/votes via the local signer. Holds no funds,
  cannot move the bond. Compromise → jail + rotate, not loss of stake.

No private key of any kind belongs in this repository, a config file, or an env file. Configs
reference key *files* you place with `0600` permissions; the release ships only the public key.

## Reproducibility
Releases are built in a pinned, content-addressed container image and are **reproducible
internally** — the same source in that image rebuilds the same bytes, which is how the release
hashes in `SHA256SUMS` are produced and cross-checked before signing. Public build-from-source
reproducibility is not offered for this closed-binary distribution; your trust rests on the
signature over `SHA256SUMS` and the pinned key, which the visor checks for you. Verify, don't
trust the download.

## The one deliberate exposure: seeds.json
Everything about your node's topology is private except one thing the project publishes on
purpose: `seeds.json`, the bootstrap peers (a genesis validator's address + the host:port of its consensus listener) a fresh node dials. That is the
single deliberate reachable-address disclosure in this bundle. No other host, no internal
network, and no peer list of any running operator is published here.

## Reporting
Report vulnerabilities to security@vordium.com. Do not open public issues for security bugs.
