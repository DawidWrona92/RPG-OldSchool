# Kontrakt renderu sprite'ów Weleszy

**Status: [DECYZJA AUTORA], 27 października 2026 r.** Sprite'y do gry powstają jako **prerender w Blenderze (Cycles)** według kontraktu poniżej. Wzorcem technicznym jest bohater z gałęzi `vibe/sprite-bohater-codex` (`assets/sprites/player/`); wartości w tabelach odczytano bezpośrednio z jego pliku `source/bohater.blend` i skryptu renderu.

Dokument ustala **wspólne zasady obrazu**, żeby postacie, potwory i otoczenie z różnych gałęzi pasowały do siebie w jednej scenie. Nie zawiera generatorów ani assetów — te pozostają na gałęziach roboczych (zob. [AGENTS.md](../../AGENTS.md)). Wygląd opisują [przewodnik artystyczny](niemir/NIEMIR_ART_DIRECTION.md) i [biblioteka szkiców](../koncepty/README.md); ten kontrakt mówi, **jak** go renderować.

> [Przewodnik artystyczny](niemir/NIEMIR_ART_DIRECTION.md) od wersji 1.2 (Markdown i PDF) odsyła w sprawach technicznych do tego kontraktu. Przy sprzeczności pierwszeństwo ma kontrakt.

## Zakres

| Obowiązuje | Jeszcze otwarte |
|---|---|
| Bohater, potwory, NPC, rekwizyty, roślinność, budynki — wszystko, co jest sprite'em w świecie gry | Importer atlasów do silnika ([Godot 4, decyzja warunkowa](../SILNIK.md)) |
| Kamera, skala, kierunki, kotwica, bazowe światło, eksport | Ostateczny grading kolorów po teście w silniku |
| Organizacja źródeł i kontrola jakości | Kafle podłoża i technika terenu (muszą jednak przyjąć tę samą kamerę i skalę) |
| | Rozmiar klatki dla dużych obiektów (zob. „Duże obiekty”) |

## Kamera i skala — obowiązkowe

| Parametr | Wartość |
|---|---|
| Typ kamery | **ortograficzna** (nie perspektywiczna) |
| Kąt | 30° nad horyzontem (obrót kamery X = 60°, Z = 90°) |
| Skala ortograficzna | 3,2 m na szerokość klatki |
| Położenie / cel | kamera (6,9282; 0; 5,2) m, oś celuje w (0; 0; 1,2) m |
| Rozdzielczość | render 384×384, zmniejszenie z premultiplikowaną alfą do **192×192** |
| Gęstość | **60 px/m**; człowiek ok. 1,8 m ≈ 105 px |
| Tło | przezroczyste (`film_transparent`), RGBA |
| Układ świata | +X = przód postaci, +Y = lewo, +Z = góra; metry; podstawa (stopy) na z = 0 |
| Kotwica | punkt świata (0; 0; 0) → piksel **(96; 158,353829)** w każdej klatce, kierunku i animacji |
| Kierunki | 8 osobnych renderów obrotu modelu o −45°: **S, SW, W, NW, N, NE, E, SE**; S = przodem do kamery; **bez lustrzanych odbić** |

**Granice klatki.** Nic z postaci nie może dotykać krawędzi klatki. Przy tej kamerze punkt na ziemi w odległości r od kotwicy, wysunięty w stronę kamery, ląduje ok. 1,04 + 0,5·r m poniżej środka klatki, a klatka kończy się 1,6 m od środka — stąd **zasięg przy ziemi w stronę kamery ≤ ok. 1,1 m**. Wysoko uniesiona broń za postacią łatwo przekracza górną krawędź. Sprawdzaj wszystkie klatki, kierunki i warianty, a nie tylko pozę spoczynkową.

## Światło i kolor bazowy

| Element | Wartość |
|---|---|
| Klucz | światło powierzchniowe 520 W, 2,3 m, barwa (0,94; 0,92; 0,85), pozycja (2,8; −3,5; 6,0) — na ekranie z lewej góry, od strony kamery |
| Wypełnienie z tyłu | powierzchniowe 140 W, 3,0 m, chłodne (0,60; 0,70; 0,85), pozycja (−3,0; 1,0; 4,0) |
| Odbicie od ziemi | powierzchniowe 65 W, 4,0 m, (0,64; 0,68; 0,74), pozycja (3,0; 4,0; 2,5) |
| Świat | kolor (0,18; 0,21; 0,26), siła 0,2 |
| Zarządzanie kolorem | **AgX**, look „Medium High Contrast”, ekspozycja −0,2, sRGB |
| Cycles | postać 64 próbki, cień 16, seed 1703, bez odszumiania, filtr 1,5 px, 4 wątki |

Światło jest **stałe względem świata** — cień nie obraca się z postacią. Warianty chłodny i ciepły (np. pochodnia) to **osobne rendery** obok bazowego; nigdy nie wpiekamy lokalnego ognia w atlas bazowy. Kolory materiałów i nastrój bierzemy z przewodnika i szkiców, ale nie zmieniamy samego zestawu świateł dla pojedynczego assetu.

## Eksport

