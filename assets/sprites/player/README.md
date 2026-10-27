# Bohater Weleszy — dopracowanie prototypu Blender → prerender

**Aktualna praca: statyczny pass detali po nowych artach autora.**
[Przegląd](reviews/detale-01/index.html) · [opis zmian](DETAIL_REVIEW.md) ·
[model roboczy](source/bohater_detale.blend).
Model `source/bohater.blend` i komplet atlasów poniżej zachowują poprzednią
rewizję 08; nowych detali nie włączono jeszcze do pełnego eksportu animacji.

Kierunek sylwetki i pipeline zatwierdzony przez autora; **bieżące dopracowanie
czeka na ponowną ocenę**. Nie jest zatwierdzonym assetem produkcyjnym.
Gałąź `vibe/sprite-bohater-codex`; punkt porównawczy `a0a6c27` zachowany w Git
oraz w `baseline/`. Obecny model jest kontynuacją tej samej postaci i rigu.

[Przegląd animowany](previews/review.html) · [kierunki przed/po 1:1](previews/porownanie-kierunki-1x.png)
· [chód przed/po](previews/porownanie-chod-1x.gif) · [model źródłowy przed/po](previews/model-zrodlowy-przed-po.png)
· [raport](REPORT.md).

## Źródła i bezpieczne ponawianie eksportu

**`source/bohater.blend` jest nadrzędnym, edytowalnym źródłem artystycznym.**
Zawiera geometrię, UV, materiały z zapakowanymi obrazami, 17 kości i zapisane
akcje szkieletu oraz elementów stroju. Można go dalej ręcznie edytować.
`render_player.py` czyta ten plik i jego klucze; nie odtwarza geometrii,
nie wywołuje recept modelowania i nigdy nie zapisuje `.blend`.

Z katalogu repozytorium:

```bash
# Pełne 160 klatek, 8 prób chłodnych i 8 ciepłych, walidacja i porównania:
bash assets/sprites/player/source/run_pipeline.sh

# Wznowienie dokładnie tego samego źródła i renderera:
bash assets/sprites/player/source/run_pipeline.sh --resume

# Pilot nie narusza gotowych atlasów ani renderów:
blender -b assets/sprites/player/source/bohater.blend -t 4 --python-exit-code 1 \
  --python assets/sprites/player/source/render_player.py -- --pilot --output /tmp/hero-pilot

# Opcjonalny wariant eksploracyjny do oceny; nie zmienia źródła:
blender -b assets/sprites/player/source/bohater.blend -t 4 --python-exit-code 1 \
  --python assets/sprites/player/source/render_player.py -- --pilot --sheathed
```

Przy zmianie `.blend` można renderować bez `--resume`. Skrypt pipeline z `--resume` ponawia tylko niezgodne składniki, zachowując zgodne; bezpośredni renderer nadal odrzuca cache innego źródła.
Audyt zawiera SHA-256 faktycznego `.blend`, renderera i obu plików każdej klatki.
Zapisuje się atomowo po klatce. Parametry i komplet audytu sprawdza eksporter.
Przed ręczną edycją zapisuj commit, a po niej aktualizuj opis źródła w
`source/art-source.json`. Manifest nie przywraca starego modelu.

