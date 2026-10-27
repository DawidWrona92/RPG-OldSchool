# Bohater Weleszy — Blender / Codex

**Powtarzalny demonstrator do oceny autora. Materiały i detal nie osiągają
jeszcze poziomu dostarczonego konceptu. To nie jest zatwierdzony asset produkcyjny.**

Baza: `vibe/welesza-sprites-03`, commit `fc8f657d393af195ddcd900602cc849dde1fffc0`.
Własna gałąź: `vibe/sprite-bohater-codex`. Wspólny SDF i cudze generatory są
niezmienione. Alternatywną metodę autoryzuje bezpośrednio zlecenie autora.

## Odtworzenie

Z katalogu `/workspace/RPG-OldSchool`:

```bash
# Model, 160 klatek, dwa warianty światła, kontrole i eksport:
bash assets/sprites/player/source/run_pipeline.sh

# Po przerwaniu tej samej wersji generatora:
bash assets/sprites/player/source/run_pipeline.sh --resume

# Próba wybranego kierunku przed pełnym przeliczeniem:
blender -b -t 4 --python-exit-code 1 \
  --python assets/sprites/player/source/build_player.py -- --pilot --directions 1
```

`--resume` porównuje SHA-256 generatora, ustawienia i sumy każdej pary obrazu
i cienia. Audyt jest zapisywany atomowo po klatce. Po zmianie modelu uruchom
bez `--resume`. Próba nadpisuje wybrane rendery i audyt: przed nią zapisz
gotowy zestaw w Git; pełny render odtworzy spójny komplet.

Sprawdzone narzędzia: Blender 4.3.2 z własnym Pythonem, `python3` 3.12.14,
NumPy 2.3.5 i Pillow 12.3.0. Są już w obrazie środowiska; nie instalowano
pakietów globalnych. Nie potrzeba usług, portów, sekretów ani sieci do
renderowania zapisanych źródeł. Build systemowy nie zawiera OpenImageDenoise:
używamy rzeczywistych próbek Cycles i supersamplingu, cztery wątki CPU.

## Model i ruch

Organiczna siatka MakeHuman CC0, osobne wykroje tuniki, kaftana i płaszcza,
odsłonięte przedramiona, podwinięte rękawy, plecak, posłanie, sakwy, buty,
pochwa i miecz. Materiały rozróżniają skórę, len, wełnę, skórę wyprawioną,
żelazo i włosy. Atrybut `rest_position` mocuje fakturę do deformowanej siatki.

Szkielet ma 17 kości, stałe długości i dwusegmentowe IK nóg/rąk. Prawa ręka
utrzymuje broń przed ciałem; lewa wykonuje większy wymach. Płaszcz ma
kontrolowaną deformację wtórną. Nie deklarujemy symulacji tkaniny ani mocapu.

`source/bohater.blend` zawiera geometrię, materiały, szkielet i prawdziwe akcje
`spoczynek` / `chod` oraz odpowiadające im akcje płaszcza. Aktywny chód:
klatki 1–25 przy 25 fps; spoczynek: 1–81.

- Spoczynek: 8 klatek po 400 ms, cykl 3,2 s.
- Chód: 12 klatek po 80 ms, cykl 0,96 s, `root_speed_mps=0.9027777778`.
- To animacja w miejscu: ruch świata wykonuje silnik z podaną prędkością.

Nowa referencja autora i decyzje: `source/REFERENCE.md`. Arkusz z rozmowy
obejrzano wizualnie. Lokalne kompozyty wykorzystują scenę 12 z repozytorium,
nie rzekomą kopię pikseli nowego obrazu z wozem.

## Kontrakt eksportu

| Parametr | Wartość |
|---|---|
| Klatka | 192×192 RGBA, filtrowanie z premultiplikowaną alfą |
| Render źródłowy | 384×384; 64 próbki postaci / 16 cienia |
| Kamera | ortograficzna, 30°, szerokość świata 3,2 m |
| Skala | 60 px/m; człowiek źródłowy 1,8 m |
| Kotwica | (96, 158.353829), stała we wszystkich klatkach |
| Kierunki | S, SW, W, NW, N, NE, E, SE; obroty −45°, bez odbić |
| Atlas | kolumny = klatki, wiersze = kierunki |

`atlas/bohater.json` zachowuje bazowy format `character`, `frame_size`,
`anchor_px`, `pixels_per_meter`, `directions`, `animations`, `durations_ms`,
`loop`, `events`, `root_speed_mps`. Dodaje `shadow_file` dla oddzielnego cienia.
Wspólnego kontraktu ani importera nie zmieniono.

- `atlas/bohater_<animacja>.png`: postać RGBA.
- `atlas/bohater_<animacja>_shadow.png`: osobny kontaktowy cień z Cycles.
- `atlas/compat/`: wcześniejszy format z cieniem w tej samej klatce.
- `renders/`: oryginalne obrazy 384 px i surowe fizyczne cienie.
- `renders/cool/`, `renders/warm/`: osobno przeliczone próby oświetlenia.

Cień jest monochromatyczną maską shadow catchera z filtracją szumu i łagodnym
wygaszeniem od 0,75 do 1,05 m od kotwicy. To jawne ograniczenie kontaktowej
łaty do klatki 192 px; dalekie cienie wypełnienia nie są w niej zachowywane.
Surowe rendery pozostają dostępne. W atlasie postaci nie ma podłoża, zdjęcia
referencyjnego ani wypieczonej pochodni.

## Sprawdzenie

```bash
blender -b assets/sprites/player/source/bohater.blend --python-exit-code 1 \
  --python assets/sprites/player/source/validate_blend.py
blender -b assets/sprites/player/source/bohater.blend --python-exit-code 1 \
  --python assets/sprites/player/source/validate_render.py
python3 -B assets/sprites/player/source/export_player.py
```

Kontrole obejmują 242 pozy, zamknięcie cykli i 22 klucze zapisanych akcji,
ponowny render z `.blend`, projekcję kotwicy/kierunków i 32 maski widoczności
miecza. Eksporter sprawdza wszystkie 160 klatek: pochodzenie, sumy plików,
granice, alfę, ciągłość szkieletu, atlas/JSON i kompensację podparcia stopy.

`previews/`: kierunki 1:1, rzeczywiste rendery 384 px, GIF/WebP, ruchome
podłoże, kompozyty świata i raporty JSON. Obraz 384 px jest renderem roboczym
2×; nie oznacza większej postaci w świecie. Silnika nie wybrano: import do
gry, animacje walki, kompletna kontrola kolizji i odbiór artystyczny są otwarte.

## Licencje

`source/third_party/`: siatka i dane MakeHuman, wersja
`a8bc2d54ff0ac92e78ff71431b1023eda42bf482`, CC0-1.0. Licencja, adresy plików
i SHA-256 są zachowane. Nie kopiujemy kodu MakeHuman (AGPL), komercyjnych
tekstur ani assetów o niejasnym pochodzeniu. Pozostała geometria i generator
powstały w tym eksperymencie. Nie zmienia to licencji całego projektu.
