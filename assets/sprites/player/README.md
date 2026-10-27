# Bohater główny (Welesza — postać gracza)

Pierwszy główny bohater gry: zwykły podróżnik, mężczyzna 30–40 lat, zmęczony
kilkudniową wędrówką w deszczu. Wygląd zgodny z arkuszem
`docs/koncepty/03-arkusz-cywile-niemiru.jpg` (język wizualny cywili Niemiru).

## Metoda: meshkit (siatki trójkątowe + software rasterizer), NIE SDF

Zlecenie dopuszczało odejście od SDF. Wybrano własny pipeline oparty na
siatkach trójkątowych, bo daje lepszą anatomię i materiały niż raymarching
brył przy tej samej skali sprite'a:

- **Geometria**: proceduralne siatki trójkątowe (lofty, elipsoidy, boxy) z
  prawidłową anatomią człowieka (7,5 głowy, barki ~2,3 głowy). Ubranie to
  osobne siatki "owijające" ciało — koszula (rękawy), kaftan i płaszcz jako
  **otwarte łuki** (`_arc_pts` + `_loft_open`), dzięki czemu widać warstwy
  ubioru, a nie sztywną rurę. Fałdy tkanin to geometria (displacement
  pierścieni), nie tekstura.
- **Szkielet i skinning**: łańcuch kości (pelvis → spine → neck → head,
  ręce: clavicle → upper → fore → hand, nogi: thigh → shin → foot) z
  liniowym skinningiem (LBS, 3 kości na wierzchołek, wagi od odległości).
  Ręce i nogi ustawiane przez IK 2-kość (`ik2` z wektorem biegunowym —
  łokieć zgina się w naturalną stronę).
- **Rasteryzacja**: własny software rasterizer (z-buffer, per-pikselowe
  cieniowanie, AO per-wierzchołkowe, kierunkowa shadow mapa, kontaktowy
  cień na ziemi). Obsługa siatek dwustronnych (`two_sided`) dla pojedynczych
  warstw tkaniny.
- **Materiały**: 13 materiałów (skóra, włosy, len, wełna, płaszcz, skóra butów,
  skóra pasków, owijki, drewno, żelazo, krawędź, płótno plecaka) z osobnymi
  parametrami albedo / specular / roughness-grit. Detale proceduralne w
  `make_shade_hook`: plamy i żyłki na skórze, mech/wilgoć na górnych
  powierzchniach tkanin, przetarcia na łokciach/kolanach, rdza i rysy na
  żelazie, połysk na noskach butów. Tonemap Reinharda + gamma + lekkie
  odbarwienie (jak sdfkit).

Kontrakt kadru zgodny z sdfkit (192×192 RGBA, ortho 30°, 8 kierunków
S/SW/W/NW/N/NE/E/SE, kotwica (96, 158.4), 60 px/m, światło z lewej góry,
przezroczyste tło, cień kontaktowy w alfa).

## Struktura

```
assets/sprites/player/
  source/
    bohater.py    # model, pozy, animacje, eksport (odtwarzalne źródło)
    meshkit.py    # silnik: siatki, szkielet, skinning, rasterizer, eksport
    _smoke.py     # szybki test środowiska
  renders/        # (puste — rendery pośrednie nie są potrzebne, atlasy są w atlas/)
  atlas/
    bohater_spoczynek.png/.gif   # 4 klatki × 8 kierunków
    bohater_chod.png/.gif        # 8 klatek × 8 kierunków
    bohater.json                 # metadane (zgodne z formatem drwala)
  previews/
    bohater_spoczynek_arkusz.png # arkusz 8 kierunków na tle
    bohater_spoczynek_{0..7}_{S..SE}.png  # pojedyncze kierunki
  README.md       # ten plik
```

## Odtworzenie wyników

Wymagania: Python 3, `numpy`, `pillow`. Bez innych zależności, bez GPU,
bez Blendera, bez zewnętrznych modeli/tekstur (wszystko proceduralne —
brak kwestii licencyjnych).

