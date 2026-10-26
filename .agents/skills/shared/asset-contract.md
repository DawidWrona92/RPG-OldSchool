# Wspólny kontrakt assetu RTS v2

## Dane wymagane

- `assetId`, `backend`, `styleVersion`, `kind` (`unit|building|tree|prop|tile|scene`), `tilePx`, `projection` (`iso2to1`), `scaleWorldUnits`, `directions`, `framesPerDirection`, `fps`, `loop`, `anchorPx` (punkt świata stykający się z podłożem), `canvasPx` i `trimOffsetPx`.
- `lightDirWorld`, `cameraAzimuthDeg`, `cameraElevationDeg`, `teamMaskMode`, `shadowMode`, `basePalette`, `sourceGenerator` oraz `runtimeVersion`.
- Ten sam format i kolejność klatek (kierunek, potem faza); kotwica i ramka stałe w całym atlasie. Nie zmieniaj kierunku kierunków bez zapisu w metadanych.

## Pliki

`asset_sprite.png` RGBA, `asset_shadow.png` RGBA lub kanał alfa, `asset_team.png` maska L, `asset_preview.png`, `asset.json`, `source.js` albo `source.py` jako kod źródłowy generatora. Dla animacji dodaj `sheet.png` i `sheet.json` z prostokątami klatek. Niezależne PNG muszą mieć spójne wymiary przed pakowaniem; kanał shadow i team musi odpowiadać pikselom sprite'a (wyjątek: maska cienia rozciągnięta poza sprite, wtedy jawny offset).

## Reguły

Przycięte alpha-bbox i shadow-bbox — błąd. Brak zajętych pikseli — błąd. Niepoprawny punkt kotwicy — błąd. Zgodność liczby kierunków i klatek — błąd. Dokładnie identyczne kolejne fazy przy zadeklarowanej animacji — ostrzeżenie (idle dopuszczalny). Równe alpha mask dla różnych kierunków — ostrzeżenie, dopiero identyczne pełne RGBA są podejrzane. Nie zakładaj, że każda para ma się różnić: model symetryczny dopuszcza powtórzenia.
