import json
import math
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ur-urp-programs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_movej_program  # noqa: E402
import make_feature_relative  # noqa: E402
import posemath as pm  # noqa: E402
import urp_tools  # noqa: E402

TEMPLATE = (ROOT / "tests" / "fixtures" / "template.xml").read_text()
RECORDING = ROOT / "examples" / "recorded_path.example.json"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


# ---- pose maths ----------------------------------------------------------------------------
def test_rotation_vector_roundtrip_including_near_pi():
    rng = np.random.default_rng(0)
    for _ in range(200):
        axis = rng.normal(size=3)
        axis /= np.linalg.norm(axis)
        for ang in (0.01, 1.0, 3.0, math.pi - 1e-9, math.pi):
            R = pm.rv2R(axis * ang)
            R2 = pm.rv2R(pm.R2rv(R))
            assert np.allclose(R, R2, atol=1e-6)


def test_pose_trans_inverse_and_composition():
    a = [0.3, -0.2, 0.1, 0.1, -0.2, 0.7]
    b = [0.05, 0.0, 0.1, 0.0, 0.0, 0.3]
    assert np.allclose(pm.pose_trans(a, pm.pose_inv(a)), [0] * 6, atol=1e-9)
    ab = pm.pose_trans(a, b)
    assert np.allclose(pm.pose_trans(pm.pose_inv(a), ab), b, atol=1e-9)


def test_offset_is_measured_in_the_first_frame():
    # a frame rotated 90 degrees about z: +x in that frame is +y in the base
    out = pm.pose_trans([1, 0, 0, 0, 0, math.pi / 2], [1, 0, 0, 0, 0, 0])
    assert np.allclose(out[:3], [1, 1, 0], atol=1e-9)


# ---- urp file helpers ------------------------------------------------------------------------
def test_pack_unpack_roundtrip(tmp_path):
    xml = tmp_path / "p.xml"
    xml.write_text(TEMPLATE)
    urp = tmp_path / "p.urp"
    assert run(SCRIPTS / "urp_tools.py", "pack", xml, urp).returncode == 0
    assert urp.read_bytes()[:2] == b"\x1f\x8b"
    assert urp_tools.read_xml(urp) == TEMPLATE


def test_outline_runs(tmp_path):
    urp = tmp_path / "p.urp"
    urp_tools.write_urp(TEMPLATE, urp)
    r = run(SCRIPTS / "urp_tools.py", "outline", urp)
    assert r.returncode == 0, r.stderr
    assert "MoveP" in r.stdout and "Waypoint" in r.stdout


def test_write_urp_rejects_malformed_xml(tmp_path):
    with pytest.raises(ET.ParseError):
        urp_tools.write_urp("<URProgram><oops></URProgram>", tmp_path / "bad.urp")


# ---- movej builder -----------------------------------------------------------------------
def test_build_movej_program(tmp_path):
    wps = json.load(open(RECORDING))["waypoints"]
    xml, n = build_movej_program.build(wps, TEMPLATE, "replay", 0.003, 0.5, 0.5, 0.5)
    root = ET.fromstring(xml)
    assert root.get("name") == "replay"
    assert n == len(wps) - 1                       # the duplicate sample was dropped
    moves = list(root.iter("Move"))
    assert len(moves) == 1 and moves[0].get("motionType") == "MoveJ"
    wp = list(root.iter("Waypoint"))
    assert wp[0].find("motionParameters").attrib == {}
    assert wp[-1].find("motionParameters").attrib == {}
    assert wp[1].find("motionParameters").get("blendRadius") == "0.003"
    assert root.find("children/MainProgram").get("runOnlyOnce") == "true"


def test_build_refuses_to_overwrite_template(tmp_path):
    t = tmp_path / "t.urp"
    urp_tools.write_urp(TEMPLATE, t)
    r = run(SCRIPTS / "build_movej_program.py", RECORDING, t, t, "--name", "x")
    assert r.returncode != 0 and "overwrite" in (r.stderr + r.stdout)


# ---- feature-relative conversion -------------------------------------------------------------
def _make_script(tmp_path, feature_pose):
    """A fake PolyScope .script: feature pose + base-frame poses for waypoints a, b, c that
    lie on the feature's plane (z = 0 in the feature frame), tool pointing into the plane."""
    lines = ["  global Sheet=p[" + ",".join(repr(v) for v in feature_pose) + "]"]
    for nm, (x, y) in {"a": (0.05, 0.02), "b": (0.10, 0.04), "c": (0.15, 0.08)}.items():
        p = pm.pose_trans(feature_pose, [x, y, 0.0, math.pi, 0, 0])
        lines.append(f"  global {nm}_p=p[" + ",".join(repr(float(v)) for v in p) + "]")
    s = tmp_path / "prog.script"
    s.write_text("\n".join(lines) + "\n")
    return s


