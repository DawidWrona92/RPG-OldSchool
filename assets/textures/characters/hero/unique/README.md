# Bohater — skóra i oko, v2: stary, mocno ogorzały podróżnik

**V1 (`bdc6529`) przyjęta przez autora jako wersja robocza. V2: PROTOTYPE_NOT_APPROVED**, do porównania i integracji przez Sola. Część B nie była wykonywana — czeka na P2.

Nowa decyzja autora w rozdz. 3 briefu na `main` @ `0d52d9efc9986db123affdc132290efcf05483e1` zastępuje dawny wiek 35–40 lat: bohater ma wyglądać na starego, mocno ogorzałego podróżnika. Trzy stare blizny i dwa pieprzyki są elementami wyglądu, bez dopisywania historii.

## Zmiany v2

- Głębszy relief czoła, skończone wachlarze kurzych łapek, bruzdy nosowo-wargowe i fałdy szyi; przyciemniona, chłodniejsza skóra i delikatna wypukłość pod oczami. Pory i przesuszenie ust pozostają mikrodetalem.
- Najsilniejsza opalenizna na nosie, kościach policzkowych, czole i uszach. Przejście żuchwa–szyja ma szerokość **49,7 mm** w skali postaci 1,8 m. Pola regionalne są ciągłe w 3D; nie ma płaskiego odcięcia koloru na żuchwie.
- Nieregularna, miękka linia włosów z drobnymi mieszkami przejściowymi. Szaroniebieskawo-brązowy cień zarostu, gęstsze ciemne mieszki i pojedyncze siwe; pokrycie policzków, żuchwy, podbródka, górnej wargi i spodu żuchwy z nieregularną górną granicą.
- Nierównomierna pigmentacja słoneczna, plamki oraz drobne rozgałęzione czerwone naczynka na nosie i policzkach. Są to zmiany pigmentacji, nie wpieczone oświetlenie.
- **Trzy asymetryczne wygojone blizny:** przez jedną brew, krótka na przeciwległym policzku i mała przy knykciach jednej dłoni. Jaśniejsze, bez czerwonego obwodu; roughness 0,43 i płytkie zagłębienie height do 0,4965. Przecinają maskę zarostu/brwi, wygładzają mikrorelief. Żadnych świeżych ran.
- **Dwa niewielkie, asymetryczne pieprzyki:** policzek i przeciwległy bok szyi. Kotwice blizn i pieprzyków są dopasowane do rzeczywistej powierzchni i odsunięte od pasa ochronnego UV.
- Spracowane dłonie: ścięgna i żyły prowadzone od nadgarstka do stawów palców z pomocniczych punktów szkieletu OBJ, ciemniejsze knykcie, zgrubienia, plamy na grzbiecie, brud w liniach i przy krótkich paznokciach. Paznokcie pozostają keratyną o niższej szorstkości.

Nie dodano tatuaży, malunków, biżuterii ani świeżych ran. Oczy zachowano **bajt w bajt** z v1. Nazwy, formaty, rozdzielczości, UV i siatka są niezmienione.

## Użycie

Basecolor i oczy: **sRGB**. Roughness, normal_opengl, height i SSS: **Non-Color**. Kolor i normalna: RGB 8 bit; roughness/SSS: grayscale 8 bit; height: grayscale 16 bit, neutralnie 0,5. Mapy ciała 4096 i pochodne 2048; oczy 512.

**Zalecana normal strength v2: 0,45**, sprawdzana w portretach 768 px w Blenderze 4.3.2. OpenGL +Y, węzeł Normal Map z bazą MikkTSpace. Nie nakładać równocześnie pełnego bump z height i normalnej. Pełny umowny zakres height: 0,002 m, centered 0,5; height opisuje mikrorelief i nie zmienia sylwetki.

SSS jest względną maską cienkich miejsc (uszy, nos, palce), nie pomiarem grubości. W podglądzie mnoży wagę SSS przez 0,30. Albedo nie korzysta ze świateł, AO ani normalnych powierzchni. Mikrodetal i drobne ślady gasną 32–56 px od brzegu UV; tło jest całkowicie wypełnione przez nearest-surface dilation. Regionalny kolor pozostaje funkcją pozycji 3D również przy szwach.

