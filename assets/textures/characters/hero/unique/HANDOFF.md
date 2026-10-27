# HANDOFF — bohater, skóra v4 / część A

## Stan i podstawa

- Gałąź: `vibe/hero-textures-gpt6`; v4 jest w commicie zawierającym ten plik.
- Baza robocza: **35df59f4c19b473530fd3fe316b35fc7b1739327**. Dłonie i szyja z tej wersji zachowane dokładnie w obu rozdzielczościach i wszystkich pięciu mapach; sclera i SSS bez zmian w całości.
- Kierunek: brief rozdz. 2–4 i koncept twarzy **19, wersja 2**, `main` @ `eb3a2ec6282855e8b659970b10a677b4232d68fe`. Wymagania autora/brief > koncept19 > twarz z planszy17. Strój nadal według planszy17.
- Status: **PROTOTYPE_NOT_APPROVED**, do oceny artystycznej i integracji. Części B nie zaczynano; czeka na P2 od Sola.

## Oddane mapy i zmiany

`hero_skin_body_{basecolor,roughness,normal_opengl,height,sss_mask}.png` (4096) i odpowiedniki `_2048.png`; `hero_eye_iris_basecolor.png` i `hero_eye_sclera_basecolor.png` (512). Nazwy, formaty i natywne UV bez zmian.

V4: różowoczerwone wygojone blizny, dodatni relief brzegów/rdzeni, niższa szorstkość, ciemniejsze środki i ślady szycia. Po **lewej stronie postaci**: skośna przez czoło nad brwią z krótszym krzyżującym cięciem i skośna pod okiem. Po prawej trzy mniejsze zadrapania. Nie są otwartymi ranami; nie dopisano historii ich powstania. Usunięto stare wklęsłe, jasne blizny i długie czerwone kreski przy nosie.

Nowe nieregularne, przerywane bruzdy czoła, relief gniewny między brwiami, kurze łapki, worki/cienie pod oczami, pory i drobne plamki twarzy. Mocniejszy zarost i wąs; losowo rozmieszczone siwe mieszki, najwięcej na podbródku; ciemna baza skóry głowy z siwizną. Nie malowano na skórze długich włosów.

Tęczówka: szarozielona/szaroorzechowa, z ciepłym oliwkowo-brązowym pierścieniem przy źrenicy i ciemnym limbusem. Iris RGBA 8 bit, okrąg 80%, źrenica około 30% średnicy tęczówki. Bez namalowanego refleksu.

**Lewa strona postaci = +X w źródłowym OBJ**, po transformacji renderera +Y świata. Z perspektywy widza frontalnego lewa strona postaci jest po prawej stronie obrazu. Dokładne kotwice blizn: `qa/v4_material_checks.json`.

## Podłączenie dla Sola

- Basecolor, iris i sclera: **sRGB**. Roughness, height, normal i SSS: **Non-Color**.
- **Normal strength 0,45**, OpenGL +Y, węzeł Normal Map / baza MikkTSpace Blendera. Height grayscale 16 bit, neutralnie 0,5; umowny pełny zakres 0,002 m. Nie dublować pełnego bump i normalnej.
- SSS to względna maska; w podglądzie mnoży wagę przez 0,30. Nie używać jej jako promienia w metrach.
- Średniej długości włosy do linii żuchwy, włókna brody/wąsa z siwizną, ciężkie łuki brwiowe i rzeźba twarzy według konceptu pozostają zadaniem modelu Sola. Tekstura nie zmienia sylwetki głowy.
- Oczy w podglądach v4 są **diagnostycznymi helperami oka z przypiętego OBJ**, z płaskim rzutem map A2. Nie zmieniają UV ciała i nie zastępują docelowych gałek z rogówką. Dodano je identycznie do porównań v3/v4.

## Gdzie oceniać

- `podglad/v4/before/` — v3 z 35df59f; `after/` — v4. Przód, profil, zbliżenie twarzy i oko, po 768 px.
- `podglad/v4/porownanie.png` — te same kamery, światła kontraktu, AgX, normal 0,45 po obu stronach.
- `podglad/v4/koncept19-v4.png` — koncept19 obok v4. Ilustracja ma własne światło, a bazowy OBJ inne rysy; to odniesienie cech, nie identyczny render.
- `podglad/skin_*.png` — bieżące pełne podglądy. Katalogi v2/v3 są archiwum.

## Kontrola i odtwarzanie

`source/build_maps.py`, `aging_v2.py`, `face_v4.py` tworzą mapy ciała; `build_eye.py` tęczówkę. `render_check.py` renderuje w Blenderze4.3.2; `compare_v4.py` składa plansze. Polecenia i wersje narzędzi w README. Generator korzysta z Git35df59f, aby przywrócić chronione regiony.

`qa/validation.json` i `manifest.json` zawierają aktualne wyniki i SHA-256. Walidacja obejmuje 12 PNG, formaty/16-bit height, skalowanie, jednostkowe wektory normalne/+Y, pary szwów, kolor pierścieni tęczówki i dokładne porównanie szyi/dłoni z bazą. `qa/v4_material_checks.json` zapisuje stronę blizn i kontrolę dodatniego reliefu.

Nie sprawdzono docelowego `.blend` Sola, finalnej rogówki, włókien, animacji, stroju ani skali gry1×. Brak akceptacji artystycznej v4. To proceduralna interpretacja materiału; geometryczne rysy konceptu wymagają rzeźby. Zgodnie z „bez zmian szyja” nie dokładano tam nowych piegów — zachowano jej pigmentację z35df59f. Po renderze Sola możliwe dalsze korekty części A; część B dopiero po przekazaniu P2.

## Wynik kontroli końcowej v4

- Wszystkie 12 map PNG poprawnie zdekodowane; wymagane rozdzielczości, tryby i głębia bitowa potwierdzone. Height pozostaje 16-bitowy, kolor i normalna RGB bez palety.
- 1137 próbek par szwów UV: mediana różnicy RGB 0, percentyl95 1, maksimum 4,651 na skali 8-bitowej (limity 2 i 8). Korelacja zielonego kanału OpenGL z pochodną height: 0,99822.
- Wszystkie piksele chronionych obszarów dłoni i szyi identyczne z35df59f we wszystkich 10 mapach. Obie pełne mapy SSS i pełny plik sclera zachowane bajt w bajt.
- Średni RGB zewnętrznego pierścienia tęczówki: (112,123,113); ciepłego wewnętrznego: (123,116,89). Minimalny relief kontrolowanego rdzenia blizn 0,50273, powyżej neutralnego 0,5.
- Wyrenderowano i obejrzano v4 w Blenderze4.3.2 przy normal0,45; porównania obejmują cztery identyczne kadry v3/v4 oraz osobne zestawienie z konceptem19. Bieżące podglądy zawierają także tył, całe ciało i dłonie. Wyniki te są kontrolą techniczną, nie akceptacją autora.
- SHA-256 i pełny spis oddanych plików: manifest; szczegółowy wynik automatyczny: `qa/validation.json`.
