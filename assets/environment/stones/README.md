# Paczka środowiska: kamienie, głaz, podłoża, scena testowa (Welesza)

**Status:** eksperyment do oceny autora — **nie** zatwierdzony asset produkcyjny.
Pierwsza paczka środowiska dla lokacji "trakt przy porzuconym wozie"
(zob. `docs/demo-fabula.md`, `docs/koncepty/17-bohater-i-woz.md`).

Branch: `vibe/environment-stones-mistral`

## Zawartość

```
assets/environment/stones/
├── source/
│   ├── envlib.py            # biblioteka: scena, kamera, światła, materiały, geometria, render
│   ├── build_env.py         # buduje assety i renderuje (sekcje: stones | grounds | scene | all)
│   ├── scena_testowa.blend  # scena testowa do edycji w Blenderze (generowana)
│   └── run.sh               # wrapper uruchamiający (ustawia ścieżki środowiska)
├── renders/                 # render 384×384 px (kamienie RGBA) i 768×768 px (podłoża, scena)
├── previews/                # arkusze poglądowe (kompozyty do przeglądu)
└── atlas/                   # sprite'y w skali gry 192×192 px + assets.json (metadane)
```

## Assety

### Kamienie i głaz (oddzielne sprite'y RGBA, cień wypalony w alfa)

| Asset | Kształt | Rozmiar (m) | Materiał | Wariant rotacji |
|---|---|---|---|---|
| `kamien_01_okrągły` | okrągławy, niski (otoczak) | 0,54 × 0,54 × 0,60 | skała mokra | `rot120` |
| `kamien_02_kanciasty` | kanciasty, wyższy, płaska góra | 0,54 × 0,54 × 0,71 | skała z mchem | — |
| `kamien_03_płaski` | płaska płyta wystająca z ziemi | 0,58 × 0,58 × 0,56 | skała sucha z mchem | — |
| `glaz_01` | duży głaz, niski i szeroki | 1,46 × 1,10 × 1,68 | skała mokra z mchem | `rot120` |

- Dla porównania: bohater ma ~1,8 m — głaz sięga mu mniej więcej do klatki piersiowej,
  kamienie to około 1/3 wysokości człowieka.
- **Punkt osadzenia:** dół obiektu na `z = 0` (origin w środku podstawy XY) —
  w silniku wystarczy postawić sprite tak, by dolna krawędź geometrycznej części
  (bez cienia) siedziała na wysokości terenu.
- **Kolizja (orientacyjna, do sprawdzenia w grze):** kamienie — okrąg fi ~0,55–0,6 m,
  wysokość 0,55–0,7 m (kamień 03 można wejść na wierzch); głaz — elipsa ~1,5 × 1,1 m,
  wysokość 1,7 m, nieprzechodni.
- **Cień jest wypalony w obraz** (Cycles rzuca cień na przezroczystą płaszczyznę,
  cień ląduje w kanale alfa razem z obiektem). Osobna warstwa cienia nie została
  wyodrębniona — można dodać później przez osobny pass (shadow catcher).

### Podłoża (materiały proceduralne, próbki 1×1 m i powierzchnie 6×6 m)

| Materiał | Opis |
|---|---|
| `bloto_trakt` | mokra, ubita ziemia: ciemne kałuże (połysk przez roughness), koleiny, nierówności |
| `sciolka_lesna` | ziemia + ~400 rozrzuconych liści i igieł (osobne małe siatki, deterministycznie) |

- Przejście błoto ↔ ściółka: nieregularna granica (losowe kliny ściółki na błocie)
  + liście przy krawędzi — `renders/przejscie_bloto_sciolka.png`.
- **W grze:** materiały jako kafle z tilingiem UV (błoto) lub rozrzucenie liści
  jako osobne obiekty/decoracje (ściółka); przejście przez kafle brzegowe lub maskę
  mieszania materiałów. Patrz sekcja "Ciągłość świata".

### Scena testowa

