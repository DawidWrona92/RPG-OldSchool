#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/../../../.."
source_path=assets/sprites/player/source
resume_requested=0
if [[ "$#" == 1 && "$1" == --resume ]]; then
  resume_requested=1
elif [[ "$#" != 0 ]]; then
  printf '%s\n' 'Użycie: run_pipeline.sh [--resume]. Piloty: render_player.py --help.' >&2
  exit 2
fi

render_saved() {
  local component_model="$1" component_folder="$2" component_lighting="$3" component_size="$4" component_sheathed="$5"
  shift 5
  local -a resume_args=() sheath_args=()
  local component_audit="$component_folder/motion_audit.json"
  if [[ "$component_sheathed" == true ]]; then
    sheath_args=(--sheathed)
    component_audit="$component_folder/sheathed/motion_audit.json"
  fi
  if (( resume_requested )); then
    if python3 -B "$source_path/cache_compatible.py" --model "$component_model" --audit "$component_audit" --lighting "$component_lighting" --size "$component_size" "${sheath_args[@]}"; then
      resume_args=(--resume)
    fi
  fi
  # Reads artistic source; incompatible generated components are rebuilt, never the model.
  blender -b "$component_model" -t 4 --python-exit-code 1 --python "$source_path/render_player.py" -- --output "$component_folder" --lighting "$component_lighting" --size "$component_size" "${sheath_args[@]}" "$@" "${resume_args[@]}"
}

python3 -B "$source_path/validate_textures.py"
blender -b "$source_path/bohater.blend" -t 1 --python-exit-code 1 --python "$source_path/inventory_source.py"
render_saved "$source_path/bohater.blend" assets/sprites/player/renders base 384 false --all
for lighting in cool warm; do
  render_saved "$source_path/bohater.blend" "assets/sprites/player/renders/$lighting" "$lighting" 384 false --pilot
done
render_saved "$source_path/bohater.blend" assets/sprites/player/renders base 384 true --pilot
render_saved assets/sprites/player/baseline/source/bohater.blend assets/sprites/player/renders/details/before base 1152 false --pilot --directions 1 3
render_saved "$source_path/bohater.blend" assets/sprites/player/renders/details/after base 1152 false --pilot --directions 1 3
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/render_closeup.py" -- --output assets/sprites/player/previews/groom/po
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/validate_intersections.py"
blender -b "$source_path/bohater.blend" -t 1 --python-exit-code 1 --python "$source_path/validate_blend.py"
blender -b "$source_path/bohater.blend" -t 4 --python-exit-code 1 --python "$source_path/validate_render.py"
python3 -B "$source_path/validate_weapon_contrast.py"
python3 -B "$source_path/validate_cache.py"
python3 -B "$source_path/export_player.py"
python3 -B "$source_path/compare_player.py"