- **Atlas na animację:** `<id>_<animacja>.png`, kolumny = klatki, wiersze = 8 kierunków w kolejności powyżej, komórka 192×192.
- **Cień osobno:** `<id>_<animacja>_shadow.png` z przebiegu z odbiornikiem cienia; ten sam układ komórek. Dopuszczalny dodatkowy eksport zgodnościowy z cieniem w klatce.
- **JSON `<id>.json`:** `frame_size`, `anchor_px`, `pixels_per_meter`, `directions`, `layout`, `camera_elevation_deg`, a dla każdej animacji: `file`, `shadow_file`, `frames`, `durations_ms`, `loop`, `events`, opcjonalnie `root_speed_mps` (prędkość, przy której stopy nie ślizgają się).
- **Okna walki w `events`** dla każdego ataku, zgodnie z kartą w [bestiariuszu](../bestiariusz-demo.md): `zapowiedz`, `aktywne`, `trafienie`, `okazja`, `parowalny`, `sygnal` (klatki z sygnałem ataku nieparowalnego).
- Podgląd (GIF lub odtwarzacz) 8 kierunków w ruchu na tle lasu — do oceny, nie do gry.

## Źródła i pochodzenie

- **Nadrzędnym źródłem jest edytowalny plik `.blend`** (geometria, UV, materiały ze spakowanymi teksturami, szkielet, zapisane akcje). Skrypt renderu tylko go czyta — nie odtwarza modelu i nie nadpisuje źródła.
- Audyt renderu zapisuje SHA-256 pliku `.blend`, skryptu i każdej klatki. **Atlas musi pochodzić z tej samej rewizji `.blend` co rendery** — po każdej zmianie modelu ponawiamy eksport.
- Zasoby zewnętrzne tylko z jasną licencją i zapisanym źródłem (np. MakeHuman CC0 z przypiętą wersją). Tekstury z biblioteki `assets/textures/` są obrazami roboczymi, nie pomiarowym PBR — zob. ich manifesty.
- Szkielet i siatkę bohatera można **ponownie wykorzystać dla ludzkich postaci** (Drwal, Powrotnik, Stróż, cywile), zamiast budować każdą od zera.

## Wersja Blendera i środowisko

**Obowiązuje linia Blender 4.3** (bohater: 4.3.2). Nie otwieramy i nie zapisujemy plików źródłowych w nowszej wersji bez decyzji autora: plik zapisany w 5.x nie otworzy się w 4.3, a skrypty renderu przestają działać (w 5.x scena nie ma już `scene.node_tree`, z którego korzysta przebieg cienia).

Bez pełnego Blendera, np. w kontenerze agenta, wystarczy moduł `bpy` z PyPI. Wersja 4.3 wymaga Pythona 3.11:

```bash
python3.11 -m venv ~/bpy43            # albo: uv venv ~/bpy43 --python 3.11
~/bpy43/bin/pip install bpy==4.3.0 "numpy<2" pillow
~/bpy43/bin/python -c "import bpy; print(bpy.app.version_string)"   # 4.3.0
```

Plik `.blend` otwiera się wtedy przez `bpy.ops.wm.open_mainfile(filepath=...)`, a skrypt renderu uruchamia się w tym samym procesie. Sprawdzono 27 października 2026 r.: `bpy` 4.3.0 odtwarza klatkę `spoczynek_0_00` bohatera i jej cień z różnicą najwyżej 1/255 na kilkudziesięciu pikselach, a render jednej klatki 384×384 na CPU trwa ok. 16 s.

Jeśli import `bpy` zgłasza brak bibliotek systemowych (np. `libX11.so.6`, `libSM`), a nie ma praw roota, można rozpakować pakiety Debiana przez `dpkg-deb -x` do katalogu użytkownika i wskazać go w `LD_LIBRARY_PATH`. Pobieraj je wtedy przez HTTPS z `deb.debian.org` i sprawdzaj sumę SHA256 każdego pakietu z indeksu `Packages`. Lepiej jednak wpisać instalację do skryptu startowego środowiska, żeby każdy wykonawca miał to samo. Odszumianie (OpenImageDenoise) nie jest potrzebne, bo kontrakt go nie używa.

## Duże obiekty i otoczenie

Drzewa, budynki, wozy i skały używają **tej samej kamery, kąta, skali 60 px/m i świateł**. Klatka może być większa niż 192×192, jeśli obiekt się nie mieści — wtedy JSON podaje rozmiar klatki i kotwicę (punkt styku z ziemią). *Dokładne zasady klatek dla dużych obiektów: propozycja do potwierdzenia przy pierwszym budynku wzorcowym.*

## Kontrola przed oddaniem

1. Kamera, skala i światła zgodne z tabelami (sprawdzone w pliku `.blend`, nie z pamięci); render w Blenderze 4.3, wersja zapisana w audycie.
2. Kotwica stała; osiem różnych kierunków, żadnego odbicia lustrzanego.
3. Postać nie dotyka krawędzi klatki w żadnej klatce i kierunku; cień może zostać przycięty, ale to odnotowujemy.
4. Brak przenikań między warstwami stroju i rekwizytami w spoczynku i każdej klatce animacji: [`tools/art/check_intersections.py`](../../tools/art/check_intersections.py); zamierzone styki wymienione jawnie w `--allow`.
5. Atlas, JSON i podglądy z tej samej rewizji źródła co rendery.
6. Ocena w skali 1× na ciemnym tle lasu, obok bohatera — sylwetka, broń i sygnały ataku czytelne.
7. Zgodność ze szkicem i kartą bestiariusza; rozbieżności zgłaszamy autorowi.

Powiązane: [przewodnik artystyczny Niemiru](niemir/NIEMIR_ART_DIRECTION.md) · [biblioteka szkiców](../koncepty/README.md) · [bestiariusz](../bestiariusz-demo.md) · [materiały bohatera](characters/HERO_MATERIAL_PLAN.md).
