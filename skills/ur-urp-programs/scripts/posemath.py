"""Small pose maths for Universal Robots poses [x, y, z, rx, ry, rz].

Positions are in meters, (rx, ry, rz) is an axis-angle rotation vector in radians
(not roll/pitch/yaw). Requires numpy.
"""
import math
import re

import numpy as np


def rv2R(rv):
    """Rotation vector -> 3x3 rotation matrix (Rodrigues)."""
    rv = np.asarray(rv, float)
    th = float(np.linalg.norm(rv))
    if th < 1e-12:
        return np.eye(3)
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def R2rv(R):
    """3x3 rotation matrix -> rotation vector, angle in [0, pi]."""
    c = max(-1.0, min(1.0, (np.trace(R) - 1) / 2))
    th = math.acos(c)
    if th < 1e-12:
        return np.zeros(3)
    if th > math.pi - 1e-6:
        # Near 180 degrees the antisymmetric part vanishes; use B = (R + I)/2 = k k^T.
        B = (R + np.eye(3)) / 2
        i = int(np.argmax(np.diag(B)))
        k = B[:, i] / math.sqrt(max(B[i, i], 1e-15))
        return k / np.linalg.norm(k) * th
    k = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * math.sin(th))
    return k * th


def pose2T(p):
    T = np.eye(4)
    T[:3, :3] = rv2R(p[3:])
    T[:3, 3] = p[:3]
    return T


def T2pose(T):
    return np.concatenate([T[:3, 3], R2rv(T[:3, :3])])


def pose_trans(a, b):
    """URScript pose_trans: start at frame a, then apply b measured in a's axes."""
    return T2pose(pose2T(np.asarray(a, float)) @ pose2T(np.asarray(b, float)))


def pose_inv(a):
    return T2pose(np.linalg.inv(pose2T(np.asarray(a, float))))


def script_poses(path):
    """Parse `global NAME_p=p[...]` lines (waypoint TCP poses in the base frame)
    from a PolyScope-generated .script file. Returns {name: [6 floats]}."""
    out = {}
    for line in open(path):
        m = re.match(r"\s*global (\w+)_p=p\[([^\]]+)\]", line)
        if m:
            out[m.group(1)] = [float(v) for v in m.group(2).split(",")]
    return out


def script_feature_pose(path, feature):
    """Return the pose of a named feature in the base frame from a generated .script
    (`global <feature>=p[...]`)."""
    pat = re.compile(r"\s*global %s=p\[([^\]]+)\]" % re.escape(feature))
    for line in open(path):
        m = pat.match(line)
        if m:
            return [float(v) for v in m.group(1).split(",")], m.group(1)
    raise KeyError(f"feature {feature!r} not found in {path}")