## Odtworzenie i sprawdzenie

Nadal ten sam generator: rasteryzacja natywnego UV, deterministyczny mikrodetal, mapy liniowe i eksport Pillow w `source/build_maps.py`. Rozszerzenie pól wieku/pigmentacji znajduje się w `source/aging_v2.py`. Bez zmiany pliku OBJ, bez dodatkowego worktree.

Wymagania: Blender 4.3 (sprawdzono 4.3.2), Python 3, NumPy 2.3.5, SciPy 1.17.0, Pillow 12.3.0. Generowanie 4K wymaga kilku–kilkunastu GB RAM.

```bash
# Od katalogu repozytorium:
git show 421c7e895e6a029181dcb7c63ab277ad7bab4ca0:assets/sprites/player/source/third_party/base.obj > /tmp/hero-base.obj
cd assets/textures/characters/hero/unique
OPENBLAS_NUM_THREADS=1 python3 source/build_maps.py --mesh /tmp/hero-base.obj
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj
python3 source/validate.py --mesh /tmp/hero-base.obj
```

MakeHuman hm08: grupa `body`, CC0 według nagłówka przypiętego OBJ. Generator nie zmienia geometrii. Po celowej regeneracji plików trzeba odświeżyć raporty i manifest przez `source/write_manifest.py`; zwykły walidator nie nadpisuje danych.

## Przed / po

`podglad/v2/before/` — v1 z `bdc6529`, ponownie wyrenderowana ze snapshotu jej map. `podglad/v2/after/` — v2. `podglad/v2/porownanie.png` zestawia portret, profil i grzbiet dłoni obok siebie bez skalowania i korekcji kolorów (`source/compare_v2.py`). Po pięć identycznych kadrów: przód, profil, dłonie z przodu, z tyłu i od grzbietu. Obie wersje: **normal strength 0,45**, kamera 768×768, te same światła kontraktu, AgX Medium High Contrast, exposure −0,2, Cycles 64 próbki, seed 1703, 4 wątki, bez denoise. Porównanie nie zmienia oświetlenia, modelu ani geometrii.

Bieżące rendery v2 (także pełne ciało przód/profil/tył i tył głowy) są w `podglad/skin_*.png`. To diagnostyka materiału, nie eksport sprite'ów. Przykład ponowienia porównania z zachowanym snapshotem v1:

```bash
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --texture-dir /tmp/hero-v1-snapshot --output-dir podglad/v2/before --comparison
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --output-dir podglad/v2/after --comparison
```

Snapshot v1 można odtworzyć przez `git show bdc6529:assets/textures/characters/hero/unique/NAZWA_MAPY` do katalogu poza checkoutem. Przekazywany `--texture-dir` wymaga map basecolor, roughness, normal_opengl i sss_mask.

`qa/validation.json`: odczyt PNG, formaty, skalowanie, normalne, pary wierzchołków szwów. `qa/v2_material_checks.json`: rzeczywiste pokrycie UV przez każdą bliznę i pieprzyk, kotwice i parametry materiału. `manifest.json`: SHA-256 wszystkich plików poza nim samym, narzędzia, źródła i wersja każdego podglądu. Archiwum instrukcji v1: `source/README-v1.md`.

## Ograniczenia

- Neutralna siatka hm08 nie jest docelową męską rzeźbą Sola. Tekstury nie dodają opadania tkanek do sylwetki ani zmiany kości twarzy. W podglądzie brak włókien włosów/zarostu i docelowych gałek/rogówki; oczodoły są puste.
- To proceduralna interpretacja starej skóry, nie skan ani ręcznie malowany portret. Zmarszczki i plamy wymagają oceny autora na modelu docelowym. Nie zatwierdzono jeszcze wyglądu v2 ani skali gry 1×, animacji i integracji ze strojem.
- Kontrola szwów i rendery nie dowodzą ich niewidoczności przy każdym mipie, deformacji i oświetleniu. Normalna/height nie są wypaleniem rzeźby high-poly, SSS nie jest pomiarem tkanki.
- Oryginalne oczy mają udokumentowane pochodzenie repozytoryjne, ale poprzednik nie zapisał użytego generatora. Nie przypisujemy im zmyślonej fotografii, modelu AI ani licencji.
