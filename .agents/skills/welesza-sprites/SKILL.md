---
name: welesza-sprites
description: Jedyna obowiązująca metoda tworzenia sprite'ów postaci i potworów Weleszy — prerender 3D z brył SDF (Python + NumPy) w kamerze Diablo 2, 8 kierunków. Używaj przy każdym zleceniu narysowania, przerysowania lub animowania postaci, wroga, bossa albo NPC. Opisuje kontrakt kadru, sposób budowy modelu, lekcje z udanych prób i zasady równoległej pracy wielu agentów.
---

# Sprite'y Weleszy — prerender SDF

Ten skill zastępuje usunięte skille graficzne (`rts-sprite-router`, `retro-rts-sprites`, `painted-rts-sprites`, `rts-prerender-3d`, `rpg-godot-pipeline`, `pixel-art`). **Nie przywracaj ich i nie rób pixel-artu składanego z figur** — dawał sześciokątne tułowia, patykowate nogi i twarze jak emotki, a żadne poprawki tego nie ratowały. Przełom dała zmiana techniki, nie dopieszczanie starej.

Wzorzec do naśladowania: `assets/sprites/prerender/drwal.py` (ENM-drwal jako ożywieniec, poza Rozłupania, 8 kierunków, zaakceptowany przez autora).

## Jak to działa

`assets/sprites/prerender/sdfkit.py` to mały raymarcher w NumPy (rdzeń od autora, z rycerza i demona):

- postać = grupy brył SDF (`sphere`, `ellipsoid`, `cone`, `box`, `cylinder`, `torus`) łączone miękko (`smin`) w obrębie grupy i twardo między grupami;
- `Sub(baza, [wycięcia], smooth)` i `Isect([bryły])` — wycinanie i przecinanie (oczodoły, ostrza, postrzępione brzegi, powłoki tkanin);
- `model.group(smooth, prims, disp=(amplituda, częstotliwość))` — szum zmieniający **kształt** powierzchni (kora, sierść, fałdy, gnijąca tkanina);
- materiały: albedo liniowe, odbłysk, `grit` (szum koloru), opcjonalna emisja; `make_hook(flags)` w pliku postaci pozwala dodać plamy, mech, żyłki, sygnały;
- oświetlenie: światło kluczowe z lewej góry ekranu (wysoko → krótki cień), niebo, odbicie od ziemi, rim light, miękkie cienie, AO; na końcu lekkie odbarwienie.

Wydajność: ok. 15–20 s na klatkę na jednym rdzeniu; CLI renderuje kierunki równolegle (8 kierunków ≈ 2,5 min na 4 rdzeniach). Wymaga tylko `numpy` i `Pillow`.

## Kontrakt kadru — NIE ZMIENIAĆ bez zgody autora

Stałe są w `sdfkit.py` (`FRAME_SIZE`, `EXTENT`, `CENTER_Z`, `SUPERSAMPLE`, `ELEVATION`, `LIGHT`). Wszystkie postacie muszą mieć tę samą skalę, kamerę i światło, inaczej nie zagrają razem w grze.

| Parametr | Wartość |
|---|---|
| Klatka | 192×192 px RGBA, wygładzone krawędzie, półprzezroczysty cień |
| Skala | 3,2 m świata na szerokość klatki (~60 px/m); człowiek ~1,8 m ≈ 105 px |
| Kamera | ortogonalna, 30° nad horyzontem, celuje w z = 1,2 m |
| Kierunki | 0 S (przodem do kamery), 1 SW, 2 W, 3 NW, 4 N, 5 NE, 6 E, 7 SE — obrót modelu, nie lustro |
| Kotwica stóp | punkt (0, 0, 0) świata → piksel ≈ (96, 158) w każdej klatce i kierunku |
| Układ świata | x do przodu postaci, y w lewo, z w górę; metry; stopy na z = 0 |
| Granice | wszystko w walcu o promieniu 1,2 m i do wysokości 2,8 m (inaczej zostanie ucięte) |
| Tło podglądu | ciemna leśna ziemia `(35, 41, 31)` |

## Nowa postać krok po kroku

1. Przeczytaj kartę postaci w `docs/bestiariusz-demo.md` (i fazy w `docs/spotkania-i-bossowie.md` dla minibossów/bossa). **To jest specyfikacja**: sylwetka, rekwizyty, zapowiedzi ataków, czego nie wolno.
2. Skopiuj `drwal.py` do `assets/sprites/prerender/<id>.py` (`<id>` = identyfikator z bestiariusza bez `ENM-`, np. `zdziczaly-pies`, `powrotnik`, `korzeniec`).
3. Zmień `POSES`, `MATERIALS`, `build(pose)` i `make_hook(flags)`. Interfejs modułu jest stały: `POSES`, `MATERIALS`, `build(pose) -> Model`, opcjonalnie `make_hook(flags)`, na końcu `run_cli("<id>", __file__)`.
4. Najpierw jeden kierunek: `python3 <id>.py <poza> 7`, obejrzyj, popraw; potem `python3 <id>.py <poza> all` (zapisze 8 klatek i arkusz w `output/<id>/`).
5. Oceń arkusz w skali 1× na tle lasu, obok `output/drwal/drwal_rozlupanie_arkusz.png` — skala i jasność mają do siebie pasować.

