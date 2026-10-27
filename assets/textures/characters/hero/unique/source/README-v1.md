# Archiwum instrukcji v1 — zaakceptowanej jako wersja robocza

## Zakres i audyt poprzedniej pracy

Zachowano bez zmian oba obrazy oczu z gałęzi `vibe/hero-textures-gpt6`, commit `744b42bb0c33fb379715889c7c779b8c68a12764`. Mają prawidłowy format PNG, 512×512, brązową tęczówkę z alfą (średnica 410 px, około 80%) i ciepłe białko z subtelnymi żyłkami. Źrenica ma około 30% średnicy tęczówki. Ich generator i model nie zostały udokumentowane przez poprzedniego wykonawcę; nie przypisujemy im zmyślonego pochodzenia ani licencji zewnętrznej fotografii.

Poprzednie dwa albedo były nieczytelnymi PNG: strumień zlib i CRC były poprawne, ale zamiast bajtu filtra w każdym wierszu zapisano pierwszy indeks palety, a na końcu dodano zero. Rekonstrukcja do audytu ujawniła beżowy szum, bez wystarczającej pigmentacji twarzy, skóry głowy i dłoni. Poprzednie normalne były paletowe, a pozostałe mapy nie dawały dostatecznych detali anatomicznych. Dziesięć map skóry zastąpiono nową, odtwarzalną syntezą materiału w natywnym UV.

Gałąź poprzednika była oparta na starszym `main` (`6d348b2`). Jej dwa commity przeniesiono lokalnie na aktualny `main` `9bf3ff94dfa62aad057594425f4f4bf2b0a44208`. Nie zmieniano innych gałęzi ani plików poza tym katalogiem.

## Co dostarczono

- Pięć map skóry 4096×4096 oraz pochodne 2048×2048: basecolor, roughness, normal_opengl, height i sss_mask.
- Oczy 512×512 zachowane od poprzednika.
- `manifest.json`: SHA-256, rozdzielczości, przestrzenie barw, metoda i źródła wszystkich plików paczki. Manifest nie hashuje sam siebie.
- `source/build_maps.py`: proceduralny materiał oparty na rzeczywistych współrzędnych powierzchni grupy `body`, bez zmiany siatki/UV. Paleta według konceptu 17 i briefu; ciemna skóra głowy, kilkudniowy brązowy zarost, subtelne brwi i usta, zaczerwienienia, opalenizna, brud dłoni i krótkie paznokcie. Bez blizn, ran, tatuaży, ozdób, AO lub oświetlenia w albedo.
- `source/render_check.py`: osiem diagnostycznych renderów materiału w Blenderze 4.3.2: przód, profil, tył (całe ciało i zbliżenia głowy), dłonie z dwóch stron.
- `source/validate.py` i `qa/validation.json`: kontrola dekodowania, formatów, skalowania, normalnych, szwów oraz sum kontrolnych.

Nie wykorzystano cudzych zdjęć ani biblioteki kafelkowych materiałów. Próba malowanego atlasu przez narzędzie `image_gen` nie zapewniła odpowiedniego rozmieszczenia UV i nie weszła do dostarczonych map. Końcowa skóra jest materiałem proceduralnym, nie skanem ani teksturą namalowaną ręcznie.

## Użycie materiału

Basecolor i obie tekstury oczu: sRGB. Roughness, normal, height i SSS: **Non-Color**. Normalna RGB, tangent space OpenGL (+Y), do węzła Normal Map z bazą MikkTSpace Blendera. Wersję 2K normalnej przeskalowano i ponownie znormalizowano.

Height to PNG grayscale **16 bitów**, 0,5 = neutralnie. Zalecany pełny zakres przemieszczenia 0,002 m; nie nakładać jednocześnie pełnego bump z height i normalnej. Relief to mikrodetal/zmarszczki, nie rzeźba twarzy. W diagnostyce normal strength 0,25; height nie zmienia sylwetki.

Roughness ma zróżnicowanie strefy T, policzków, ust, zarostu, skóry głowy i dłoni. SSS jest względną maską grubości: uszy, nos i palce jaśniejsze. W diagnostyce maska mnoży wagę SSS przez 0,30; to propozycja podłączenia, nie pomiar fizyczny.

Mikrodetal wygaszono w pasie 32–56 px od brzegu wysp UV. Pigmentację regionalną obliczono z pozycji 3D, aby odpowiadające sobie brzegi miały ten sam ton. Małe wyspy opisane na planszy UV jako „oczy” obejmują powierzchnię łączącą się z powiekami (wspólne indeksy wierzchołków OBJ), dlatego w atlasie skóry nie zastępujemy ich białkiem A2. Poza wyspami mapy są wypełnione najbliższą skórą (dylatacja całego tła, powyżej wymaganych 16 px). Tło atlasu nie służy do wyświetlania; wielokątne granice w jego podglądzie wynikają z dylatacji.

## Odtworzenie i kontrola

Wymagania: Python 3 z NumPy, SciPy i Pillow; Blender **4.3** do renderów. Generowanie 4K potrzebuje kilku GB RAM. Dwukrotne wykonanie zapisanego generatora na oryginalnym OBJ dało identyczne SHA-256 wszystkich dziesięciu końcowych map skóry. Zweryfikowane narzędzia: Python 3.12, NumPy 2.3.5, SciPy 1.17.0, Pillow 12.3.0 i Blender 4.3.2. Pracujemy w istniejącym checkoutcie, bez zakładania dodatkowych worktree.

Siatkę należy odczytać z gałęzi wzorcowej, nie przełączać na nią checkoutu:

