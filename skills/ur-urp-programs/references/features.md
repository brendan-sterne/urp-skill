# Features and feature-relative moves

Observed on PolyScope 5.25.1 programs. The conversion below was checked by diff and by geometry, but a
converted file has **not** yet been confirmed to open in PolyScope (see `version-matrix.md`).

## Feature references
Each `Move` has a `<feature>` child:

- Base frame: `<feature class="GeomFeatureReference" referencedName="Joint_0_name"/>`
- A named feature from the installation: `<feature class="GeomFeatureReference" referencedName="MyPlane"/>`
- A reference to another Move's feature element, by relative path:
  `<feature class="GeomFeatureReference" reference="../../../../SpecialSequence/children/Move/feature"/>`

A program usually contains **one** real `<feature>` element (in the first Move); later Moves point at it by
path. To change the frame of one Move without changing the others, give that Move its own explicit
`<feature referencedName="..."/>` element. Editing the shared element would change every Move that points at it.

## How waypoints store the frame
A waypoint stores `JointAngles`, `TCPOffset` and a `BaseToFeature` pose. There is no stored pose in the
feature's frame.

- Base-relative Move: `BaseToFeature` is all zeros.
- Feature-relative Move: `BaseToFeature` equals the feature's pose in the base frame (observed: it matches the
  feature's `global NAME=p[...]` in the generated script).
- Pose in the feature's frame is derived: `pose_trans(pose_inv(BaseToFeature), pose_in_base)`.

## Converting a Move to feature-relative
1. Give the Move its own `<feature referencedName="X"/>`.
2. Set `BaseToFeature` of every waypoint of that Move (including circle via and end points) to X's pose in the
   base frame.
3. Leave `JointAngles` alone. The arm goes to the same physical places until X is re-taught, after which the path
   follows X.

`scripts/make_feature_relative.py` does this, refuses to overwrite its input, checks the diff size
(program name + feature element + N waypoint poses) and prints the waypoints in X's frame.

Sanity check: for a path drawn on a plane feature, every waypoint's z in that plane's frame should be about 0.
In the case this was developed on, all 16 waypoints came out within 0.03 mm.

## Getting poses
- The PolyScope-generated `.script` beside the program defines each feature (`global NAME=p[...]`, pose in
  base) and each waypoint (`<waypoint>_p=p[...]` TCP pose in base with the TCP offset applied, and
  `<waypoint>_q=[...]` joints). Use these rather than your own forward kinematics.
- A plane feature in the installation is stored as taught points, not as a pose. Take the pose from the
  generated script.
- Poses are `[x, y, z, rx, ry, rz]`, meters and a rotation vector in radians. `scripts/posemath.py` has
  `pose_trans`, `pose_inv` and conversions (numpy; includes the near-180-degree case).
