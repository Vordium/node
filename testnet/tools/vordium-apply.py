#!/usr/bin/env python3
"""Sign a validator application on the operator's OWN box, with the validator key.
Input: the join request printed by `vordium --join-request --name "<name>"` (a file), the contact, the chain id.
Output: the application JSON on stdout — paste it into the apply page. Nothing is sent anywhere.
The private key is read from --keyfile (default secrets/validator.key, 64 hex — the key the signer daemon
uses), used once to sign, and never printed or logged. Without --sign it prints only the message that would be signed.
  usage: vordium-apply.py --join JOIN.json --chain-id 101102 --email you@example.org [--telegram @you] [--note "…"]
                          [--node-id <wg public key or empty>] [--keyfile PATH] [--sign]
The message (lines joined by "\\n", no trailing newline) and the id rule:
  Vordium Validator Application / Chain: / Address: / Hot key: / VRF: / Name: / Node: / Contact: / Submitted:
  Contact = keccak256 of the canonical JSON of `contact` (keys sorted, no spaces), 0x hex;
  id      = keccak256 of the UTF-8 bytes of the message text.
"""
import argparse, json, sys, time
from eth_keys import keys
from eth_utils import keccak


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def message(app):
    j = app["join"]
    return "\n".join([
        "Vordium Validator Application",
        f"Chain: {app['chainId']}",
        f"Address: {j['address'].lower()}",
        f"Hot key: {j['hotKey'].lower().removeprefix('0x')}",
        f"VRF: {j['vrfPubkey'].lower().removeprefix('0x')}",
        f"Name: {j['name']}",
        f"Node: {app['nodeId']}",
        f"Contact: 0x{keccak(canon(app['contact']).encode()).hex()}",
        f"Submitted: {app['submittedAtMs']}",
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--join", required=True, help="file holding the output of `vordium --join-request`")
    ap.add_argument("--chain-id", type=int, required=True, help="101102 for the test network, 101101 for the live network")
    ap.add_argument("--email", required=True)
    ap.add_argument("--telegram", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--node-id", default="", help="the node's wg public key, or empty")
    ap.add_argument("--keyfile", default="secrets/validator.key")
    ap.add_argument("--sign", action="store_true", help="sign and print the application (default: print the message only)")
    a = ap.parse_args()
    jr = json.load(open(a.join))
    if jr.get("kind") != "vordium-validator-join" or jr.get("version") != 1:
        print(json.dumps({"error": "not a version-1 join request"})); sys.exit(2)
    if len(a.note) > 500:
        print(json.dumps({"error": "note is longer than 500 characters"})); sys.exit(2)
    join = {"kind": "vordium-validator-join", "version": 1, "address": jr["address"].lower(),
            "hotKey": jr["hotKey"].lower().removeprefix("0x"), "vrfPubkey": jr["vrfPubkey"].lower().removeprefix("0x"),
            "name": jr["name"]}
    app = {"kind": "vordium-validator-application", "version": 1, "chainId": a.chain_id, "join": join,
           "nodeId": a.node_id, "contact": {"email": a.email, "telegram": a.telegram, "note": a.note},
           "submittedAtMs": int(time.time() * 1000)}
    msg = message(app)
    app_id = "0x" + keccak(msg.encode()).hex()
    if not a.sign:
        print(json.dumps({"message": msg, "id": app_id, "signed": False})); return
    raw = open(a.keyfile).read().strip()
    raw = raw[2:] if raw.startswith("0x") else raw
    if len(raw) != 64:
        print(json.dumps({"error": "keyfile must hold 64 hex chars"})); sys.exit(2)
    pk = keys.PrivateKey(bytes.fromhex(raw)); del raw
    if pk.public_key.to_checksum_address().lower() != join["address"]:
        print(json.dumps({"error": "this key does not control the join request's address — nothing signed"})); sys.exit(3)
    b = msg.encode()
    s = pk.sign_msg_hash(keccak(b"\x19Ethereum Signed Message:\n" + str(len(b)).encode() + b))
    app["signature"] = "0x" + (s.r.to_bytes(32, "big") + s.s.to_bytes(32, "big") + bytes([27 + s.v])).hex()
    print(json.dumps({"id": app_id, "application": app}, indent=1))


if __name__ == "__main__":
    main()
