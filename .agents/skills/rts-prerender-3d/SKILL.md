---
name: rts-prerender-3d
description: Generuje szczegółowe izometryczne sprite'y budynków, wież, drzew i machin RTS poprzez rasteryzację teksturowanego modelu 3D do PNG z osobnym cieniem, maską drużyny i walidacją za pomocą rtcore.js.
---

# Pre-render 3D — backend potwierdzony

## Backend i uruchomienie

Dostarczono `scripts/rtcore.js`, czyli rzeczywistą implementację JS. Nie wykonuj dawnych wywołań `rk.*` lub Pythonowych `snake_case`; używaj wyłącznie metod `rt.*` w formie `camelCase`. Oryginalny rdzeń JS jest samodzielny, lecz do zapisu plików potrzebujesz hosta (np. Node `fs`). Domyślna projekcja: 2:1, tile 96 px, oś Z w górę, słońce prawa-góra i cień lewo-dół.

## Sprawdzony przykład

```js
const rt=require('./scripts/rtcore.js');
const fs=require('fs');
const textures=rt.standardTextures(['roof','plaster','timber','stone','grass']);
const m=rt.standardModel(textures);
m.box('stone',[0,0,0.23],[2.4,1.8,0.46]);
m.box('plaster',[0,0,0.95],[2.2,1.6,1.1]);
rt.gableRoof(m,1.1,0.8,1.50,0.7,{material:'roof'});
const camera=new rt.Camera({tilePx:96,halfExtent:3.6,supersample:2,target:[0,0,1.0]});
const result=rt.renderSprite(m,camera,{trim:true});
const check=rt.validateSprite(result,{kind:'building'});
if(check.some(x=>x[0]==='ERR'))throw new Error(JSON.stringify(check));
for(const [name,bytes] of Object.entries(rt.saveSprite(result,'house').files)) fs.writeFileSync(name,bytes);
```

## Workflow

1. Przed modelem zidentyfikuj paletę, rozmiar kafla, oświetlenie, kąt kamery i bazę (0,0,0). Dopasuj do już istniejącego zestawu.
2. Zacznij od dużych brył: `rt.Model` / `rt.standardModel`, `box`, `beam`, `lathe`, `cylinder`, `blob`, `addObj`; potem tekstury, krawędzie, ramy, okna, komin, rekwizyty.
3. Gotowe elementy: `gableRoof`, `halfTimberWall`, `roundTower`, `treeOak`, `treePine`, `palisade`, `barrel`, `crate`, `wheel`, `bush`. Sprawdzaj argumenty w kodzie przy nietypowych konfiguracjach.
4. Kolor gracza tylko przez materiały `team`, `team_dark`, `team_light`; maska drużyny powstaje niezależnie od barwy RGB.
5. Szkic renderuj z niewielkim supersamplingiem, oceniaj sylwetkę w 1× (`rt.reviewStrip`), następnie dodawaj detale. Nie traktuj zwiększenia skali podglądu jako zwiększenia jakości w grze.
6. `frameClipped` oraz techniczne ERR napraw przed eksportem; dla dużych cieni zwiększ `halfExtent`. `rt.validateSprite`, `rt.report` i ręczna ocena są obowiązkowe.
7. Dla kilku kierunków wywołaj `rt.renderSprite(model,camera,{viewAngleDeg:angle,trim:false})`, następnie `rt.validateSheet`, `rt.packSheet`, `rt.saveSheet`. Kotwica i ramka muszą być zgodne.
8. Eksportuj `rt.saveSprite` (sprite, shadow, team, preview, JSON) oraz kod generatora.

## Geometria custom i istotna pułapka importera

`references/meshkit.md` i `scripts/meshkit.js` zapewniają konturowe pryzmy (także wklęsłe) z prawidłowym kierunkiem normalnych. **Ważne:** `rt.Model.addObj(material, obj)` używa *jednego* materiału dla całego tekstu OBJ — **ignoruje** instrukcje `usemtl`. Aby mieć inny materiał na tarczy, jej bokach i tylnej pokrywie, wywołaj `meshkit.splitObjByGroup(obj)` i dodaj każdą grupę do modelu osobnym `m.addObj(material,group.obj,opts)`.

## Uczciwe ograniczenia

Silnik sprawdza się w budynkach, wieżach, terenie i rekwizytach. Realistycznych twarzy, animacji humanoidów, kościowego riggingu, globalnych odbić i sprzętowych shaderów PBR nie ma w dostarczonym runtime. Przede wszystkim nie obiecuj animowanych jednostek Diablo na podstawie pojedynczego statycznego renderu.

## Dołączone pliki

- `scripts/rtcore.js` — bazowy silnik;
- `scripts/meshkit.js`, `references/meshkit.md` — naprawiony i przetestowany generator OBJ;
- `../demo/real/render-real.js` — działające przykłady dwóch assetów 3D;
- `../shared/asset-contract.md`, `../shared/qa.md` — ujednolicone wyniki i QA.

## Tryb Godot dark-fantasy (v4)

Sceny ARPG: priorytetem kamienne ściany, portale, nagrobki, kolumny, wozy, krypty. Utrzymuj rzeczywiste rzuty i wspólne oświetlenie; osobne cienie i punkty zakotwiczenia. Dla kolizji i zasłaniania postaci dostarcz odrębną logiczną bryłę i ew. foreground/occluder — sprite PNG nie niesie tych danych.

Wysoką jakość ruchomych humanoidów można uzyskać przy użyciu zewnętrznego animowanego modelu 3D lub rozbudowanego modelu postaci, a nie wyłącznie kilku prymitywów. Nie kwantyzuj outputów 3D zgodnie z zasadami pixel-artu; pozostaw miękką alfę i tekstury. Połączenie stylów wymaga próbek na prawdziwym tle gry.
