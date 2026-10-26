# Decyzje stylu graficznego — seria sprite'ów 01

Status: zapis decyzji wykonawczych, nie zatwierdzona karta stylistyczna całej gry. Data: 26 października 2026 r.

## Skąd wzięły się reguły stylu

1. **Wybór narzędzia**: `rts-sprite-router/SKILL.md` dla ARPG Diablo-like wskazuje tryb DARK FANTASY (`retro-rts-sprites/scripts/pixelcraft.py`). Obowiązkowe lektury: `references/art-direction.md`, `references/reference-learning.md`.
2. **Referencje autora**: autor dostarczył 10 screenów — 8 z Diablo II: Resurrected (D2R) i 2 z Sacred. Pliki pozostają poza repozytorium (prawa autorskie Blizzard/Ascaron); zgodnie z `reference-learning.md` wykorzystujemy wyłącznie abstrakcyjne zasady stylu, nie assety.
3. **Pomiar**: wszystkie kadry zmierzone narzędziem `pixelcraft.analyze_reference()` (rozmiar, liczba kolorów, dominujące grupy barw, luminancja) oraz ocenione wizualnie kadr po kadrze. Wyniki pomiarów: `../.agents/skills/retro-rts-sprites/references/learned/welesza-d2r-sacred.md`.

## Decyzje

| # | Decyzja | Uzasadnienie |
|---|---|---|
| D1 | Bazą stylu jest wyłącznie D2R | Decyzja autora: „odrzućmy wszystko to co z Sacred nie pokrywa się z D2R". Sacred posłużył tylko do potwierdzenia elementów wspólnych (kamera izometryczna, skala postaci). |
| D2 | Paleta jednostek przyciemniona i zdesaturowana względem terenu | Pomiary D2R: pełna luminancja 0–255, groza przez ciemność i desaturację; jednostka nie jaśniejsza od średniej sceny. |
| D3 | Rim light 1 px po stronie lewej-górnej | Widoczny w kadrach D2R jako subtelne rozjaśnienie krawędzi jednostek; poprawia czytelność sylwetki na ciemnym tle boru. |
| D4 | Czerwień tylko jako sygnał (atak nieparowalny, krew, ogień) | W D2R czerwień 0° występuje wyłącznie jako akcent zagrożenia; spójne z bestiariuszem (sygnał wizualny groźnego ruchu). |
| D5 | Zakaz ditheringu na tkaninach, płaskie płaszczyzny + ostre refleksy metalu | Potwierdzone wizualnie w D2R; zgodne z regułami `art-direction.md` („pillow shading" zakazany). |
| D6 | Kontur `#15151c`, nie czysta czerń | Reguła `art-direction.md` potwierdzona kadrami D2R. |
| D7 | Screeny referencyjne poza repo, bez konwersji na assety | Prawa autorskie + procedura `reference-learning.md` („nie kopiuj cudzych gotowych assetów do własnej gry"). |

## Co z tego wynika dla serii 01

Seria 01 (ENM-zdziczaly-pies, ENM-powrotnik, ENM-drwal) została przerysowana wg D1–D6 w commicie „Przerysuj serie 01 w stylu D2R". Źródło: `assets/sprites/welesza-01/generate_sprites.py`; reguły trwale zapisane w karcie wyuczonej `.agents/skills/retro-rts-sprites/references/learned/welesza-d2r-sacred.md`.

Seria 02 i kadry ART-01–04 z `pakiet-04-obrazy.md` mają korzystać z tej samej karty, zanim powstaną nowe decyzje.

## Granice

- Karta nie rozstrzyga stylu finalnej gry; to decyzja autora po obejrzeniu serii porównawczej (procedura z `pakiet-04-obrazy.md`).
- Wartości luminancji i barw są robocze; przy wyborze silnika i pipeline'u mogą wymagać osobnej walidacji (np. kontrast na docelowym ekranie Godota).
- Nie przeanalizowano animacji referencyjnych; reguły faz ruchu pozostają z `art-direction.md`.
