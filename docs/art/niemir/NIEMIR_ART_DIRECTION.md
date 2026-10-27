# WELESZA / NIEMIR
## Przewodnik artystyczny i plan produkcji środowiska

**Wersja:** 1.2 · **Data:** 27 października 2026 · **Status:** kierunek artystyczny uzgodniony z autorem; technologia grafiki ustalona w [kontrakcie renderu](../KONTRAKT-RENDERU.md); rozmieszczenie szczegółowe i parametry gry do walidacji  
**Zakres:** osada Niemir, jej bezpośrednie otoczenie, architektura, materiały, oświetlenie, zestaw assetów i kontrola jakości.  
**Odbiorcy:** art director, concept artist, environment artist, animator, programista silnika, projektant poziomów oraz agenci LLM współpracujący nad Weleszą.

> **Zasada nadrzędna:** Niemir jest prawdziwym, zamieszkanym miejscem, które od dawna żyje w cieniu lasu i strachu. Groza wynika z funkcji, historii oraz nieobecności — nie z nieustannego dekorowania wszystkiego makabrą i magicznymi efektami.

---

## 01. Status decyzji i granice dokumentu

Ten dokument przekłada zaakceptowaną koncepcję fabularną Weleszy i uzgodniony kierunek estetyczny Niemiru na praktyczny brief dla wykonawców. Mówi, **co** ma być widać; **jak** to renderować, ustala [kontrakt renderu](../KONTRAKT-RENDERU.md). **Nie** zatwierdza silnika gry, konkretnych hitboxów, metrycznej skali mapy, ostatecznej geometrii budynków ani historycznego wyjaśnienia tajemnicy strażnic.

- **[KANON]** Fakty z zaakceptowanej fabuły `docs/demo-fabula.md`: funkcje osady, jej izolacja, skała i źródło, palisada, ludzie, zabobony, brak pól i główny przebieg demo.
- **[KIERUNEK ZATWIERDZONY]** Surowa, ciasna, użytkowa osada; izometryczna kamera gry; stonowana paleta, wilgoć i chłodny las, małe lokalne źródła ciepła. Autor zaakceptował tę wizję do dalszego rozwijania.
- **[PROPOZYCJA]** Dokładny podział działek, orientacja obiektów, wzorce architektury, położenie rekwizytów i warianty iluminacji. Można je zmienić po ocenie panoramy ART-01.
- **[DECYZJA AUTORA]** Technologia grafiki: sprite'y i otoczenie to prerender w Blenderze 4.3 (Cycles) według [kontraktu renderu](../KONTRAKT-RENDERU.md) — wspólna kamera ortograficzna 30°, skala 60 px/m, zestaw świateł, kierunki, kotwica i eksport.
- **[DO TESTU]** Zachowanie kamery w działającej grze, zasłanianie postaci, przechodniość, nawigacja, wymiary obiektów i import atlasów do silnika, którego jeszcze nie wybrano.

Przy konflikcie źródeł obowiązuje najpierw decyzja autora, potem zatwierdzona fabuła; zapisy w `docs/pakiet-04-mapa.md` są propozycją projektu przestrzeni. Nowe obrazy nie mogą samodzielnie ustanawiać faktów fabularnych.

## 02. Tożsamość wizualna: „bezpieczne miejsce pod naciskiem lasu”

**Cel emocjonalny:** pierwsze spojrzenie ma obiecywać schronienie; drugie ma ujawnić ślady lęku i niedostatku. Nocą z mroku wyłaniają się tylko brama i kilka okien. Za dnia widoczna jest praca, zużycie i prowizoryczne naprawy. Po powrocie z wyprawy osada ma działać jako czytelna, znajoma baza, nie jako drugi labirynt.

**Słowa-klucze:** wilgoć, ciężar, drewno, mech, zacieki, naprawy, cisza, zawieszenie, niedopowiedzenie, obyczaj, schronienie.

