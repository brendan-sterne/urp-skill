# `.urp` format notes (PolyScope 5)

Observed on programs saved by PolyScope 5.25.1. Not an official specification.

## Container
- A `.urp` is **gzip-compressed XML** (`file` says "gzip compressed data"). Older forum posts describe a
  RAR archive; that was not the case for the files observed here.
- `.installation` files are gzip-compressed too, but contain INI sections (including safety limits) and an XML
  `<Features>` section. Read them; do not edit them.
- `.variables` files are plain XML.
- Beside each saved program PolyScope writes `name.script` (generated URScript), `name.txt` (a short outline)
  and `name.oldN` (previous saves; `old0` is the latest).
- Whether PolyScope accepts an uncompressed `.urp` has not been tested.

## Root element
```
<URProgram name="..." installation="default" installationRelativePath="default"
           directory="/programs" createdIn="5.25.1" lastSavedIn="5.25.1"
           robotSerialNumber="..." crcValue="...">
```
- `crcValue` is **not** a hash of the program: different programs saved in the same session carry the same
  number. What it is derived from is unknown. When generating a program, copy it from a program saved
  recently on the same robot.
- `<kinematics>` is the robot's calibration (`deltaTheta`, `a`, `d`, `alpha`, `jointChecksum`) and is
  repeated inside every waypoint. It is most of the file's size. Its numbers do not match nominal DH
  parameters, so do not use them for forward kinematics (use the generated `.script`, below).

## Program tree
Inside `<children>`, in order: `InitVariablesNode`, optional `SpecialSequence type="BeforeStart"` (runs once),
`MainProgram` (`runOnlyOnce` controls looping), optional `Thread` nodes, then `SubProgram` definitions.

| Node | Notes |
|---|---|
| `Move motionType="MoveJ"/"MoveL"/"MoveP"` | `speed`, `acceleration`, optional `blendRadius` (MoveP), a `<feature>` child, `Waypoint` children. For MoveJ the blend is per waypoint (`<motionParameters blendRadius="..."/>`) |
| `CircleMove` | inside a MoveP; two Waypoints: the via point and the end point |
| `Waypoint type="Fixed"/"Relative"` | `name`, `kinematicsFlags`, `<position>` (`JointAngles`, `TCPOffset`, `Kinematics`), `BaseToFeature` |
| `gui.program.direction.MoveDirectionNode` | "move in direction" step; its `Until` child has `type="DISTANCE"` or `"TOOL_CONTACT_DETECTION"` |
| `Set type="AnalogOutput"/"DigitalOutput"`, `Wait type="DigitalInput"/"NoWait"` | child `<pin referencedName="..."/>` and a value |
| `Assignment` | a `variable` and an `expression` |
| `If` (with ElseIf), `Switch`/`Case`, `Loop type="While"/"Forever"`, `Timer action="Start"/"Stop"` | control flow |
| `Thread`, `CallSubProgram` | parallel logic and subprograms |
| `Folder name="..." keepHidden="false"` | grouping; children go in `<children>` |
| `Comment comment="..."` | annotation, for example `<Comment comment="empty for now"/>` |
| `Popup`, `Halt` | message and stop |
| `SuppressedNode` | wraps a disabled node; the original is under `suppressedNode class="..."` |
| `Script` | see below |
| `Contributed strategyProgramNodeType="..."` | URCap-provided node |

`kinematicsFlags`: values `4` and `-1` were seen. How PolyScope chooses them was not determined; generators
here copy the value from a real waypoint.

## Expressions
Stored one character per element: `<ExpressionChar character="0"/>`, with
`<ExpressionToken token="False"/>` for keywords. A value `0.0` is three elements.

## Script nodes
- `<Script type="File">` has `<file>/programs/name.script</file>` and `<cachedContents>` holding a copy of the
  file's text **as of the last save of the program**. Editing the `.script` file outside PolyScope leaves the
  cache stale; when PolyScope refreshes it was not determined.
- `<Script type="Line">` holds one inline URScript line in an `<expression>`.

## URCaps
`<Contributed>` carries `strategyClass`, `strategyProgramNodeType`, `strategyURCapDeveloper`,
`strategyURCapName` and a `dataModel` of key/value pairs. A program that uses a URCap needs that URCap installed
to load properly. Palletizing programs add many `Angle`, `JointPosition` and `Length` nodes plus variables such
as `CornerItem_1..4`, `Grid_Pattern_1`, `Pallet_1_cnt`.

## Inspecting
Print a condensed tree: skip `kinematics`, expressions and checksums; keep node type, name, `motionType`, speed
and joint angles. `scripts/urp_tools.py outline` does this.
