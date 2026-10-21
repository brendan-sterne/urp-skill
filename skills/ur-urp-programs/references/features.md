# Features and feature-relative moves

Observed on PolyScope 5.25.1 programs and in URSim 5.26.1. The key formula below was obtained from
PolyScope's own generated script, and the conversion in this file was verified against it (see
"Verification").

## Feature references
Each `Move` has a `<feature>` child:

- Base frame: `<feature class="GeomFeatureReference" referencedName="Joint_0_name"/>`
- A named feature from the installation: `<feature class="GeomFeatureReference" referencedName="MyPlane"/>`
- A reference to another Move's feature element, by relative path:
  `<feature class="GeomFeatureReference" reference="../../../../SpecialSequence/children/Move/feature"/>`

A program usually contains **one** real `<feature>` element (in the first Move); later Moves point at it by
path. To change the frame of one Move without changing the others, give that Move its own explicit
`<feature referencedName="..."/>` element. Editing the shared element would change every Move that points at it.

## What PolyScope does with a waypoint (the formula)
A waypoint stores `JointAngles`, `TCPOffset` and a `BaseToFeature` pose. From the joints, PolyScope computes the
TCP pose in the **base frame** (the generated script's `<waypoint>_p`). The target it commands is:

```
target_in_base = pose_trans(feature_now, pose_trans(pose_inv(BaseToFeature), waypoint_p_in_base))
```

(`feature_now` is the feature's current pose in the base frame; the generated script writes the middle term as a
literal pose.) Consequences:

- If `BaseToFeature` equals the feature's pose, the target is the original physical position, and the path
  **follows the feature** if the feature is later re-taught or moved.
- If `BaseToFeature` is all zeros (the waypoint was taught in the base frame) and the Move's feature is switched
  to a feature **afterwards**, the path is reinterpreted as being relative to the feature and shifts in space by the
  feature's pose. Switching a Move's feature in the UI after teaching does not rewrite `BaseToFeature`
  (seen with a point feature in URSim 5.26.1: the XML changed the feature reference only).
- A waypoint **taught while the feature is selected** gets `BaseToFeature` = that feature's pose at that moment.
- A `Relative` waypoint is `movej(pose_add(get_target_tcp_pose(), pose_sub(to_p, from_p)))` in the script: it stores a
  from-position and a to-position (`relativeFromPosition` and `position`) and moves by their difference.

## Converting a Move to feature-relative (keeping the path where it is)
1. Give the Move its own `<feature referencedName="X"/>`.
2. Set `BaseToFeature` of every waypoint of that Move (including circle via and end points) to X's pose in the
   base frame.
3. Leave `JointAngles` alone. The arm goes to the same physical places, and the path follows X from then on.

`scripts/make_feature_relative.py` does this, refuses to overwrite its input, checks the diff size (program name +
feature element + N waypoint poses) and prints the waypoints in X's frame.

## Verification
Done in URSim 5.26.1 (2026-10-21) on a real 16-waypoint program converted this way:
- The converted file **opens in PolyScope's program tree** and displays correctly (with the lab installation loaded
  so that the feature exists).
- After saving it through the UI, PolyScope's regenerated script used `pose_trans(MyPlane, pose_trans(<middle>,
  <wp>_p))` for every waypoint, with `<middle>` equal to `pose_inv(MyPlane)` (difference 5e-13) and `<wp>_p` equal to
  the original program's base pose.
- So the commanded targets equal the original base-relative targets (worst difference 6.6e-13 m over all 16
  waypoints).

The feature must exist in the installation that is loaded; otherwise the generated script has no pose for it.

Sanity check that also works without URSim: for a path drawn on a plane feature, every waypoint's z in that plane's
frame should be about 0 (all 16 were within 0.03 mm).

## Getting poses
- The PolyScope-generated `.script` beside the program defines each feature (`global NAME=p[...]`, pose in
  base) and each waypoint (`<waypoint>_p=p[...]` TCP pose in base with the TCP offset applied, and
  `<waypoint>_q=[...]` joints). Use these rather than your own forward kinematics.
- A plane feature in the installation is stored as taught points, not as a pose. Take the pose from the
  generated script.
- Poses are `[x, y, z, rx, ry, rz]`, meters and a rotation vector in radians. `scripts/posemath.py` has
  `pose_trans`, `pose_inv` and conversions (numpy; includes the near-180-degree case).
