# Node catalog (PolyScope 5.26.1, URSim)

Every node on PolyScope's node list, added once from the Program tab with its default settings, saved, and
read back. The full XML is in `examples/node-defaults-5.26.1.xml`. This describes what PolyScope itself writes,
so it is the safest form to copy when generating a program. Variants of each node (for example the other
Wait types) are listed where they have been explored; the rest are marked as not yet explored.

Observed in URSim 5.26.1 (UR3 model), 2026-10-21. Other versions were not checked.

## Rules PolyScope enforces (messages shown by the UI)
- A **Direction** node can only be inserted inside a MoveL or MoveP ("only allowed inside a MoveL or MoveP").
- **Event** (and **Thread**) must be at the top level: select a top-level row (such as `Robot Program`) before
  adding. They are written after `MainProgram`, as siblings of it.
- Changing a Move's type (MoveJ, MoveL, MoveP) keeps its waypoints and switches its default speed and
  acceleration units (joint `°/s`, `°/s²` for MoveJ; tool `mm/s`, `mm/s²` for MoveL/MoveP).

## Document structure
`<children>` of the root, in order: `InitVariablesNode`, optional `SpecialSequence type="BeforeStart"` (only if
"Add Before Start Sequence" is ticked), `MainProgram`, then top-level `Event`, `Thread` and `SubProgram` nodes.
`MainProgram runOnlyOnce="false"` corresponds to "Program Loops Forever" being ticked.

`InitVariablesNode` lists the variables that have an **initial value** (for example `Pallet_1_cnt = 1`,
`qNearApproach = [0,0,0,0,0,0]`); variables with no initial value (`var_1`, `timer_1`) appear only where they are
declared, inside their node.

## Basic nodes
| UI node | XML as written with defaults | Notes |
|---|---|---|
| Move | `<Move motionType="MoveL" speed="0.25" acceleration="1.2" useActiveTCP="true" positionType="CartesianPose" optimoveEnabled="false" optiMoveSpeed="0.3" optiMoveAcceleration="0.09">` + `<feature class="GeomFeatureReference" referencedName="Joint_0_name"/>` + `<children>` | Added as MoveJ (UI default 60 °/s, 80 °/s²; XML `speed="1.0471975511965976" acceleration="1.3962634015954636"`), with one child Waypoint. Panel: type MoveJ/MoveL/MoveP, Feature (Base), Set TCP (Use active TCP), Motion Controls (Classic), speed and acceleration, "Use joint angles" |
| Waypoint | `<Waypoint type="Fixed" name="Waypoint_2" kinematicsFlags="-1"><motionParameters/></Waypoint>` | **A waypoint that has not been taught has no `<position>` element and `kinematicsFlags="-1"`.** Taught waypoints seen in real programs have `<position>` and `kinematicsFlags="4"`. Panel: Fixed / Relative / Variable position, Set Waypoint, Edit pose, Stop at this point or Blend with radius, shared or own speed, "Add Until" |
| Direction | `<gui.program.direction.MoveDirectionNode selectedDirection="XPlus"><children><Until type="NONE" allowActions="false"/></children></gui.program.direction.MoveDirectionNode>` | Inside MoveL/MoveP only. Written before the waypoints. Panel: shared or specific feature, direction (X+ ...) or direction vector, shared parameters or own tool speed (250 mm/s) and acceleration (1200 mm/s²) |
| Wait | `<Wait type="Undefined"/>` | Nothing chosen yet. Options: No Wait, Wait N seconds (default 0.01), Wait for Digital Input (High/Low), Wait for Analog Input (> or <, mA), Wait for expression. Configured Wait types: `Sleep` (see `format.md`) and others, not yet explored |
| Set | `<Set type="Undefined"/>` | Configured forms (analog/digital output) are in `format.md`; the UI options were not yet explored |
| Popup | `<Popup type="Message" haltProgram="false" inputType="Text"/>` | |
| Halt | `<Halt/>` | |
| Comment | `<Comment/>` | A comment with text is `<Comment comment="..."/>` |
| Folder | `<Folder name="Folder" keepHidden="false"><children><Placeholder/></children></Folder>` | An empty container always holds `<Placeholder/>` |
| Set Payload | `<SetPayload workpieceName="no_workpiece" payloadTransitionTime="0.05"/>` | Refers to a named payload from the installation (the `.txt` outline shows its mass 1.03 kg, centre of gravity and inertia) |

