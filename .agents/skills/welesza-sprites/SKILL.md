---
name: welesza-sprites
description: Jedyna obowiązująca metoda tworzenia sprite'ów postaci i potworów Weleszy — prerender 3D z brył SDF (Python + NumPy) w kamerze Diablo 2, 8 kierunków. Używaj przy każdym zleceniu narysowania, przerysowania lub animowania postaci, wroga, bossa albo NPC. Opisuje kontrakt kadru, sposób budowy modelu, lekcje z udanych prób i zasady równoległej pracy wielu agentów.
---

# Sprite'y Weleszy — prerender SDF

Ten skill zastępuje usunięte skille graficzne (`rts-sprite-router`, `retro-rts-sprites`, `painted-rts-sprites`, `rts-prerender-3d`, `rpg-godot-pipeline`, `pixel-art`). **Nie przywracaj ich i nie rób pixel-artu składanego z figur** — dawał sześciokątne tułowia, patykowate nogi i twarze jak emotki, a żadne poprawki tego nie ratowały. Przełom dała zmiana techniki, nie dopieszczanie starej.

**Wzorzec wyglądu: szkice naczelnego w [`docs/koncepty/`](../../../docs/koncepty/README.md)** — sprite ma się do nich zbliżać (sylwetka, ubiór, rekwizyty, kolory). Karta w bestiariuszu opisuje zachowanie i ataki, szkic — wygląd; przy sprzeczności pytaj autora.

Wzorzec techniczny: `assets/sprites/prerender/drwal.py` — ENM-drwal jako ożywieniec, kompletny do gry: szkielet z IK, 6 animacji w 8 kierunkach, 4 warianty wyglądu, atlas PNG + JSON. Format eksportu: `assets/sprites/prerender/README.md`.

## Jak to działa

`assets/sprites/prerender/sdfkit.py` to mały raymarcher w NumPy (rdzeń od autora, z rycerza i demona):

- postać = grupy brył SDF (`sphere`, `ellipsoid`, `cone`, `box`, `cylinder`, `torus`) łączone miękko (`smin`) w obrębie grupy i twardo między grupami;
- `Sub(baza, [wycięcia], smooth)` i `Isect([bryły])` — wycinanie i przecinanie (oczodoły, ostrza, postrzępione brzegi, powłoki tkanin);
- `model.group(smooth, prims, disp=(amplituda, częstotliwość))` — szum zmieniający **kształt** powierzchni (kora, sierść, fałdy, gnijąca tkanina);
- `Xf` — ruch sztywny części ciała (obrót wokół punktu + przesunięcie); `model.group(..., xf=Xf(...))`. Bryły opisuje się w pozycji spoczynkowej, a faktura liczy się w niej, więc nie „pływa” w animacji;
- `Model(clip_ground=True)` obcina wszystko pod ziemią (ostrze wbite w grunt, leżące ciało); `Model(scale=…)` skaluje całą postać względem stóp (warianty wzrostu);
- materiały: albedo liniowe, odbłysk, `grit` (szum koloru), opcjonalna emisja; `make_hook(flags)` w pliku postaci pozwala dodać plamy, mech, żyłki, sygnały;
- oświetlenie: światło kluczowe z lewej góry ekranu (wysoko → krótki cień), niebo, odbicie od ziemi, rim light, miękkie cienie, AO; na końcu lekkie odbarwienie.

Wydajność: ok. 10–12 s na klatkę na jednym rdzeniu (grupy daleko od promienia są pomijane dzięki kulom otaczającym — wynik identyczny). CLI renderuje równolegle na wszystkich rdzeniach: pełny zestaw Drwala (41 klatek × 8 kierunków) ≈ 25 min na 4 rdzeniach. Wymaga tylko `numpy` i `Pillow`.

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
| Granice | wszystko w walcu o promieniu `BOUND_R` = 1,5 m i do wysokości 2,8 m; na ekranie |y| ≤ 1,6 m od środka kadru — wysoko uniesiona broń lub daleki zasięg łatwo wychodzą poza klatkę (patrz lekcje) |
| Tło podglądu | ciemna leśna ziemia `(35, 41, 31)` |