| Pliki | Rola |
|---|---|
| `source/bohater.blend` | Nadrzędne źródło do dalszej pracy i renderowania; **nie wygenerowany cache** |
| `source/art-source.json` | Pochodzenie, rewizja, SHA i przypisania materiałów |
| `source/render_player.py` | Render zapisanych akcji, osobna postać i cień, opcjonalne światło/pochwa |
| `source/export_player.py`, `compare_player.py` | Atlasy, kompatybilny eksport i podglądy z rzeczywistych klatek |
| `source/build_player.py` | Archiwalny bootstrap prototypu; wymaga nowej ścieżki `--bootstrap-output` i `--save-only`; odmawia nadpisania istniejącego pliku lub `bohater.blend` |
| `source/refine_player.py`, `polish_player.py`, `adjust_carry.py` | Jednorazowe, wersjonowane recepty kolejnych korekt istniejącego modelu; chronione rewizją, **nie wywoływane przez pipeline** |
| `source/motion_player.py` | Recepta dopracowania kluczy; renderer korzysta z kluczy zapisanych w `.blend`, więc zachowuje późniejsze ręczne poprawki |
| `source/third_party/` | Przypięte źródła MakeHuman CC0 i licencja |
| `renders/`, `atlas/`, `previews/` | Wyniki generowane; można odtworzyć z zapisanego `.blend` i skryptów |
| `baseline/` | Chroniony punkt porównawczy; model i atlasy zachowane lokalnie; pełny oryginał również w commicie z `checkpoint.json` |

Nie uruchamiaj bootstrapu jako sposobu eksportowania poprawek. Dostarczony
`.blend` wystarcza do odtworzenia obrazu bez ponownego budowania postaci,
pobierania anatomii czy dostępu do sieci. Zapakowane tekstury uniezależniają
render od ścieżki roboczej; oryginalne PNG pozostają osobno w bibliotece.

## Materiały

Pobrano planszę 17 z aktualnego `main` (`7ce5c4b`) i wyłącznie zasoby materiałowe
z `vibe/hero-materials-chunk02-gpt6` (`c6c1a67`, następnie `ff74eb7`). Nie zmieniono tych gałęzi.
54 PNG zweryfikowano względem SHA Git blob z trzech dostarczonych manifestów.
Ich opis: autorskie obrazy proceduralne, bez zewnętrznych fotografii; materiały
robocze, nie pomiarowe PBR. Nie przypisujemy im nowej licencji CC0.

| Zestaw | Obiekty |
|---|---|
| `linen_shirt_worn` | koszula, tunika, podwinięte rękawy i owijki |
| `wool_cloak_dark_brown` | płaszcz, kaptur, warstwa naramienna |
| `leather_vest_weathered_brown` | kaftan, pasy, sakwy, przetarte brzegi |
| `wool_trousers_charcoal` | spodnie i podeszwy |
| `leather_boots_dark_mud` | noski, cholewki, pochwa i ciemne rzemienie |
| `leather_backpack_aged` | główna bryła plecaka, klapa, kieszenie |
| `canvas_bedroll_ashen` | zrolowane posłanie |
| `leather_straps_worn` | pasy, szelki, rzemienie i pochwa |
| `iron_hardware_blackened` | sprzączki, jelec, głowica, okucia |
| `steel_sword_weathered` | głownia i szlif |
| `skin_traveler_weathered` | skóra głowy, szyi, przedramion i dłoni |
| `hair_dark_umber` | fryzura, brwi, krótki zarost i wąs |

UV w przestrzeni spoczynkowej: V 0,32 m, U całkowita liczba powtórzeń, cylindry ze szwem
z tyłu dla tkanin/butów, projekcja YZ plecaka, cylinder wzdłuż Y posłania.
Basecolor sRGB; roughness i height Non-Color. Użyto **height → subtelny Bump**;
normal OpenGL zachowano w dostarczonej paczce, ale nie podłączono, aby nie
zdublować reliefu i nie zakładać poprawnych tangentów każdego małego wykroju.

Bazowy wzór wełny tworzył na pilocie efekt plam kamuflażu: udział w kolorze
ograniczono do 22%, skóry do 48%. Len zachowuje większy udział mapy. Różnice
materiałów wspiera forma, kolor, roughness i geometria fałd, nie sam mikrosplot.
Atrybut `wear_mask` dodaje miejscowe błoto do butów, dolnych nogawek i płaszcza.
To maska wykonana na tym modelu, nie oczekujący jeszcze zewnętrzny zestaw masek.
Później dołączono także Chunk03: metale, rzemienie, skórę człowieka, włosy i cztery nakładki. Maska krawędzi pochodzi z geometrii; dostarczony breakup ją moduluje. Błoto działa jako lokalny decal RGBA, a szwy wyłącznie na istniejących obszyciach.