**Czego unikamy:** dużego miasta, monumentalnych murów, rycerskiego zamku, pól i farm za płotem, barwnego jarmarku, gotyckiej katedry, „strasznych” trupów w każdym kadrze, neonowych run, nadmiaru świecących przedmiotów, dekoracji niepowiązanych z zajęciem mieszkańców. Słowiański klimat wynika z obyczajów, nazewnictwa, materiałów i funkcji; powtarzany na wszystkim jeden ornament byłby sztuczny.

### Rozróżnienie warstw

1. **Funkcja przed dekoracją.** Budynek i rekwizyt powinny zdradzać, co robi mieszkaniec: kuźnia naprawia, gospoda karmi, zielarka suszy rośliny, strażnica pilnuje wspólnego ognia.
2. **Narracja przez brak.** Puste miejsce przy stole, zamknięta stajenka, niedziałająca waga, buty lub pozostałości zapasów mają mówić więcej niż efektowne sceny grozy.
3. **Jedna czytelna hierarchia.** Brama — plac i źródło — strażnica i gospoda. Detale nie mogą konkurować z tymi punktami.
4. **Las jako ściana świata.** Drzewa, skały i gęsty podszyt domykają kadr; żadnej wielkiej panoramy krainy za palisadą.

## 03. Krajobraz, światło i paleta

### Materiały i ich rola

| Materiał | Wygląd i zastosowanie | Uwaga wykonawcza |
|---|---|---|
| Stare drewno | Zgaszony brąz i szarość; belki, dachy, płoty, rusztowania | Różna wilgotność i naprawy; nie kopiować identycznej deski w każdym domu |
| Mokry kamień | Chłodne szarozielone płaszczyzny, porosty; fundamenty, skała, źródło | Skała źródlana jest czytelnym landmarkiem |
| Leśna roślinność | Głęboka zieleń, oliwka, brudne zielenie; mchy, paprocie, świerki | Unikać fluorescencji i jednolitej zielonej plamy |
| Żelazo i skóra | Zmatowiałe, zużyte; okuwanie bramy, kuźnia, uprzęże | Funkcjonalne detale, nie zdobiona zbrojownia |
| Len i wełna | Zgaszone beże, popiel, brunatne szarości; tkaniny, ubiory, płachty | Skromne i wilgotne, nie jaskrawe stroje świąteczne |
| Ogień i olej | Małe, ciepłe plamy bursztynu; pochodnie, paleniska, wspólna latarnia | Rzadkie światło jest nagrodą wzrokową, nie wszędobylską dekoracją |

**Próbki barw do konceptów, NIE wymagana paleta techniczna:** drewno `#423D31`, kamień `#62685B`, zieleń `#454A36`, bursztyn `#B47837`, błoto `#3F3931`, mgła `#72766F`. Bazowe zarządzanie kolorem (AgX, ekspozycja, światła) ustala kontrakt renderu; ostateczny grading kolorów zapadnie po teście w silniku.

### Reguły iluminacji

- Światło ogólne: chłodne, rozproszone, szare niebo. Zewnętrzny las ciemniejszy niż wnętrze osady, lecz nadal czytelny.
- Ogień: lokalny, ciepły, selektywny (brama, dom gościnny, kuźnia, strażnica). Nie rozstawiać latarni przy każdym płocie.
- Wspólna latarnia jest przedmiotem fabularnym; jej zapalenie ma być wydarzeniem inscenizacyjnym, nie kolorową eksplozją magii.
- Mgła: wzmacnia głębię i izolację; nie może zasłonić drzwi, ścieżki, interaktywnego NPC ani zapowiedzi ataku poza osadą.
- Noc, poranek i finał to **warianty scen**, a nie automatycznie zatwierdzony symulator pory dnia.

## 04. Układ osady i nawigacja

**[KANON]** Niemir leży przy skalnym źródle pośród lasu; ma kilkanaście domów, kuźnię, dom gościnny, skład i dawną strażnicę. **[PROPOZYCJA PAKIETU 04]** Jedna główna brama, krótka pętla domów przy palisadzie, dziedziniec ćwiczeń oraz plac u źródła. We wnętrzu palisady nie projektujemy obowiązkowych starć.

### Proponowana topologia, bez kierunków geograficznych