## Advanced nodes
| UI node | XML as written with defaults | Notes |
|---|---|---|
| Loop | `<Loop type="Forever"><children><Placeholder/></children></Loop>` | Other loop types (While, count) not yet explored |
| SubProg | `<CallSubProgram/>` | Shows as `Call` in the tree; no target chosen yet. The subprogram definitions seen in real files are top-level `SubProgram` nodes |
| Assignment | `<Assignment valueSource="Expression"><variable name="var_1" prefersPersistentValue="false" favourite="false"><initializeExpression/></variable><expression/></Assignment>` | The other value source seen in real programs is `Operator` (asks the operator) |
| If | `<If type="If" checkContinuously="false"><expression/><children><Placeholder/></children></If>` | `type="ElseIf"` seen in real programs |
| Script | `<Script type="Line"><expression/></Script>` | `type="File"` seen in real programs (see `format.md`) |
| Event | `<Event><expression/><children><Placeholder/></children></Event>` | Top level only |
| Thread | `<Thread name="Thread_1" runOnlyOnce="false"><children><Placeholder/></children></Thread>` | Top level only. Options: Loops Forever (ticked), Track program execution |
| Switch | `<Switch><expression/></Switch>` | `Case` children are added from the node's panel; not yet explored |
| Timer | `<Timer action="Undefined"><variable name="timer_1" prefersPersistentValue="false" favourite="false"><initializeExpression/></variable></Timer>` | `action="Start"/"Stop"` seen in real programs |
| Home | `<SafeHome positionOptionType="SPEED_AND_ACCELERATION" speed="1.0471975511965976" acceleration="1.3962634015954636" nextMotionTime="2.0"/>` | UI name "Home", XML name `SafeHome`. Moves to the home position defined in the installation, by speed/acceleration or by time (2 s) |

## Templates
| UI node | XML | Notes |
|---|---|---|
| Seek | `<Stack type="Undefined" itemThickness="0.0" motionType="MoveL" speed="0.25" acceleration="1.2" useActiveTCP="true" positionType="CartesianPose" optimoveEnabled="false" optiMoveSpeed="0.3" optiMoveAcceleration="0.09">` with `<nextPositionExpression/>`, `<foundPoseVariable name="pose_1" .../>`, `<feature reference="../../Move/feature"/>` | UI name "Seek", XML name `Stack`. The feature is a relative-path reference to an earlier Move's feature |
| Force | `<Force type="Simple">` with `<feature reference=.../>`, `<selection value="0, 0, 1, 0, 0, 0"/>`, `<wrench .../>`, `<limitsForce .../>`, `<limitsMotion .../>`, `<children><Placeholder/></children>` | |
| Palletizing | `<Contributed strategyClass="PalletNode" strategyProgramNodeType="Palletizing" strategyURCapDeveloper="Universal Robots" strategyURCapName="polyscope-pallet-impl">` with a `dataModel` of variables (`Pallet_1`, `Pallet_1_cnt`, `_lno`, `_lct`, `_sep`, `_tct`, `qNearApproach`, `referencePoint`, `separatorPoint`) and `Patterns`, `Layers`, `At Each Item` child Contributed nodes | **A built-in node written in the URCap `Contributed` form**; the same node seen in real programs |
| Conveyor Tracking | `<Contributed strategyClass="ConveyorTracking" strategyProgramNodeType="Conveyor Tracking" strategyURCapDeveloper="Universal Robots" strategyURCapName="Conveyor Tracking">` | Shown as "(disabled)" in the tree until a conveyor is configured |
| Screwdriving | `<Contributed strategyClass="ScrewdrivingProgramNode" strategyProgramNodeType="Screwdriving" strategyURCapDeveloper="Universal Robots" strategyURCapName="polyscope-screwdriving-impl">` with variables `SD_1`, `SD_1_td`, `SD_1_tID` (-1), `SD_1_time`, `SD_1_pos`, `SD_1_dist`, `SD_1_run` (1) and an `Until` Contributed child holding a `Comment` | Warns that a Start I/O and TCP must be defined in the installation |

