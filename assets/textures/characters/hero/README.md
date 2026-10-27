# Bohater Weleszy — biblioteka tekstur pod Blendera

**Paczka v0.1 · Chunk 01/04 · status PROTOTYPE / do zatwierdzenia.**

Materiały dopasowano do referencji `docs/koncepty/17-bohater-i-woz.jpg` i aktualnych renderów `vibe/sprite-bohater-codex`. Są to **realne osobne pliki PNG**, nie plansza referencyjna. Każdy zestaw zawiera:

- `*_basecolor.png` — kolor bazowy w sRGB, bez napisów ani renderowanego światła.
- `*_roughness.png` — artystyczna mapa chropowatości, **Non-Color**.
- `*_height.png` — syntetyczna wysokość mikrofaktury, **Non-Color**.
- `*_normal_opengl.png` — normal wyprowadzony z height, OpenGL/+Y, **Non-Color**; zweryfikować orientację w docelowym shaderze.

**512×512 px / PNG**; `Base Color` i `Normal` paletowane w pliku dla bezstratnego zapisu wybranych barw, roughness i height w skali szarości. Żaden materiał nie jest skanem lub zmierzonym zestawem PBR. Zobacz [manifest](manifest.json) i [plan](../../../../docs/art/characters/HERO_MATERIAL_PLAN.md).

## Podłączenie w Blenderze 4.x

1. Przygotuj stabilne UV dla elementu stroju; aktualny generator Codexa używa również `rest_position` i proceduralnego Noise/Wave — nowe Image Texture wymagają dopracowania mapowania.
2. `Image Texture (Base Color, sRGB)` → `Principled BSDF/Base Color`.
3. `Image Texture (Roughness, Non-Color)` → `Principled BSDF/Roughness`.
4. `Image Texture (Normal, Non-Color)` → `Normal Map` (Tangent Space) → `Principled BSDF/Normal`. Dobierz małą intensywność normal i sprawdź w świetle bocznym.
5. Height może zamiast normal zasilić subtelny `Bump/Height`; nie łącz dwóch wypukłości bez świadomego ustawienia węzłów.
6. Test: płaszcz i rękawy na wszystkich ośmiu kierunkach w **192 px**, z chłodnym i ciepłym oświetleniem; weryfikuj powtarzanie, moiré, błędny połysk i zasłanianie detalu przez geometrię.

**Nie** można polegać na fakturze do zbudowania fałd, marszczeń, przeszyć, krawędzi kaftana czy dobrze wyglądającego plecaka. To są również zadania modelarskie i UV. Nie kopiować siłowo generatora Codexa ani nie resetować jego materiałów.

## Materiały

| Zestaw | Zastosowanie |
|---|---|
| `linen_shirt_worn` | tunika i podwinięte rękawy |
| `wool_cloak_dark_brown` | płaszcz, kaptur i warstwa naramienna |
| `leather_vest_weathered_brown` | kaftan, pasy, sakwy i próbnie plecak |

## Weryfikacja

- Wygenerowano 12 PNG (3 × 4); potwierdzono sumy kontrolne Git blob po przesłaniu danych.
- Zgodność UV i renderu na modelu Codexa: **nieprzetestowana**; akceptacja artystyczna: **otwarta**.
- Rozdzielczość 512 px to materiał testowy do sprite'a, nie produkcyjny standard 4K. Dalsze powiększanie nie tworzy automatycznie nowych szczegółów.