```text
                        [SKAŁA + ŹRÓDŁO]
                              |
           [DOMY] --------- [PLAC] -------- [STRAŻNICA / LAMPA]
             |                |                       |
             |         [DOM GOŚCINNY]                 |
             +--------------- + ---------------------+
                              |
                   [KUŹNIA] [ZIELARKA]
                              |
                     [DZIEDZINIEC]
                              |
                         [BRAMA]
                              |
                     [ROZSTAJ / LAS]
```

Ten schemat definiuje **relacje funkcjonalne**, nie odległości i nie ostateczne usytuowanie brył. W panoramie ART-01 drzewa, skała i palisada mają wyglądać organicznie. Teren jest nierówny i przez lata narastały na nim dostawki. Nie planujemy siatki równych ulic ani osi symetrii.

**Pierwsza ścieżka gracza:** brama i Żegota → widoczny plac i źródło → dom gościnny Miłki. Rano: dziedziniec i ćwiczenie → brama → rozstaj i las. Po kolejnych wyprawach strażnica i usługi stają się naturalnymi celami powrotu.

**Warunki czytelności:** gracz rozpoznaje jedyne główne wyjście; źródło i wieżyczka strażnicy odróżniają się sylwetką; kuźnia i zielarka mają osobne budynki; drogi gospodarcze wracają ku placowi. Ścieżka poza palisadą nie staje się drugim wyjściem doliny.

## 05. Karty miejsc i briefy produkcyjne

### NMR-01 — Brama i palisada

**Funkcja:** granica bezpieczeństwa, pierwszy i powracający landmark. **Postać:** Żegota. **Sylwetka:** grube pionowe pale, ciężkie skrzydła, prosty daszek, niewielki punkt światła. **Motywy kanoniczne:** rzemienie, żelazne obręcze, ptasie kości, poczerniałe zioła pod daszkiem; kontrola dłoni przybysza. **Ograniczenia:** żadnych baszt zamku, drugiej monumentalnej bramy czy niepotwierdzonej ikonografii magicznej. Obszar przed bramą ma pozwalać odczytać kierunek ruchu bez strzałki na ekranie.

### NMR-02 — Dziedziniec ćwiczeń

**Funkcja:** bezpieczna nauka ruchu, ataku i uniku. **Postać:** Żegota podczas treningu. Ubita ziemia, miejsce na pal treningowy, proste bariery na obrzeżach. Środek pozostaje otwarty. Szczegółowe wymiary i odległość uniku `U` mierzymy w prototypie; dekoracje nie mogą kończyć pierwszego odskoku na drzewie.

### NMR-03 — Plac przy źródle

**Funkcja:** centrum orientacji i handlu; naturalny węzeł codzienności. **Postacie:** Domarad, Sambor, Milorad. Skała, wypływająca woda, drewniane koryta, wydeptane przejścia, ślady pod kopytami, waga towarowa i ograniczone miejsce rozładunku. **Nie** monumentalny rynek z szeregiem straganów. Źródło widoczne jako stały punkt, także kiedy ogień jest wygaszony.

### NMR-04 — Dom gościnny

**Funkcja:** pierwsze schronienie, nocleg i powrót po wyprawie. **Postacie:** Miłka, Sulir; Czcibor po odnalezieniu wg propozycji mapy. Dłuższy użytkowy dom z czytelnym wejściem, ławą, opałem, przygaszonymi oknami; wewnątrz wspólny ogień i osobna zamknięta izba związana z zadaniem „Trzeci przy stole”. Najcieplejsze wizualnie miejsce, ale nadal biedne i zużyte.

### NMR-05 — Kuźnia Radosta

**Funkcja:** naprawa i handel bronią. Otwarta część warsztatu; kowadło, miech, naczynie na wodę, stojaki z odzyskiwanym żelazem, zapas węgla drzewnego. Ciepły punkt żaru. Miejsce pokazuje oszczędność materiału, nie bogatą produkcję zbroi. Radost bada też uszkodzony słup z lasu.

### NMR-06 — Chata zielarki Dobrawy