```bash
# Z katalogu repozytorium; commit jest przypięty, plik trafia poza checkout.
git show 421c7e895e6a029181dcb7c63ab277ad7bab4ca0:assets/sprites/player/source/third_party/base.obj > /tmp/hero-base.obj
cd assets/textures/characters/hero/unique
OPENBLAS_NUM_THREADS=1 python3 source/build_maps.py --mesh /tmp/hero-base.obj
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj
python3 source/validate.py --mesh /tmp/hero-base.obj
```

MakeHuman hm08 jest CC0; informacja znajduje się w nagłówku OBJ. Przód modelu to +Z i góra +Y w źródłowym OBJ. Renderer przelicza te osie na kontraktowe +X przód, +Z góra, wysokość 1,8 m. Nie modyfikuje pliku OBJ, dokumentów ani źródłowego `.blend`.

`podglad/skin_*.png` powstały z aktualnych map, a nie ze starego atlasu. Użyto świateł, AgX, ekspozycji, 64 próbek, seeda i 4 wątków z kontraktu. Kadry są ortograficznymi zbliżeniami materiału 768 px; **nie** są eksportem sprite'ów z kamery gry. Walidator sprawdza zapisane wyniki, a nie tylko istnienie plików. W kontroli 1137 par wierzchołków szwów mediana różnicy RGB wyniosła 0, percentyl 95: 1/255, maksimum: około 5/255 (próbkowanie interpolowane). Znak kanału zielonego normalnej zgadza się z gradientem height (korelacja 0,998). Aby odświeżyć raport, użyj `--write-report`, następnie przelicz manifest; normalna walidacja nie nadpisuje raportu.

## Czego nie sprawdzono i znane wady

- Nie sprawdzono docelowego `.blend` Sola, włókien włosów/zarostu, rogówki ani finalnego podłączenia oczu. Podglądy bazowej grupy `body` mają puste oczodoły; nie przedstawiają finalnego oka. Obrazy A2 zweryfikowano osobno jako obrazy, nie na finalnej kuli oka.
- Nie zatwierdzono wieku 35–40 lat ani zgodności portretu z konceptem: sama neutralna siatka hm08 ma łagodne rysy. Tekstury nie zastąpią męskiej rzeźby żuchwy, kości policzkowych i łuków brwiowych. Skóra głowy jest ciemną bazą pod osobne włókna.
- Zarost, paznokcie, zmarszczki i brud są proceduralną interpretacją; paznokcie i linie dłoni wymagają oceny artystycznej. Brak ręcznego malowania anatomii i skanowanych porów. Nie deklarujemy jakości fotogrametrii ani akceptacji artystycznej.
- Kontrola szwów obejmuje osiem renderów i pomiary par wspólnych wierzchołków. Nie jest dowodem braku wszystkich szwów przy każdym mipie, deformacji i kierunku światła.
- Nie wykonano oceny 1× na tle lasu, animacji, pełnej postaci ze strojem ani portretu z docelowymi oczami i włosami. Weryfikacja tych kryteriów oraz ostateczne światło gry należą do integracji Sola.
- Height/normal i SSS są artystycznymi mapami mikrodetalu, bez wypalania rzeźby high-poly i bez pomiaru grubości tkanki. Nie używać SSS jako gotowej wartości radius w metrach.
- Oryginalne oczy nie mają źródła generatora; pochodzenie poza wskazanymi commitami pozostaje niepotwierdzone.

Część B (ubranie) nie była wykonywana. Ta paczka pozostaje **PROTOTYPE_NOT_APPROVED** do przeglądu PM/autora.


## Odpowiedź na review 744b42b

1. **Naprawione w 1016449:** albedo zapisane standardowym `Pillow Image.save`; wszystkie 12 PNG dekoduje się przez `Image.open(...).load()`.
2. **Naprawione w 1016449:** albedo i normalne RGB 8 bit, roughness/SSS L 8 bit, height grayscale 16 bit, w obu rozdzielczościach. Walidator jawnie kontroluje wszystkie te tryby.
3. **Zastąpione w 1016449:** atlas pigmentacji wyprowadzony z położeń powierzchni OBJ: usta, oczodoły, nos, uszy, zarost i skóra głowy, dłonie/paznokcie/brud, przedramiona/szyja i jaśniejsze ciało pod ubraniem. Materiał powstał proceduralnie; nie jest ręcznie namalowanym ani fotograficznym portretem. Czytelność wieku i charakteru wymaga artystycznej oceny z rzeźbą Sola. Albedo nie korzysta ze świateł, normalnych powierzchni ani AO.
4. **Zastąpione w 1016449:** height i RGB normalna mają anatomiczne maski zmarszczek czoła, kurzych łapek, bruzd nosowo-wargowych i linii dłoni oraz mikrodetal porów. To mikrorelief, nie rzeźba sylwetki ani skan.
5. **Zastąpione w 1016449:** szorstkość jest przypisana do anatomii (T, policzki, usta, zarost, dłonie), SSS do uszu/nosa/palców; następnie rasteryzowane w natywne UV grupy body. Brak prostokątnych masek narysowanych niezależnie od wysp.
6. **Zachowane:** oba pliki oczu są identyczne bajt w bajt z 744b42b.

Po review rendery przeniesiono do wymaganego `podglad/`, poprawiono tam ścieżkę w rendererze i ponowiono pięć zbliżeń i dodano trzy ujęcia całego ciała na przypiętym OBJ w Blenderze 4.3.2. Odświeżono manifest i raport walidacji. Zachowano też oryginalną historię 744b42b przez merge bez zmiany drzewa plików, aby opublikować wynik zwykłym push, bez wymuszania nadpisania gałęzi zdalnej.
