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
- `crcValue` is the robot's **safety checksum** (the value the pendant shows in the top-right corner as two
  groups of four hex digits, for example `8286 7A6B`) written as an unsigned 32-bit decimal
  (`0x82867A6B` = `2189851243`). It is not a hash of the program: it is identical for every program saved
  while the safety configuration is unchanged, and it changes when the installation's safety settings
  change. Confirmed in URSim with a controlled pair (same program saved under two installations gave two
  values, and each equalled the corner code shown for that installation), and consistent with files from two
  real robots, whose values changed in steps as their safety configurations changed. When generating a
  program, use the current safety checksum of the target robot: read it from the pendant corner, or copy it
  from a program saved on that robot since its last safety change. URSim loaded files whose `crcValue` did
  not match its own without complaint (what a physical pendant does on a mismatch was not tested).
- `<kinematics>` is the robot's calibration (`deltaTheta`, `a`, `d`, `alpha`, `jointChecksum`) and is
  repeated inside every waypoint. It is most of the file's size. Its numbers do not match nominal DH
  parameters, so do not use them for forward kinematics (use the generated `.script`, below).

## What PolyScope rewrites when it saves
Observed by loading a real program in URSim 5.26.1 and saving it unchanged through the UI:
- `crcValue` becomes the current robot's safety checksum (see above); `robotSerialNumber` becomes the
  current robot's; `lastSavedIn` becomes the current version while `createdIn` keeps the original.
- `directory` becomes the real folder and `installationRelativePath` is recomputed relative to the program's
  folder (for example `../default` for a program saved one folder below the installation).
- The top-level `<kinematics>` becomes the current robot's calibration. A waypoint's `<Kinematics>` keeps the
  calibration it was taught with.
- Saving again without changes is stable (same `crcValue`, same content). Floating-point values are
  re-formatted (`-0.34945677303969` became `-0.3494567730396901`), so do not compare text across saves.
- Companion files `name.script` and `name.txt` are written, and the `*` modified marker clears.
- The `*` marker after a program name also appears when a real, known-good program is loaded, so it does not
  mean the file is bad.

## Back-references
PolyScope serializes repeated objects with XStream-style references. A waypoint's `<Kinematics>` is written as
`<Kinematics reference="../../../../../../../../kinematics"/>` when it equals the robot's current top-level
calibration, and as an explicit block when it does not (18 explicit and 1 reference in one real program; all
explicit after saving under a different calibration). A Move's `<feature>` can likewise be a relative-path
`reference`. Both forms are valid; a generator can always write the explicit form.

## Container across versions
Programs saved by PolyScope 5.13.1, 5.25.1 and 5.26.1 were all gzip-compressed XML with the same root element
and tree layout. `createdInPolyscopeProgramVersion` was `0` or `2` and `lastSavedInPolycopeProgramVersion`
was `2` (the attribute name really is spelled "Polycope").

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
| `Wait type="Sleep"` | child `<waitTime>` holds the duration |
| `Placeholder` | an unfinished node left in the tree (seen as a program's only node) |
| `SuppressedNode` | wraps a disabled node; the original is under `suppressedNode class="..."` |
| `Script` | see below |
| `Contributed strategyProgramNodeType="..."` | URCap-provided node |

`kinematicsFlags`: `-1` is a waypoint that has not been taught (it has no `<position>`), and `4` is a taught
waypoint (seen on every taught waypoint, from real robots and URSim). Other values were not seen; generators here
write `4` for waypoints with joint angles.

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