**Funkcja:** lekarstwa, wiedza o lesie i miejscowych obyczajach. Osobny mniejszy dom przy strefie usług. Suszone rośliny, kosze, gliniane naczynia, osłonięta wnęka na zapasy. Zioła wynikają z pracy, a nie jednolitego mistycznego ornamentu. Chata nie musi świecić niczym sklep z magią.

### NMR-07 — Strażnica osady

**Funkcja:** przechowywanie wspólnej latarni i ważny powrót fabularny. **Postać:** Wszebora. Niska pionowa sylwetka: stary kamienny fundament, lekka drewniana góra, częste naprawy; wyraźnie inna niż ciężkie, niskie ruiny leśne z piecem Dźwigacza. Nie dopowiadać wieku, budowniczych, połączenia podziemnego ani genezy lampy. Dwa stany prezentacji: zwykła wizyta i zapalenie zdobytej latarni.

### NMR-08 — Domy przy palisadzie

**Funkcja:** skala życia osady, żałoba, prywatność. **Postacie i skojarzenia:** Dzierżka — obrzęd i buty; Mściwuj — zapiski i obowiązki grabarza; Borzęta — węgiel i zapasy, jeśli lokalizacja potwierdzona. Warianty dachów, drewnianych łączeń, dostawionych komórek, zamkniętych okiennic i stosów opału. Nie budować kilkunastu identycznych interaktywnych wnętrz. Wewnętrzne historie domów wymagają odrębnego zatwierdzenia.

### NMR-09 — Skład kupiecki i rekwizyty

**Funkcja:** dawne szlaki handlowe i obecny niedostatek. Zamknięte magazyny, waga, liny, puste zagrody dla zwierząt jucznych, nieliczne pakunki, używane wozy. Ślady transportu są starsze niż ostatni kryzys; scenografia nie zdradza tajemnicy księgi przewozowej.

### NMR-10 — Obrzeża i las

**Funkcja:** odizolowanie osady i czytelna droga wypraw. Gęste pnie, paprocie, kamienie, błoto, krótkie zejścia do wody. Brak pól. Korony zasłaniające ścieżkę powinny mieć regułę zanikania/przedniego przesłaniania w silniku. Obszary walki poza osadą wymagają osobnego blockoutu i kontroli czytelności ataków.

## 06. NPC i opowiadanie przez otoczenie

| Postać | Miejsce z dokumentów | Sygnał scenograficzny |
|---|---|---|
| Żegota | Brama / dziedziniec | Kontrola przejścia, ćwiczenia, ochrona przed lasem |
| Wszebora | Strażnica | Wspólna latarnia i pilnowanie rytuału |
| Miłka, Sulir | Dom gościnny | Nocleg, stół i milczenie o wozie |
| Domarad, Sambor, Milorad | Plac | Organizacja osady, handel, codzienna praca |
| Radost | Kuźnia | Naprawy zamiast wystawnych nowych wyrobów |
| Dobrawa | Chata zielarki | Zioła, lekarstwa, obyczaje |
| Dzierżka, Mściwuj, Borzęta | Domy i osada — lokalizacja robocza | Żałoba, zapiski, węglarstwo |
| Nawoja | Brama i przygotowanie wypraw — rozmieszczenie robocze | Wiedza o ścieżkach, tropy lasu |
| Czcibor | Leśne schronienie / później gospoda — propozycja | Zaginiony mieszkaniec, bez dopisywania nowej osoby |

To kierunki inscenizacyjne, nie ostateczna mapa harmonogramów NPC. Nie ustala się teraz pełnego cyklu dobowego ani nowych zależności fabularnych.

## 07. Cztery sceny dramaturgiczne osady

| Stan | Ton i światło | Element obowiązkowy | Zakaz |
|---|---|---|---|
| Prolog / pierwsza noc | Chłodny deszcz, nikłe ciepło bramy i gospody | Żegota, zamykane wejście, droga do Miłki | Pełne ujawnienie lasu i grozy |
| Poranek / przygotowania | Rozproszone chłodne światło; użytkowa codzienność | Dziedziniec, ruch do wozu, dostępne usługi | Tłoczny jarmark |
| Powrót z latarnią | Znacząca zmiana w strażnicy | Wszebora i wspólne źródło płomienia | Neonowe efekty i nowa kosmologia |
| Finał demo | Znajome miejsce z drobnymi zmianami zachowania | Pakowane wozy, część zamkniętych drzwi | Uroczysty festyn zwycięstwa |

