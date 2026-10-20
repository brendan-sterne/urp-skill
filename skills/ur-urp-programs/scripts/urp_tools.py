#!/usr/bin/env python3
"""Inspect and convert Universal Robots PolyScope 5 .urp programs.

  urp_tools.py unpack prog.urp [prog.xml]   decompress to XML
  urp_tools.py pack   prog.xml prog.urp     gzip an XML file back into a .urp
  urp_tools.py outline prog.urp             condensed, human-readable program tree

A .urp saved by PolyScope 5.25/5.26 is gzip-compressed XML. This tool also reads a
plain-XML file. Standard library only.
"""
import collections
import gzip
import sys
import xml.etree.ElementTree as ET

# Elements that are bulk calibration/expression noise when reading a program.
SKIP = {
    "kinematics", "Kinematics", "TCPOffset", "JointAngles", "BaseToFeature", "motionParameters",
    "relativeFromPosition", "expression", "initializeExpression", "deltaTheta", "a", "d", "alpha",
    "jointChecksum", "position", "ExpressionChar", "ExpressionToken", "ExpressionVariable",
    "dataModel", "data", "variables", "variable", "pin", "feature", "state", "children",
}


def read_xml(path):
    raw = open(path, "rb").read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


def write_urp(xml_text, path):
    ET.fromstring(xml_text)  # refuse to write malformed XML
    with gzip.GzipFile(path, "wb", mtime=0) as g:
        g.write(xml_text.encode("utf-8"))


def expr_text(e):
    if e is None:
        return ""
    return "".join(x.get("character") or x.get("token") or "" for x in e.iter()
                   if x.tag.startswith("Expression"))


def describe(e):
    t = e.tag
    keep = ("name", "type", "motionType", "strategyProgramNodeType", "action", "runOnlyOnce", "class")
    attrs = " ".join(f"{k}={v}" for k, v in e.attrib.items() if k in keep)
    extra = ""
    if t == "Move":
        extra = f" speed={e.get('speed')} accel={e.get('acceleration')}"
        f = e.find("feature")
        if f is not None and f.get("referencedName"):
            extra += f" feature={f.get('referencedName')}"
    elif t == "Waypoint":
        j = e.find("position/JointAngles")
        if j is not None:
            extra = " q=[" + ",".join(f"{float(v):.2f}" for v in j.get("angles").split(",")) + "]"
        m = e.find("motionParameters")
        if m is not None and m.get("blendRadius"):
            extra += f" blend={m.get('blendRadius')}"
    elif t == "Assignment":
        v = e.find("variable")
        extra = f" {v.get('name') if v is not None else '?'} = {expr_text(e.find('expression'))}"
    elif t in ("If", "Loop", "Wait", "Set"):
        ex = expr_text(e.find("expression"))
        if ex:
            extra += " " + ex
        p = e.find("pin")
        if p is not None and p.get("referencedName"):
            extra += f" pin={p.get('referencedName')}"
    return t + (" " + attrs if attrs else "") + extra


def walk(e, depth, out):
    if e.tag in SKIP and e.tag != "children":
        return
    if e.tag != "children":
        out.append("  " * depth + describe(e))
        depth += 1
    for c in e:
        walk(c, depth, out)


def outline(path):
    root = ET.fromstring(read_xml(path))
    print(f"{root.get('name')}: created {root.get('createdIn')}, saved {root.get('lastSavedIn')}, "
          f"installation {root.get('installation')}")
    counts = collections.Counter(e.tag for e in root.iter() if e.tag not in SKIP)
    print("nodes:", dict(counts.most_common()))
    caps = sorted({(e.get("strategyURCapName"), e.get("strategyProgramNodeType"))
                   for e in root.iter("Contributed")})
    if caps:
        print("URCap nodes:", caps)
    lines = []
    children = root.find("children")
    for c in children if children is not None else []:
        walk(c, 0, lines)
    print("\n".join(lines))


def main(argv):
    if len(argv) < 3 or argv[1] not in ("unpack", "pack", "outline"):
        sys.exit(__doc__)
    cmd = argv[1]
    if cmd == "unpack":
        out = argv[3] if len(argv) > 3 else argv[2].rsplit(".", 1)[0] + ".xml"
        open(out, "w").write(read_xml(argv[2]))
        print("wrote", out)
    elif cmd == "pack":
        if len(argv) < 4:
            sys.exit(__doc__)
        write_urp(open(argv[2]).read(), argv[3])
        print("wrote", argv[3])
    else:
        outline(argv[2])


if __name__ == "__main__":
    main(sys.argv)
