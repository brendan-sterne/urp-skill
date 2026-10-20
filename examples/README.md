# Examples

`recorded_path.example.json` is a **synthetic** recording (invented numbers, documentation IP address) in the
format written by `record_path.py`: 7 samples at 4 Hz, one of which is a duplicate from a "pause" that
`build_movej_program.py` drops.

It is for trying the tools and for the tests. It is not a real robot path and must not be played on a real
robot: `build_movej_program.py` needs a template program saved on your own robot to produce a loadable file.
