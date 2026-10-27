# Welesza — karty 12 sektorów świata (v0.1)

> **Status: propozycja do greyboxu i testów.** Układ to 4 kolumny × 3 rzędy, sektor 6×6 komórek planu. Granice sektorów są techniczne, nigdy fabularne.

## Indeks sektorów

| Sektor | Strefa | Najważniejszy obowiązek |
|---|---|---|
| **S00** | Zachodnia granica boru | Niegrywalne tło |
| **S01** | Niemir i skalne źródło | Niemir |
| **S02** | Północne ścieżki | Północne przedpole i korytarz zamkniętego skrótu |
| **S03** | Wschodni las i podejście | Górny skalny grzbiet i zaplecze leśnej strażnicy |
| **S10** | Zerwany most i wóz | Porzucony wóz, dwie drogi obejścia, urwany most i podmokły brzeg |
| **S11** | Rozstaj oraz cmentarne miejsce | Rozstaj pod drzewem, pamiętna pętla, cmentarne miejsce |
| **S12** | Kamienie i obóz | Kamienne drogi, pierwszy słup, obóz węglarzy i wejście do traktu |
| **S13** | Ruiny oraz finał | Ruiny, piec Dźwigacza, komora poniżej gruntu, finałowa arena Stróża |
| **S20** | Nieprzebyta skarpa i podmokłości | Południowo-zachodnie podmokłości — granica doliny |
| **S21** | Polana z pieśnią | Polana z pieśnią i boczna droga od trzech kamieni |
| **S22** | Sidła i jama Zbieracza | Ślady sideł, jama Zbieracza i drugi / trzeci słup |
| **S23** | Suchy szlak i granica doliny | Południowy skraj kamiennego traktu i odległe tło |

## S00: Zachodnia granica boru

**Rola:** Niegrywalne tło: gęsty bór i skaliste ograniczenie doliny.

**Geometria i styl:** Nie budować pustych kilometrów. Pnie i skały stopniowo zamykają trasę; podłoże zgaszone, bez fałszywych przejść..

**Walidacja:** Fizyczna granica zachodnia, bez drugiej bramy i skrótu do mostu..

**Punkty projektowe:** brak — dekoracyjne zamknięcie świata.


## S01: Niemir i skalne źródło

**Rola:** Niemir: źródło, palisada, domy, gospoda, strażnica, kuźnia i dziedziniec.

**Geometria i styl:** Jedna nieregularna polana, kamienna skała na skraju, niewielki plac. Drzwi usług i jedyna brama czytelne z głównego traktu. Bez walki w osadzie..

**Walidacja:** Test: od bramy do gospody i Wszebory bez zasłonięć; dachy reagują na kamerę; nie dodawać pól..

**Punkty projektowe:** `spring` (Źródło w skale), `watch_village` (Strażnica Niemiru), `houses` (Domy przy palisadzie), `inn` (Dom gościnny), `square` (Plac Niemiru), `services` (Kuźnia i zielarka), `training` (Dziedziniec ćwiczeń), `gate` (Brama Niemiru)


## S02: Północne ścieżki

**Rola:** Północne przedpole i korytarz zamkniętego skrótu.

**Geometria i styl:** Wyłącznie logiczne dojście do skrótu obóz→rozstaj. Gęsty las i skarpa tłumaczą niedostępność przed otwarciem zasuwy..

**Walidacja:** Test: bariera skrótu istnieje fizycznie i jest otwierana od strony obozu; bez przenosin postaci..

**Punkty projektowe:** `shelter` (Leśne schronienie)


## S03: Wschodni las i podejście

**Rola:** Górny skalny grzbiet i zaplecze leśnej strażnicy.

**Geometria i styl:** Ciężkie skały osłaniają tajemniczą bryłę ruin od północy, pozwalając zaplanować dyskretne zbliżenie od obozu..

**Walidacja:** Test: nic nie prowadzi z górnego skraju bezpośrednio do komory lub za Stróża..

**Punkty projektowe:** brak — dekoracyjne zamknięcie świata.


## S10: Zerwany most i wóz

**Rola:** Porzucony wóz, dwie drogi obejścia, urwany most i podmokły brzeg.

**Geometria i styl:** Prolog nocą bez obowiązkowej walki. Rankiem osobne telegraphy Psa i Powrotnika; koń, pakunki, księga. Szlak do mostu kończy się prawdziwą wyrwą..

**Walidacja:** Test: obie strony wozu drożne także dla wroga; most widoczny lecz nieprzekraczalny; powrót do bramy..

**Punkty projektowe:** `wagon` (Porzucony wóz), `bridge` (Brzeg i zerwany most), `loop_mark` (Oznaczone drzewo)


