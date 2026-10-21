---
name: ur-urp-programs
description: Inspect, edit and generate Universal Robots PolyScope 5 .urp programs (unofficial). Reads the gzip-XML format, converts a Move to feature-relative, records hand-guided paths into a MoveJ program.
---

# Universal Robots `.urp` programs

Unofficial, community-maintained, and based on reverse engineering: UR does not document the
`.urp` format and it changes between PolyScope versions. Treat everything here as "observed on the
versions listed in `references/version-matrix.md`", not as a specification.

## Non-negotiable safety rules

Generated or edited programs **move a real robot arm**. Always:

1. **Never overwrite a program.** Write a new file next to the original, with a new name, and keep a
   backup of anything you touch on a robot (`cp -p x x.bak`).
2. **Never run a program for the user.** Upload or save it, tell the user exactly what changed, and let them
   open it in PolyScope, set a low speed, clear the area and press play. Do not send `play`, `power on` or
   `brake release` unless the user explicitly asks for that specific action.
3. **Never use another robot's program as a template.** The serial number, calibration block and
   `crcValue` are robot-specific. Use a program saved by PolyScope on the *target* robot.
4. **Diff before you hand it over.** After any edit, compare against the original and confirm that only the
   intended lines changed. Say plainly that PolyScope has not yet opened the file, because that is true until
   the user does it.
5. **Do not put credentials in files, notes or logs.** Pass passwords through environment variables.
6. If anything about a file looks different from `references/format.md` (new attributes, a different root
   element, not gzip), stop and tell the user rather than guessing.

## Workflow

1. **Get the files.** Programs live in `/programs` on the robot, each with companions `name.script`
   (the generated URScript), `name.txt` and `name.oldN`. Copy them with `scp` (SSH must be enabled) or a USB
   stick. See `references/robot-access.md`.
2. **Look before editing.** `scripts/urp_tools.py outline prog.urp` prints a condensed tree; `unpack` gives
   the raw XML. A `.urp` is gzip-compressed XML, mostly calibration noise, so always collapse it.
3. **Edit with a script, not by hand**, and keep edits minimal:
   - `scripts/make_feature_relative.py` makes one Move relative to a feature and prints the waypoints in the
     feature's frame.
   - `scripts/record_path.py` + `scripts/build_movej_program.py` turn a hand-guided path into one `MoveJ`.
4. **Verify.** The scripts parse the XML, check the diff size and refuse to overwrite inputs. Add your own
   check (for example, waypoints that should lie on a plane should have z of about 0 in that plane's frame).
5. **Check that PolyScope's loader accepts it**, if URSim is available: `scripts/ursim_load_check.py` loads the
   file in URSim and runs negative controls so a pass means something (`references/ursim.md`). This shows the
   file parses; it does not show it looks right on a pendant or is right for your robot.
6. **Hand over** as a new file, with the checklist in rule 2.

## Key facts (details in `references/`)

- `.urp` = gzip XML. Root `<URProgram>` with a `<kinematics>` calibration block and a `<children>` tree:
  `InitVariablesNode`, optional `SpecialSequence type="BeforeStart"`, `MainProgram`, optional `Thread`s and
  `SubProgram`s. Expressions are stored one character per element.
- A waypoint stores `JointAngles`, a `TCPOffset` and a `BaseToFeature` pose, not a pose in the feature's frame.
  PolyScope commands `pose_trans(feature_now, pose_trans(pose_inv(BaseToFeature), waypoint_pose_in_base))`.
  So switching a Move's feature after teaching shifts the path unless `BaseToFeature` is set to that feature's
  pose (`make_feature_relative.py` does this; verified against PolyScope's own script generator).
- The generated `.script` next to a program is the best source of numbers: it defines each feature as
  `global NAME=p[...]` and each waypoint's base-frame TCP pose as `<waypoint>_p=p[...]`.
- A `Script type="File"` node caches the file's text inside the `.urp` (`cachedContents`), so editing the
  `.script` file outside PolyScope leaves the cache stale.
- `crcValue` in the header is the robot's **safety checksum** (the corner code on the pendant, hex to decimal),
  not a hash of the program. Use the target robot's current value when generating a program.
- Saving through PolyScope rewrites the header, kinematics and float formatting (see `references/format.md`),
  so compare programs structurally, not as text.
- Poses are `[x, y, z, rx, ry, rz]`: meters and an axis-angle rotation vector in radians (not roll/pitch/yaw).

## Files in this skill

- `references/format.md`: node types, expressions, Script nodes, URCaps, checksums.
- `references/features.md`: feature references, `BaseToFeature`, converting a Move, getting poses.
- `references/robot-access.md`: network, dashboard, SSH and `scp` gotchas, real-time packet layout.
- `references/node-catalog.md`: every node on PolyScope's node list as PolyScope writes it with default settings
  (plus the rules it enforces); the full XML is in `examples/node-defaults-5.26.1.xml`.
- `references/ursim.md`: running URSim, checking that PolyScope accepts a file, and driving the pendant over VNC.
- `references/urscript-notes.md`: pose functions and snippets that came up while doing this.
- `references/version-matrix.md`: what was verified, on which PolyScope version, and what was not.
- `scripts/`: `urp_tools.py`, `make_feature_relative.py`, `record_path.py`, `build_movej_program.py`,
  `ursim_load_check.py`, `dashboard.py`, `pendant_ui.sh`, `posemath.py` (Python 3, numpy for the pose maths).
