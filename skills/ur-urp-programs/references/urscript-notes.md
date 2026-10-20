# URScript notes that came up

Checked against the URScript manual as remembered and, where noted, on a robot. Verify against the manual for
your software version.

- **No dictionary type.** Use parallel lists and a lookup loop, or integer indexes:
  ```
  def lookup_cost(item, default):
    i = 0
    while i < get_list_length(items):
      if items[i] == item:
        return costs[i]
      end
      i = i + 1
    end
    return default
  end
  ```
  The list-length function is `get_list_length(list)`.
- **Pose in the base frame from a feature plus an offset:** `pose_trans(feature, offset)`. It returns a pose; it
  does not move the robot. The offset is measured along the feature's axes. `pose_add` adds components in the
  base axes and is only safe for position-only offsets.
- **Offset relative to the tool:** `pose_trans(get_actual_tcp_pose(), offset)`. Use `get_target_tcp_pose()` for a
  repeatable start, because the actual pose carries small tracking error and chained "relative" moves drift.
- **Tool pointing into a plane:** a plane's +Z is out of the plane, and a tool normally points along its own +Z,
  so rotate 180 degrees about a horizontal plane axis:
  `pose_trans(Plane, p[0, 0, h, 3.141592653589793, 0, 0])`. Check the plane's Z direction first.
- **Spin one joint continuously:** `speedj([0, 0, 0, 0, 0, w], a, t)` inside a `while True` loop; stop with
  `stopj(a)`. Start slow and mind any tool cabling. On the robot this was developed on, joint 6 stored angles of
  about 64 rad in a saved program, so wrist 3 was not limited to one turn.
- Poses are `p[x, y, z, rx, ry, rz]`: meters and a rotation vector in radians.
