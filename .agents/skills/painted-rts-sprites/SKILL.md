---
name: painted-rts-sprites
description: Generuje szczegółowe izometryczne sprite'y malarskie 2.5D historycznego RTS z teksturami, osobnym cieniem i maską drużyny; obsługuje budynki, rekwizyty, jednostki i osiem kierunków dzięki silnikowi painter.js.
---

# Painted RTS — backend potwierdzony

## Wymagania i wynik

Uruchamiaj `scripts/painter.js` w Node albo kompatybilnym runtime JS. Rdzeń jest pozbawiony operacji plikowych; host zapisuje obiekt `pt.saveSprite(result,name).files`. Wyjścia: `sprite.png` RGBA, `shadow.png` RGBA, `team.png` L, `preview.png` oraz JSON kotwicy. Typowy tile: 96 px; elewacja kamery 30°, słońce prawa-góra.

## Minimalny przykład

```js
const pt = require('./scripts/painter.js');
const P = pt.sprite({ width: 450, height: 370, anchor: [225,295], supersample: 2 });
pt.house(P,{style:'stone',roofTone:'tile',w:2.1,d:1.6,team:true,seed:7});
const result=P.render();
const findings=pt.validateSprite(result,{kind:'building',expectTeam:true});
if(findings.some(x=>x[0]==='ERR')) throw new Error(JSON.stringify(findings));
const files=pt.saveSprite(result,'stone_house').files;
// W Node: Object.entries(files).forEach(([name,data]) => fs.writeFileSync(name,data));
```

## Procedura produkcyjna

1. Rozpoznaj referencję: skala, nasycenie, cień, orientacja, punkt kotwicy, liczba kierunków.
2. Dla budynku użyj gotowych elementów (`house`, `tower`, `tent`, `well`, `wagonWheel` itd.); dla człowieka `humanoid`/`horse` i ustawienia `yaw`, `moving`, `phase`.
3. Przy własnym obiekcie zbuduj sylwetkę z `P.box`, `P.ellipsoid`, `P.frustum`, `P.rod`, `P.poly`, `P.wall`, `P.roof`; sprawdź rzeczywiste sygnatury w `scripts/painter.js`.
4. Dodaj tekstury i materiały przez `pt.material({color,team:true})`, pamiętając że maska drużyny jest osobnym kanałem.
5. Renderuj w ramce z dużym marginesem; `frameClipped=true` to błąd. `trim:true` tylko dla pojedynczego assetu.
6. Wizualnie oceń 1× i powiększenie. Użyj `pt.validateSprite`; ostrzeżenia wymagają świadomego przeglądu, nie automatycznego odrzucenia.
7. Dla atlasu użyj `pt.renderFrames({frame,directions:8,phases,build})`, `pt.validateSheet`, `pt.packSheet`, `pt.saveSheet`.
8. **Wbudowane** `pt.humanoid`/`pt.house` już używają `yaw`/`rot` i wykonują obrót. **Własne** modele rysowane w stałej orientacji mogą wymagać wirtualnego obrotu; patrz `references/viewdir.md`. Nie obracaj natywnych modeli drugi raz.
9. Po atlasie sprawdź wszystkie pary kierunków (`scripts/direction-check.js`), zgodność kotwic i kadrów oraz ręcznie poprawność orientacji broni, frontu i tyłu.
10. Zapisz skrypt budujący oraz sprite, cień, maskę, podgląd i metadane.

## Ograniczenia potwierdzone

Silnik tworzy przekonujące budynki, ale wbudowany humanoid pozostaje **uproszczoną figurą bez twarzy**. Nie należy obiecywać realistycznego rygu lub proceduralnych animacji klasy Diablo 2. Cień pada na ziemię, nie obejmuje realistycznego global illumination i interakcji wielu obiektów. Duże obiekty wymagają kontroli zasłaniania.

## Dołączone materiały

- `references/viewdir.md`: obroty i pułapki atlasów;
- `references/rzemioslo.md`: projektowanie bardziej szczegółowego wyposażenia — pełny katalog wymaga osobnych implementacji, nie jest funkcją bazową silnika;
- `scripts/direction-check.js`, `scripts/silhouette-check.js`: uzupełniające testy;
- `../demo/real/render-real.js`: **wykonany** kod demonstracyjny i eksport PNG;
- `../shared/asset-contract.md`, `../shared/qa.md`: kontrakt wyjścia.

Każda deklaracja jakości wymaga obejrzenia rzeczywistego renderu, a nie wyłącznie zaliczenia walidatora.

## Tryb Godot dark-fantasy (v4)

Dla scen Diablo-like renderuj głównie statyczne rekwizyty, architekturę i roślinność. Bohaterów traktuj jako prototypowe sylwetki: warstwuj widoczne części sprzętu i kontroluj zamiany widoczności ręki/tarczy pomiędzy kierunkami. Porównuj klatki z tłem gry, nie tylko na transparentnym PNG. 

Używaj wspólnej kotwicy przy zmianach sprzętu; nie pozwól, aby broń w klatce ataku wymuszała przesunięcie korpusu. Analizę czytelności i powtórzeń kierunków przeprowadź na pełnym atlasie w `painted-rts-sprites/scripts/direction-check.js`. Aby przenieść asset do Godot, zachowaj jego osobną warstwę cienia i maskę team, jeśli potrzebne; nie redukuj go automatycznie do 24 kolorów i twardej alfy.

Łączenie z nowym pixel-artem jest możliwe jedynie po jawnej walidacji wspólnej skali i stylistyki. Sama izometria 2:1 nie gwarantuje harmonii między ręcznie klastrowanym pikselem a miękkim renderem Painted.
