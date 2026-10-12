# Vordium mainnet — operator guide

Chain id **101101** (0x18aed). Genesis sha256 `2c1c0679fa6ab8358f1d3e8d294a8d1c73ac2e2caf9079f1216abedc3d9fdf4f`
(also in [`genesis.sha256`](genesis.sha256)).

| | |
|---|---|
| Release channel | `https://binaries.vordium.com/mainnet/` |
| Release index | `https://binaries.vordium.com/mainnet/releases.json` (read `current`; each release names its `rollback`) |
| Mirror | the signed text files (`releases.json`, `SHA256SUMS.<id>`, their `.asc`, `genesis.sha256`) are also in this folder; binaries are served only from the channel |
| Public RPC | `https://rpc.vordium.com` |
| Release key | `C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE` (ed25519) — [`../pub_key.asc`](../pub_key.asc) |

**The one rule: a validator runs nothing it has not verified against the pinned release key.** The `vordium-visor`
binary enforces that rule at every start. Do not skip it and do not run the node binary directly. The trust model and
the two-key rule are in [`../SECURITY.md`](../SECURITY.md).

---

## Two keys — read this first

- **Operator key (cold).** Your identity as the validator's operator. It registers the validator and bonds or unbonds
  self-stake. Keep it offline (a hardware wallet or an air-gapped machine). It is never copied onto the node box and
  never appears in any config file. You sign with it off the box and submit only the signature.
- **Validator hot key.** Generated **on the node box** and used by the local signer to sign every block and vote. It
  holds **no funds** and **cannot move your bond**. If it is ever compromised the worst case is jailing and a key
  rotation, not loss of stake.

No private key of any kind is ever written into a config file, an environment file, or this repository. Config files
carry *paths to* key files that you place with `0600` permissions.

---

## 1. Download the release and verify it

All commands run from the install directory `/opt/vordium`.

```
B=https://binaries.vordium.com/mainnet
ID=$(curl -fsS $B/releases.json | jq -r .current)
mkdir -p /opt/vordium/bin && cd /opt/vordium
curl -fsS -O $B/pub_key.asc -O $B/releases.json -O $B/releases.json.asc \
     -O $B/SHA256SUMS.$ID -O $B/SHA256SUMS.$ID.asc -O $B/genesis.sha256
curl -fsS -o bin/vordium-visor $B/vordium-visor && curl -fsS -o bin/$ID $B/$ID
SIGNER=$(awk '/vordium-signer-/{print $2}' SHA256SUMS.$ID) && curl -fsS -o bin/$SIGNER $B/$SIGNER
```

Check the key, then the signatures, then the files:

```
gpg --show-keys --with-fingerprint pub_key.asc      # must read C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE
gpg --import pub_key.asc
gpg --verify SHA256SUMS.$ID.asc SHA256SUMS.$ID && gpg --verify releases.json.asc releases.json
(cd bin && sha256sum -c --ignore-missing ../SHA256SUMS.$ID) && chmod 755 bin/vordium-visor bin/$ID bin/$SIGNER
ln -sfn /opt/vordium/bin/$ID bin/vordiumchain
echo "VORDIUM_RELEASE_ID=$ID" > visor-release.env   # names the release the visor checks at every start
```

The visor checks four things at every start and refuses to continue if any fails: the node binary's hash is in the
signed manifest under its own name; the manifest signature is by the pinned release key and no other;
`genesis.json` matches `genesis.sha256`; and `pub_key.asc` carries the pinned fingerprint. A refusal prints a
`REFUSE[...]` line naming the check that failed.

## 2. Confirm the genesis = the chain you mean to join

The genesis file is not published: an admitted validator receives it privately. Check it before first boot:

```
sha256sum config/genesis.json      # must equal the contents of genesis.sha256 (2c1c0679…)
```

A live node reports the same value: `curl -s https://rpc.vordium.com/status | jq -r .genesis_sha256`.
If it does not match, you are looking at a different chain.

## 3. Generate the validator hot key on the box

```
mkdir -p secrets && chmod 700 secrets
( umask 077
  openssl rand -hex 32 > secrets/validator.key   # 64 hex characters
  head -c 32 /dev/urandom > secrets/vrf-seed )   # exactly 32 raw bytes
```

Both files stay on this machine. Your validator address is derived from the hot key; never hand-type it anywhere.

## 4. Configure the node

```
cp mainnet/config/node.toml.template config/node.toml
cp mainnet/config/node.env.template  node.env
```

Edit only `[paths]`, `[keys]` and `[pruning]` for your machine. Leave `[validators]` and `[consensus]` exactly as
shipped: every validator runs the same values. `[network] peers` and `validator_endpoints` stay empty for now; they
are sent to you when your application is accepted, and the node refuses to start without them.

## 5. Print your join request

```
./bin/vordiumchain --join-request --name "<your name>" > join.json
```

It prints your public values only: address, hot key, VRF key, name. Nothing secret.

## 6. Register and bond with your operator (cold) key

Registration is signed **off the box** with the operator key and submitted as a signature only. Build the self-signed
op, sign it on your cold machine, then submit the signed body to the public intake:

```
curl -s -X POST https://rpc.vordium.com/submit \
     -H 'content-type: application/json' --data @registervalidator.signed.json
```

`/submit` accepts only self-signed public ops. Your bond is escrowed by the op you signed and is releasable only by
your operator key.

## 7. Install the units and start

```
sudo cp mainnet/ops/vordium-bft.service /etc/systemd/system/
sudo mkdir -p /etc/systemd/system/vordium-bft.service.d
sudo cp mainnet/ops/visor.conf /etc/systemd/system/vordium-bft.service.d/visor.conf   # the visor gates every start
sudo cp mainnet/ops/vordium-logrotate.conf /etc/logrotate.d/vordium
sudo cp mainnet/ops/vordium-prune.service mainnet/ops/vordium-prune.timer /etc/systemd/system/
sudo systemctl daemon-reload
./bin/vordiumchain --check-config          # must end with "peering OK" and exit 0
sudo systemctl enable --now vordium-bft vordium-prune.timer
journalctl -u vordium-bft -f
```

The node signs through the local signer daemon (`vordium-signer-<id>`, listed in the same signed manifest), which
must be running before the node starts; its unit file comes with your acceptance, together with the peer list.

systemd runs the visor before the node; a refusal stops the unit by design. If the node refuses to start, read the
`REFUSE[...]` line in the journal first.

## Updating

When a new release is published, `releases.json` names it as `current` and the previous one as its `rollback`.
Download and verify it as in step 1, re-point `bin/vordiumchain`, write its id into `visor-release.env`, then restart.
To roll back, do the same with the `rollback` id; its signed checksums stay in this folder alongside the current ones.

## Monitor

```
curl -s 127.0.0.1:9002/status | jq '{sync_state, chain_head, binary_sha8, genesis_sha256}'
curl -s https://rpc.vordium.com/registry/entry/<your address> | jq '.data.entry
  | {status, seated, jailed, jail_reason, jailed_until_ms, missed_slots}'
```

`sync_state` should read `live` and `chain_head` should keep rising.