## Configured variants (URSim 5.26.1, 2026-10-21)
Each variant was set up in the UI, saved, and read back.

**Wait**
| UI option | XML |
|---|---|
| Wait N seconds | `<Wait type="Sleep"><waitTime>0.01</waitTime></Wait>` |
| Wait for Digital Input | `<Wait type="DigitalInput"><pin referencedName="digital_in[0]"/><digitalValue>0</digitalValue></Wait>` (Low = 0) |
| Wait for Analog Input | `<Wait type="AnalogInput"><analogComparison>0</analogComparison><analogValue>4.0</analogValue></Wait>` (the input pin is added when one is chosen) |
| Wait for expression | `<Wait type="Condition"><expression/></Wait>` |
| No Wait | `<Wait type="NoWait"/>` |

The pin is always stored under its **canonical name** (`digital_in[0]`), even when you pick a user-named input such as
`switch1` from the dropdown. The installation maps names to pins.

**Set**
| UI option | XML |
|---|---|
| Set Digital Output | `<Set type="DigitalOutput"><pin referencedName="digital_out[2]"/><digitalValue>1</digitalValue></Set>` (named output `conveyor_on` is `digital_out[2]`; High/On = 1) |
| Set Analog Output | `<Set type="AnalogOutput"><pin referencedName="analog_out[0]"/><analogValue>4.0</analogValue></Set>` |
| Set Single Pulse | `<Set type="SingleDigitalPulseActionState"><SingleDigitalPulseActionState hiPulseInSeconds="0.5"><pin referencedName="digital_out[0]"/></SingleDigitalPulseActionState></Set>` |
| other options | "Set `<Output>` to f(x)", "Increment installation variable by one" and the "Set TCP" checkbox were seen in the UI but not saved |

**Popup:** `<Popup type="Warning" haltProgram="true" message="hello" inputType="Text"/>`. Types: Message, Warning, Error;
"Halt program execution at this popup" is `haltProgram`.

**Loop**
| UI option | XML |
|---|---|
| Loop always | `<Loop type="Forever">` |
| Loop X times | `<Loop type="Counting" count="0"><loopVariable name="Loop_1" .../>...` |
| Loop when expression is True | `<Loop type="While" checkContinuously="true"><expression/>...` |

**If / Else:** "Add ElseIf" and "Add Else" create **sibling** nodes, not nested ones: `<If type="If">`,
`<If type="ElseIf">`, `<If type="Else">`, each with `checkContinuously="false"`, `<expression/>` and a `<children>`
(an empty one holds `<Placeholder/>`). Even `Else` carries an empty `<expression/>`.

**Waypoint types** (dropdown: Fixed, Relative, Variable position)
- Taught Fixed waypoint (after "Set Waypoint"): `<Waypoint type="Fixed" name="Waypoint_2" kinematicsFlags="4"><motionParameters/><position><JointAngles .../><TCPOffset .../><Kinematics .../></position><BaseToFeature .../></Waypoint>`. `kinematicsFlags` is `4` for a taught waypoint, `-1` for an untaught one.
- Relative: `<Waypoint type="Relative" ...>` holds `<relativeFromPosition>` (JointAngles, TCPOffset, Kinematics) and `<position>` (the "to" point), both taught with "Set Point". The script moves by `to_p - from_p` from the current pose.
- Variable position was in the dropdown but not configured.

