#!/usr/bin/env python3
"""Build a .urp with ONE MoveJ through waypoints recorded by record_path.py.

usage: build_movej_program.py recording.json template.urp out.urp --name NAME
                              [--blend-mm 3] [--speed 0.5] [--accel 0.5] [--dedup-mm 0.5]
                              [--safety-checksum "8286 7A6B"]

`template.urp` must be a real program saved by PolyScope on the SAME robot (it contains
fixed waypoints). The header, calibration block, TCP offset and per-waypoint Kinematics
block are copied from it so they match that robot. Never use another robot's file: the
serial number, calibration and crcValue are robot-specific.

`crcValue` in the header is the robot's safety checksum. It is copied from the template; if the robot's
safety configuration has changed since the template was saved, pass the value shown in the pendant's
top-right corner with --safety-checksum (two groups of four hex digits, converted to decimal here).

The output is a new file; it is never written over the template. First replay should be
slow (the defaults are 0.5 rad/s and 0.5 rad/s^2) and the program runs once.
"""
import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET

from urp_tools import read_xml, write_urp


def build(wps, tpl, name, blend_m, speed, accel, dedup_mm, safety_checksum=None):
    kept = [wps[0]]
    for w in wps[1:-1]:
        if math.dist(w["tcp"][:3], kept[-1]["tcp"][:3]) * 1e3 >= dedup_mm:
            kept.append(w)
    kept.append(wps[-1])

    head = tpl[:tpl.index("</kinematics>") + len("</kinematics>")]
    head = re.sub(r'(<URProgram name=")[^"]*"', r'\g<1>%s"' % name, head, count=1)
    if safety_checksum:
        crc = int(safety_checksum.replace(" ", ""), 16)
        head, n = re.subn(r'crcValue="\d+"', f'crcValue="{crc}"', head, count=1)
        if n != 1:
            raise SystemExit("template header has no crcValue attribute")

    m = re.search(r'<Waypoint type="Fixed"[^>]*>.*?</Waypoint>', tpl, re.S)
    if not m:
        raise SystemExit("template has no Fixed waypoint to copy structure from")
    wp = m.group(0)
    tcp = re.search(r'<TCPOffset pose="([^"]*)"/>', wp).group(1)
    kin = re.search(r'<Kinematics .*?</Kinematics>', wp, re.S).group(0)
    flags = re.search(r'kinematicsFlags="([^"]*)"', wp).group(1)
    if flags == "-1":
        flags = "4"

    parts, n = [], len(kept)
    for i, w in enumerate(kept):
        mp = "<motionParameters/>" if i in (0, n - 1) else f'<motionParameters blendRadius="{blend_m}"/>'
        angles = ", ".join(repr(float(v)) for v in w["q"])
        parts.append(f'''            <Waypoint type="Fixed" name="Waypoint_{i + 1}" kinematicsFlags="{flags}">
              {mp}
              <position>
                <JointAngles angles="{angles}"/>
                <TCPOffset pose="{tcp}"/>
                {kin}
              </position>
              <BaseToFeature pose="0.0, 0.0, 0.0, 0.0, 0.0, 0.0"/>
            </Waypoint>''')

    body = f'''
  <children>
    <InitVariablesNode/>
    <MainProgram runOnlyOnce="true" InitVariablesNode="false">
      <children>
        <Move motionType="MoveJ" speed="{speed}" acceleration="{accel}" useActiveTCP="true" positionType="CartesianPose" optimoveEnabled="false" optiMoveSpeed="0.3" optiMoveAcceleration="0.09">
          <feature class="GeomFeatureReference" referencedName="Joint_0_name"/>
          <children>
{chr(10).join(parts)}
          </children>
        </Move>
      </children>
    </MainProgram>
  </children>
</URProgram>'''
    xml = head + body
    root = ET.fromstring(xml)  # must be well-formed
    got = [w.find("position/JointAngles").get("angles") for w in root.iter("Waypoint")]
    assert len(got) == len(kept)
    for g, w in zip(got, kept):  # joint angles must round-trip exactly
        assert [float(v) for v in g.split(",")] == [float(v) for v in w["q"]]
    return xml, len(kept)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("recording")
    p.add_argument("template")
    p.add_argument("out")
    p.add_argument("--name", required=True, help="program name stored inside the file")
    p.add_argument("--blend-mm", type=float, default=3.0)
    p.add_argument("--speed", type=float, default=0.5)
    p.add_argument("--accel", type=float, default=0.5)
    p.add_argument("--dedup-mm", type=float, default=0.5)
    p.add_argument("--safety-checksum", help='pendant corner code, e.g. "8286 7A6B" (hex); sets crcValue')
    a = p.parse_args()
    if a.out == a.template:
        sys.exit("refusing to overwrite the template")
    wps = json.load(open(a.recording))["waypoints"]
    xml, n = build(wps, read_xml(a.template), a.name, a.blend_mm / 1e3, a.speed, a.accel, a.dedup_mm,
                    a.safety_checksum)
    write_urp(xml, a.out)
    print(f"{len(wps)} recorded -> {n} waypoints; blend {a.blend_mm} mm; MoveJ {a.speed} rad/s, "
          f"{a.accel} rad/s^2; wrote {a.out}")


if __name__ == "__main__":
    main()
