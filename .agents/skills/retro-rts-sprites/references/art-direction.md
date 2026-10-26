# Dark-fantasy Pixel Art — praktyczne reguły, v4

Inspiracje metodyczne: Gamezxz/pixel-art-studio, MIT. Techniki zostały opracowane na nowo dla izometrycznego ARPG w Godot, nie kopiujemy rysunków autora.

## Zamysł i wybór backendu

Zachowaj **dwa warianty retro**: `spritekit.js` (niewielkie kafle 64×32 i kod ASCII → PNG/SVG, oryginalna skala) oraz `pixelcraft.py` (Pillow, wielowarstwowe szczegółowe 2D, 8 kierunków; animacje). Żaden z nich nie zastępuje statycznych budynków `painter.js` / `rtcore.js` w estetyce prerenderu Diablo II. Nie skaluj starych 24×32 jednostek do 96×116 bez przeprojektowania anatomii.

## Bramka jakości dla każdej jednostki

1. **Brief**: natywny rozmiar docelowy (np. 64×80 lub 96×116); docelowy ekran Godot przy 1×; paleta 8–20 kolorów dla postaci (większe sceny wymagają więcej); światło; tło; kotwica stóp.
2. **Sylwetka**: obiekt musi być rozpoznawalny na ciemnym i jasnym tle bez barw. Nie zaczynaj od źrenic i nitów. Zróżnicowanie klas kształtem: miecz vs. włócznia, tarcza, kaptur, naramienniki.
3. **Masowe plamy koloru**: cień, baza i światło z odchyleniem odcieni; metal ma ostre skupione refleksy, tkanina miękkie duże powierzchnie, kości ciepły mid-tone. Nigdy „pillow shading” — przyciemnianie wszystkich krawędzi jak balon.
4. **Gęstość detalu**: najpierw czytelne skupiska (cluster 2–4 px), potem pojedyncze piksele uzasadnione refleksami. Kontur 1px, selektywny (jaśniejszy po stronie światła); wycisz szum na krawędziach.
5. **Kompozycja przestrzenna**: ręcznie narysowana widoczność sprzętu, głowy i kończyn dla każdego kierunku; nie obracaj gotowego PNG o 45° filtrem biliniowym. Bliską stronę rozjaśnij, dalszą ściemnij, części schowane za tarczą mogą być zasłonięte tylko celowo.
6. **Animacja**: kluczowe pozy (contact, passing, opposite contact, passing) przed interpolacją; czas osobno per klatka, idle może być ping-pong. Sprawdź trzy pętle i brak ślizgania nóg. Faza walki: anticipation → hit/reach → recovery, nie równy czas klatek.
7. **Bramka techniczna**: wszystkie 8 kierunków, identyczny canvas i anchor we wszystkich frame'ach, brak uciętych pikseli, stabilna kotwica przez długą broń i osiem pozycji obrotu. Porównuj RGBA między wszystkimi parami kierunków; symetryczne obiekty wyjątek jawny.
8. **Bramka artystyczna**: oceniaj w 1× na dwóch rzeczywistych podłożach z gry, do oceny używaj też powiększenia 4×/8× przez nearest. Obowiązkowo co najmniej dwie iteracje po pierwszym renderze. Obiekty podobne gatunkowo mają dzielić paletę i kierunek oświetlenia.

## Jak nie używać pixel-artowego cleanupu

Nie aplikuj `clean_import()` do atlasów `painter.js` i `rtcore.js` domyślnie: twarda alfa, sztuczne próbkowanie oraz limit 24 kolorów zniszczą miękkie cienie. Tego używaj tylko przy świadomej konwersji *na pixel art*. Światło/kontrast między backendami normalizuj przez kolor grading po ocenie na tło, bez zamiany na sztywną paletę.

## Reprodukcja

`python demo/arpg/render_demo.py` tworzy PNG źródłowe 1× i atlasy 8×4 w formacie zgodnym z `RpgAtlas.gd`; należy porównać wynik z wizualnym briefem. Długie animacje ataku wymagają osobnego większego canvasu wspólnego dla całej akcji i offsetu tej samej fizycznej kotwicy.
