# Reaching the robot

All commands below are for a robot you own or are authorized to work on. Examples use the documentation
address 192.0.2.10; replace it with your robot's.

## Network
The robot must be reachable from your computer, normally over Ethernet on the same subnet. With a USB Ethernet
adapter on macOS, give the adapter a manual address on the robot's subnet (no router), for example:
`sudo networksetup -setmanual "<adapter service name>" 192.0.2.100 255.255.255.0`, and revert with
`sudo networksetup -setdhcp "<adapter service name>"`. If you swap adapters, macOS may reuse the old service
name and its old manual address: check `ifconfig` and `route -n get <robot ip>`.

## Dashboard server (port 29999)
Plain-text TCP, one command per line, one reply per command. Read-only queries are safe:
`PolyscopeVersion`, `get robot model`, `get serial number`, `robotmode`, `safetystatus`,
`is in remote control`, `get loaded program`, `programState`, `running`.

State-changing commands (`load`, `play`, `pause`, `stop`, `power on`, `brake release`) need the robot in
**Remote Control** mode, and `play` moves the arm. Do not send them unless the user asked for that action.

## SSH / SCP for program files
- Enable on the pendant: Settings > Security > Secure Shell, then Apply (the Security section needs the admin
  password). Authentication can be password and/or key. The login user is `root`; see UR's documentation for
  credentials, and never store them in files or notes.
- Programs are in `/programs` (the same folder as `/data/programs`).
- Observed gotcha: with "Disable inbound access to additional interfaces (by port)" set to `1-65535`, port 22
  stayed closed even with SSH enabled; changing the range to leave 22 open (`1-21,23-65535`) fixed it. The
  manual says an enabled service should override the block; that did not hold for SSH in this case.
- The server is old OpenSSH (6.7). A current OpenSSH client connected without extra options.
- **File names with spaces:** an upload to `host:/programs/Name\ With\ Spaces.urp` created a file whose name
  contained literal backslashes. Upload to a name without spaces and rename with `ssh ... mv`, then list the
  folder to confirm. Downloads with the escaped form worked.
- Before overwriting anything on the robot, copy it (`cp -p x x.bak`). Upload edited programs as new files.
- When finished, restore the port block, disable SSH, and put the adapter back on DHCP.
- USB stick is the no-setup alternative (the pendant file browser shows it under `/programs/usbdisk`).

## Real-time interface (port 30003, read-only listening)
A fixed-size packet about every 2 ms on an e-Series. On PolyScope 5.25.1 it was 1220 bytes of big-endian data:
the first 4 bytes are the length, the time (double) is at byte 4, the actual joint positions (6 doubles, rad) at
byte 252 and the actual TCP pose (6 doubles, base frame) at byte 444. These offsets come from UR's client
interface documentation and gave plausible values on 5.25.1; other versions may differ, so check the packet
length first (`scripts/record_path.py` warns).

Read the newest packet in a continuous loop; sleeping between reads leaves you reading queued, stale packets.

For anything beyond a one-off read, RTDE (port 30004) is the better interface: named fields such as
`actual_TCP_pose` and `actual_q`, at a rate you choose (for example with the `ur_rtde` library).