### Pozy i animacje

Wszystkie stawy postaci trzymaj w słowniku pozy (`POSES["nazwa"]`), a `build(pose)` niech wylicza z nich geometrię. Nowa klatka animacji = nowa poza, model bez zmian. Animacje z bestiariusza, w kolejności ważności: zapowiedź każdego ataku, sam atak i okazja po nim (np. ostrze grzęźnie w ziemi), spoczynek, chód, trafienie, śmierć. Pojedyncza poza nie jest celem — liczy się, czy ruch czyta się w walce.

## Zasady stylu (z dokumentów projektu)

- Ciemno, ziemiście, lekko odbarwione: jednostka nie jaśniejsza i nie bardziej nasycona niż las. Albedo materiałów zwykle 0,03–0,13 (liniowo); jaśniejsze tylko akcenty fabularne (jasny szew fartucha, łatka psa, kościany gwizdek).
- **Czerwień wyłącznie jako sygnał** ataku nieparowalnego (emisja tylko w pozach zapowiedzi/ataku), krew lub ogień. Nigdy jako kolor skóry czy dekoracja.
- **Bez makabry**: żadnych otwartych ran, żeber na wierzchu, flaków. Groza z sylwetki, postawy, światła i rekwizytów. Ożywieniec = popielata, woskowa skóra, zapadnięte oczodoły, mętny blask oczu, zbutwiałe ubranie, mech.
- Bez dzieci jako wrogów, bez świecących run, bez broni palnej, bez „magicznego wilka”.
- Rekwizyt z karty postaci musi być czytelny w skali 1× — przesadź go (łatka, szew, worek, obroża), bo detal poniżej 3 px znika.
- Broń i telegraf ataku muszą przebijać sylwetkę **w każdym z 8 kierunków**.

## Lekcje z Drwala (sprawdzone, oszczędzą Ci iteracji)

- Płaska broń ułożona w płaszczyźnie x–z znika patrząc od przodu. Przechyl płaszczyznę zamachu (np. nad bark, składowa y ≠ 0), a ramę ostrza licz z `cross(kierunek_trzonka, kierunek_ostrza)`.
- Pasek krawędzi ostrza (osobny materiał) musi być **grubszy** niż samo ostrze, inaczej chowa się w środku i emisja jest niewidoczna.
- Kształt topora: prostokąt ∩ duża kula (łukowata krawędź) minus dwa walce przy oku (szyjka/broda). Sam prostokąt czyta się jak tasak albo młotek.
- Tkaniny opinające ciało (fartuch, płaszcz): powłoka = elipsoida minus trochę mniejsza elipsoida, przecięta prostopadłościanem ograniczającym fragment. Płaski `box` wygląda jak deska albo tarcza.
- Amplitudy `disp`: tułów ≤ 0,004, twarz ≤ 0,0015, kończyny/onuce ~0,006, włosy/kora 0,01–0,015. Więcej = postać wygląda jak kamień.
- Postać ginie w tle, gdy ubranie i skóra mają podobną jasność. Skóra ożywieńca jaśniejsza od ubrania daje odczyt „trup” z daleka.
- Rozchylone łokcie i ręce nad głową tworzą trójkąt — mocny, czytelny telegraf.
- Nie dopieszczaj pojedynczego kadru. Autor ocenia postać w ruchu; doprowadź ją do czytelności i przejdź do póz/animacji.

## Praca równoległa wielu agentów

- **Jedna postać = jeden plik `<id>.py` + jeden katalog `output/<id>/`.** Nie edytuj cudzych plików postaci.
- **`sdfkit.py` jest wspólny.** Nie zmieniaj istniejących funkcji, stałych kontraktu, światła ani kamery. Brakującą bryłę lub operację dopisz najpierw lokalnie w pliku postaci; do `sdfkit.py` dodawaj tylko nowe funkcje na końcu, w osobnym commicie z krótkim opisem. Zmiana zachowania istniejącej funkcji zmienia wszystkie postacie — wymaga zgody autora i ponownego renderu.
- ID materiałów są lokalne dla postaci (słownik w jej pliku) — nie ma konfliktów.
- Każdy agent pracuje na własnej gałęzi `vibe/sprite-<id>`, commituje generator **i** wyrenderowane PNG (klatki + arkusz).
- Nie zmieniaj kanonu: interpretacje postaci (np. „demon czy ożywieniec”) zapisz w docstringu pliku postaci jako wybór wykonawczy do potwierdzenia przez autora, nie w dokumentach projektu.
- Wątpliwości dotyczące kierunku konsultuj z autorem — nie zgaduj za niego.

## Czego jeszcze nie ma

- System szkieletu z interpolacją póz i eksport atlasu z JSON (kotwica stóp, czasy klatek) — kolejny krok. Do tego czasu pozy są statyczne, a kotwica stóp wynika ze stałego kadru: ≈ (96, 158) px.
- Silnik gry nie jest wybrany; format eksportu ustalimy po jego wyborze.
