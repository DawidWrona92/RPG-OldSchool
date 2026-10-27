#!/bin/sh
# Uruchamia pipeline środowiska Weleszy (kamienie + podłoże + scena testowa).
#
# Wymaga środowiska przygotowanego poza repo (patrz README.md):
#   /tmp/bpyenv   — rozpakowany wheel bpy (Blender 5.2.3, cp313)
#   /tmp/pylibs   — numpy + pillow dla Pythona 3.13
#   /tmp/xlibs    — biblioteki X11/GL (libX11, libGL, libEGL, libgomp…)
#
# Użycie:
#   ./run.sh                # wszystko (stones + grounds + scene)
#   ./run.sh stones         # tylko kamienie i głaz
#   ./run.sh grounds        # tylko podłoże
#   ./run.sh scene          # tylko scena testowa
set -e
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

export PYTHONPATH="/tmp/bpyenv:/tmp/pylibs${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="/tmp/xlibs/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

exec python3.13 "$HERE/build_env.py" --only "${1:-all}"