`renders/scena_testowa_trakt.png` (kadr szeroki) + `scena_testowa_zblizenie.png`
(zbliżenie materiałów): pas błota (1,8 m szerokości) wzdłuż traktu, ściółka po bokach,
3 kamienie, głaz i **żółty znacznik skali 1,8 m** (słupek z poprzeczkami na głowę
i pas — zamiennik sprite'a bohatera; sprite Codexa nie był kopiowany).

## Technologia i kontrakt renderu

- **Silnik:** Blender 5.2.3 jako moduł Pythona (`bpy` wheel, CPython 3.13),
  renderer **Cycles CPU** (EEVEE/Workbench wymagają GPU/EGL — w środowisku
  headless bez GPU się wykładają; Cycles CPU działa stabilnie).
- **Kamera (kontrakt zgodny ze sprite'ami postaci — sdfkit/meshkit):**
  projekcja ortograficzna, nachylenie 30° nad horyzontem, azymut 45°,
  skala 60 px/m, tło przezroczyste (RGBA).
- **Oświetlenie bazowe (chłodne, spójne dla wszystkich assetów):**
  - klucz: SUN, kolor (0.72, 0.80, 0.96), energia 2.2, z lewej góry ekranu,
    elewacja 52°, azymut −38°;
  - wypełnienie: AREA z dołu, zimny (0.42, 0.40, 0.36), energia 12 — odbicie ziemi;
  - rim: AREA z prawej, chłodny (0.55, 0.65, 0.85), energia 6 — separacja sylwetki.
- **Render:** 64 próbki + denoisery OpenImageDenoise, view transform „Standard"
  (bez filmowego tonemappingu — bliżej wyglądowi sdfkit/meshkit).
- **Rozdzielczości:** kamienie renderowane w 384×384 (2× supersampling),
  sprite'y docelowe 192×192 (downscale Lanczos na alfa premultiplikowanej);
  podłoża i scena w 768×768.
- **Paleta** (z `docs/art/niemir/NIEMIR_ART_DIRECTION.md`): skała `#62685B`,
  błoto `#3F3931`, zieleń mchu `#454A36`, akcent bursztynowy `#B47837`
  (nieużyty w tej paczce — zarezerwowany na późniejsze ciepłe światło).
- **Geometria:** proceduralna — icosphere/kostka + modyfikatory Displace
  (tekstura Voronoi, kilka skal) + Smooth, aplikowane; deterministyczna
  (zablokowane seedy). Liście/igły: spłaszczone icosphere rozrzucone
  deterministycznie (`random.Random(seed)`).

## Odtworzenie wyników

### Zależności

- Python 3.13 (do uruchomienia `bpy`)
- Blender jako moduł: wheel `bpy==5.2.3` z PyPI (cp313, ~400 MB)
- numpy + Pillow dla Pythona 3.13
- biblioteki systemowe X11/GL (libX11, libGL, libEGL, libgomp, libxkbcommon…)
  — wymagane nawet przy renderze CPU, bo `bpy` je linkuje

### Przygotowanie środowiska (sprawdzone w sandboxie, Ubuntu 24.04, bez roota)

```bash
# 1. bpy wheel
pip download bpy==5.2.3 --python-version 3.13 --only-binary=:all: -d /tmp/wheels
cd /tmp && mkdir bpyenv && cd bpyenv && unzip -q /tmp/wheels/bpy-5.2.3-*.whl

# 2. numpy + pillow dla 3.13
pip download numpy pillow --python-version 3.13 --only-binary=:all: -d /tmp/wheels313
cd /tmp && mkdir pylibs && cd pylibs
for w in /tmp/wheels313/*.whl; do unzip -q -o "$w"; done

# 3. biblioteki X11/GL (bez roota: pobierz .deb i rozpakuj)
mkdir -p /tmp/debs /tmp/xlibs /tmp/aptlists
apt-get update -o Dir::State::Lists=/tmp/aptlists
cd /tmp/debs
apt-get download libx11-6 libxrender1 libxfixes3 libxi6 libxkbcommon0 libsm6 libice6 \
  libxext6 libgl1 libegl1 libgomp1 libxxf86vm1 libxau6 libxdmcp6 libbsd0 \
  libglvnd0 libglx0 libglx-mesa0 mesa-libgallium \
  libxcb1 libxcb-render0 libxcb-shm0 libxcb-xfixes0 libxcb-randr0 libxcb-image0 \
  libxcb-keysyms1 libxcb-sync1 libxcb-xinerama0 libxcb-icccm4 libxcb-shape0
for d in /tmp/debs/*.deb; do dpkg-deb -x "$d" /tmp/xlibs; done

# 4. uruchomienie
export PYTHONPATH=/tmp/bpyenv:/tmp/pylibs
export LD_LIBRARY_PATH=/tmp/xlibs/usr/lib/x86_64-linux-gnu
python3.13 assets/environment/stones/source/build_env.py --only all
# lub przez wrapper:  assets/environment/stones/source/run.sh [stones|grounds|scene]
```

Uwagi:
- `--only` przyjmuje też pojedyncze nazwy assetów, np.
  `--only kamien_01_okrągły,glaz_01`.
- Pełny przebieg (`all`) zajmuje ~15–20 min na CPU (Cycles, 64 próbki).
- Alternatywnie: otworzyć wygenerowany `source/scena_testowa.blend`
  w Blenderze 5.x GUI i renderować/stawiać kamery ręcznie.
- Bez `bpy` dostępnego jako moduł Pythona skrypt się nie uruchomi —
  nie ma w repo fallbacku na inny renderer.

## Kontrola jakości — testy faktycznie wykonane

| Test | Wynik |
|---|---|
| Przezroczystość RGBA (kamienie, głaz) | ✅ kanał alfa obecny, piksele półprzezroczyste na krawędziach i w cieniu |
| Granice obrazów (brak ucięcia geometrii/cienia) | ✅ margines ≥ 27 px z każdej strony na wszystkich 6 sprite'ach 384 px i 192 px |
| Brak dziur w masce alfa (poza zamierzonym cieniem) | ✅ 0 osobnych komponentów „dziur" w alfa |
| Skala (60 px/m, kontrakt kamery) | ✅ znacznik 1,8 m = ~1,85 m zmierzone na renderze sceny; weryfikacja projekcji ortho na kuli 0,7 m (41 px na 192 px przy ortho_scale 3,2) |
| Spójność światła/kamer | ✅ wszystkie assety z jednej konfiguracji (`envlib.setup_lights`/`setup_camera`) — ten sam rig oświetlenia i kamera izo 30°/45° |
| Powtarzalność podłoża (kafelkowanie) | ⚠️ testowe kafelkowanie 2×2 wykonane (`previews/kafelkowanie_*_2x2.png`), ale **ocena wizualna szwów nie została przeprowadzona** — materiały są proceduralne (noise), błoto kafelkuje się przez powtórzenie UV, ściółka przez osobne obiekty liści |
| Ponowne renderowanie (reproducibility) | ✅ cały pipeline uruchomiony wielokrotnie od zera; seedy zablokowane — kolejne uruchomienia dają te same kształty (różnice wyłącznie szumowe w Cycles) |
| Skala gry (192 px) | ✅ warianty 192×192 w `atlas/`, kontrola granic i alfa — zaliczone |
| Zgodność plików z metadanymi | ✅ `atlas/assets.json` opisuje rozmiary, punkty osadzenia, kolizje, warianty |

**Testy NIE wykonane (do zrobienia przy ocenie):**
- wizualna ocena szwów kafelkowania na dużej powierzchni (brak możliwości
  przeglądu obrazów w środowisku wykonawczym — kontrola była numeryczna);
- dopasowanie wyglądu do referencji `docs/koncepty/17-bohater-i-woz.jpg` —
  wymaga oceny autora;
- test w silniku gry (kolizje, kotwica stóp, sortowanie sprite'ów) — silnik nie wybrany;
- warianty kierunków kamery (każdy asset ma jedno ujęcie — zgodnie z zakresem).

## Ograniczenia i uczciwa ocena

**Co działa:**
- spójny kontrakt kamery/światła ze sprite'ami postaci (ten sam izo 30°/45°, 60 px/m);
- assety jako osobne RGBA z cieniami, gotowe do składania lokacji;
- warianty rotacji pokazują, że zestaw da się urozmaicać bez nowych modeli;
- pełna powtarzalność: geometria i rozmieszczenie deterministyczne, pipeline
  uruchamialny od zera jedną komendą.

**Co jest uproszczone / wymaga ręcznej poprawy:**
- **Kształty kamieni** powstają z displace-modifierów — wyglądają „narzędziowo",
  nie jak rzeźbione skały; na zbliżeniu widać szum zamiast struktur geologicznych.
  Docelowo: ręczne sculptowanie lub lepsze zestawy displacementów.
- **Cień wypalony w alfa** — brak osobnej warstwy; przy dynamicznym oświetleniu
  (np. pochodnia) cień będzie „zamrożony" w sprite'ie.
- **Błoto** — kałuże to mieszanka koloru i roughness (brak prawdziwych odbić,
  bez envmapy połysk jest płaski).
- **Ściółka nie jest teksturą bezszwową** — liście to osobne siatki; przy kafelkowaniu
  powierzchni rośnie liczba obiektów (koszt draw calls / pamięć przy dużym świecie).
- **Jeden kierunek kamery** na asset — przy ruchu kamery wokół lokacji (jeśli gra
  na to pozwoli) będą potrzebne kolejne ujęcia lub rotacja sprite'a w płaszczyźnie.
- **Brak sprite'a bohatera w scenie** — użyty znacznik 1,8 m; porównanie
  z rzeczywistym bohaterem (branch Codexa) do zrobienia przy ocenie.

## Ciągłość świata / modularność

- Kamienie i głaz to **pojedyncze, niezależne sprite'y** z ustalonym punktem
  osadzenia (dół na `z = 0`) — można je rozmieszczać na dowolnym fragmencie terenu,
  mieszać z wariantami rotacji, losować skalę w wąskim zakresie (±10%).
- Podłoża projektowane jako **kafle**: błoto = materiał kafelkowalny (tiling UV);
  ściółka = materiał bazowy + dekoracje (liście). Przejście robione jako
  nieregularna krawędź — w grze: kafle brzegowe albo maska mieszania.
- **Ograniczenia dla seamless world:** brak prawdziwych tekstur bezszwowych
  (ściółka zwiększa liczbę obiektów przy powtarzaniu); brak systemu
  „chunków" terenu; kolizje są orientacyjne; cienie wypalone w sprite'ach
  wykluczają dynamiczne cienie bez osobnego passu. Silnik gry nie jest jeszcze
  wybrany — integracja (sortowanie Y, kotwice, kolizje) do ustalenia po wyborze.

## Źródła i licencje

- Całość wygenerowana proceduralnie własnym kodem (`source/envlib.py`,
  `source/build_env.py`) — **bez zewnętrznych modeli i tekstur**, prawa autorskie
  bez zastrzeżeń.
- Blender/bpy: GPL (zgodnie z licencją Blendera) — użyty jako narzędzie,
  nie jako źródło assetów.
