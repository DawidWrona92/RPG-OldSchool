#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/../../../.."
source_path=assets/sprites/player/source

# Render authoritative source; never call build_player.py or refine_player.py here.
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --all "$@"
for lighting in cool warm; do
  blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --lighting "$lighting" "$@"
done
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --sheathed "$@"
for version in before after; do
  model_path="$source_path/bohater.blend"
  if [[ "$version" == before ]]; then model_path=assets/sprites/player/baseline/source/bohater.blend; fi
  blender -b "$model_path" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --portrait --directions 1 3 --output "assets/sprites/player/renders/details/$version" "$@"
done
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/validate_intersections.py"
blender -b "$source_path/bohater.blend" --python-exit-code 1 --python "$source_path/validate_blend.py"
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/validate_render.py"
python3 -B "$source_path/export_player.py"
python3 -B "$source_path/compare_player.py"
