#!/usr/bin/env python3
"""Record a hand-guided path from a UR e-Series robot. Read-only: it only listens.

usage: record_path.py --host ROBOT_IP [--out recorded_path.json]

Listens to the real-time interface (port 30003) and writes joint-angle waypoints sampled
at 4 Hz.

  * Arms once the robot has been still for 1 s and remembers that resting pose.
  * Starts recording when the TCP moves more than --start-mm from the resting pose, or any
    joint moves more than --start-rad (this catches a pure wrist twist).
  * Stops when the TCP has moved less than --stop-mm (and joints less than --stop-rad)
    over the last --hold seconds.
  * The first waypoint is the resting pose; the last is the final resting pose.

Real-time packet layout (e-Series, big-endian doubles), offsets from the UR client-interface
documentation: time at byte 4, q_actual at 252, actual TCP pose at 444. The packet was
1220 bytes on PolyScope 5.25.1 (the only version this was checked against). If your robot
sends a different size the script warns, because the offsets may differ.
"""
import argparse
import json
import math
import socket
import struct
import sys
import time

EXPECTED_PACKET = 1220


def read_packet(sock):
    buf = b""
    while len(buf) < 4:
        chunk = sock.recv(4 - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    n = struct.unpack("!i", buf[:4])[0]
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    t = struct.unpack("!d", buf[4:12])[0]
    q = list(struct.unpack("!6d", buf[252:300]))
    tcp = list(struct.unpack("!6d", buf[444:492]))
    return n, t, q, tcp


def dist(a, b):
    return math.dist(a[:3], b[:3])


def jmax(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def record(a):
    sock = socket.create_connection((a.host, a.port), timeout=10)
    window, rest, state = [], None, "ARMING"
    waypoints, next_t, t_rec0 = [], None, None
    wall0 = time.time()
    warned = False
    log(f"connected to {a.host}:{a.port}; waiting for the robot to be still...")
    while True:
        n, t, q, tcp = read_packet(sock)
        if n != EXPECTED_PACKET and not warned:
            log(f"WARNING: packet is {n} bytes (expected {EXPECTED_PACKET}); offsets may differ")
            warned = True
        window.append((t, q, tcp))
        while window and t - window[0][0] > a.hold:
            window.pop(0)
        still = (t - window[0][0] >= a.hold - 0.01 and
                 all(dist(w[2], tcp) < a.stop_mm / 1e3 and jmax(w[1], q) < a.stop_rad for w in window))

        if state in ("ARMING", "WAITING") and time.time() - wall0 > a.wait:
            log("timed out; nothing recorded")
            return None
        if state == "ARMING":
            if still:
                rest, state = (q, tcp), "WAITING"
                log("armed. Start moving the arm (freedrive) whenever you are ready.")
        elif state == "WAITING":
            if dist(tcp, rest[1]) > a.start_mm / 1e3 or jmax(q, rest[0]) > a.start_rad:
                state, t_rec0 = "RECORDING", t
                waypoints.append({"t": 0.0, "q": rest[0], "tcp": rest[1]})
                next_t = t + a.period
                log("motion detected: recording")
        else:  # RECORDING
            while t >= next_t:
                waypoints.append({"t": round(next_t - t_rec0, 3), "q": q, "tcp": tcp})
                next_t += a.period
            if still:
                cutoff = t - a.hold - t_rec0          # drop samples from the stationary hold
                waypoints = [w for w in waypoints if w["t"] < cutoff] or waypoints[:1]
                waypoints.append({"t": round(t - t_rec0, 3), "q": q, "tcp": tcp})
                log(f"robot stopped: {len(waypoints)} waypoints over {waypoints[-1]['t']:.2f} s")
                return waypoints
            if t - t_rec0 > a.max_record:
                log("max record time reached; saving what we have")
                waypoints.append({"t": round(t - t_rec0, 3), "q": q, "tcp": tcp})
                return waypoints


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--host", required=True, help="robot IP address")
    p.add_argument("--port", type=int, default=30003, help="real-time interface port")
    p.add_argument("--out", default="recorded_path.json")
    p.add_argument("--period", type=float, default=0.25, help="seconds between waypoints (0.25 = 4 Hz)")
    p.add_argument("--start-mm", type=float, default=2.0)
    p.add_argument("--stop-mm", type=float, default=1.0)
    p.add_argument("--start-rad", type=float, default=0.003)
    p.add_argument("--stop-rad", type=float, default=0.002)
    p.add_argument("--hold", type=float, default=1.0, help="seconds still before the path ends")
    p.add_argument("--wait", type=float, default=600, help="give up waiting after this many seconds")
    p.add_argument("--max-record", type=float, default=180)
    a = p.parse_args()
    wps = record(a)
    if wps is None:
        return 2
    with open(a.out, "w") as f:
        json.dump({"host": a.host, "sample_hz": 1 / a.period, "waypoints": wps}, f, indent=1)
    log(f"saved {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