**Move with a feature.** Dropdown choices were Base, Tool and the installation's point features. The XML change is
only `<feature referencedName="back_wall"/>`. See `features.md` for what that does to taught waypoints (it
reinterprets them unless `BaseToFeature` is set accordingly).

**Teaching in URSim.** "Set Waypoint" / "Set Point" need the simulated robot powered on (power button, ON, then START;
the dashboard shows `POWER_OFF` until then). The Move screen then accepts the current pose with OK, and jogging
needs the arrow held down (press and hold the mouse button for a few seconds).

**Flow control and structure**
| UI | XML |
|---|---|
| Switch + "+ Case" + "Default Case" | `<Switch><expression/><children>` with `<Case caseValue="1">`, `<Case caseValue="2">` and the default case as `<Case caseValue="2147483647">` (the maximum 32-bit integer); each case has `<children>` (empty = `<Placeholder/>`) |
| Timer Start / Stop / Reset | `<Timer action="Start"/"Stop"/"Reset">` each with its own `<variable name="timer_N" .../>` |
| Assignment, source Operator | `<Assignment valueSource="Operator" valueType="Integer"><variable .../></Assignment>`. Request types: Yes/No, whole number, decimal number, text string; the operator message is an attribute (seen as `message=` in a real program) |
| Call (SubProg inside the program) | `<CallSubProgram/>` until a target is chosen |
| SubProg with a **top-level row selected** | a definition: `<SubProgram name="SubProgram_1" keepHidden="false" keepSynchronizedWithDisk="false"><children><Placeholder/></children></SubProgram>`, written after `MainProgram`. Panel: Rename, Load File, Save SubProgram, "Keep SubProgram File Updated", "Hide Subprogram Tree" |
| "Add Before Start Sequence" ticked | `<SpecialSequence type="BeforeStart"><children><Placeholder/></children></SpecialSequence>` before `MainProgram` |
| Script, type File, no file chosen | **PolyScope fails to save the program** ("Unable to Save Program"): the written file stops at `<Script type="File"><cachedContents>` and is truncated. Choose a file or use type Line |

**Direction `Until` conditions** (inside the Direction node)
| UI | XML |
|---|---|
| Distance | `<Until type="DISTANCE" allowActions="false" deceleration="3.0" distanceNodeType="STOP"><Distance>-1.0</Distance><motionParameters blendRadius="0.0"/></Until>` |
| Tool Contact | `<Until type="TOOL_CONTACT_DETECTION" allowActions="false" retraction="0.0" decelerationAcceleration="3.0" decelerationAngularAcceleration="34.90658503988659"/>` |
| I/O Input | `<Until type="IO" allowActions="false" ioType="NONE"/>` |
| Expression | `<Until type="EXPRESSION" allowActions="false"><ExpressionBranch/></Until>` |
| none yet | `<Until type="NONE" allowActions="false"/>` |

**Move options**
| UI | XML |
|---|---|
| Set TCP: flange (other choices: Ignore Active TCP, Use active TCP, hande) | `useActiveTCP="false"` and a `<tcp referencedName="flange"/>` child (before `<feature>`) |
| Motion Controls: OptiMove | `optimoveEnabled="true"` (Classic is `"false"`) |
| "Use joint angles" ticked | `positionType="JointAngles"` (otherwise `"CartesianPose"`) |
| Waypoint type Variable position, Blend with radius | `<Waypoint type="Variable" name="Variable" kinematicsFlags="-1"><motionParameters blendRadius="0.05"/></Waypoint>` (50 mm is the default once "Blend with radius" is chosen) |

**Backups.** Saving over an existing file keeps the previous version as `name.old0` (and so on), which is where the `.oldN`
companions come from.

## Not yet explored
"Set `<Output>` to f(x)", "Increment installation variable by one", Set TCP, the Direction "Add Action" toggle, a real
Script `File` node with a chosen file, a Call with a chosen target, URCap nodes other than the built-in templates, and
the Event/Thread options.