Wskazane stany są briefem inscenizacyjnym. Nie przesądzają o real-time weather systemie czy o harmonogramie wszystkich mieszkańców.

## 08. Perspektywa, skala i czytelność świata

Ten rozdział określa **wrażenie wizualne i funkcjonalne**. Parametry techniczne — kamerę, skalę, światło, eksport i kontrolę jakości — wiążąco opisuje [kontrakt renderu](../KONTRAKT-RENDERU.md); przy sprzeczności pierwszeństwo ma kontrakt.

- **Perspektywa:** kamera ortograficzna 30° nad horyzontem, jak w klasycznym action RPG; ta sama dla postaci, budynków i przyrody.
- **Skala:** 60 px/m dla wszystkich obiektów; człowiek (ok. 1,8 m) ma ok. 105 px. Bohater ma naturalne proporcje względem drzwi, domów, drzew i drogi.
- **Światło:** jeden zestaw świateł z kontraktu, stały względem świata; chłodny las i lokalne bursztynowe źródła ciepła jako osobne warianty renderu, nigdy wpieczone w bazowy atlas.
- **Czytelność:** dachy i wysokie obiekty nie mogą trwale zasłaniać gracza, celów interakcji ani drogi.
- **Grywalność:** graficzny obraz kolizji, wejść i przejść wymaga weryfikacji w działającej scenie, nie tylko na ilustracji.

**Technologia jest ustalona:** prerender w Blenderze 4.3 (Cycles). Nadrzędnym źródłem każdego assetu jest edytowalny plik `.blend`; wzorcem technicznym jest bohater z gałęzi `vibe/sprite-bohater-codex`. Specyfikację renderu i eksportu zawiera wyłącznie [kontrakt renderu](../KONTRAKT-RENDERU.md) — ten przewodnik jej nie powtarza.

## 09. Biblioteka assetów i logika wariantów

| Rodzina | Warianty / podzespoły | Priorytet |
|---|---|---|
| Ziemia | ubita ziemia, błoto, koleiny, kałuża, kamień, trawa, ściółka | P0 |
| Brama/palisada | moduł prosty, narożnik, brama, daszek, braki/naprawy | P0 |
| Landmarki | skała i źródło, drewniane koryta, latarnia strażnicy | P0/P1 |
| Gospoda | bryła, dach, próg, wejście, ława, stos opału | P0 |
| Warsztaty | kuźnia, chata zielarki, narzędzia, zioła | P1 |
| Zabudowa | 3–4 bryły bazowe domów, dachy i dostawki | P1 |
| Handel | waga, beczki, skrzynie, wozy, worki, uprzęże | P1 |
| Natura | skały, świerki, drzewa liściaste, pnie, mech, podszyt | P1 |
| Efekty | dym, żar, ogień, woda, mgła, mokrość | P1/P2 |
| Wnętrza | tylko obszary konieczne dla rozmów i zadań | P2 |

**Zasada wariantów:** nie mnożymy budynków przez losową zmianę barwy; różnicujemy zużyciem, konstrukcją i rekwizytami. Każda rodzina ma własną kartę: wymiary świata, punkt zakotwiczenia, zasięg kolizji, warianty oświetlenia, warstwy, warianty i plik źródłowy `.blend`.

## 10. Plan produkcji i odpowiedzialność

### Faza I — Makieta i ART-01 [P0]

1. Zrobić plan 2D/topologię i bryłowy blockout 3D wszystkich stref bez dekoracji.
2. Wykonać `ART-01`: panorama Niemiru z kamery z kontraktu renderu (ortograficzna 30°) — nie malowana panorama z przypadkowych perspektyw.
3. Sprawdzić obowiązkowe punkty: jedna brama, palisada, skała ze źródłem, mały plac, strażnica, droga do domu gościnnego; bez pól i wielkiego miasta.
4. Przed zatwierdzeniem nie utrwalać proporcji i rozmieszczenia jedynie na podstawie efektowności obrazu.