def test_make_feature_relative(tmp_path):
    feature = [0.5, 0.1, 0.02, 0.0, 0.0, 0.5]
    script = _make_script(tmp_path, feature)
    urp = tmp_path / "prog.urp"
    urp_tools.write_urp(TEMPLATE, urp)
    out = tmp_path / "prog_feature.urp"
    table = tmp_path / "table.md"
    r = run(SCRIPTS / "make_feature_relative.py", urp, script, "--move-index", "1",
            "--feature", "Sheet", "--out", out, "--name", "converted", "--table", table)
    assert r.returncode == 0, r.stderr + r.stdout
    new = ET.fromstring(urp_tools.read_xml(out))
    assert new.get("name") == "converted"

    moves = list(new.iter("Move"))            # [0] BeforeStart MoveJ, [1] MoveP, [2] final MoveJ
    assert moves[1].find("feature").get("referencedName") == "Sheet"
    assert [w.find("BaseToFeature").get("pose") for w in moves[1].iter("Waypoint")] == \
           [", ".join(repr(v) for v in feature)] * 3
    # the other Moves are untouched
    assert moves[0].find("feature").get("referencedName") == "Joint_0_name"
    assert moves[2].find("feature").get("reference")
    assert all(w.find("BaseToFeature").get("pose") == "0.0, 0.0, 0.0, 0.0, 0.0, 0.0"
               for m in (moves[0], moves[2]) for w in m.iter("Waypoint"))
    # waypoints on the plane have z ~ 0 in the feature frame, and x/y match what we built
    rows = [l.split("|")[1:-1] for l in table.read_text().splitlines() if l.startswith("| a ")
            or l.startswith("| b ") or l.startswith("| c ")]
    assert len(rows) == 3
    for row, (x, y) in zip(rows, [(0.05, 0.02), (0.10, 0.04), (0.15, 0.08)]):
        vals = [float(v) for v in row[1:]]
        assert abs(vals[0] - x) < 1e-4 and abs(vals[1] - y) < 1e-4 and abs(vals[2]) < 1e-6


def test_make_feature_relative_refuses_in_place(tmp_path):
    script = _make_script(tmp_path, [0.5, 0.1, 0.02, 0, 0, 0.5])
    urp = tmp_path / "prog.urp"
    urp_tools.write_urp(TEMPLATE, urp)
    r = run(SCRIPTS / "make_feature_relative.py", urp, script, "--move-index", "1",
            "--feature", "Sheet", "--out", urp, "--name", "x")
    assert r.returncode != 0


def test_list_moves(tmp_path):
    script = _make_script(tmp_path, [0.5, 0.1, 0.02, 0, 0, 0.5])
    urp = tmp_path / "prog.urp"
    urp_tools.write_urp(TEMPLATE, urp)
    r = run(SCRIPTS / "make_feature_relative.py", urp, script, "--list")
    assert r.returncode == 0 and "[1] MoveP: 3 waypoints" in r.stdout


# ---- recorder, against a fake robot -----------------------------------------------------------
def _packet(t, q, tcp):
    import struct
    buf = bytearray(1220)
    buf[0:4] = struct.pack("!i", 1220)
    buf[4:12] = struct.pack("!d", t)
    buf[252:300] = struct.pack("!6d", *q)
    buf[444:492] = struct.pack("!6d", *tcp)
    return bytes(buf)


def test_recorder_starts_on_motion_and_stops_when_still(tmp_path):
    import socket
    import threading

    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        t, dt = 0.0, 0.002
        def send(q, tcp):
            nonlocal t
            conn.sendall(_packet(t, q, tcp))
            t += dt
        rest = [0.5, -1.5, -1.5, -1.5, 1.5, 0.0]
        for _ in range(int(2.0 / dt)):                      # 2 s still
            send(rest, [0.4, 0.0, 0.1, 0, 3.14, 0])
        n = int(3.0 / dt)                                   # 3 s moving at 50 mm/s
        for i in range(n):
            f = i / n
            send([rest[0] + 0.3 * f] + rest[1:], [0.4 + 0.15 * f, 0.0, 0.1, 0, 3.14, 0])
        final_q, final_tcp = [rest[0] + 0.3] + rest[1:], [0.55, 0.0, 0.1, 0, 3.14, 0]
        try:
            for _ in range(int(3.0 / dt)):                  # 3 s still again
                send(final_q, final_tcp)
        except OSError:
            pass                                            # recorder hung up after stopping
        conn.close()

    threading.Thread(target=serve, daemon=True).start()
    out = tmp_path / "rec.json"
    r = run(SCRIPTS / "record_path.py", "--host", "127.0.0.1", "--port", port, "--out", out)
    assert r.returncode == 0, r.stdout + r.stderr
    wps = json.load(open(out))["waypoints"]
    assert 11 <= len(wps) <= 15, len(wps)                   # ~3 s at 4 Hz, plus start and end
    assert wps[0]["q"][0] == pytest.approx(0.5)             # first = resting pose
    assert wps[-1]["q"][0] == pytest.approx(0.8, abs=1e-3)  # last = final resting pose
    assert all(abs(w["tcp"][0] - 0.4) <= 0.15 + 1e-6 for w in wps)


