# Bohater Weleszy v2 — statyczna przebudowa F0–F3

**Jedynym aktywnym źródłem jest [source/bohater_v2.blend](source/bohater_v2.blend).**
Stan roboczy przed B1/B2, do oceny autora. Bez nowych animacji i atlasów.

[Przegląd](reviews/v2-f0-f3/index.html) · [raport](V2_REVIEW.md) · [HANDOFF](HANDOFF.md) · [P1](handoff/p1/manifest.json) · [P2](handoff/p2/manifest.json).

- Pełne ciało MakeHuman CC0, 19158 natywnych indeksów wierzchołków OBJ, 13378 ścian `body`, **nienaruszone natywne UV**.
- Szkielet MakeHuman `default.mhskel`, **163 kości**, wagi `default_weights.mhw`; dopasowana poza neutralna, bez akcji animacji.
- Głowa według konceptu 19 i nadrzędnych decyzji pisemnych: starsza i ogorzała, pełna żuchwa, włosy średniej długości z siwizną, broda i wąs z włókien. Skóra GPT 6 v3, spakowana; szarozielona tęczówka oczekuje v4.
- Strój według 17: nowe części, unikatowe UV około 1024 px/m, utrwalone drapowania Cloth i późniejsze poprawki geometrii. Obecne materiały są **tymczasowe**; P2 służy przygotowaniu tekstur.
- Miecz w pochwie przy lewym biodrze (D1). Kamera, światła, skala, kotwica i przezroczystość pozostają zgodne z kontraktem z `main`.

## Bezpieczne użycie źródła

Plik `.blend` jest nadrzędny. Skrypty `v2_body.py`, `v2_head*.py`, `v2_*fit*.py` i pozostałe recepty zapisują historię konkretnych poprawek i mają strażniki rewizji. **Nie są wywoływane przez render i nie służą regenerowaniu ręcznie poprawionego źródła.** `v2_body.py` odmawia nadpisania istniejącego pliku.

Renderer `v2_render_static.py` otwiera zapisany model, renderuje statyczny widok i audyt SHA, nigdy nie zapisuje modelu. Klatki postaci i cienia są oddzielne RGBA. Przykład z katalogu repozytorium:

```sh
blender -b assets/sprites/player/source/bohater_v2.blend -t 4 --python-exit-code 1 \
  --python assets/sprites/player/source/v2_render_static.py -- \
  --mode game --directions 0 --output /tmp/bohater-v2-pilot
```

`--mode model` to trzy większe widoki diagnostyczne, `portrait` portret 768, `p1` ciało z szablonem UV. Te kamery diagnostyczne nie zmieniają zapisanego kontraktu kamery gry. Przegląd w 1× powstaje z renderów 384 przez premultiplikowany Lanczos do 192.

## Przekazanie P2

```sh
blender -b assets/sprites/player/source/bohater_v2.blend -t 4 --python-exit-code 1 \
  --python assets/sprites/player/source/v2_bake_p2.py -- --resume
python3 assets/sprites/player/source/v2_finish_p2.py
```

Wznowienie wymaga zgodnego SHA modelu, bakera i wszystkich gotowych plików części. Po zmianie źródła wypalać do świeżego katalogu, zachowując poprzednią paczkę jako archiwum. Pełna paczka ma `complete: true`, 22 części i 154 PNG; [opis map](handoff/p2/README.md). Renderer ani baker nie zmieniają geometrii/UV zapisanego źródła.

Kontrole: `v2_validate_source.py`, `v2_validate_body.py`, `v2_render_poses.py` oraz narzędzie PM [check_intersections.py](../../../tools/art/check_intersections.py). Dokładny zakres i wyjątki są w raporcie. Nie utożsamiać kontroli powierzchni siatek w jednej statycznej klatce z pełną kontrolą Curves, samoprzenikań czy animacji.

## Archiwum

`source/bohater.blend` (rev08), `source/bohater_detale.blend`, `atlas/`, `renders/`, `previews/` i `reviews/detale-01/` pokazują **starszy prototyp**. Pozostają do porównań i odzyskania; sumy źródeł w `source/archive-sources.json`. [Dawne instrukcje prototypu](README-ARCHIVE-PROTOTYPE.md) i jego pipeline nie są domyślnym eksportem v2.

Pochodzenie MakeHuman/targetów i licencja CC0: `source/third_party/manifest.json`, `targets/manifest.json`, `LICENSE.ASSETS.md`. Tekstury GPT 6 zachowują własny manifest, commit pochodzenia i ograniczenia — nie są przedstawiane jako skany PBR.
