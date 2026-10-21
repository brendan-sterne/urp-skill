# Using URSim to check and learn

URSim is UR's offline simulator of the controller and PolyScope. It is a safe place to test whether PolyScope
accepts a generated file and to see exactly what PolyScope writes for a given UI action. Nothing here
touches a physical robot.

## Running it (Apple Silicon Mac, Docker/OrbStack)
URSim is x86_64 Linux only. Run the image under emulation (OrbStack uses Rosetta, which is much faster than
QEMU):

```
docker run -d --name ursim --platform linux/amd64 -e ROBOT_MODEL=UR3 \
  -p 5900:5900 -p 6080:6080 -p 29999:29999 -p 30001-30004:30001-30004 -p 502:502 \
  -v ~/ursim-programs:/ursim/programs universalrobots/ursim_e-series
```

`ROBOT_MODEL` is fixed when the container is created (UR3, UR5, UR10, ...). The mounted folder is where the
pendant's file browser opens, so files you save in the UI appear on your computer. The `programs.UR5`-style
folders shown in the browser are symlinks to unmounted folders inside the container.

PolyScope in the image identified itself as `5.26.1.140514` and started in Local mode, powered off. It takes
about a minute to come up after `docker run`.

## Checking that PolyScope accepts a file
Use the dashboard `load` command (no UI needed): `scripts/ursim_load_check.py` copies files into the mounted
folder, loads each, and confirms with `get loaded program`. It first runs two negative controls (a truncated
gzip and a text file) and refuses to report results unless both are rejected. In URSim:
- `load` works in Local mode.
- An accepted file replies `Loading program: <path>, <installation path>`.
- A rejected file replies `Error while loading program: <path>: unknown failure`, and the previously loaded
  program stays loaded. The detail is in the container's `/ursim/polyscope.log` (for non-gzip input:
  `SAXParseException: Content is not allowed in prolog`).
- `load installation <file>` switches the installation (this changes the safety checksum shown on the
  pendant, and therefore the `crcValue` of programs saved afterwards).

## Driving the pendant over VNC (to see what PolyScope writes)
The pendant is a normal VNC desktop on port 5900 (the noVNC page on 6080 is a front end for it). With no
browser tool available, a script can drive it: `scripts/pendant_ui.sh` wraps `vncdotool` to send clicks and
keys and to save a 1280x800 screenshot, which you then look at. Experiments are minimal pairs: make one change
in the UI, save under a new name, unpack both files and diff them (`urp_tools.py unpack`).

Practical notes from doing this:
- **The UI is slow under emulation** (3 to 8 seconds per action). Use long pauses and confirm each step from a
  screenshot before the next click. A click sent too early lands on whatever is on screen at that moment.
- **Layout shifts:** the Save icon's x position depends on the program name's width, so take a screenshot
  first. The Save menu has Save All, Save Program As... and Save Installation As.... Save All is greyed out
  when nothing is modified.
- **Filename entry:** clicking the filename field opens an on-screen keyboard with its own text box. Typed
  text goes into that box; its green **Submit** key both accepts the name and saves the program. Any extra
  click on the keyboard types a character (an apostrophe was added once this way; Backspace removes it).
- **Watching:** a second, view-only viewer can watch without interfering:
  `http://localhost:6080/vnc.html?view_only=true`. A normal viewer sends input to the same screen and will
  collide with scripted clicks.
- Loading a program with the dashboard and then saving it through the UI is the quickest way to see PolyScope's
  canonical form of a file.

## Safety checksum of URSim's stock installation
Corner code `8286 7A6B` = `crcValue 2189851243` for URSim 5.26.1's own installation. A real robot's value
depends on its safety configuration.
