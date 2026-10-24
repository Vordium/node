# Vordium test network — operator quickstart

The test network runs the same node as the live network, built for chain id **101102** (0x18aee) with its own genesis.
Test VORD and test USDC have no value. Use it to rehearse every step before you run a validator on the live network.

| | |
|---|---|
| Chain id | `101102` |
| Genesis sha256 | `8b5d414c5cd5d18bc468b64f87ac8e2c2b5ff494c769d5e09dcf50ce75a59792` |
| Genesis file | `https://testnet.vordex.xyz/genesis.json` (public on the test network) |
| Release channel | `https://binaries.vordium.com/testnet/` |
| Release index | `https://binaries.vordium.com/testnet/releases.json` (read `current`; it changes with every test release) |
| Mirror | the signed text files (`releases.json`, `SHA256SUMS.<id>`, their `.asc`, `genesis.sha256`) are also in this folder of `github.com/Vordium/node`; binaries are served only from the channel |
| Public RPC | `https://rpc-testnet.vordium.com` (JSON-RPC) · `https://testnet.vordex.xyz/chain` (node routes) |
| Release key | `C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE` (same key as the live network) |

The trust rules are the ones in [SECURITY.md](../SECURITY.md) and the [mainnet guide](../mainnet/README.md): two keys (cold operator key, hot validator key), no
private key in any file of this repository, and nothing runs that the visor has not verified against the pinned key.

## 1. Install the visor

All commands run from the install directory `/opt/vordium` (the same layout as the mainnet guide).

```
B=https://binaries.vordium.com/testnet
ID=$(curl -fsS $B/releases.json | jq -r .current)
mkdir -p /opt/vordium/bin && cd /opt/vordium
curl -fsS -O $B/pub_key.asc -O $B/releases.json -O $B/releases.json.asc \
     -O $B/SHA256SUMS.$ID -O $B/SHA256SUMS.$ID.asc -O $B/genesis.sha256
curl -fsS -o bin/vordium-visor $B/vordium-visor && curl -fsS -o bin/$ID $B/$ID
```

Check the key, then the signature, then the files. Do this once by hand; after that the visor does it.

```
gpg --show-keys --with-fingerprint pub_key.asc      # must read C5EB 4728 F660 369C E519 D834 B48F B4B7 1EFD 48AE
gpg --import pub_key.asc
gpg --verify SHA256SUMS.$ID.asc SHA256SUMS.$ID && gpg --verify releases.json.asc releases.json
(cd bin && sha256sum -c ../SHA256SUMS.$ID) && chmod 755 bin/vordium-visor bin/$ID
ln -sfn /opt/vordium/bin/$ID bin/vordiumchain
echo "VORDIUM_RELEASE_ID=$ID" > visor-release.env   # names the release installed now; the visor updates it
```

**Updates.** `vordium-visor update` follows the channel: it reads the signed `releases.json`, downloads the next
release, runs the same four checks, and switches at your validator's turn. Validators switch one at a time, a few
minutes apart, and only while every seated validator is voting. A release that is not signed by the release key,
names another chain or genesis, or is older than the one installed is refused. If the node is not live on the new
release within three minutes, the visor switches back and stops updating until you clear it. Run it as a service:

```
bin/vordium-visor update --channel https://binaries.vordium.com/testnet --state-dir /opt/vordium/data/visor \
  --link /opt/vordium/bin/vordiumchain --unit vordium-bft --config /opt/vordium/config/node.toml \
  --node-rpc http://127.0.0.1:9002 --validator <your address> --pubkey /opt/vordium/pub_key.asc \
  --genesis /opt/vordium/config/genesis.json --genesis-sha256 /opt/vordium/genesis.sha256 \
  --release-env /opt/vordium/visor-release.env --manifest-dir /opt/vordium --dry-run --once
```

