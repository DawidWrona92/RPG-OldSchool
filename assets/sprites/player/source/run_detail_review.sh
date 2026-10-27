#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/../../../.."
source_path=assets/sprites/player/source
review_path=assets/sprites/player/reviews/detale-01
# Read saved artistic files only. No modeling recipe is invoked.
blender -b "$source_path/bohater_detale.blend" -t 1 --python-exit-code 1 --python "$source_path/inventory_source.py" -- --manifest "$source_path/bohater_detale.source.json"
blender -b "$source_path/bohater_detale.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --output "$review_path/renders"
blender -b "$source_path/bohater_detale.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --directions 1 3 --size 1152 --output "$review_path/duze"
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --directions 1 3 --size 1152 --output assets/sprites/player/renders/details/after
blender -b "$source_path/bohater_detale.blend" -t 4 --python-exit-code 1 --python "$source_path/render_closeup.py" -- --samples 128 --output "$review_path/glowa-po"
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_closeup.py" -- --views front --samples 128 --output "$review_path/glowa-przed"
for lighting in cool warm; do
  blender -b "$source_path/bohater_detale.blend" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --pilot --directions 1 --lighting "$lighting" --output "$review_path/$lighting"
done
blender -b "$source_path/bohater_detale.blend" -t 1 --python-exit-code 1 --python "$source_path/validate_detail_source.py"
python3 -B "$source_path/validate_detail_reproduction.py"
python3 -B "$source_path/export_detail_review.py"