### Faza II — Style frame i karta stylistyki [P0]

Dwa lub trzy warianty **identycznego kadru i układu** o różnej szczegółowości/teksturze. Wybrać poziom czytelności odpowiadający skali gry. Kamera, skala i bazowe światło są ustalone w kontrakcie; tu wybieramy paletę materiałów i sposób przejścia między chłodem lasu a ciepłem osady (warianty renderu).

### Faza III — Budynki wzorcowe [P0/P1]

Brama, gospoda, strażnica, kuźnia, zwykła chata. Każdy obiekt: bryła, sylwetka 1×, proporcja wobec postaci, materiał, światło, metadane oraz logiczna kolizja. Zatwierdzić wzorce przed masową produkcją zabudowy.

### Faza IV — Środowisko i modularność [P1]

Ziemia, palisada, roślinność, zabudowa wariantowa i rekwizyty. Zbudować bibliotekę ze spójnymi nazwami i identyfikatorami. Scena ma opowiadać przez praktyczne ślady życia, nie przez przypadkowe ozdoby.

### Faza V — Test grywalności [P0/P1]

Sprawdzić przechodniość, zasłanianie i relacje wysokości z postacią w naturalnej skali. Warunki: widoczny Żegota, wejście do gospody, możliwość treningu i powrotu z lasu. Import atlasów do silnika zostanie określony po wyborze silnika.

## 11. Rejestr prac

| ID | Wynik do odbioru | Priorytet | Status |
|---|---|---|---|
| NMR-01 | Plan izometryczny + ART-01 | P0 | do wykonania |
| NMR-02 | Brama i palisada | P0 | do wykonania |
| NMR-03 | Plac oraz źródło | P0 | do wykonania |
| NMR-04 | Gospoda i przejście od bramy | P0 | do wykonania |
| NMR-05 | Dziedziniec ćwiczeń | P0 | do wykonania |
| NMR-06 | Strażnica i wspólna latarnia | P1 | do wykonania |
| NMR-07 | Kuźnia i chata zielarki | P1 | do wykonania |
| NMR-08 | Modułowe domy | P1 | do wykonania |
| NMR-09 | Skład kupiecki i rekwizyty | P1 | do wykonania |
| NMR-10 | Las za palisadą | P1 | do wykonania |
| NMR-11 | Warianty światła i stanu osady | P2 | do wykonania |
| NMR-12 | Wnętrza wymagane zadaniami | P2 | do wykonania |

**P0** = element pierwszego grywalnego fragmentu, nie koniecznie finalny asset AAA; **P1** = pozostały rdzeń osady; **P2** = uzupełnienie po pomiarach i integracji.

## 12. Bramki jakości i definicja „gotowe”

Każdy obiekt ma przejść kolejno:

1. **Brief i kanon:** porównać z fabułą/mapą. Nie dopisywać samodzielnie historii.
2. **Sylwetka 1×:** rozpoznawalna funkcja budynku i wejście; także w ciemniejszym wariancie światła.
3. **Perspektywa i skala:** kamera, 60 px/m i kotwica zgodne z kontraktem renderu; czytelne proporcje bohatera względem świata.
4. **Spójność materiałów:** ten sam zestaw świateł z kontraktu, kontrast i poziom zużycia.
5. **Integracja techniczna:** lista kontrolna kontraktu renderu (kotwica, źródło `.blend`, metadane, brak przycinania) oraz kolizja i przesłanianie.
6. **Test sceny:** gracz wchodzi od bramy do gospody bez pomyłki, trafia na plac, poznaje strażnicę i może wrócić do lasu.

**Otwarte miary do prototypu:** D — średnica kolizji bohatera; B — obrys przeciwnika; U — pełny unik; A — zasięg ataku; V — widoczny obszar podłoża. Nie udawać sprawdzonych metrów, zanim te wartości powstaną w działającej grze.

