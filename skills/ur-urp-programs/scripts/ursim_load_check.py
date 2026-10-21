#!/usr/bin/env python3
"""Check whether PolyScope accepts .urp files, using URSim and the dashboard `load` command.

usage: ursim_load_check.py --programs-dir DIR [--host localhost] [--rel-dir loadtest] FILE.urp [FILE.urp ...]

DIR is the folder URSim has mounted as its programs directory (for example the host side of
`-v ~/ursim-programs:/ursim/programs`). The files are copied into DIR/REL_DIR and loaded one at a time.

The check is only trustworthy if the harness can tell good from bad, so it always runs two built-in
negative controls first (a truncated gzip and a plain-text file): both must be REJECTED. A file is
ACCEPTED when `load` replies "Loading program" AND `get loaded program` then names that file; it is
REJECTED when the reply is an error or the previously loaded program is still loaded.

What this does and does not tell you: it shows that PolyScope's parser accepts the file in URSim. It does
not show how the program looks in the UI, that URCaps are present, or that the program is safe or correct
on a physical robot. URSim loads files even if their crcValue (safety checksum) or calibration differs.
"""
import argparse
import gzip
import os
import shutil
import sys
import time

from dashboard import session

POSITIVE = "Loading program"


def load(host, port, rel_dir, name, settle):
    path = f"{rel_dir}/{name}"
    _, out = session(host, port, [f"load {path}"])
    reply = out[0][1]
    time.sleep(settle)
    _, out2 = session(host, port, ["get loaded program"])
    loaded = out2[0][1]
    ok = reply.startswith(POSITIVE) and loaded.endswith(path.split("/")[-1])
    return ok, reply, loaded


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--programs-dir", required=True)
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=29999)
    p.add_argument("--rel-dir", default="loadtest")
    p.add_argument("--settle", type=float, default=3.0, help="seconds to wait after each load")
    p.add_argument("files", nargs="+")
    a = p.parse_args()

    dest = os.path.join(a.programs_dir, a.rel_dir)
    os.makedirs(dest, exist_ok=True)

    # negative controls, built here so they are always available
    good = a.files[0]
    with open(good, "rb") as f:
        head = f.read(400)
    open(os.path.join(dest, "_ctl_truncated.urp"), "wb").write(head)
    open(os.path.join(dest, "_ctl_text.urp"), "wb").write(b"this is not a program")
    # make sure there is a known previous program, so a failed load is visible
    shutil.copy(good, os.path.join(dest, "_ctl_baseline.urp"))
    ok, _, _ = load(a.host, a.port, a.rel_dir, "_ctl_baseline.urp", a.settle)
    if not ok:
        sys.exit("could not load the baseline program; is URSim up and the programs dir mounted?")

    bad = 0
    for ctl in ("_ctl_truncated.urp", "_ctl_text.urp"):
        ok, reply, _ = load(a.host, a.port, a.rel_dir, ctl, a.settle)
        status = "ok (rejected as expected)" if not ok else "PROBLEM: accepted"
        print(f"control {ctl:20} {status}: {reply[:80]}")
        bad += ok
    if bad:
        sys.exit("a negative control was accepted; results below would not be trustworthy")

    failures = 0
    for f in a.files:
        name = os.path.basename(f).replace(" ", "_")
        shutil.copy(f, os.path.join(dest, name))
        ok, reply, loaded = load(a.host, a.port, a.rel_dir, name, a.settle)
        print(f"{'ACCEPTED' if ok else 'REJECTED':9} {name}: {reply[:100]}")
        failures += not ok
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
