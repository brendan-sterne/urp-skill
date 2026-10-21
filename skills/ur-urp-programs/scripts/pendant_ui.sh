#!/bin/bash
# Send mouse/keyboard actions to URSim's pendant over VNC and save a screenshot (PNG) afterwards.
#
# usage: pendant_ui.sh OUT.png ACTION [ACTION ...]
#   ACTION is a vncdotool command, quoted if it has spaces:
#     "move 937 30"  "click 1"  "pause 8"  "key ctrl-a"  "type hello.urp"  "key enter"
#   With no actions it just captures the screen:  pendant_ui.sh now.png "pause 1"
#
# Setup (once): python3 -m venv ~/.venvs/vnc && ~/.venvs/vnc/bin/pip install vncdotool
#   VNC_PY  path of the venv (default ~/.venvs/vnc)   VNC_HOST  host::port (default localhost::5900)
#
# URSim runs under x86 emulation on Apple Silicon and the pendant UI is slow: wait 3-9 s after a click
# before the next one, and look at the screenshot to confirm each step. This is for URSim, not a real robot.
VENV="${VNC_PY:-$HOME/.venvs/vnc}"
HOST="${VNC_HOST:-localhost::5900}"
OUT="$1"; shift
cmd=()
for a in "$@"; do read -ra parts <<< "$a"; cmd+=("${parts[@]}"); done
perl -e 'alarm 90; exec @ARGV' "$VENV/bin/vncdotool" -s "$HOST" "${cmd[@]}" capture "$OUT" 2>&1 | tail -2
