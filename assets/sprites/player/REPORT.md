# Bohater Weleszy — dopracowanie zatwierdzonego prototypu

**Status: wersja do ponownej oceny autora. Kierunek zatwierdzony, bieżący asset
nie ma zatwierdzenia produkcyjnego.** Gałąź `vibe/sprite-bohater-codex`.
Punkt „przed”: `a0a6c27e33b5d634e1ccad59e7634e4ab4d7ccde`, zachowany razem
z modelem w [baseline](baseline/checkpoint.json). To ta sama postać i szkielet;
nie rozpoczęto ataków, uników, śmierci ani innych postaci.

Najnowsza praca nad detalami jest osobną wersją roboczą: `source/bohater_detale.blend`.
Poniższe kompletne atlasy i testy dotyczą zachowanego modelu rewizji 08.

## Materiał do przeglądu

- [Odtwarzacz przed/po, osiem kierunków 1:1](previews/review.html).
- [Osiem kierunków przed/po 1:1](previews/porownanie-kierunki-1x.png).
- [Chód przed/po](previews/porownanie-chod-1x.gif), [spoczynek przed/po](previews/porownanie-spoczynek-1x.gif).
- [Chód na ruchomym podłożu — osiem kierunków](previews/chod-podloze-8-kierunkow-1x.gif).
- [Większe rzeczywiste rendery modelu przed/po](previews/model-zrodlowy-przed-po.png).
- [Włosy, zarost i oczy — zbliżenie przed/po korekcie autora](previews/wlosy-zarost-przed-po.png).
- [Broń N/NW w fazach chodu, dwa podłoża](previews/bron-N-NW-1x.gif).
- [Miecz dobyty / w pochwie — opcja do wyboru](previews/bron-dobyta-pochwa-1x.png).
- [Bazowe, chłodne i ciepłe światło — osiem kierunków](previews/materialy-swiatlo-8-kierunkow-1x.png).
- [Ilustracja koncepcyjna 17 z osobnym sprite'em](previews/koncept17-porownanie-1x.png).
- [Edytowalny model nadrzędny](source/bohater.blend), [pochodzenie i materiały](source/art-source.json), [eksport](atlas/bohater.json).

Zbliżenie włosów „przed” jest stanem sprzed korekty fryzury (`c064e98`),
po integracji materiałów, a nie pierwotnym checkpointem `a0a6c27`.
Porównania całej postaci używają oryginalnego checkpointu. Portrety diagnostyczne
mają bliższą kamerę; nie są podglądem skali gry. Większe rendery całej postaci
powstały w 1152 px przy tej samej kamerze i skali świata co sprite 192 px.

## Co zmieniono

**Ubranie i materiały.** Zachowano topologię płaszcza i jego istniejące klucze,
zmieniając rozkład fałd, ukośne napięcie tkaniny i nierówny dół. Zmniejszono
objętość lnu pod kaftanem, dopasowano otwarcie skórzanych połaci i ich brzegi,
dodano miejscowe zagniecenia rękawów i kolan. Grubość tkaniny nadal jest
geometrią. Naprawiono wskazany przez autora jasny fragment przy kroczu:
to był zbyt długi, źle zakryty dół tuniki. Teraz dolne pierścienie koszuli są
wpuszczone pod pas i spodnie; nie wystają między nogawkami.

Zintegrowano trzy paczki z biblioteki autora: len, wełnę, skórę kaftana,
spodnie, buty, plecak, płótno posłania, rzemienie, żelazo, stal, skórę człowieka
i włosy. Dostarczone normal mapy pozostają w repozytorium; w shaderach użyto
alternatywnie subtelnego **height → Bump**, bez podwójnego reliefu.
Basecolor sRGB, pozostałe dane Non-Color, metale mają mapy Metallic.

Pierwszy pilot wełny dawał zbyt plamisty efekt — [zachowany przykład](previews/iterations/materialy-pilot01-zbyt-plamiste.png).
Udział tej bazy w kolorze obniżono do 22%, skóry do 48%. Pozostałe kanały nadal
wpływają na reakcję materiału. Nie rozjaśniono globalnie sceny ani ekspozycji.
Maska zużycia z biblioteki jest mnożona przez odległość od rzeczywistych krawędzi
siatki; wilgoć i lokalny decal błota ograniczono do niskich partii stroju.
Trim szwów przypisano wyłącznie istniejącym krawędziom kaftana i klinom plecaka.

UV są stabilne względem pozy spoczynkowej: V ma okres 0,32 m, U całkowitą liczbę
powtórzeń wokół wykroju (dla płaszcza cztery). Plecak używa projekcji YZ,
posłanie cylindra wzdłuż Y; stal mapowania wzdłuż rzeczywistej głowni.
To kontrolowane mapowanie robocze, nie pełny produkcyjny unwrap każdego wykroju.

**Plecak i posłanie.** Dodano klinowe szwy, kieszenie, szelki prowadzone przez
barki do korpusu, miękkie zagniecenie klapy i obrzeże płótna. Rozróżniono
skórę plecaka i płótno posłania. Drobna bezwładność jest zapisana w kluczach
kształtu; nie ma symulacji fizyki luźnego ładunku.

**Głowa.** Po uwadze autora zmieniono gładką krótką powłokę na nieregularne
pasma grzywki, przy uszach i karku, z drobnymi włóknami przy nasadzie. Zarost
przeniesiono z błędnie wybranej wysokości nosa na policzki, żuchwę i podbródek;
dodano wąs i przejście gęstości. Poprawiono osadzenie gałek i tęczówek
wewnątrz oczodołów oraz łuki brwi. To interpretacja fryzury z planszy 17,
nie identyczna twarz z ilustracji. Palce zachowują istniejący model i chwyt;
nie dodano osobnego rigu palców ani animacji twarzy.

**Ruch.** Zachowano `spoczynek` i `chod`. Zmieniono bob i kołysanie miednicy,
przeciwskręt klatki, stabilizację głowy i opóźnienie swobodnego ramienia.
Stopa przechodzi z podparcia piętą do wybicia palcem. Płaszcz i ładunek mają
niewielkie, opóźnione klucze wtórne. Podłoże w podglądzie przesuwa się z
prędkością zgodną z cyklem; siatka ma okres pozwalający zapętlić ruch bez skoku.
To animacja kluczowana, bez mocapu i symulacji tkaniny.

## Broń — propozycja i otwarta decyzja

Głownia nadal ma 0,70 m długości i 0,044 m szerokości. Nie powiększono jej do
licznika pikseli. Dodano fizyczną fazę szlifu 0,8 mm i osobny materiał stali.
Wypróbowano niższe niesienie na zewnątrz, a następnie bardziej zrównoważone
niesienie przy biodrze: dłoń około (0,01; −0,40; 1,07) m, kierunek ostrza
(0,40; −0,40; −0,82), znormalizowany. Broń i palce obracano wspólnie wokół
nadgarstka. Wymiana pozy ma poprawić odcięcie od ciała, nie tylko maskę.

Decyzja, czy podczas eksploracji miecz jest stale dobyty, **pozostaje otwarta**.
Osobny podgląd odkłada tę samą geometrię do istniejącej pochwy. Nie jest to
ukończona akcja chowania miecza ani gotowy wariant swobodnego ruchu dłoni.
Nie włączono go do atlasów bazowych i nie zapisano na stałe w modelu.

## Kontrakt i kompozycja

| Parametr | Wynik |
|---|---|
| Klatka / alfa | 192×192 RGBA, premultiplikowane zmniejszenie z 384×384 |
| Kotwica | (96, 158.353829), bez przesuwania klatek |
| Kierunki | S, SW, W, NW, N, NE, E, SE; osiem obrotów, bez odbić |
| Kamera / skala | ortograficzna 30°, kadr 3,2 m, 60 px/m; anatomia 1,8 m |
| Spoczynek | 8×400 ms, cykl 3,2 s |
| Chód | 12×80 ms, cykl 0,96 s; 0,9027777778 m/s |
| Atlas spoczynku / chodu | 1536×1536 / 2304×1536; kolumny = fazy, wiersze = kierunki |
| Cień | oddzielny shadow catcher; kompatybilny eksport z cieniem w klatce zachowany |

Żaden parametr globalnego kontraktu gry nie został zmieniony. Objętość włosów
jest geometrią fryzury, nie zmianą skali całego bohatera. Ciepła pochodnia jest
osobnym renderem, nie elementem wszystkich klatek bazowych.

Planszę 17 pobrano z `main` (`7ce5c4b`), materiały z `c6c1a67` i `ff74eb7`
na wskazanej gałęzi, bez zmiany `main` i cudzych gałęzi. Kompozyty sceny przy
wozie są **ilustracją koncepcyjną, nie działającą sceną gry**. Tła nie skalowano;
przyjęto lokalnie 60 px/m przy kotwicy (590,810), ponieważ ilustracja nie ma
pewnej skali świata. Sprite zachowuje natywne wymiary, również w wycinkach.

## Źródła, pochodzenie, ochrona

`source/bohater.blend` jest nadrzędnym edytowalnym źródłem, z zapakowanymi PNG
i akcjami. Eksport nie wywołuje generatora modelu ani recept dopracowania,
nie zapisuje `.blend`. Walidacja ruchu czyta rzeczywiste zapisane akcje zamiast
przywracać pozy proceduralne. Ręcznie poprawione klucze nie są nadpisywane.
Archiwalny bootstrap wymaga nowego pliku i odmawia nadpisania źródła artystycznego.
Historia i manifesty odróżniają kolejne jawne pasy edycji od wygenerowanych wyników.

Anatomia i dane rigu MakeHuman są przypięte do
`a8bc2d54ff0ac92e78ff71431b1023eda42bf482`, CC0-1.0; licencja i SHA zachowane.
54 dostarczone PNG sprawdzono względem manifestów Git blob. Biblioteka opisuje
je jako autorskie obrazy proceduralne bez stocku; nie są pomiarowymi materiałami
PBR i nie przypisujemy im licencji CC0 danych MakeHuman. Nie dodano zasobów
zewnętrznych o niejasnym pochodzeniu.

## Ograniczenia wymagające dalszej oceny

Wygląd nadal jest bardziej stylizowany i prostszy niż ilustracja. Nasada włosów
i drobne pasma mogą wymagać kolejnego groomingu; głowa jest neutralną bazą,
a nie wyrzeźbionym portretem mężczyzny z planszy. Nie deklarujemy poziomu
fotorealistycznego konceptu. Większość mikrofaktury i szczegółów twarzy zanika
w skali gry, dlatego do oceny są również widoki 1:1.

Plecak ma roboczą projekcję UV, która może rozciągać detal na bocznych ściankach.
Nie wykonano pomiarowej kontroli każdego szwu UV ani testu we wszystkich filtrach
nieustalonego silnika. Nie ma dynamicznej tkaniny, pełnej animacji palców,
ciągłej kontroli kolizji ani sprawdzenia wszystkich samoprzecięć. Gęste próbki
szkieletu nie stanowią dowodu naturalności animacji.

Wcześniejszy test powierzchni podeszwy wykazał do około 3,7 mm zagłębienia przy
wybiciu (około 0,22 px w rzucie poziomym); końcowy raport zachowuje rzeczywisty
pomiar, oddzielnie od idealnego kontaktu pivotu. To ograniczenie obecnej siatki
buta, nie „pełna poprawność kontaktu” na podstawie samego wzoru.

## Wykonane kontrole — pełny eksport rewizji 08

Źródło: SHA-256 `bf6a8221718b7484565f562a3fb731ec6f224414ff6bf4a28598b4d7178be7f3`.

- 160 klatek bazowych: RGBA, przezroczyste granice, marginesy i zgodne hashe postaci/cienia.
- 28 dodatkowych par postać/cień: chłodne i ciepłe światło, pochwa oraz duże rendery przed/po; pochodzenie zweryfikowane oddzielnie.
- 242 próbki zapisanych akcji i 22 klucze: największa szczelina stawów 0,000000400 m, błąd długości kości 0,000000412 m; błąd zamknięcia pętli 0.
- Kotwica z kamery: (95,999960; 158,353849) px; osiem poprawnych projekcji kierunków.
- 13 par podparcia: największy błąd kompensacji ruchu z rzeczywistych landmarków stopy 0,000000246 m.
- Ponowny render z zapisanego `.blend`: identyczne dekodowane piksele RGBA dla spoczynku S0.
- Izolowana naprawa uszkodzonej klatki: identyczne piksele postaci i cienia; odrzucenie cache innego źródła; wznowienie pełnego zestawu 160/160 bez renderowania.
- 160 komórek atlasu kompatybilnego zgodnych z kompozycją osobnej postaci i cienia; czasy GIF/WebP odczytane z gotowych animacji.
- Chromium: załadowano osiem atlasów; canvas 1:1, pauza, zmiana klatek i odtwarzanie, bez błędów JavaScript.
- BVH: 20 póz, ostrze wobec siedmiu wskazanych powierzchni oraz dolny płaszcz wobec spodni — nie wykryto przecięć w tym zakresie. Nie badano pełnych objętości, wszystkich dodatków ani wszystkich subklatek. Minimum powierzchni podeszwy względem z=0: −0,003733 m.

**Pełna kontrola broni wykazała regresję pozy:** W, fazy chodu **4–7** mają
0 widocznych pikseli broni. NW jest słaby zwłaszcza w fazie 2 (5 px),
w fazach 1/3 jest 6 px. N ma 78–92 px w chodzie, lecz poprawa N nie rekompensuje
regresji W. Tej pozy nie uznajemy za rozwiązanie czytelności ani za gotową do
integracji. Osiem kierunków i podglądy wszystkich faz pokazują problem jawnie.
Drugi kandydat poprawiał W (minimum 36 px), ale pogarszał NW (2 px); również nie
został przyjęty. Po nowej dyspozycji autora prace skupiają się na detalach renderu,
a rozstrzygnięcie pozy pozostaje otwarte.

Dane maszynowe: `previews/*validation.json`, `technical-report.json`.
Nowy statyczny pass detali jest osobno w `source/bohater_detale.blend` i ma
własny manifest; nie przypisujemy mu powyższych wyników animacji rewizji 08.
