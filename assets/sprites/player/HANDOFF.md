# Bohater v2 — przekazanie pracy

Gałąź: `vibe/sprite-bohater-codex`. **Aktywne źródło: `source/bohater_v2.blend`.** Stan roboczy przed B2; nie jest wzorem zatwierdzonym do produkcji.

## Wiążące ustalenia

- Dokumentacja i decyzje autora mają pierwszeństwo nad konceptami. Głowa według [19](../../../docs/koncepty/19-bohater-twarz.md), strój według [17](../../../docs/koncepty/17-bohater-i-woz.md).
- Stary, mocno ogorzały, silny podróżnik; pełne policzki i mocna żuchwa, ciężkie brwi, bruzdy i zmęczony wyraz. Włosy średniej długości do żuchwy, ciemnobrązowe z siwizną, potargane. Broda i wąs z włókien, więcej siwizny na podbródku.
- D1: miecz w pochwie przy lewym biodrze. D2: pełna grupa `body` MakeHuman, ta sama topologia i natywne UV. D3: `default.mhskel`, 163 kości, `default_weights.mhw`.
- Nie animować i nie eksportować atlasów przed zgodą B2. Sześć pojedynczych póz diagnostycznych nie oznacza rozpoczęcia animacji.

## Źródła i tekstury

- `source/bohater.blend` (rev08) i `source/bohater_detale.blend` są archiwum. Sumy w `source/archive-sources.json`; nie nadpisywać.
- Skóra **v3** z gałęzi `vibe/hero-textures-gpt6`, commit `bc1da51`: skopiowany katalog `assets/textures/characters/hero/unique/`, 51 plików zgodnych z manifestem. Nie scalano gałęzi. Obrazy ponownie załadowane i spakowane w v2.
- Basecolor/oczy sRGB, mapy danych Non-Color, normal OpenGL strength 0,45, maska SSS × 0,30. Height pozostawiony niepodłączony obok normalnej, aby nie dublować reliefu. Blizny i pieprzyki wyłącznie z tekstury.
- **Oczekiwane v4:** szarozielona tęczówka i dalsze poprawki skóry od GPT 6. Obecna tęczówka z paczki v3 jest jeszcze brązowa. Nazwy obrazów i natywne UV umożliwiają podmianę bez przebudowy shaderów.
- MakeHuman i targety CC0, przypięta rewizja i SHA w `source/third_party/`. Nie dodano zewnętrznych zdjęć ani zasobów o nieustalonym pochodzeniu.

## Stan i kontrole w toku

F0–F1: jedno źródło v2, pełne ciało, 163 kości. Zachowane 19158 indeksów wierzchołków OBJ, 13378 ścian grupy body i 53512 narożników natywnego UV. `handoff/p1/` zawiera pierwsze widoki UV i pomiary sześciu prób; po zmianach pozy trzeba odświeżyć P1 i obrazy sześciu póz.

F2: rzeźba i włókna zmienione według 19, skóra v3. Pierwszy średni groom był zbyt równy — kolejny pass rozbija go na falujące, nierówne pasma. Portret końcowy do odświeżenia po dopasowaniu stroju.

F3: nowe części stroju, osobne UV, trzy rzeczywiste symulacje Cloth utrwalone w siatkach. Pierwsze drapowanie odrzucone jako niestabilne; drugie: 16 klatek, kolizje i self-collision. Potem poprawki artystyczne barków i luzów; metadane w scenie i częściach. **Przenikania nadal są naprawiane; nie deklarujemy zera. P2 jeszcze niewydane.**

## Wznowienie

1. Sprawdzić `git status`, bieżącą rewizję sceny i najnowszy commit; nie uruchamiać dawnych recept na nowym źródle. Każda ma strażnika rewizji. Renderer nie uruchamia recept ani nie zapisuje `.blend`.
2. Kontrola całego modelu narzędziem PM z main:

```sh
blender -b -t 4 --python-exit-code 1 --python tools/art/check_intersections.py -- \
  assets/sprites/player/source/bohater_v2.blend --frame 1 --json /tmp/v2-intersections.json
```

Lista `--allow` może wymieniać tylko rzeczywiście zamierzone, konkretne styki (osadzone oczy i połączenia miecza). Nigdy całych warstw ubrań. Narzędzie bada siatki, nie Curves, przenikanie brył całkowicie zawartych ani samoprzenikanie pojedynczego obiektu.

3. `source/v2_render_static.py`: read-only `--mode portrait|model|game|p1 --output ...`; kontraktowe światło pozostaje zapisane w modelu. `model`/`portrait` są kamerami diagnostycznymi, `game` zachowuje kamerę 30°, ortho 3,2 m i kotwicę (96; 158,353829) przy 192 px.
4. Po ustabilizowaniu geometrii: `v2_bake_p2.py` + `v2_finish_p2.py`, manifest SHA i siedem plików na część. Nie wypalać niestabilnego stroju i nie mieszać źródeł SHA w paczce.
5. Często commitować i wypychać na własną gałąź. Na koniec zaktualizować ten plik, raport, linki i zakres faktycznie wykonanych kontroli.