Run it once with `--dry-run --once` and read what it would do; then drop both flags and run it as a service
(`testnet/ops/vordium-visor-update.service`). The node's own unit keeps the boot check on every start
(`testnet/ops/visor.conf`). To pause updates: `echo paused > /opt/vordium/data/visor/HALTED`.

## 2. Get the genesis and check it

```
curl -fsSLo config/genesis.json https://testnet.vordex.xyz/genesis.json
sha256sum config/genesis.json      # must be 8b5d414c…9792
```

The chain is identified by this hash, never by its chain id. A running test node reports the same value:
`curl -s https://testnet.vordex.xyz/chain/status | jq -r .genesis_sha256`.

## 3. Generate the hot key on the box

```
mkdir -p secrets && chmod 700 secrets
( umask 077
  openssl rand -hex 32 > secrets/validator.key   # 64 hex characters
  head -c 32 /dev/urandom > secrets/vrf-seed )   # exactly 32 raw bytes
```

Both files stay on this machine. The hot key signs blocks and votes; it holds no funds.

## 4. Configure the node

```
cp testnet/config/node.toml.template config/node.toml
cp testnet/config/node.env.template  config/node.env   # two Arbitrum Sepolia RPC URLs, no keys
```

Leave `[consensus]` exactly as shipped. `[network] peers` and `validator_endpoints` stay empty for now: the node
refuses to start without them (`peering INVALID`), and they are sent to you when your application is accepted (step 7).

## 5. Print your join request

```
./<node binary> --join-request --name "<your name>" > join.json
```

It prints your public values only: address, hot key, VRF key, name. Nothing secret.

## 6. Sign your application

The tools in `testnet/tools/` need Python 3 with `eth-keys` and `eth-utils`
(`pip install eth-keys eth-utils`). They read the key once, in memory, and never print it.

```
python3 testnet/tools/vordium-apply.py --join join.json --chain-id 101102 \
    --email you@example.org [--telegram @you] [--note "…"] --sign > application.json
```

Without `--sign` it prints only the message it would sign. It sends nothing: submit `application.json` on the
validator application page.

## 7. On acceptance

When your application is accepted and your validator is seeded, you receive:

- the peer list for `[network] peers` and `validator_endpoints`;
- confirmation of your seeded bond.

There are no public seeds yet: the validator p2p port answers only seated validators, so the peer list comes with
acceptance. Fill it in, then run `./<node binary> --check-config`. It must end with `peering OK` and exit 0.

## 8. Start, catch up, unjail

Start the node through the visor (step 1). A newly seeded validator joins **jailed, with no jail period**. Once your
node has caught up (`sync_state` is `live`, see step 9), unjail it:

```
python3 testnet/tools/vordium-unjail.py --network testnet --nonce 1          # dry run: prints the message
python3 testnet/tools/vordium-unjail.py --network testnet --nonce 1 --go     # submit
```

- `--nonce` is your next unused validator op nonce: 1 the first time, one higher each time after.
- By default the tool sends through the public endpoint. Your own node also works (`--rpc http://127.0.0.1:9002`):
  it forwards the signed unjail to the seated validators.
- It refuses, and signs nothing, when you are not jailed, the jail period is not over, or your bond is below the minimum.

You are seated from the next epoch (33,000 heights). Missing too many slots jails you again; each repeat within 30 days
doubles the jail period (1 h, 2 h, 4 h … up to 128 h). The unjail step is the same each time.

## 9. Monitor

On the box:

```
curl -s 127.0.0.1:9002/status | jq '{sync_state, chain_head, binary_sha8, genesis_sha256}'
journalctl -u vordium-bft -f
```

From anywhere, your registry entry (status, seat, jail, missed slots):

```
curl -s https://testnet.vordex.xyz/chain/registry/entry/<your address> | jq '.data.entry
  | {status, seated, jailed, jail_reason, jailed_until_ms, jail_offences, missed_slots}'
```

`sync_state` should read `live` and `chain_head` should keep rising. `jailed: true` with a `jail_reason` means
step 8 again once `jailed_until_ms` has passed.
