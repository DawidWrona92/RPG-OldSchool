# Retro scena 1:1 — Niemir (brama + osada), sprite'y 1:1 z kadrów

Grywalna mini-scena: tłem są **oryginalne kadry** z usuniętymi postaciami (inpainting),
a postacie to **prawdziwe sprite'y wycięte 1:1 z tych kadrów** (GrabCut + template matching).

## Jak odpalić

- **Najprościej**: pobierz `niemir-1to1.html` (samodzielny plik ~1,4 MB, assety wbudowane
  base64) i otwórz dwuklikiem w przeglądarce.
- Alternatywnie `index.html` + `game.js` + `assets/`.

## Sterowanie

- `W A S D` / strzałki — chodzenie; `Shift` — bieg.
- Scena 1 (brama): środkową ścieżką do góry pod bramę → przejście do osady.
- Scena 2 (osada): zejście w dół → powrót do bramy.

## Postacie

- **Bohater** (sterowany): sprite wycięty z oryginalnego kadru sceny 1 (60x124),
  z brązowym ubraniem, mieczem i tarczą. Oddech + para z ust.
- **Strażnik**: sprite wycięty z kadru sceny 1 (56x116). NIE stoi w miejscu —
  spaceruje przed bramą między 4 punktami, co przystanek zatrzymuje się na ~2,6 s.
  Podczas postoju oddycha (ruch torsu) i bucha parą z ust.
- Oba tła (scena 1 i scena 2) mają **usunięte postacie inpaintingiem** — bohater
  i strażnik nie "siedzą" w tle.

## Pipeline assetów (Python/OpenCV, offline)

- Lokalizacja postaci: multi-scale template matching close-upów do scen (TM_CCOEFF_NORMED).
- Segmentacja: GrabCut (init mask) + morfologia + wypełnianie dziur.
- Usuwanie z tła: dilatacja maski + `cv2.inpaint` (TELEA).
- Pliki: `assets/scena1_czyste.jpg`, `assets/scena2_czyste.jpg`,
  `assets/bohater.png`, `assets/straznik.png`.

## Stan / handoff

- Walidacja: `node --check` + smoke-test w `vm` (ruch, oba przejścia, cykl
  spacer/postój strażnika) — wszystkie przechodzą.
- Otwarte: kolizje z NPC, interakcje, dźwięki, więcej NPC w osadzie.
- Nie jest kontraktem produkcyjnym (produkcja: Blender/Cycles wg KONTRAKT-RENDERU.md).
