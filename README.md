# urp-skill

An **unofficial** agent skill (and a few small Python tools) for working with Universal Robots
**PolyScope 5 `.urp` programs**: read them, make targeted edits, and generate simple programs.

> Not affiliated with, endorsed by or supported by Universal Robots A/S. "Universal Robots", "UR" and
> "PolyScope" are trademarks of their owner and are used here only to describe compatibility.
> The `.urp` format is undocumented and changes between versions. Everything here comes from observing files
> saved by the authors' own robots and/or ursim. **Read [SAFETY.md](SAFETY.md) before using anything on a real robot.**

## What's in it

```
skills/ur-urp-programs/
  SKILL.md                       the skill (for Claude Code and other agents that read SKILL.md)
  references/                    format notes, node catalog (every node and variant), features, URCaps, URSim,
                                 robot access, URScript notes, version matrix
  scripts/
    urp_tools.py                 unpack / pack / outline a .urp
    make_feature_relative.py     make one Move relative to a feature; prints waypoints in its frame
    record_path.py               record a hand-guided path from the robot (read-only)
    build_movej_program.py       turn a recording into one MoveJ program
    ursim_load_check.py          check that PolyScope (in URSim) accepts files, with negative controls
    dashboard.py                 minimal Dashboard Server client (port 29999)
    pendant_ui.sh                send clicks/keys to URSim's pendant over VNC and take a screenshot
    posemath.py                  pose_trans / pose_inv / rotation-vector maths (numpy)
examples/                        a synthetic recording, and PolyScope's own XML for every node type and many variants (5.26.1)
tests/                           pytest suite using synthetic fixtures only
```

## Status

Summary (details in [`references/version-matrix.md`](skills/ur-urp-programs/references/version-matrix.md)):

- **Verified** on programs saved by PolyScope 5.13.1, 5.25.1 and 5.26.1: the file is gzip XML with the same
  layout; node and field meanings (`references/format.md`, `references/node-catalog.md`); how feature-relative
  waypoints are stored and what PolyScope does with them; that `crcValue` is the robot's safety checksum; what
  PolyScope rewrites on save; how expressions and back-references are encoded; that the scripts produce exactly the
  intended diff.
- **Verified in URSim 5.26.1**: PolyScope's loader accepts the programs these tools generate and rejects corrupt
  files (with negative controls); a feature-converted program opens in the program tree, and PolyScope's own
  regenerated script commands the original targets.
- **Not yet confirmed**: that a generated program looks right on a **physical** pendant, or runs as intended.
  Please try it with the speed slider low and tell us what happens (open an issue with your PolyScope version).
- Third-party URCaps: External Control and Schmalz install in URSim and their nodes work; the Robotiq and OnRobot
  URCaps fail at startup in URSim, so their node XML has to come from programs saved on a real robot
  (`references/urcaps.md`).
- PolyScope X (`.urpx`) is out of scope.

## Scope and limits

- **Robots and versions:** UR e-Series with PolyScope 5.x (programs from 5.13.1 to 5.26.1 were read; 5.25.1 and 5.26.1 were
  used for edits). CB3 robots and PolyScope X are not covered.
- `record_path.py` decodes the **e-Series real-time packet** (1220 bytes on 5.25.1). Other layouts, including CB3, differ, and
  the script warns when the packet size is unexpected.
- `build_movej_program.py` writes one base-frame `MoveJ` of joint waypoints that runs once, and needs a template program saved
  by PolyScope on the same robot.
- `make_feature_relative.py` needs the `.script` that PolyScope generates next to the program, the feature must exist in the
  loaded installation, nested Moves are not supported, and waypoint names that PolyScope sanitizes in the script (spaces and
  similar) may not match (it warns).
- `ursim_load_check.py` relies on the dashboard reply texts seen in URSim 5.26.1, and `pendant_ui.sh` is only a wrapper: the
  click coordinates in `references/ursim.md` are for URSim 5.26.1's 1280x800 pendant (UR3 model) and will differ elsewhere.
- The example XML files were produced by URSim 5.26.1 (UR3) with its stock installation, so names such as `flange`, `hande`
  and `back_wall` are URSim's, not yours.
- `urp_tools.py`, `dashboard.py` and `posemath.py` are general. Python 3 and numpy are required; some network setup commands in
  `references/robot-access.md` are for macOS.

## Use as a Claude Code skill

Copy or symlink the skill folder into a skills directory:

```
mkdir -p ~/.claude/skills
cp -R skills/ur-urp-programs ~/.claude/skills/
```

The scripts use Python 3 and `numpy` (`pip install numpy`); tests use `pytest`.

## Use the scripts directly

```
python3 skills/ur-urp-programs/scripts/urp_tools.py outline my_program.urp
python3 skills/ur-urp-programs/scripts/ursim_load_check.py --programs-dir ~/ursim-programs my_program.urp

python3 skills/ur-urp-programs/scripts/make_feature_relative.py my_program.urp my_program.script --list
python3 skills/ur-urp-programs/scripts/make_feature_relative.py my_program.urp my_program.script \
    --move-index 1 --feature MyPlane --out my_program_feature.urp --name "My program feature"

python3 skills/ur-urp-programs/scripts/record_path.py --host 192.0.2.10 --out path.json
python3 skills/ur-urp-programs/scripts/build_movej_program.py path.json template_from_your_robot.urp \
    replay.urp --name replay        # add --safety-checksum "XXXX XXXX" (the pendant's corner code) if it changed
```

`template_from_your_robot.urp` must be a program saved by PolyScope on the **same** robot; it supplies the
calibration block, TCP offset and header. Outputs are always new files.

## Tests

```
python3 -m pytest
```

The tests use invented numbers only (a synthetic program, a synthetic recording, and a fake robot server for
the recorder). No robot is required.

## Contributing

Reports are the most valuable contribution: PolyScope version, what you tried, whether the file opened, and
whether anything differed from `references/format.md`. Please do not attach programs, installations or
screenshots that contain serial numbers, calibration data, customer information or credentials.

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). The software is provided "as is", without
warranty of any kind. You are responsible for the safety of any robot cell you run it on.
