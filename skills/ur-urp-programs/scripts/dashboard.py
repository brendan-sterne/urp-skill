#!/usr/bin/env python3
"""Minimal client for the Universal Robots Dashboard Server (TCP port 29999).

usage: dashboard.py --host HOST CMD [CMD ...]

The Dashboard Server is plain text: the server sends a greeting line, then you send one command per
line and read one reply line per command. Examples (read-only): "PolyscopeVersion", "robotmode",
"is in remote control", "get loaded program", "programState".

State-changing commands (play, pause, stop, power on, brake release, load ...) change what a real robot
does. On a real robot `play` moves the arm. This script sends whatever you ask it to: do not point it at
a real robot with a motion command unless you mean it.
"""
import argparse
import socket


def session(host, port, cmds, timeout=6.0):
    """Send commands on one connection. Returns (greeting, [(cmd, reply), ...])."""
    s = socket.create_connection((host, port), timeout=timeout)

    def read_line():
        s.settimeout(timeout)
        buf = b""
        try:
            while not buf.endswith(b"\n"):
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
        except socket.timeout:
            pass
        return buf.decode(errors="replace").strip()

    greeting = read_line()
    out = []
    for c in cmds:
        s.sendall((c + "\n").encode())
        out.append((c, read_line()))
    s.close()
    return greeting, out


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=29999)
    p.add_argument("commands", nargs="+")
    a = p.parse_args()
    greeting, out = session(a.host, a.port, a.commands)
    print(greeting)
    for c, r in out:
        print(f"> {c}\n  {r}")


if __name__ == "__main__":
    main()