## Nowa postać krok po kroku

1. Przeczytaj kartę postaci w `docs/bestiariusz-demo.md` (i fazy w `docs/spotkania-i-bossowie.md` dla minibossów/bossa). **To jest specyfikacja**: sylwetka, rekwizyty, zapowiedzi ataków, okazje dla gracza, czego nie wolno.
2. Skopiuj `drwal.py` do `assets/sprites/prerender/<id>.py` (`<id>` = identyfikator z bestiariusza bez `ENM-`, np. `zdziczaly-pies`, `powrotnik`, `korzeniec`).
3. Zmień szkielet spoczynkowy, `MATERIALS`, `build(pose, flags)`, `make_hook(flags)`, pozy i `ANIMS`. Interfejs modułu: `MATERIALS`, `POSES` (pozy kluczowe do podglądu), `ANIMS`, `build(pose)` lub `build(pose, flags) -> Model`, opcjonalnie `make_hook(flags)`; na końcu wywołanie `run_anim` / `run_cli` jak w `drwal.py`.
4. Pojedyncza poza: `python3 <id>.py <poza> 7` (podgląd), potem animacje w szkicu: `python3 <id>.py anim all --szkic` — 96 px, jeden kierunek, kilka sekund; pliki trafiają do katalogu tymczasowego, nic nie nadpisuje.
5. Sprawdź, czy wszystko mieści się w klatce (rzut kamery: patrz lekcje) i czy IK nie zgłasza „cel poza zasięgiem”.
6. Pełny render: `python3 <id>.py anim all` → `output/<id>/<id>_<animacja>.png` (atlas), `<id>_<animacja>.gif` (podgląd), `<id>.json`. Dla wariantów: `--wariant=b` → `output/<id>-b/`.
7. Oceń GIF-y w ruchu, na tle lasu, obok `output/drwal/` — skala i jasność mają do siebie pasować.

## Szkielet, pozy i animacje (jak w `drwal.py`)

- **Szkielet spoczynkowy** to stałe punkty: miednica, nasada szyi, biodra/kolana/kostki, barki/łokcie/nadgarstki. Wszystkie bryły opisujesz w tej pozycji.
- **Poza = cele, nie kąty stawów**: położenie miednicy, obrót tułowia (yaw/pitch/roll wokół miednicy), obrót bioder (opcjonalnie), obrót głowy, cele kostek, położenie i kierunek broni, chwyt dłoni na broni albo wolny cel dłoni, kierunki łokci (`pole`). Kolana i łokcie liczy `ik()`.
- Każda kość to `bone(restA, restB, a, b)` → `Xf`: odcinek spoczynkowy trafia na wyliczony; ręce i nogi nie rozrywają się i mają stałą fakturę.
- Broń buduj w jej własnym układzie (x = trzonek, z = ostrze) i ustawiaj jednym `Xf`. Kierunek ostrza: `swing` = oś zamachu → ostrze patrzy w stronę ruchu; dla broni niesionej podaj `edge` jawnie.
- `pose(**zmiany)` = BASE + zmiany; `mix(a, b, t)` interpoluje pozy (kierunek broni po normalizacji). Klatki pośrednie animacji to zwykle `mix` dwóch póz kluczowych; cykle (oddech, chód) generuj funkcją od fazy.
- `ANIMS[nazwa] = dict(frames=[...], durations=[ms...], loop=bool, events={...}, root_speed_mps=…)`. W `events` zapisz dla gry: `zapowiedz` (klatki telegrafu), `aktywne` (klatki zadające obrażenia), `trafienie` (klatka kontaktu), `okazja` (klatki, w których gracz może bezpiecznie kontrować), `parowalny`, `sygnal` (klatki z czerwonym sygnałem).
- Minimalny zestaw do gry: spoczynek, chód, każdy atak z bestiariusza (zapowiedź → cios → okazja → powrót), trafienie, śmierć (ostatnia klatka zostaje jako zwłoki).