## Kontrakt i ruch

| Parametr | Wartość — bez zmiany globalnego kontraktu |
|---|---|
| Klatka | 192×192 RGBA; premultiplikowane filtrowanie z 384×384 |
| Kotwica | (96, 158.353829), stała |
| Kierunki | S, SW, W, NW, N, NE, E, SE; obroty −45°, bez odbić |
| Kamera / skala | ortograficzna 30°, 3,2 m kadru, 60 px/m; człowiek źródłowy 1,8 m |
| Spoczynek | 8×400 ms, cykl 3,2 s; zapisane klucze 1–81 przy 25 fps |
| Chód | 12×80 ms, cykl 0,96 s; klucze 1–25; ruch świata 0,9027777778 m/s |
| Cycles | 64 próbki postaci / 16 cienia; seed 1703; bez denoisera; 4 wątki CPU |
| Atlas | kolumny = fazy, wiersze = kierunki |

Chód w miejscu: dodano pracę miednicy, przeciwskręt klatki, spokojniejszą głowę,
opóźnienie swobodnego ramienia, pivot pięty/palca i drobny wtórny ruch ładunku.
To kontrolowane klucze, nie symulacja tkaniny ani mocap. Miecz zachowuje wymiary;
proponowana poza prowadzi ostrze w dół i na zewnątrz, szczególnie dla N/NW.
Wariant w pochwie jest wyłącznie porównaniem — decyzja o eksploracji otwarta,
dłoń i akcje tego wariantu nie są ukończoną nową animacją.

`atlas/bohater_<animacja>.png` oraz `_shadow.png`: osobna postać i kontaktowy
cień. `atlas/compat/` zachowuje wcześniejszy format z cieniem w klatce.
Światło ciepłe jest osobno w `renders/warm/`, chłodne w `renders/cool/`;
nie wypieczono pochodni w atlas bazowy. Większe ujęcia to rzeczywiste rendery
1152 px z tą samą skalą świata, a nie powiększone sprite'y.

Kompozyty `koncept17-*` pokazują **ilustrację koncepcyjną, nie scenę gry**.
Tło zachowuje oryginalne piksele. Ponieważ jego skala nie jest skalibrowana,
przyjęto lokalnie 60 px/m przy kotwicy (590,810); postać pozostaje 1:1.

## Kontrole i ograniczenia

`validate_blend.py`: 242 próbki szkieletu, pętle, 22 pozy kluczowe.
`validate_render.py`: ponowny render z `.blend`, kotwica, kierunki i maski miecza.
`validate_intersections.py`: próbki rzeczywistych powierzchni miecza/ubrania oraz
dolnego płaszcza/spodni; zakres i wyjątki podane w raporcie, bez pełnej kontroli kolizji.
Eksporter sprawdza 160 klatek, alfę, granice, sumy plików i kontakt stopy;
porównywarka weryfikuje 160 komórek zgodności atlasu kompatybilnego.

Blender 4.3.2, Python 3.12, NumPy i Pillow są dostępne w obrazie środowiska.
Nie potrzeba usług, sekretów, portów ani instalacji globalnych. Dokładne wyniki,
słabe kierunki/fazy i zakres oceny wizualnej zapisuje [REPORT.md](REPORT.md).

Opcjonalna kontrola odtwarzacza w dostępnym Chromium/Playwright:

```bash
python3 -B assets/sprites/player/source/validate_viewer.py
```

Uruchamia tymczasowy serwer wyłącznie na loopback na czas testu, potem go
zamyka. Odtwarzacz i GIF-y nie wymagają stałej usługi ani serwera gry.
