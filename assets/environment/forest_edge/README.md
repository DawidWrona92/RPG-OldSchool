# ENV-01 — skraj boru / podłoże + obiekty / Welesza

**Status: techniczny proof of concept v0.1. Styl graficzny NIEZATWIERDZONY.**

Cel: pierwszy edytowalny i deterministyczny pipeline środowiska, niezależny od renderera SDF postaci. To **nie** jest gotowa lokacja gry, przerenderowana panorama ani ekran o jakości ilustracji referencyjnej. Proste proceduralne drzewa, kamienie i krzewy są **placeholderami**, których docelowy wygląd musi zostać zastąpiony znacznie lepszymi assetami. Najbardziej wartościowym wynikiem są struktura danych, projekcja, tekstury, testy i diagnostyka.

## Kontekst

- `docs/art/niemir/NIEMIR_ART_DIRECTION.md` — uzgodniony art direction.
- `docs/pakiet-04-mapa.md`, `docs/pakiet-04-poczatek.md` — prolog i pierwsza wyprawa. Scena prototypowa to teren **przy wozie**; sam wóz nie został jeszcze zbudowany.
- `assets/sprites/prerender/README.md` — zgodna izometria postaci: 30°, 60 px/metr; stopy na gruncie.
- Nie ma wybranego silnika gry, więc eksport ma format neutralny: obraz + osobne przezroczyste propsy + JSON.

## Co działa

- Reprodukowalne obrazy z `SEED=424107`, niezależne od generowania sprite'ów postaci.
- Cztery powtarzalne, bezszwowe zestawy materiałów (`albedo`, `normal`, `roughness`, `height`, każdy 256×256): `forest_floor`, `mud`, `stone`, `moss`.
- Podłoże w orientacji izometrycznej 30° z niejednorodnym błotnistym szlakiem, rozległą polaną i miejscami mokrymi.
- Oddzielne RGBA: dwa świerki, dwie skały, dwa krzewy, pień i pniak. Wszystkie bez wpieczonego tła.
- `scene.json` zawiera pozycje w metrach, projekcję, anchor i orientacyjne promienie kolizji (nie są sprawdzonymi hitboxami).
- Viewer przeglądarkowy potrafi nałożyć obiekty, kolizje i marker testowy. **Nie implementuje pathfindingu ani grywalnej walki.**
- `validation.json`, testy poprawności materiałów, formatów i metadanych.

## Uruchomienie

```bash
python -m pip install numpy pillow scipy
python assets/environment/forest_edge/generate.py
python assets/environment/forest_edge/test_assets.py
python -m http.server 8000
# otwórz http://localhost:8000/assets/environment/forest_edge/viewer.html
```

## Dostarczone artefakty

- `output/scene_ground.png` — płaskie podłoże z projekcją kamery, do testów renderowania.
- `output/scene_preview.png` — wstępny kadr, tylko kontrola integracji.
- `output/debug/collision_preview.png` — nakładki kolizji (przybliżenia).
- `output/materials/*` — tileable materiały do późniejszego wykorzystania w shaderach i modelach 3D.
- `output/props/*.png` — placeholdery transparentnych obiektów.
- `output/scene.json`, `output/validation.json` — metadane i walidacja.

## Ograniczenia i następna iteracja

**Ważne: prototyp 2.5D nie osiąga jakości screena referencyjnego.** Prosty proceduralny rysunek obiektów nie powinien być używany jako finalna grafika Weleszy. Docelowe drzewa, pnie, głazy, kałuże i wóz zalecamy modelować i renderować w Blenderze do przezroczystych sprite'ów, z normalami, realistycznym drewnem, listowiem i dobrym AO. SDF postaci nie trzeba zmieniać.

Kolejny etap po ocenie: rzeczywiste modele wysokiej jakości, wóz z prologu, wysokość nad gruntem, osobne maski przysłaniania postaci, następnie zintegrowana grywalna polana. Kolizje, oba obejścia wozu, widoczność telegraphów i czas uniku wymagają testu z realnym bohaterem w silniku gry.

## Odpowiedzialność i licencje

Materiały i propsy są autorskimi, proceduralnie generowanymi assetami; generator nie pobiera cudzych tekstur, grafik ani modeli. Żadnych plików innych autorów nie modyfikuje. Ten katalog jest niezależny od systemu postaci.