## Warianty (żeby wrogowie nie byli klonami)

`VARIANTS` w pliku postaci: skala wzrostu (±5%), tusza, zgarbienie, głowa (włosy / łysy / kaptur / kołpak), broda, rękawy, odcienie materiałów (mnożnik albedo w `make_hook`), ilość mchu, drobne akcesoria, kształt ostrza. Wybór flagą `--wariant=x`.
- **Sylwetka z bestiariusza zostaje w każdym wariancie** (u Drwala: szerokie barki, długi topór, ciemny fartuch z jednym jasnym szwem) — gracz musi rozpoznać typ wroga i jego ataki.
- Animacje, ich czasy i zasięg broni są wspólne — warianty nie zmieniają rozgrywki. Długości broni nie zmieniaj (zasięg = hitbox).
- Wyższy wariant łatwiej wychodzi poza klatkę: sprawdzaj rzut dla największej skali.

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
- **Mieszczenie w klatce**: punkt (x, y, z) w metrach trafia na ekranie na wysokość (z − 1,2)·cos30° ± r·sin30°, gdzie r = √(x²+y²) (+ gdy punkt jest za postacią). Musi być w ±1,6 m. Uniesiony nad głowę topór (z ≈ 2,3 m, r ≈ 0,8 m) jest na granicy — policz to dla końców broni we wszystkich klatkach i wariantach, zanim puścisz pełny render.
- Biodra i fartuch obracają się domyślnie tylko w części razem z tułowiem. Dla póz leżących/klęczących ustaw `hips` jawnie, inaczej fartuch sterczy pionowo z leżącego ciała.
- Gdy IK zgłasza cel poza zasięgiem, przesuń chwyt bliżej końca trzonka albo obniż broń — ręka „nie dosięgająca” trzonka jest od razu widoczna.
- Dwuręczny chwyt: odległość między dłońmi na trzonku 0,1–0,3 m; większa przy szerokich zamachach sprawia, że druga ręka nie sięga.
- Szkic (`--szkic`) wystarcza do oceny ruchu; pełny render dopiero po poprawkach.
- Nie dopieszczaj pojedynczego kadru. Autor ocenia postać w ruchu; doprowadź ją do czytelności i przejdź do póz/animacji.

## Lista kontrolna przed oddaniem postaci (z recenzji Drwala i Psa)

Sprawdź każdy punkt na GIF-ach i atlasie w skali 1×, na tle lasu, obok `output/drwal/`.