**Pięć warunków akceptacji panoramy i osady:**

- Gracz bez minimapy znajduje bramę, plac i gospodę.
- Źródło i strażnica mają unikalne, czytelne sylwetki.
- Postacie mają wiarygodną skalę wobec drzwi i dachów.
- Detale nie przykrywają ważnych przejść, NPC i komunikatów walki.
- Cała scena ma wspólną temperaturę światła i poziom realizmu z docelowym wyglądem bohatera i przeciwników.

## 13. Zarządzanie współpracą i aktualizacją dokumentacji

- **Art direction:** jedna zatwierdzona karta stylu Niemiru; uwagi zapisujemy jako konkretne różnice względem tej karty, nie arbitralne zmiany palety w pojedynczych obiektach.
- **Role:** art director tworzy brief/recenzję; environment artist lub agent tworzy model `.blend` i render według kontraktu; level designer sprawdza układ oraz trasy; programista silnika waliduje formaty, kolizje i zasłanianie; autor zatwierdza nowe fakty fabularne i krytyczne zmiany kierunku.
- **Git:** osobne gałęzie do eksperymentów graficznych i implementacji; `main` jest źródłem dokumentacji świata, kierunku artystycznego i [kontraktu renderu](../KONTRAKT-RENDERU.md). Pliki `.blend`, skrypty i rendery zostają na gałęziach roboczych.
- **Źródło prawdy:** edytowalny Markdown na `main`, PDF jako publikacja do czytania. Zmiany zaczynamy od `.md`, po czym regenerujemy PDF. W PR zaznaczamy: kanon, zatwierdzony kierunek, propozycję lub test.
- **Sprawy otwarte:** finalny silnik i import atlasów, mierzalna skala mapy, ustalenie szczegółowych działek, zakres wnętrz, optymalizacja assetów oraz rozmiar klatek dużych obiektów (budynek wzorcowy wg kontraktu).

## 14. Pierwszy obraz referencyjny: ART-01

**Format pracy:** duża panorama z kamery gry (ortograficzna 30°, jak w kontrakcie renderu), pokazująca **całe wnętrze palisady i niewielki obrąbek lasu**. Kompozycja zgodna z planem przestrzennym; żadnych dodanych dla efektu monumentów, nowych bram lub pól. W kadrze muszą być czytelne: wejście, ciepłe światło, droga do gospody, źródło w skale, niewielki plac, strażnica oraz warsztaty.

**Materiał do oceny:** obraz pełny + ten sam obraz w zbliżeniu odpowiadającym grze + podgląd z nałożoną sylwetką człowieka w naturalnej skali. Osobno zaznaczyć hipotetyczne wejścia, kluczowe przejścia i miejsca zasłaniania. ART-01 jest **następnym etapem**, nie częścią już zatwierdzonego gotowego projektu mapy.

## 15. Źródła wewnętrzne

1. `docs/demo-fabula.md` — zaakceptowana koncepcja fabularna i mieszkańcy.
2. `docs/pakiet-04-mapa.md` — propozycja topologii osady, stref, orientacji i warunków prototypu.
3. `docs/pakiet-04-poczatek.md` — przebieg pierwszego wejścia, nocleg, trening i pierwsza wyprawa.
4. `docs/pakiet-04-obrazy.md` — brief ART-01–ART-07 oraz ograniczenia języka wizualnego.
5. `docs/pakiet-04-przeglad.md` i `docs/graphs/layout-demo.json` — kontrola zależności, nie walidacja geometrii.
6. `docs/koncepty/README.md` — biblioteka zatwierdzonych referencji wizualnych potworów, mieszkańców i otoczenia.
7. `docs/art/KONTRAKT-RENDERU.md` — wiążąca specyfikacja kamery, skali, światła, eksportu i kontroli jakości sprite'ów.

**Zasada końcowa:** Niemir nie musi wyglądać na wielki, by pozostał w pamięci. Musi być rozpoznawalny, prawdziwy, zamieszkany i na tyle niepokojący, żeby opuszczenie jego bramy było decyzją.