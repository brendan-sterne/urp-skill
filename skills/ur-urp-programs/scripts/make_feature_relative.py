#!/usr/bin/env python3
"""Make one Move in a .urp relative to a feature (plane/point/frame) instead of the base.

usage: make_feature_relative.py prog.urp prog.script --list
       make_feature_relative.py prog.urp prog.script --move-index N --feature NAME \
                                --out new.urp --name "New program name" [--table table.md]

How PolyScope 5 stores this (observed on 5.25.1): a waypoint holds its JointAngles and a
BaseToFeature pose. For a base-relative move BaseToFeature is all zeros; for a feature-relative
move it equals the feature's pose in the base frame. The pose in the feature frame is derived,
not stored. So the conversion gives the Move its own <feature referencedName=...> element and
sets BaseToFeature on every waypoint of that Move to the feature's pose. Joint angles do not
change, so the arm goes to the same physical places until the feature is re-taught.

`prog.script` is the PolyScope-generated script saved next to the program. It supplies the
feature's pose (`global NAME=p[...]`) and each waypoint's base-frame TCP pose (`<wp>_p`),
which are used for the printed table of poses in the feature frame.

Output is a NEW file. Review the printed change summary, then open it in PolyScope.
"""
import argparse
import difflib
import re
import sys
import xml.etree.ElementTree as ET

from posemath import pose_inv, pose_trans, script_feature_pose, script_poses
from urp_tools import read_xml, write_urp

MOVE_RE = re.compile(r"<Move motionType=.*?</Move>", re.S)
ZERO = '<BaseToFeature pose="0.0, 0.0, 0.0, 0.0, 0.0, 0.0"/>'


def list_moves(xml):
    for i, m in enumerate(MOVE_RE.finditer(xml)):
        blk = m.group(0)
        mt = re.search(r'motionType="(\w+)"', blk).group(1)
        f = re.search(r"<feature [^>]*/>", blk)
        wps = re.findall(r'<Waypoint [^>]*name="([^"]*)"', blk)
        print(f"[{i}] {mt}: {len(wps)} waypoints, feature: {f.group(0) if f else 'none'}")
        print(f"      first: {wps[0] if wps else '-'}   last: {wps[-1] if wps else '-'}")


def convert(xml, index, feature_pose_str, feature):
    blocks = list(MOVE_RE.finditer(xml))
    if not 0 <= index < len(blocks):
        raise SystemExit(f"move index {index} out of range (0..{len(blocks) - 1})")
    blk = blocks[index].group(0)
    if blk.count("<Move ") != 1:
        raise SystemExit("nested Move blocks are not supported")
    pose = ", ".join(v.strip() for v in feature_pose_str.split(","))
    new_feat = f'<feature class="GeomFeatureReference" referencedName="{feature}"/>'
    new_blk, n_feat = re.subn(r"<feature [^>]*/>", new_feat, blk, count=1)
    if n_feat != 1:
        raise SystemExit("the selected Move has no <feature> element")
    new_blk, n_b2f = re.subn(r'<BaseToFeature pose="[^"]*"/>', f'<BaseToFeature pose="{pose}"/>', new_blk)
    return xml.replace(blk, new_blk, 1), blk, n_b2f


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("urp")
    p.add_argument("script")
    p.add_argument("--list", action="store_true", help="list the Moves and exit")
    p.add_argument("--move-index", type=int)
    p.add_argument("--feature")
    p.add_argument("--out")
    p.add_argument("--name", help="new program name stored in the file")
    p.add_argument("--table", help="write the feature-frame pose table (markdown) here")
    a = p.parse_args()

    xml = read_xml(a.urp)
    if a.list:
        list_moves(xml)
        return
    if None in (a.move_index, a.feature, a.out, a.name):
        sys.exit("need --move-index, --feature, --out and --name (or --list)")
    if a.out == a.urp:
        sys.exit("refusing to overwrite the input program")

    fpose, fstr = script_feature_pose(a.script, a.feature)
    new_xml, old_blk, n = convert(xml, a.move_index, fstr, a.feature)
    new_xml = re.sub(r'(<URProgram name=")[^"]*"', r'\g<1>%s"' % a.name, new_xml, count=1)
    ET.fromstring(new_xml)

    changed = [l for l in difflib.ndiff(xml.splitlines(), new_xml.splitlines()) if l[:1] in "+-"]
    print(f"feature {a.feature} pose (base): p[{fstr}]")
    print(f"updated {n} waypoint BaseToFeature poses; {len(changed)} changed lines "
          f"(expect {2 * (n + 2)}: name + feature + {n} waypoints, old and new)")

    sp = script_poses(a.script)
    names = re.findall(r'<Waypoint [^>]*name="([^"]*)"', old_blk)
    rows, missing = [], []
    for nm in names:
        if nm in sp:
            rows.append((nm, pose_trans(pose_inv(fpose), sp[nm])))
        else:
            missing.append(nm)
    if missing:
        print("warning: no base pose in the script for:", ", ".join(missing))
    lines = [f"| waypoint | x | y | z | rx | ry | rz |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {nm} | " + " | ".join(f"{v:.5f}" for v in p_) + " |" for nm, p_ in rows]
    table = "\n".join(lines)
    print("\nWaypoints in the feature frame (m, rad):\n" + table)
    if a.table:
        open(a.table, "w").write(f"Feature `{a.feature}` pose in base: p[{fstr}]\n\n{table}\n")

    write_urp(new_xml, a.out)
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