```bash
cd assets/sprites/player/source

python3 bohater.py test              # kontrola techniczna (kotwica, alfa, granice)
python3 bohater.py arkusz spoczynek  # arkusz 8 kierunków + PNG do previews/
python3 bohater.py anim spoczynek    # atlas spoczynku (PNG + GIF + JSON)
python3 bohater.py anim chod         # atlas chodu
python3 bohater.py anim all          # wszystkie animacje
python3 bohater.py anim chod --szkic # szybki podgląd 96 px, kierunek SE
```

Pełny eksport (`anim all`, 192 px, supersampling ×4) zajmuje ~5–7 minut
na wielordzeniowym CPU (96 klatek × 8 kierunków, renderowanie równoległe).

## Animacje

| Animacja | Klatki | Czas/klatkę | Uwagi |
|---|---|---|---|
| `spoczynek` | 4 | 260 ms | oddech (miednica, kręgosłup, głowa), lekki ruch miecza |
| `chod` | 8 | 115 ms | cykl z fazą podporową 60% (stopa nieruchoma względem ziemi — brak ślizgania) i fazą lotu 40% (smoothstep + uniesienie 7 cm), przeniesienie ciężaru (miednica), przeciwstawny ruch barków, kołysanie miecza |

Prędkość root motion chodu: 0,83 m/s (z `root_speed_mps` w JSON).

## Kontrola jakości (co sprawdzono)

- Kotwica: dół ciała (alfa > 0,85) w każdej klatce i kierunku w zakresie
  y = 149–165 (kotwica 158,4; ±7 px na kierunki boczne — wynik geometrii
  izometrycznej, nie błąd).
- Wysokość postaci na ekranie: 90–101 px (1,78 m × cos30° × 60 px/m ≈ 92 px).
- Brak dziur w sylwetce (0 pikseli alfa≈0 otoczonych ciałem) we wszystkich
  8 kierunkach.
- Marginesy: wszystkie piksele (w tym cień) wewnątrz klatki z zapasem ≥ 2 px.
- Alfa: pełne krycie na ciele (max = 255), przezroczystość poza postacią.
- Miecz: trzymany jedną (prawą) dłonią, opuszczony wzdłuż uda, klingą w dół;
  dłoń dokładnie na osi trzonka (odległość 0,0 m). Lewa ręka swobodna.
- Chód: faza podporowa liniowa (brak ślizgania stopy po ziemi).

## Znane ograniczenia (do poprawy w kolejnych etapach)

- Brak jeszcze animacji: bieg, atak, Garda/parada, trafienie, śmierć, unik.
- Twarz: bez szczegółowych rysów (oczy to zagłębienia, nie gałki) — celowe
  przy 100 px wysokości sprite'a, model źródłowy można rozwinąć.
- Płaszcz/kaftan: pojedyncze warstwy tkaniny (nie symulacja fizyczna) —
  ruch podczas chodu jest subtelny, nie faluje swobodnie.
- Cień: kierunkowy + kontaktowy, bez cienia od konkretnego źródła światła
  (pochodnia) — projekt oświetlenia dynamicznego do ustalenia.
- `meshkit.py` i `bohater.py` są osobnymi kopiami (nie współdzielą kodu
  z `sdfkit.py`) — celowe, żeby nie modyfikować istniejącego pipeline'u.

## Propozycja migracji (dla autora)

Meshkit daje lepszą anatomię i czytelniejsze materiały niż SDF przy tej
samej rozdzielczości. Koszt migracji innych postaci: przepisanie definicji
modelu z SDF na siatki (1–2 dni na postać dla osoby znającej meshkit).
Korzyść: spójna jakość wszystkich postaci, łatwiejsze animacje (ten sam
szkielet), mniej artefaktów SDF (przenikania, "plastik").

Nie migrować bez akceptacji — Drwal i pozostałe postacie zostają na SDF.
