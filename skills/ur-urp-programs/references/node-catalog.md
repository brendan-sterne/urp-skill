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

## Not yet explored
The variants of Wait, Set, Popup, Waypoint (Relative/Variable), Move (features, TCP, blend), Direction `Until`
conditions, Loop (While/count), If/Else, Switch cases, Timer actions, Script (file), Assignment (operator input),
SubProgram definitions, URCap nodes, and the "Add Before Start Sequence" option.
