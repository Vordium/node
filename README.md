# Vordium node

The verified release bundle for running a Vordium validator. Vordium is an EVM L1
for AI agents. chainId **101101** (0x18aed).

**The one rule: a validator runs nothing it has not verified against a key that was
published before the binary existed.** The `vordium-visor` binary enforces that rule at
every start. Do not skip it and do not run the node binary directly.

---

## Two-key model — read this first

You hold **two** independent keys. They are never the same key and never live in the
same place.

- **Operator key (COLD).** Your identity as the validator's operator/owner. It authorises
  on-chain actions that move value or change your registration: registering the validator,
  bonding/unbonding self-stake, governance. **Keep it offline** — a hardware wallet or an
  air-gapped machine. It is never copied onto the node box and never appears in any config
  file. You sign with it off the box and submit only the resulting signature.

- **Validator hot key (secp256k1 consensus key).** Generated **on the node box**, used by
  the local signer to sign every block and vote. It is hot because it signs constantly.
  It holds **no funds** and **cannot move your bond** — that needs the operator cold key.
  If it is ever compromised the worst case is jailing + a key rotation, not loss of stake.

Consequence, stated bluntly: **no private key of any kind is ever written into a config
file, an environment file, or this repository.** Config files carry *paths to* key files
that you place with `0600` permissions; the release ships only the *public* release key.

---

## The 7-step operator path

Commands assume you have downloaded the release set (`<sha16>` — the node binary, named by its release id exactly as the signed manifest lists it — `vordium-visor`,
`SHA256SUMS.<sha16>`, `SHA256SUMS.<sha16>.asc`, `genesis.json`, `genesis.sha256`) and this repo's
`pub_key.asc` into one directory. `<sha16>` is the 16-hex release id printed in `RELEASES.md` (current: `0e49718dc0147cfd`).
Each release has its own signed manifest `SHA256SUMS.<sha16>`. The plain `SHA256SUMS` (+ `.asc`) is the **frozen** manifest of the
launch release `fa2af621c5c64bb9`: it is signed, it is never edited, and it will never list a later release — always verify
against `SHA256SUMS.<sha16>` for the release you run.

### 1. Verify the release before you trust a single byte of it
The visor checks four things and refuses to continue if any fails: the node binary's hash
is in the signed manifest under its own name; the manifest signature is by the pinned
release key and no other; `genesis.json` matches `genesis.sha256`; and `pub_key.asc`
carries the pinned fingerprint. Run it by hand once to see it pass:

```
sha256sum -c SHA256SUMS.<sha16>          # the signed manifest names the node binary `<sha16>`
./vordium-visor pub_key.asc SHA256SUMS.<sha16> SHA256SUMS.<sha16>.asc \
    <sha16> <sha16> genesis.json genesis.sha256
echo "exit=$?"     # 0 = accept, 1 = REFUSE (read the REFUSE[...] line), 2 = usage
```

The pinned release fingerprint is compiled into the visor and printed on every refusal:
`C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE` (ed25519, expires 2028-09-11). If your
downloaded `pub_key.asc` does not carry that fingerprint, stop — you have the wrong key.

### 2. Confirm the genesis discriminator = the chain you mean to join
The chain is identified by its **genesis sha256**, never by chain id alone (chain id is
reused across relaunches). Confirm you are joining the intended network:

```
sha256sum genesis.json          # must equal the contents of genesis.sha256
cat genesis.sha256              # 2c1c0679… for this network
```

A live node also publishes it: `curl -s https://rpc.vordium.com/status | jq -r .genesis_sha256`.
It must match `genesis.sha256`. If it does not, you are looking at a different chain.

### 3. Generate your validator HOT key on the box
Generate it locally; it never leaves this machine. Place the key material under `secrets/`
with `0600` file / `0700` dir permissions:

```
mkdir -p secrets && chmod 700 secrets
./<sha16> keygen --out secrets/validator.key      # writes 0600
./<sha16> vrf-keygen --out secrets/vrf-seed       # writes 0600
```

Note the derived validator address it prints — that is the address you register in step 6.
Do **not** hand-type it anywhere; the node derives its identity from this key file.

### 4. Configure `node.toml` from the template
Copy `config/node.toml.template` to `config/node.toml`. It carries **no keys** — paths, ports,
the `[consensus]` activation heights (the launch set at 0, plus `aa1998_activation_height = 625000`
from release `22f590437dec5b67` and `aa2001_activation_height = 845000` from release `bddf26dbac2bfb0a` —
every validator runs the same values; do not edit them), and the seven genesis validators' **public** identities under `[validators]`. Peering
is the one thing you fill in: copy the `seeds.json` entries for this genesis into `[network]`
`peers` and `validator_endpoints`, **in the same order as `[validators].set`** — the node builds its
route table from the two lists by position and refuses to boot with no routes.

```
cp config/node.toml.template config/node.toml
# edit [paths]/[keys]/[pruning] for your machine; fill [network] peers + validator_endpoints from seeds.json
```

### 5. Install the ops units (the visor gates every start)
```
sudo cp ops/vordium-bft.service /etc/systemd/system/
sudo mkdir -p /etc/systemd/system/vordium-bft.service.d
sudo cp ops/visor.conf /etc/systemd/system/vordium-bft.service.d/visor.conf   # ExecStartPre = the visor
sudo cp ops/vordium-logrotate.conf /etc/logrotate.d/vordium
sudo cp ops/vordium-prune.service ops/vordium-prune.timer /etc/systemd/system/
sudo systemctl daemon-reload
```
Edit `visor.conf`'s `<sha16>` to the release you installed (see the comment in that file):
a stale name produces `REFUSE[binary-hash-mismatch-for-name]`, which is the point.

### 6. Register + bond with your OPERATOR COLD key
Registration is signed **off the box** with the operator cold key and submitted as a
signature only. Build the self-signed op (RegisterValidator / ConvertToSelfBond), sign it
on your cold machine, then submit the signed body to the public intake:

```
# on your COLD machine: produce a signed body (see docs.vordium.com/validators)
# then, from anywhere:
curl -s -X POST https://rpc.vordium.com/submit \
     -H 'content-type: application/json' --data @registervalidator.signed.json
```
`/submit` accepts only self-signed public ops; a control op is refused. Your bond never
leaves your control — it is escrowed by the op you signed, releasable only by your cold key.

### 7. Start the node
```
sudo systemctl enable --now vordium-bft
sudo systemctl enable --now vordium-prune.timer
journalctl -u vordium-bft -f
```
`systemd` runs the visor as `ExecStartPre`; a refusal (non-zero) **stops the unit** by
design. If the node ever refuses to start, read the `REFUSE[...]` line in the journal
first — it names exactly which of the four checks failed.

---

## What is in this repo
Text and config only — no binaries, no source, no keys (other than the public release key).
See `RELEASES.md` for the current release ids and `SECURITY.md` for the trust model.

| file | purpose |
|---|---|
| `pub_key.asc` | the **public** release-signing key (fingerprint pinned in the visor) |
| `genesis.json` / `genesis.sha256` | the network's genesis + its discriminator hash |
| `seeds.json` | bootstrap peers (validator address + host:port), keyed by `genesis_sha256` |
| `config/node.toml.template` | node config template (no addresses, no keys) |
| `ops/` | systemd unit, visor drop-in, logrotate, pruner |
| `RELEASES.md` | release ids + how a release is cut and verified |
| `SECURITY.md` | trust model, the two-key rule, the deliberate `seeds.json` exposure |

Binaries (`<sha16>` — also served as `vordium-<sha16>`, byte-identical — and `vordium-visor`) and the signed `SHA256SUMS.<sha16>` are served from
`binaries.vordium.com`, not from this repo.