## S11: Rozstaj oraz cmentarne miejsce

**Rola:** Rozstaj pod drzewem, pamiętna pętla, cmentarne miejsce.

**Geometria i styl:** Przede wszystkim nawigacja: rozpoznawalna sylwetka drzewa, podążanie za ciepłym punktem osady, rozbieżne ścieżki. Pętla zatacza łuk i wraca do wozu od przeciwnej strony..

**Walidacja:** Test: anomalia bez wczytywania i teleportu; dojście do grobu nie blokuje głównego zadania..

**Punkty projektowe:** `crossroads` (Rozstaj pod pochylonym drzewem), `grave` (Cmentarne miejsce / buty), `pillar_whole` (Słup cały)


## S12: Kamienie i obóz

**Rola:** Kamienne drogi, pierwszy słup, obóz węglarzy i wejście do traktu.

**Geometria i styl:** Trzy odrębne kierunki badania kamieni, żadna kolejność obowiązkowa. W obozie stos drewna tworzy dwie flankujące trasy i osłonę przeciw Łucznikowi..

**Walidacja:** Test: bezpieczny odwrót z kamieni, aktywna najwyżej jedna skoordynowana grupa spotkania..

**Punkty projektowe:** `stones` (Węzeł kamiennych dróg), `pillar_fallen` (Słup powalony), `pillar_broken` (Słup rozbity), `camp` (Obóz węglarzy), `tools` (Narzędzia pod korą), `old_road` (Odsłonięty dawny trakt)


## S13: Ruiny oraz finał

**Rola:** Ruiny, piec Dźwigacza, komora poniżej gruntu, finałowa arena Stróża.

**Geometria i styl:** Fizyczny kompleks na jednym obszarze: dojście do Dźwigacza od obozu, zejście schodami do komory; oddzielona od niej droga do Stróża otwierana od kamieni po zapaleniu latarni..

**Walidacja:** Test: dwa boki pieca, brak nielegalnego obejścia finałowej bramki, zejście bez podmiany sceny..

**Punkty projektowe:** `ruins` (Leśna strażnica / Dźwigacz), `chamber` (Komora korzeni i latarni), `guardian` (Arena Stróża), `dry_road` (Suchy szlak (granica demo))


## S20: Nieprzebyta skarpa i podmokłości

**Rola:** Południowo-zachodnie podmokłości — granica doliny.

**Geometria i styl:** Atmosferyczne tło, martwe pnie i grząski grunt. Nie tworzymy tu questów bez powodu ani ukrytej drugiej trasy przez potok..

**Walidacja:** Test: naturalna granica terenu nie udaje szerokiej dostępnej drogi..

**Punkty projektowe:** brak — dekoracyjne zamknięcie świata.


## S21: Polana z pieśnią

**Rola:** Polana z pieśnią i boczna droga od trzech kamieni.

**Geometria i styl:** Wyraźnie poboczne spotkanie: Żałobnica + Powrotnik. Co najmniej dwa sposoby przerwania osłony, nagroda nie służy do odblokowania finału..

**Walidacja:** Test: czytelna zapowiedź i droga odwrotu, bez ostrzału poza widokiem..

**Punkty projektowe:** `song` (Polana z pieśnią)


## S22: Sidła i jama Zbieracza

**Rola:** Ślady sideł, jama Zbieracza i drugi / trzeci słup.

**Geometria i styl:** Znaki pułapek widoczne przed zejściem do jamy. Opcjonalny miniboss bez wpływu na uzyskanie lampy ani pokonanie Stróża..

**Walidacja:** Test: możliwość ominięcia bez walki i powrót na normalną trasę, żadnych ślepych zagłębień..

**Punkty projektowe:** `snares` (Ślady sideł), `collector` (Jama Zbieracza)


## S23: Suchy szlak i granica doliny

**Rola:** Południowy skraj kamiennego traktu i odległe tło.

**Geometria i styl:** Finał kończy się krótkim fragmentem suchej drogi; dalsza Welesza pozostaje nieopracowana i nie jest obiecywana jako grywalna..

**Walidacja:** Test: teren nie sugeruje nieskończonego świata za granicą demo, bez sztucznego ekranu ładowania..

**Punkty projektowe:** brak — dekoracyjne zamknięcie świata.

## Reguła granicy sektorów

Przekroczenie linii sektorów nie wyzwala teleportu, ściemnienia ekranu, pauzy animacji ani zmiany mapy. Każdy widoczny element przeciwległej strony jest wczytany lub zastąpiony poprawnym LOD jeszcze przed wejściem postaci. Aktor w walce może chwilowo wymusić obecność kilku sąsiednich sektorów.