#!/usr/bin/env python3
"""A jailed validator unjails ITSELF: UnjailValidator, signed by its own validator key.

Runs ON the validator's own box. Reads the private key from --keyfile (default secrets/validator.key,
64 hex — the key the signer daemon uses), derives the address, reads the validator's registry entry, and builds the
EXACT EIP-191 text the node verifies ("Vordium Admin\\nChain: <id>\\n
[Genesis: <sha256>\\n]Action: Unjail Validator\\nValidator: 0x<addr>\\nNonce: <n>"), signs it and POSTs
{"op":"UnjailValidator", ...} to /submit. The private key is never printed or logged. Default is DRY-RUN.

It refuses to sign (nothing sent) unless the entry says the unjail can be accepted: jailed, not a reserved seat, bond
at or above the minimum, and the jail period over (`jailed_until_ms` — the base period doubles per recent
offence, `jail_offences`). The chain checks all of it again; a refused unjail still consumes its nonce, so
the tool waits for the period rather than trying early.

  usage: vordium-unjail.py [--network mainnet|testnet] [--rpc URL] [--keyfile PATH] [--nonce N] [--go]
"""
import argparse, json, sys, time, urllib.request, urllib.error
from eth_keys import keys
from eth_utils import keccak
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import vordium_signing  # the signing phase (legacy / window / genesis-bound)


def rpc_post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


NETWORKS = {
    "mainnet": {"rpc": "https://rpc.vordium.com", "releases": "https://rpc.vordium.com/releases.json",
                "spec": "https://rpc.vordium.com/network-spec.json"},
    "testnet": {"rpc": "https://testnet.vordex.xyz/chain", "releases": "https://testnet.vordex.xyz/releases.json",
                "spec": "https://testnet.vordex.xyz/network-spec.json"},
}


def rpc_get(url):
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read() or b"{}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", choices=sorted(NETWORKS), default="mainnet")
    ap.add_argument("--rpc", default=None, help="node base URL (default: the network's public endpoint). A jailed node cannot place its own unjail in a block, so send it through a seated node.")
    ap.add_argument("--keyfile", default="secrets/validator.key")
    ap.add_argument("--nonce", type=int, required=True, help="the next unused validator op nonce (one above the last one you used)")
    ap.add_argument("--go", action="store_true", help="submit (default: dry-run)")
    vordium_signing.add_cli(ap)
    a = ap.parse_args()
    net = NETWORKS[a.network]
    a.rpc = (a.rpc or net["rpc"]).rstrip("/")
    if a.releases == vordium_signing.DEFAULT_RELEASES: a.releases = net["releases"]
    if a.spec == vordium_signing.DEFAULT_SPEC: a.spec = net["spec"]
    raw = open(a.keyfile).read().strip()
    raw = raw[2:] if raw.startswith("0x") else raw
    if len(raw) != 64:
        print(json.dumps({"error": "keyfile must hold 64 hex chars"})); sys.exit(2)
    pk = keys.PrivateKey(bytes.fromhex(raw)); del raw
    address = pk.public_key.to_checksum_address()
    chain_id = int(rpc_post(a.rpc + "/", {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []})[1]["result"], 16)
    look = rpc_get(a.rpc + "/registry/entry/" + address.lower()).get("data") or {}
    e = look.get("entry") or {}
    params = (rpc_get(a.rpc + "/registry/set").get("data") or {}).get("params") or {}
    now_ms = int(time.time() * 1000)
    why = None
    if not look.get("found"):
        why = "not a registered validator"
    elif e.get("status") != "jailed":
        why = f"not jailed (status {e.get('status')})"
    elif e.get("reserved"):
        why = "a reserved seat does not unjail itself"
    elif int(e.get("bond") or 0) < int(params.get("min_bond") or 0):
        why = "bond below the minimum"
    elif now_ms < int(e.get("jailed_until_ms") or 0):
        why = f"jail period not over: {(int(e['jailed_until_ms']) - now_ms) // 1000} s left (offences {e.get('jail_offences', 0)})"
    if why:
        print(json.dumps({"error": f"nothing signed: {why}", "address": address, "entry": e})); sys.exit(3)
    try:
        phase = vordium_signing.signing_phase(a.rpc + "/", chain_id, a.releases, a.spec, a.genesis)
    except vordium_signing.SigningPaused as ex:
        print(json.dumps({"error": f"nothing signed: {ex}"})); sys.exit(6)
    msg = "\n".join(vordium_signing.with_genesis_line(["Vordium Admin", f"Chain: {chain_id}", "Action: Unjail Validator",
        f"Validator: 0x{address[2:].lower()}", f"Nonce: {a.nonce}"], phase))
    digest = keccak(b"\x19Ethereum Signed Message:\n" + str(len(msg.encode())).encode() + msg.encode())
    sig = pk.sign_msg_hash(digest)
    sig65 = sig.r.to_bytes(32, "big") + sig.s.to_bytes(32, "big") + bytes([sig.v + 27])
    body = {"op": "UnjailValidator", "validator": address, "nonce": a.nonce, "signature": "0x" + sig65.hex()}
    out = {"validator": address, "chain_id": chain_id, "nonce": a.nonce, "message": msg, "signing_format": phase["kind"], "dry_run": not a.go}
    if not a.go:
        print(json.dumps(out)); return
    code, resp = rpc_post(a.rpc + "/submit", body)
    out.update({"http": code, "response": resp})
    print(json.dumps(out))
    sys.exit(0 if code in (200, 202) else 5)


if __name__ == "__main__":
    main()