# ---- dashboard + URSim load check, against a fake dashboard server -------------------------------
def _fake_dashboard(programs_dir):
    """Mimics URSim's replies: gzip-parseable files load, anything else is an error and the
    previously loaded program stays loaded."""
    import gzip as _gz
    import socket
    import threading

    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    state = {"loaded": None}

    def handle(conn):
        conn.sendall(b"Connected: Universal Robots Dashboard Server\n")
        f = conn.makefile("rwb")
        for raw in f:
            cmd = raw.decode().strip()
            if cmd.startswith("load "):
                rel = cmd[5:]
                path = pathlib.Path(programs_dir) / rel
                try:
                    ET.fromstring(_gz.decompress(path.read_bytes()))
                    state["loaded"] = "/ursim/programs/" + rel
                    reply = f"Loading program: /ursim/programs/{rel}, /ursim/programs/default.installation"
                except Exception:
                    reply = f"Error while loading program: /ursim/programs/{rel}: unknown failure"
            elif cmd == "get loaded program":
                reply = f"Loaded program: {state['loaded']}"
            else:
                reply = "?"
            f.write((reply + "\n").encode())
            f.flush()

    def serve():
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            threading.Thread(target=handle, args=(conn,), daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    return srv


def test_dashboard_session(tmp_path):
    import dashboard
    srv = _fake_dashboard(tmp_path)
    greeting, out = dashboard.session("127.0.0.1", srv.getsockname()[1], ["get loaded program"], timeout=2)
    assert greeting.startswith("Connected:") and out[0][1].startswith("Loaded program")
    srv.close()


def test_ursim_load_check_accepts_good_and_rejects_bad(tmp_path):
    srv = _fake_dashboard(tmp_path)
    port = srv.getsockname()[1]
    good = tmp_path / "good.urp"
    urp_tools.write_urp(TEMPLATE, good)
    bad = tmp_path / "bad.urp"
    bad.write_bytes(good.read_bytes()[:50])             # truncated gzip
    r = run(SCRIPTS / "ursim_load_check.py", "--programs-dir", tmp_path, "--host", "127.0.0.1",
            "--port", port, "--settle", "0.1", good, bad)
    assert "ACCEPTED" in r.stdout and "good.urp" in r.stdout, r.stdout + r.stderr
    assert "REJECTED" in r.stdout and "bad.urp" in r.stdout, r.stdout
    assert "rejected as expected" in r.stdout            # negative controls worked
    assert r.returncode == 1                             # one file failed
    srv.close()


def test_safety_checksum_sets_crcvalue():
    wps = json.load(open(RECORDING))["waypoints"]
    xml, _ = build_movej_program.build(wps, TEMPLATE, "x", 0.003, 0.5, 0.5, 0.5, safety_checksum="8286 7A6B")
    assert ET.fromstring(xml).get("crcValue") == "2189851243"          # 0x82867A6B
    xml2, _ = build_movej_program.build(wps, TEMPLATE, "x", 0.003, 0.5, 0.5, 0.5, safety_checksum="DEADBEEF")
    assert ET.fromstring(xml2).get("crcValue") == "3735928559"         # 0xDEADBEEF


# ---- expression variable references in the outline ---------------------------------------------
def test_outline_resolves_variable_references(tmp_path):
    xml = """<URProgram name="t" installation="default"><kinematics/><children><MainProgram><children>
      <Assignment valueSource="Expression">
        <variable name="var_1"><initializeExpression/></variable>
        <expression><ExpressionChar character="5"/><ExpressionChar character="+"/><ExpressionChar character="2"/></expression>
      </Assignment>
      <Assignment valueSource="Expression">
        <variable name="var_2"><initializeExpression/></variable>
        <expression>
          <ExpressionVariable><ProgramVariable reference="../../../../Assignment/variable"/></ExpressionVariable>
          <ExpressionChar character="*"/><ExpressionChar character="2"/>
        </expression>
      </Assignment>
      <If type="If"><expression>
          <ExpressionVariable><ProgramVariable reference="../../../../Assignment[2]/variable"/></ExpressionVariable>
          <ExpressionChar character="&gt;"/><ExpressionChar character="6"/></expression><children><Placeholder/></children></If>
    </children></MainProgram></children></URProgram>"""
    urp = tmp_path / "t.urp"
    urp_tools.write_urp(xml, urp)
    out = run(SCRIPTS / "urp_tools.py", "outline", urp).stdout
    assert "var_1 = 5+2" in out
    assert "var_2 = var_1*2" in out          # the reference resolved to the first assignment's variable
    assert "If" in out and "var_2>6" in out  # [2] picks the second Assignment
