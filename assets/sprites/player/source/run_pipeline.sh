#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/../../../.."
source_path=assets/sprites/player/source

# Render authoritative source; never call build_player.py or refine_player.py here.
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --all "$@"
for lighting in cool warm; do
  blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --lighting "$lighting"
done
blender -b "$source_path/bohater.blend" --python-exit-code 1 --python "$source_path/validate_blend.py"
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/validate_render.py"
python3 -B "$source_path/export_player.py"
python3 -B "$source_path/compare_player.py"