- [ ] **Czytelność na tle lasu.** Główny materiał (futro, ubranie) ma albedo ≥ ~0,05; postać nie jest ciemniejszą plamą niż Drwal. Z kierunku N (od tyłu) dalej widać, co to jest — nie pniak ani kamień.
- [ ] **Cechy gatunku widoczne w każdej pozie spoczynkowej i ruchu.** Psu stoją uszy, człowiekowi widać głowę i ramiona. Ukrywaj je (położone uszy, schowana głowa) tylko tam, gdzie to celowy sygnał — wtedy telegraf zyskuje kontrast z resztą animacji.
- [ ] **Rekwizyty z karty mają co najmniej 3 px w 1×.** Rzemienie, łatki, szwy, cienkie kończyny: przesadź grubość i jasność. Kończyny poniżej stawu nie cieńsze niż ~0,035 m.
- [ ] **Liczba klatek.** Zapowiedź ataku: 2–3 klatki narastającego ruchu, nie jedna zamrożona klatka. Cykl chodu/biegu: 6–8 klatek (4 to za mało — wygląda jak ślizganie). Śmierć: ≥ 5 klatek. Trafienie: ≥ 2.
- [ ] **Wszystko mieści się w klatce** we wszystkich klatkach, kierunkach i wariantach (wzór w lekcjach). Pamiętaj o wypadach do przodu (kłapnięcie, cios) — czubek pyska czy broni łatwo przekracza `BOUND_R`.
- [ ] **Zasięg przy ziemi w stronę kamery ≤ ~1,1 m od środka.** Punkt na ziemi w odległości r ląduje na ekranie na wysokości −1,04 − 0,5·r m, a klatka kończy się na −1,6 m. Długie korzenie, ogony, wypady i leżące ciała sprawdź z kierunków S, SW i SE. Jeśli postać musi sięgać dalej, zgłoś autorowi potrzebę większej klatki zamiast godzić się na ucięcie.
- [ ] **Obie strony ciała są na miejscu.** Z kierunków S i N widać lewą i prawą kończynę (rękę, łapę, korzeń). Częsty błąd: współrzędne prawej strony podane już z minusem i dodatkowo mnożone przez `side = -1` — obie kończyny lądują po jednej stronie.
- [ ] **Bez wpieczonego podłoża.** Żadnej trawy, ziemi ani „cokołu” pod postacią — teren rysuje gra, a podstawa przesuwałaby się razem z potworem i zostawała po śmierci. Dozwolony jest tylko cień z renderera.
- [ ] **Jeden format eksportu:** `ANIMS` + `run_anim` (atlas na animację, JSON z `events`). Nie pisz własnego eksportera — gra ma mieć jeden importer. Warianty flagą `--wariant=<litera>`.
- [ ] **Okna walki w `events`** dla każdego ataku: `zapowiedz`, `aktywne`, `trafienie`, `okazja`, `parowalny` (z karty w bestiariuszu).
- [ ] **Zacommitowane PNG odpowiadają kodowi.** Po zmianie modelu lub póz wyrenderuj ponownie albo usuń stare klatki — nie zostawiaj wyników poprzedniej wersji.
- [ ] **Ton zgodny z kartą.** Porównaj docstring i efekty (świecące oczy, krew, „demoniczność”) z opisem w bestiariuszu. Emisja tylko tam, gdzie karta lub zasady stylu jej wymagają; odblask oczu zwierzęcia — słaby. Rozbieżności zgłoś autorowi zamiast rozstrzygać.

## Praca równoległa wielu agentów

- **Jedna postać = jeden plik `<id>.py` + jeden katalog `output/<id>/`.** Nie edytuj cudzych plików postaci.
- **`sdfkit.py` jest wspólny.** Nie zmieniaj istniejących funkcji, stałych kontraktu, światła ani kamery. Brakującą bryłę lub operację dopisz najpierw lokalnie w pliku postaci; do `sdfkit.py` dodawaj tylko nowe funkcje na końcu, w osobnym commicie z krótkim opisem. Zmiana zachowania istniejącej funkcji zmienia wszystkie postacie — wymaga zgody autora i ponownego renderu.
- ID materiałów są lokalne dla postaci (słownik w jej pliku) — nie ma konfliktów.
- Każdy agent pracuje na własnej gałęzi `vibe/sprite-<id>`, commituje generator **i** wynik (atlasy PNG, JSON, GIF-y).
- Nie zmieniaj kanonu: interpretacje postaci (np. „demon czy ożywieniec”) zapisz w docstringu pliku postaci jako wybór wykonawczy do potwierdzenia przez autora, nie w dokumentach projektu.
- Wątpliwości dotyczące kierunku konsultuj z autorem — nie zgaduj za niego.

## Czego jeszcze nie ma

- Silnik gry nie jest wybrany. Eksport (atlas z równą siatką 192 px + JSON z kotwicą, czasami i oknami walki) jest neutralny; importer napiszemy po wyborze silnika.
- Atlas nie jest przycinany do zawartości — prostota kosztem rozmiaru pliku.
