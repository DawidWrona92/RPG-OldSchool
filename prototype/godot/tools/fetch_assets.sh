#!/usr/bin/env bash
# Kopiuje do projektu assety z ich gałęzi źródłowych (nie są commitowane tutaj).
# Użycie: prototype/godot/tools/fetch_assets.sh [gałąź-bohatera]
set -euo pipefail
cd "$(dirname "$0")/.."
HERO_BRANCH="${1:-origin/vibe/sprite-bohater-codex}"
git fetch -q origin "${HERO_BRANCH#origin/}" main
mkdir -p assets/hero assets/ground
for f in bohater.json bohater_spoczynek.png bohater_spoczynek_shadow.png bohater_chod.png bohater_chod_shadow.png; do
  git show "$HERO_BRANCH:assets/sprites/player/atlas/$f" > "assets/hero/$f"
done
git show origin/main:assets/textures/environment/ground/forest_litter_mixed.png > assets/ground/forest_litter_mixed.png
echo "Bohater z $(git rev-parse --short "$HERO_BRANCH"), podłoże z $(git rev-parse --short origin/main)"
