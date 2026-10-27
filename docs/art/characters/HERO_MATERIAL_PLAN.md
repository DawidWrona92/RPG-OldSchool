# Welesza — biblioteka materiałów bohatera / plan przekazania Codexowi

**Status: paczka robocza do oceny autora, NIE zatwierdzone materiały finalne.**

## Punkt odniesienia
- `docs/koncepty/17-bohater-i-woz.jpg` i `docs/koncepty/17-bohater-i-woz.md` — trzy widoki podróżnika.
- `vibe/sprite-bohater-codex:assets/sprites/player/README.md`, `REPORT.md`, `previews/osiem-kierunkow-render-384.png` oraz `source/REFERENCE.md` — skontrolowane przy przygotowaniu paczki.
- Kierunek: **zwykły podróżnik**, zgaszony len, ciemna wełna, znoszona skóra, ciemne spodnie, buty, plecak, posłanie, żelazny miecz. Żadnego nowego wyposażenia kanonicznego.

## Wnioski z renderu Codexa
- Postać ma siatkę MakeHuman CC0, płaszcz, osobny kaftan, rękawy, pasy i plecak; już posiada proceduralne materiały, ale skóra i tkaniny są zbyt jednorodne.
- W skali sprite'a 192×192 większość mikrofaktury zanika: najważniejsza jest **makroróżnica materiałów** i drobne przetarcia w miejscach widocznych, nie ekstremalny szum.
- Tekstury nie poprawią samej geometrii płaszcza, twarzy, włosów, butów ani jakości animacji.
- Obecny skrypt Blendera korzysta z `rest_position` i shaderów proceduralnych. Integracja map UV będzie osobnym zadaniem Codexa, w **jego** gałęzi, bez zmiany przez opiekuna biblioteki.

## Chunks i kryteria

| Chunk | Rezultat | Status |
|---|---|---|
| **01 — bazowe tkaniny i skóra** | 3 materiały: len koszuli, ciemnobrązowa wełna płaszcza, skóra kaftana; 4 mapy na materiał + instrukcja | **Paczka do recenzji / zrealizowana** |
| **02 — wyposażenie podróżnika** | ciemna skóra butów, skóra plecaka, zszarzałe płótno posłania, ciemna wełna spodni | **Dostarczona** (`c6c1a67`), [opis](../../../assets/textures/characters/hero/README.chunk02.md); zintegrowana na `vibe/sprite-bohater-codex` |
| **03 — detale i uzbrojenie** | rzemienie, żelazo, stal miecza, skóra człowieka, włosy i 4 nakładki zużycia (krawędzie, wilgoć, błoto, szwy) | **Dostarczona** (`aa7ac7a`, `ff74eb7`), [opis](../../../assets/textures/characters/hero/README.chunk03.md); zintegrowana na `vibe/sprite-bohater-codex` |
| **04 — weryfikacja Blendera** | próbne renderowanie na kopii modelu 8 kierunków i w skali 192 px, porównanie z referencją, rekomendacja przyjęcia/odrzucenia | W toku na `vibe/sprite-bohater-codex` (rendery po integracji są gotowe; atlas i porównania wymagają ponownego eksportu) |

**Handoff po każdym chunku:** ścieżka i SHA commitu, manifest map, czego nie sprawdzono, lista wad, kolejny chunk. Kolejny chunk uruchamiamy po wiadomości autora „kontynuuj”; brak działań w tle.

## Odbiór
1. Sprawdź każdy PNG i hash; brak napisów, cieni wymalowanych na bazowej tkaninie, artefaktów alfy.
2. `Base Color` = sRGB; `Roughness`, `Height`, `Normal` = Non-Color.
3. Mapy o rozdzielczości 512×512 są tworzone proceduralnie do prototypu, a nie z fotogrametrii. Normal OpenGL (+Y) wyprowadzona z syntetycznego reliefu; nie jest pomiarowym PBR.
4. Periodyczne wzory i szum zostały przygotowane do powtarzania, lecz faktyczne szwy UV, skala faktury i wynik w Cycles wymagają osobnego testu Codexa.
5. Nie zastępuj kontrolowanego geometrycznego szwu losowym wzorem; testuj pod chłodnym światłem i ciepłym ogniskiem.

**Nie zmieniano brancha `vibe/sprite-bohater-codex`, modelu, materiałów Blendera ani renderów postaci.**
