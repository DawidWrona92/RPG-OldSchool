# Welesza — bohater, Chunk 03/04: uzbrojenie, detal, skóra, maski

**Stan:** gotowa biblioteka źródłowych map obrazowych do integracji; prototyp **NIEZATWIERDZONY artystycznie**. Pakiet nie zmienia modelu Codexa, animacji ani wyposażenia kanonicznego.

## Zakres dostawy

W 5 nowych zestawach znajdują się łącznie **22 osobne tekstury PBR-style PNG** (w tym 2 metaliczne), rozdzielczość **512×512**:

| Materiał | Element bohatera | Uwaga techniczna |
| --- | --- | --- |
| `leather_straps_worn` | rzemienie, paski, pochwa | skóra matowa i cieńsza niż kaftan; **Metallic=0** |
| `iron_hardware_blackened` | sprzączki, klamry, jelec, nitowanie | ciemne żelazo; oddzielna mapa `metallic` |
| `steel_sword_weathered` | głownia miecza | jaśniejsza stal, wydłużone rysy; oddzielna mapa `metallic` |
| `skin_traveler_weathered` | twarz, kark, przedramiona | ogólny materiał skóry, **nie atlas twarzy** ani mapa blizn; zachować delikatne SSS |
| `hair_dark_umber` | pasma włosów | ślady pasm w materiale, **nie zastępuje** geometrii fryzury |

Każda baza: `*_basecolor.png` (sRGB), `*_roughness.png`, `*_height.png`, `*_normal_opengl.png` (wszystkie Non-Color). Dwie metaliczne bazy mają też `*_metallic.png` (Non-Color). Normal OpenGL/+Y generowany z syntetycznej wysokości; szczegóły nie są pomiarowym PBR i wymagają kontrolowanego shaderu.

## Maski i nakładki

| Plik | Format | Włączenie do materiału |
| --- | --- | --- |
| `overlays/edge_wear_breakup_mask.png` | 512², grayscale | stochastyczna *modulacja* zużycia, **pomnożyć przez maskę krawędzi z UV/curvature**; sam obraz nie rozpoznaje geometrycznych krawędzi |
| `overlays/wetness_breakup_mask.png` | 512², grayscale | maska miejscowego przyciemnienia Base Color oraz obniżenia Roughness; efekt umiarkowany, bez malowanego światła |
| `overlays/mud_spatter_decal_rgba.png` | 512², RGBA | brud z alfą jako lokalny decal, np. na dół płaszcza, buty i spodnie; **nie jest bezszwowy** |
| `overlays/stitching_trim_strip_rgba.png` | 1024×256, RGBA | odcinek szwu / trim po wyznaczonej krzywej UV; nie kopiować przypadkowo na całą powierzchnię stroju |

## Integracja w Blenderze / zadanie Codexa

1. Przenieś potrzebne PNG z `main` (dawniej gałąź `vibe/hero-materials-chunk02-gpt6`, scalona 27.10.2026), nie naruszając danych `vibe/sprite-bohater-codex`. Użyj stabilnego UV lub jawnie kontrolowanego mapowania; aktualny model Codexa korzysta z `rest_position`, `Noise/Wave`.
2. Zachowaj dotychczasowe kontrasty: len koszuli, ciężka ciemnobrązowa wełna płaszcza, brunatna skóra kaftana, jasne płótno posłania i ciemne spodnie. W metalach podłącz `Metallic`, aby żelazo było bardziej matowe od stali miecza.
3. Integruj maski na dedykowanych regionach UV/mesh. Mnożenie `edge_wear_breakup_mask` przez rzeczywistą maskę krawędzi jest obowiązkowe; brud to lokalne decal/alpha, nie losowa plama na każdym fragmencie ciała. Szwy wymagają prowadzenia wzdłuż odpowiednich krawędzi.
4. Testuj `Base Color` w sRGB; wszystkie inne mapy w `Non-Color`. `Normal Map` w Tangent Space z małą mocą. `Height` służy ewentualnie do alternatywnego, delikatnego `Bump` i **nie może dublować** normal.
5. Skóra postaci: zachować łagodną transmisję podpowierzchniową, a nie metaliczny połysk. Włosy: materiał może zawierać kierunkowy detal, ale powłoka geometryczna nadal wymaga poprawy przez Codexa.
6. Wykonaj porównanie 8 kierunków (S/SW/W/NW/N/NE/E/SE), końcowego sprite'a **192×192**, ruchu i dwóch temperatur światła. Sprawdź aliasing, przesycenie metalu i czytelność broni na ciemnym tle.

## Granice paczki

To zestaw niezależnych materiałów i nakładek, **nie kompletna mapa UV specyficzna dla modelu**. Nie naprawi sylwetki, riggu, ruchu miecza, deformacji płaszcza ani wyglądu twarzy. Nie umieszczać na `main` jako artystycznie zatwierdzonych przed renderem testowym. Zobacz `manifest.chunk03.json` oraz `CODEX_HANDOFF.chunk03.md`.

**Uwaga o plikach przezroczystych:** decale błota i szwy zostały zapisane jako paletowane PNG (color type 3 z tRNS), które po wczytaniu zachowują alfę/RGBA. Dzięki temu mieszczą się w limicie odczytu GitHub Contents API. Maska alpha nadal wymaga odpowiedniego podłączenia w shaderze.
