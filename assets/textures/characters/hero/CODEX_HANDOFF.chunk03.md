# Codex — gotowy pakiet materiałów PBR, Chunk 03

**Źródło:** branch `vibe/hero-materials-chunk02-gpt6`, katalog `assets/textures/characters/hero/`. Modyfikacje są dodane obok Chunks 01 i 02; nie ma zmian w Twoich plikach modelu.

**Skoncentruj się na integracji** pięciu zestawów: rzemienie, kute żelazo, stal głowni, skóra podróżnika, włosy; plus cztery maski/nakładki. Poprzednie cztery zestawy (spodnie, buty, plecak, posłanie) są w tym samym branchu. Materiały Chunk 01 istnieją na `main`.

**Kontrakt:** BaseColor=sRGB, Roughness/Metallic/Height/Normal=Non-Color; normal OpenGL +Y, tangent. Zmniejsz siłę normal, jeśli mikrowzory powodują morę. Nie oczekuj, że gotowe PNG same wiedzą, gdzie przebiega szew lub krawędź: krawędziową maskę wygeneruj z modelu/UV, a `edge_wear_breakup_mask` potraktuj jako jej multiplikator; mud jako lokalny decal RGBA; stitching jako trim.

**Odbiór:** identyczna kamera / ekspozycja i animacje stare vs nowe; osiem kierunków w 192 px; test na chłodnym tle boru i przy ciepłej latarni. Pokaż 1:1 oraz przynajmniej jedną planszę większą do diagnostyki UV. Zgłoś różnice względem `docs/koncepty/17-bohater-i-woz.jpg` i wady, których nie rozwiązuje teksturowanie. Bez automatycznego scalania eksperymentu z main.
