# Bohater — skóra i oko, v3: dojrzała, ogorzała twarz

**V2 (`2701714`) przyjęta przez autora jako wersja robocza. V3: PROTOTYPE_NOT_APPROVED**, do oceny i integracji przez Sola. Część B czeka na P2.

## Zmiany po review v2

**Drobna korekta po review v3:** usunięto wszystkie rysowane poziome bruzdy szyi z height, pochodnej normalnej i modulacji szorstkości. Opalenizna i rozmyta granica zarostu pozostają bez zmian. Podglądy v3 i manifest odświeżono przy normal 0,45.

- **Czoło:** trzy poziome bruzdy wyłącznie nad brwiami w środkowej części. Mają różne długości, przesunięcia, krzywizny, szerokości i głębokości oraz łagodne, nierówne zakończenia. Brak sinusoidalnego rytmu i bruzd biegnących przez skronie; maska tych bruzd jest na skroniach zerowa.
- **Kurze łapki:** po dwie krótkie, płytkie linie przy zewnętrznym kąciku oka, z lekką asymetrią. Bruzdy nosowo-wargowe pozostają bez zmian.
- **Dłonie i przedramiona:** całkowicie usunięto sinusoidalne kreski z pigmentu i height, więc także z pochodnej normalnej; usunięto pola żył i ścięgien oraz ich kolor. Zostały delikatnie ciemniejsze, zaokrąglone knykcie, miękkie zgrubienia i subtelny, rozproszony brud w zagłębieniach oraz przy paznokciach. Nie rysujemy linii zagłębień. Usunięto też cienką bliznę dłoni wraz z pozostałymi kreskami; pozostają **dwie wygojone blizny twarzy i dwa pieprzyki**.
- **Zarost na szyi:** usunięto poziome bramkowanie według wysokości głowy. Wspólna maska cienia zarostu, mieszków, siwizny i szorstkości kończy się teraz nieregularnym, asymetrycznym łukiem pod żuchwą, rozmytym ku grdyce. Szerokość rozmycia wynosi około 4,4 cm w skali postaci 1,8 m.

Zachowano płynną opaleniznę v2, linię włosów, dyskretną pigmentację, zarost z siwizną, blizny i pieprzyki twarzy. Są elementami wyglądu, bez dopisywania historii. Bez tatuaży, malunków, biżuterii i świeżych ran. Oczy pozostają identyczne bajt w bajt z v2. Nazwy, rozdzielczości, formaty, UV i siatka są niezmienione.

## Materiał i generator

**Normal strength: 0,45** — w tej wartości oceniono zarówno v2, jak i v3 na portretach 768 px. Basecolor i oczy: sRGB. Roughness, normal_opengl, height i SSS: Non-Color. Kolor i normalna RGB 8 bit; roughness/SSS grayscale 8 bit; height grayscale 16 bit, neutralnie 0,5. Ciało 4096 i pochodne 2048, oczy 512.

Normalna OpenGL +Y do węzła Normal Map z bazą MikkTSpace. Umowny pełny zakres height 0,002 m, centered 0,5; nie nakładać równocześnie pełnego bump i normalnej. SSS jest maską względną, nie pomiarem tkanki; w podglądzie mnoży wagę SSS przez 0,30.

Ten sam `source/build_maps.py`: natywne UV grupy `body`, interpolowane pozycje 3D, deterministyczne pory i eksport Pillow. Pola materiału v2 rozwinięte do v3 pozostają w `source/aging_v2.py` (historyczna nazwa modułu). Światła, AO i normalne powierzchni nie uczestniczą w obliczaniu albedo. Drobne cechy gasną 32–56 px od krawędzi UV, tło jest całkowicie wypełnione nearest-surface dilation. Kolor regionalny pozostaje ciągłym polem pozycji 3D.

## Przed / po

`podglad/v3/before/`: v2 z commita `27017148d13eb9c422ff54da760775f7eb16a331`, ponownie wyrenderowana ze snapshotu jej map. `podglad/v3/after/`: v3. Po trzy kadry: **przód, profil i grzbiet dłoni**. `podglad/v3/porownanie.png` zestawia je bez skalowania i korekcji kolorów.

Obie wersje mają identyczną kamerę 768×768, niezmieniony OBJ, **normal 0,45**, światła kontraktu, AgX Medium High Contrast, exposure −0,2, Cycles 64 próbki, seed 1703, 4 wątki i brak denoise. To diagnostyka materiału, nie eksport sprite'ów.

Bieżące rendery v3 (także tył głowy, pełne ciało i inne strony dłoni) są w `podglad/skin_*.png`. Starsze porównania w `podglad/v2/` zachowano jako archiwum; nie przedstawiają aktualnych map v3.

## Odtworzenie

Wymagania: Blender 4.3 (sprawdzono 4.3.2), Python 3, NumPy 2.3.5, SciPy 1.17.0, Pillow 12.3.0. Generowanie 4K wymaga kilku–kilkunastu GB RAM. Korzystamy z istniejącego checkoutu, bez dodatkowego worktree.

```bash
# Z katalogu repozytorium; odczyt przypiętego MakeHuman hm08 CC0:
git show 421c7e895e6a029181dcb7c63ab277ad7bab4ca0:assets/sprites/player/source/third_party/base.obj > /tmp/hero-base.obj
cd assets/textures/characters/hero/unique
OPENBLAS_NUM_THREADS=1 python3 source/build_maps.py --mesh /tmp/hero-base.obj
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj
python3 source/validate.py --mesh /tmp/hero-base.obj
```

Przykład powtórzenia porównania (snapshot v2 można odtworzyć przez `git show 2701714:assets/textures/characters/hero/unique/NAZWA_MAPY` do katalogu poza checkoutem):

```bash
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --texture-dir /tmp/hero-v2-review-snapshot --output-dir podglad/v3/before --view front profile hands_dorsal
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --output-dir podglad/v3/after --view front profile hands_dorsal
python3 source/compare_v2.py --version 3
```

`--texture-dir` wymaga basecolor, roughness, normal_opengl i sss_mask. Świadoma regeneracja wymaga następnie odświeżenia manifestu przez `source/write_manifest.py` oraz raportu walidacji. Zwykły walidator nie nadpisuje danych.

`qa/validation.json`: odczyt PNG, formaty, skalowanie, normalne, pary wierzchołków szwów i SHA-256. `qa/v3_material_checks.json`: parametry v3, pokrycie UV przez dwie blizny i dwa pieprzyki, jawne wyłączenie pól żył/ścięgien/linii dłoni. Manifest zawiera SHA-256 wszystkich plików poza nim samym, narzędzia, źródła oraz poprawną wersję materiału każdego podglądu. Instrukcje v1/v2 zachowano w `source/README-v1.md` i `source/README-v2.md`.

## Ograniczenia

- Neutralna siatka hm08 nie jest docelową rzeźbą Sola. Materiał nie zmienia kości twarzy ani sylwetki. Brak włókien włosów/zarostu i docelowych gałek/rogówki; oczodoły są puste.
- Proceduralna interpretacja skóry, nie skan ani ręcznie malowany portret. V3 wymaga oceny autora na modelu docelowym. Nie wykonano oceny w skali gry 1×, animacji i integracji ze strojem.
- Render i pomiar par szwów nie dowodzą ich niewidoczności przy każdym mipie i deformacji. Height/normal nie są wypaleniem rzeźby high-poly; SSS nie jest pomiarem fizycznym.
- Oczy mają udokumentowane pochodzenie repozytoryjne; poprzednik nie zapisał generatora. Nie przypisujemy im zmyślonego modelu AI ani fotografii.
