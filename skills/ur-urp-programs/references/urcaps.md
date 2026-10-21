# URCap nodes in `.urp` programs

How URCap-provided nodes look in a program, and how to install URCaps in URSim to explore them. Observed on
PolyScope 5.13.1 to 5.26.1 programs and URSim 5.26.1 (2026-10-21).

## The `Contributed` form
Every URCap node (and PolyScope's own palletizing, conveyor tracking and screwdriving templates) is written as:

```
<Contributed strategyClass="..." strategyProgramNodeType="..." strategyURCapDeveloper="..." strategyURCapName="...">
  <dataModel>
    <data key="..." value="..."/>
    <Variable key="..."><variable name="..." .../></Variable>
  </dataModel>
  <state isChildrenLocked="true"/>   <!-- optional -->
  <children>...</children>           <!-- optional -->
</Contributed>
```

The four `strategy*` attributes identify the node. The `dataModel` keys and values belong to the URCap, are not
documented by UR, and differ per URCap, per node and sometimes per version. **Treat `dataModel` as opaque**: copy a
node verbatim from a program saved on the target robot, change only values you understand, and never invent keys.

A URCap that declares program variables has them registered by PolyScope in `InitVariablesNode` (the Schmalz URCap
adds `MagnetON` and `PartPresent`, initial `False`), and refers to them from the node with `<Variable key="...">`.

## Observed nodes
Keys only; values vary.
| URCap (developer) | Node: class | dataModel keys seen |
|---|---|---|
| Robotiq_Grippers (Robotiq Inc.) | Gripper Activate: `com.robotiq.urcap.gripper.GripperActivate` | `ResetAndActivateKey` |
| | Gripper: `com.robotiq.urcap.gripper.GripperNode` | `position`, `force`, `speed`, `positionInDouble`, `forceInDouble`, `speedInDouble`, `slaveIds` (`[9]`), `blocking`, `robotCompliant` |
| | Grip Check: `...gripper_validation_node`, If: `...gripper_validation_if_node` | `DimensionKey`, `DimensionPositiveGapKey`-style gap keys, `GripperIdKey`, `ModelDefinedKey`, `ObjectDetectedKey`, `DimensionValidationKey` |
| OnRobot (OnRobot A/S) | 2FG Grip / 2FG Release: `com.onrobot.urcap.unified.2FG Grip` / `... Release` | `twofg.external-grip.target-width`, `twofg.internal-grip.target-width` (meters) |
| Schmalz Gripper (J.Schmalz GmbH) | `com.JSchmalzGmbH.SchmalzGripper.SchmalzGripSwing` | Suction (default): `Variable` keys `dummyPartPresent`, `dummy_magnetOn`; Release / Part Present: `NodeFunctions` = `2` / `3` |
| External Control (FZI) | `com.fzi.externalcontrol.ExternalControlNode` | none (empty `dataModel`; the host address is an installation setting) |
| polyscope-pallet-impl (Universal Robots) | Palletizing, Patterns, Pattern, Item, Layers, At Each Item, Generated Movements | many; see below |
| Conveyor Tracking, polyscope-screwdriving-impl (Universal Robots) | `ConveyorTracking`, `ScrewdrivingProgramNode` | see `node-catalog.md` |

**Palletizing is robot-specific.** Its `Item` and `At Each Item` data models embed the robot's calibration
(`calibrationDeltaTheta`, `...A`, `...D`, `...Alpha`, `...JointChecksum`), `baseToFeature`, `TCPOffset` and joint
positions. A palletizing program is therefore not portable between robots, and editing one by hand is risky.

## Installing URCaps in URSim
1. Put the URCap file (`.jar` or `.urcap`) in the folder mounted at `/urcaps` (`-v ~/urcaps:/urcaps`).
2. Restart the container (`docker restart ursim`). On restart the log (`/ursim/polyscope.log`) shows each URCap
   starting (for example `URcap enabling external control registering!`).
3. A **URCaps** category appears in the Program tab's node list with each URCap's nodes.
4. Add the nodes, save, unpack and diff as for any other node (`ursim.md`).

Verified with External Control 1.0.5 and Schmalz Gripper 4.4.2, both taken from a real robot's `/root/.urcaps/`
(on e-Series the installed bundles are `.jar` files there; other vendors install elsewhere). Alternatively install
through PolyScope: Settings > System > URCaps, the `+` button, then restart PolyScope.

Limits: gripper URCaps will add and save nodes without hardware, but communication and installation screens do not
work; a URCap built for an older URCap API may not load; and a program that uses a URCap that is not installed still
passed URSim's `load` check, but how its nodes look in the tree was not checked.

## Do not redistribute vendor files
URCap `.jar`/`.urcap` files are the vendors' software. Keep them local, never commit them to this repository (they
are in `.gitignore`), and use the XML structure above, not copies of the files.
