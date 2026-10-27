#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/../../../.."
source_path=assets/sprites/player/source

# All generated outputs stay inside the isolated player experiment.
# Pass --resume to reuse frames only after source/settings/hash verification.
blender -b -t 4 --python-exit-code 1 --python "$source_path/build_player.py" -- --all "$@"
for lighting in cool warm; do
  blender -b -t 4 --python-exit-code 1 --python "$source_path/build_player.py" -- --pilot --directions 1 --lighting "$lighting"
done
blender -b "$source_path/bohater.blend" --python-exit-code 1 --python "$source_path/validate_blend.py"
blender -b "$source_path/bohater.blend" --python-exit-code 1 --python "$source_path/validate_render.py"
python3 -B "$source_path/export_player.py"
