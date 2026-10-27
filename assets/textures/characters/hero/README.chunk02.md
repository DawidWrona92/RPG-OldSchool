# Welesza — biblioteka tekstur bohatera: Chunk 02 (wyposażenie)

**Paczka czterech rzeczywistych zestawów PBR (16 PNG, 512×512). Status: PROTOTYPE_NOT_APPROVED.** Nie jest to nowe wyposażenie ani zmiana koncepcji postaci; zakres pochodzi z `docs/koncepty/17-bohater-i-woz.jpg` na `main` oraz dokumentu `docs/art/characters/HERO_MATERIAL_PLAN.md`. Na `main` istnieje już Chunk 01 (len koszuli, wełna płaszcza, skóra kaftana).

| ID | Przypisanie do modelu Codexa | Efekt |
| --- | --- | --- |
| `wool_trousers_charcoal` | nogawki spodni | matowa ciemna brunatnoszara wełna, splot skośny |
| `leather_boots_dark_mud` | cholewy i noski butów | ciemna skóra, skala zagnieceń i mikroporów |
| `leather_backpack_aged` | główna bryła plecaka | zgaszona postarzana brązowa skóra |
| `canvas_bedroll_ashen` | rulon posłania na plecaku | zszarzałe grube płótno, inny splot niż koszula |

Dla każdego: `*_basecolor.png` w **sRGB**, `*_roughness.png`, `*_height.png`, `*_normal_opengl.png` jako **Non-Color**. `Normal` jest OpenGL/+Y, wyliczoną z syntetycznej wysokości mikrofaktury. Materiały autorskie proceduralne, nie skanowane ani pomiarowy PBR. Nie mają wbudowanego kierunkowego oświetlenia, dużych szwów ani plam błota dopasowanych do powierzchni konkretnej odzieży. Wzór źródłowy okresowy, natomiast poprawność UV i filtrowania musi zweryfikować Codex.

## Przekazanie Codexowi

1. Pracuj na **własnej gałęzi** `vibe/sprite-bohater-codex`; nowy materiał dostarczono bez modyfikowania `assets/sprites/player/source/bohater.blend`, `source/build_player.py` ani atlasów. Przenieś same cztery zestawy z tej gałęzi do swojego środowiska.
2. Obecny generator korzysta z `rest_position` i proceduralnego `Noise/Wave`; nowe `Image Texture` wymagają właściwych UV lub jawnego planu mapowania. Zmień skrypt tak, by regeneracja nie przywracała starych shaderów.
3. Podłącz `Base Color`, `Roughness`, subtelną `Normal Map` (`Tangent Space`, zwykle mała siła). `Height` traktuj jako alternatywny input `Bump`, nie podwójną wypukłość. Dla tkanin `Metallic=0`.
4. Sprawdź nie tylko render 384 px, ale końcowe sprite'y **192 px** we wszystkich kierunkach S/SW/W/NW/N/NE/E/SE; testuj chłodne i ciepłe oświetlenie, migotanie i aliasing podczas chodu. W razie mory zmień skalę splotu / redukuj normal, a nie podnoś rozdzielczość atlasu.
5. Sprawdź kolor płaszcza vs nowe spodnie, obrys plecaka, kontrast butów na ciemnym tle, zachowaj ślady użytkowania bez „plastikowego” połysku. Gdy tkaniny się zlewają, zgłoś konkretne klatki i nie wprowadzaj pozornej poprawy przez globalne rozjaśnienie.

## Ograniczenia i QA

- Brak UV-aligned masek zabrudzeń i szwów; planowany **Chunk 03**.
- PNG 512 px nie zapewniają, że tekstura jest czytelna po eksporcie do sprite'a — odbiór materiału tylko po renderze z modelu.
- Niezależne ślady normal/height to mikrofaktura, nie zastępują przestrzennego modelowania fałd i krawędzi plecaka.
- Pełna mapa plików i SHA Git blob: [manifest.chunk02.json](manifest.chunk02.json).
