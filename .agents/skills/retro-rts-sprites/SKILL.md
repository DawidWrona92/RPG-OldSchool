---
name: retro-rts-sprites
description: Tworzy małe sprite'y, budynki, jednostki, kafle i sceny 2:1 w pixel-arcie retro RTS, z deterministyczną paletą, konturem, walidacją i eksportem SVG/PNG przez spritekit.js. Użyj dla klasycznego wyglądu niskiej rozdzielczości; nie dla realistycznych pre-renderów.
---

# Retro RTS sprites — backend potwierdzony

## Start

Skrypt silnika: `scripts/spritekit.js` (oryginalny silnik). Uruchomienie w Node:

```js
const kit = require('./scripts/spritekit.js');
const g = kit.makeGrid(32, 40);
kit.shadeEllipse(g,16,16,10,9,{light:'L',base:'B',shadow:'D'},{seed:1});
const pal = {L:kit.tone('PIXELART','foliage',2),B:kit.tone('PIXELART','foliage',1),D:kit.tone('PIXELART','foliage',0)};
const rows = kit.gridToRows(g);
const qa = kit.validate(rows,pal,{width:g.w,height:g.h,mode:'PIXELART'});
if (!qa.ok) throw new Error(qa.errors.join('; '));
const svg = kit.asciiToSvg(rows,pal,{scale:4,strict:true});
const png = kit.encodePng(kit.upscale(kit.rasterize(rows,pal),4));
```

W przeglądarce bez Node możliwy jest eksport SVG. PNG przez `kit.encodePng` używa Node `zlib` i `Buffer`. Jeśli środowisko ich nie udostępnia, nie obiecuj PNG bez alternatywnego enkodera.

## Praca krok po kroku

1. Ustal styl `PIXELART` (kontur) albo `PRERENDER` (trzy tony z ciemniejszym brzegiem). Nie mieszaj w jednym zestawie bez świadomego dopasowania.
2. Ustal kotwicę, rozmiar kafla 64×32, paletę i kierunek światła (lewy-górny). Typowo jednostka 24×32, drzewo 32×40; większe jednostki mogą wymagać większego płótna.
3. Narysuj **samą sylwetkę** przez `fillPolygon`, `fillEllipse`, `isoBox`, `hipRoof` i zweryfikuj ją w docelowym rozmiarze.
4. Dodaj trzy tony na materiał funkcjami `shadeEllipse`, `shadeRegion`, później dopiero detale; jedno źródło światła.
5. W `PIXELART` użyj `outline` dla całego widocznego brzegu, w `PRERENDER` — `rimDarken`; nie używaj czarnego konturu #000000.
6. Cień rysuj w osobnym znaku palety `PALETTES.SHADOW`, przed obiektem. Dopilnuj by nie zasłonił sylwetki.
7. Uruchom `validate`; błędy napraw, ostrzeżenia oceniaj na obrazie. Podgląd w 1×, 3× i 8×. Eksportuj SVG i/lub PNG oraz kod generatora.
8. Jeśli tworzysz scenę, użyj `makeSprite`, `composeScene`, `validateScene`, `sceneToSvg`/`sceneToRgba`. Algorytm sortowania jest przybliżony: kontroluj ręcznie zasłanianie wysokich i wielokaflowych obiektów.

## Gwarantowane API

`PALETTES`, `tone`, `makeGrid`, `getCell`, `setCell`, `gridToRows`, `fillRect`, `fillPolygon`, `fillEllipse`, `drawLine`, `fillDiamond`, `shadeEllipse`, `shadeRegion`, `outline`, `rimDarken`, `isoBox`, `hipRoof`, `validate`, `asciiToSvg`, `rasterize`, `upscale`, `encodePng`, `makeSprite`, `composeScene`, `validateScene`.

## Ograniczenia i jakość

- 12 lub 24 kolory wg wielkości płótna; wyłącznie kolory zadeklarowane w palecie.
- Wskaźnik `qa.ok` potwierdza poprawność techniczną, nie atrakcyjność artystyczną.
- Dla klatek ruchu zachowaj kotwicę i rozmiar, nie kopiuj jednego kierunku jako całego atlasu.
- Wspólny format wyjścia i bramki QA: `../shared/asset-contract.md`, `../shared/qa.md` w zestawie wieloskilli.
- Wzorcowe działające generatory i wynik: `../demo/real/render-real.js`, `../demo/real/output/retro_*.png`.

**Nie twierdź, że po odtworzeniu samego SVG otrzymano pełny pipeline PNG.**

## Tryb DARK FANTASY (v4 — do gry Godot)

Dla stylizowanych, ręcznie dopracowanych 2D jednostek i lochów skorzystaj z dodatkowego oryginalnego warsztatu Python/Pillow `scripts/pixelcraft.py`. Zachowuje `spritekit.js` bez zmian (zgodność z poprzednimi projektami). Ten tryb nie jest „skrótem do Diablo II-quality”; wykonuje jawne warstwy i rysowanie natywnych pikseli.

Obowiązkowe lektury: `references/art-direction.md` i `references/reference-learning.md`. `pixelcraft.py` zawiera: `Layered`, `PixelPen`, `ramp`, `stats`, `frame_checks`, `make_atlas`, `save_atlas`, `analyze_reference`, `clean_import`.

Działający przykład ośmiokierunkowej jednostki i sceny: `../demo/arpg/render_demo.py`, wynik `demo/arpg/output/`. PNG powstaje rzeczywiście w Pythonie/Pillow przy rozdzielczości 1×; nie wyświetlaj go jako pre-renderu 3D ani obrazu wygenerowanego przez silnik `spritekit.js`. `pixelcraft.py` jest niezależnym nowym backendem w obrębie skilla retro, nie stanowi kopii `pixelstudio.py` z GitHub.

Nie stosuj domyślnego ograniczenia 12–24 kolorów z `spritekit.js` do osobnego warsztatu `pixelcraft.py`; kontroluj budżet palety zależnie od rozmiaru i zamierzonego stylu. Zapewnij importerowi Godot stałe ramki i kotwice (zobacz `rpg-godot-pipeline`).
