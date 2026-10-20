# Safety

Programs produced or edited with these tools can move an industrial robot arm. A robot can injure people and
damage equipment. This project is **unofficial**, **not safety-rated** and has **no warranty**.

## Before you open or run anything you generated
- Treat every generated or edited program as untrusted until you have reviewed it on the teach pendant.
- Open it in PolyScope and check the program tree and waypoints. Do not rely on this project's description of
  what a file does.
- Run it with the speed slider low, the work area clear, and your hand on the emergency stop. The first move of a
  program goes from wherever the arm is to its first waypoint, which can be a large jump.
- Do not use a program, template or calibration block from one robot on another robot.
- Replayed recordings reproduce positions, not timing or speed. Check clearances along the whole path.

## How the tools try to help
- Outputs are written to new files; inputs are never overwritten.
- Edits are checked by XML parse and diff size.
- The recorder only listens to the robot. The tools do not send motion commands.

## What they cannot do
- They cannot tell you a program is safe, collision-free or within your risk assessment.
- They have not been validated by Universal Robots, and the file format they rely on is undocumented.

Follow your robot manufacturer's instructions and your site's safety procedures. If you find a way these
tools could do something unsafe, please open an issue.
