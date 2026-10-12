"""The signing phase for the validator operator tools (vordium-register-validator.py,
vordium-attest-hotkey.py, vordium-convert-self-bond.py). The same rule as the vordium SDK and the app:

    head <  H - 3000        legacy          today's message, unchanged
    H - 3000 <= head < H    window          refused: a signature made now could land on either side of H
    head >= H               genesis-bound   the EIP-191 message carries `Genesis: <sha256>` as line 3

H (`aa2007_activation_height`) is read from the chain's release list (releases.json: any release's `activations` or
`activation_key`/`activation_height`), never typed. No release naming it = the switch is not scheduled = legacy. The
genesis is the network spec's `genesisSha256`, and it must agree with the node's `/status` genesis. Anything
unreadable, ambiguous or contradictory refuses to sign. A throwaway sandbox (whose node reports its own genesis file
while it signs under the compiled pin) passes `--genesis` to name the signing genesis explicitly.
Standard library only.
"""
import json
import re
import urllib.request

ROLLB_KEY = "aa2007_activation_height"
ROLLB_WINDOW = 3000
# The public hosts refuse the default Python user agent, so every request names this tool.
_opener = urllib.request.build_opener()
_opener.addheaders = [("User-Agent", "vordium-operator-tools/1")]
urllib.request.install_opener(_opener)

DEFAULT_RELEASES = "https://rpc.vordium.com/releases.json"
DEFAULT_SPEC = "https://rpc.vordium.com/network-spec.json"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class SigningPaused(RuntimeError):
    pass


def _get_json(src):
    if src.startswith(("http://", "https://")):
        req = urllib.request.Request(src, headers={"User-Agent": "vordium-operator-tools", "Cache-Control": "no-store"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    with open(src) as f:
        return json.load(f)


def _is_height(v):
    # 0 = active from genesis (a chain that signs genesis-bound from block 0, e.g. the test network).
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 2**53 - 1


def activation_height(releases, chain_id):
    """H from releases.json: an int, or None when no release names the key. Raises ValueError when inconsistent."""
    if not isinstance(releases, dict) or not isinstance(releases.get("releases"), list):
        raise ValueError("the chain's release list could not be read")
    if releases.get("chain_id") != chain_id:
        raise ValueError(f"the release list is for chain {releases.get('chain_id')}, not {chain_id}")
    found = set()
    for rel in releases["releases"]:
        if not isinstance(rel, dict):
            continue
        if rel.get("activation_key") == ROLLB_KEY:
            if not _is_height(rel.get("activation_height")):
                raise ValueError(f"a release names {ROLLB_KEY} without a valid height")
            found.add(rel["activation_height"])
        for a in rel.get("activations") or []:
            if isinstance(a, dict) and a.get("key") == ROLLB_KEY:
                if not _is_height(a.get("height")):
                    raise ValueError(f"a release names {ROLLB_KEY} without a valid height")
                found.add(a["height"])
    if len(found) > 1:
        raise ValueError(f"the release list names {ROLLB_KEY} at {len(found)} different heights")
    return next(iter(found)) if found else None


def _norm(g):
    s = str(g).lower()
    return s[2:] if s.startswith("0x") else s


def signing_phase(eth_rpc, chain_id, releases_src=DEFAULT_RELEASES, spec_src=DEFAULT_SPEC, genesis_override=None,
                  status_url=None):
    """{"kind": legacy|window|genesis-bound, "H", "head", "genesis"}; raises SigningPaused when nothing may be signed."""
    try:
        H = activation_height(_get_json(releases_src), chain_id)
    except Exception as e:
        raise SigningPaused(f"the signing format cannot be confirmed: {e}")
    if H is None:
        return {"kind": "legacy", "H": None, "head": None, "genesis": None}
    try:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}).encode()
        req = urllib.request.Request(eth_rpc, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            head = int(json.loads(r.read())["result"], 16)
    except Exception as e:
        raise SigningPaused(f"the chain's current height could not be read ({e})")
    if head < H - ROLLB_WINDOW:
        return {"kind": "legacy", "H": H, "head": head, "genesis": None}
    if head < H:
        raise SigningPaused(f"the chain switches its signing format at height {H:,}, {H - head:,} heights from now; "
                            "signing is paused until it passes — try again in a few minutes")
    if genesis_override:
        g = _norm(genesis_override)
    else:
        try:
            g = _norm(_get_json(spec_src).get("genesisSha256"))
            if status_url:
                n = _norm(_get_json(status_url).get("genesis_sha256"))
                if n != g:
                    raise SigningPaused("the network spec and the node disagree about the genesis")
        except SigningPaused:
            raise
        except Exception as e:
            raise SigningPaused(f"the genesis could not be read ({e})")
    if not _HEX64.match(g):
        raise SigningPaused("the genesis is malformed")
    return {"kind": "genesis-bound", "H": H, "head": head, "genesis": g}


def with_genesis_line(lines, phase):
    """EIP-191 messages from H: `Genesis: <sha256>` as line 3, directly after `Chain: <id>`."""
    if phase["kind"] == "legacy":
        return list(lines)
    if len(lines) < 2 or not lines[1].startswith("Chain: "):
        raise ValueError('an EIP-191 message must carry "Chain: <id>" as line 2')
    return [lines[0], lines[1], f"Genesis: {phase['genesis']}", *lines[2:]]


def add_cli(ap):
    """The three flags every operator tool takes."""
    ap.add_argument("--releases", default=DEFAULT_RELEASES, help="release list (URL or file) that names the signing-format height")
    ap.add_argument("--spec", default=DEFAULT_SPEC, help="network spec (URL or file) that names the genesis")
    ap.add_argument("--genesis", default=None, help="SANDBOX ONLY: the signing genesis (64 hex), skipping the spec/node check")
