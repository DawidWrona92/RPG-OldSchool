# Welesza — bezszwowy świat: kontrakt techniczny v0.1

> **PROPOZYCJA, nie implementacja.** Działa niezależnie od wyboru silnika 2D/3D. Nie wybiera SDF, Blendera, atlasów ani pipeline'u grafiki.

## 1. Co znaczy „bez ekranów ładowania”

- Bohater nie przechodzi do innej sceny przy bramie, na trakcie, w obozie, w ruinach ani schodząc do komory.
- Silnik może wczytywać i usuwać zasoby **asynchronicznie**, zanim znajdą się w kadrze; gracz nie widzi paska ładowania ani czarnego ekranu maskującego zmianę mapy.
- Stany zadań, bossów i przedmiotów trwają niezależnie od tego, czy sektor jest w pamięci.
- Możliwe krótkie fabularne przejścia czasu (nocleg) nie mogą zastępować ładowania przy zwykłym chodzeniu.
- Zewnętrzna dolina ma jeden globalny układ współrzędnych; wysokość (`z`) jest częścią tego samego świata.

## 2. Dwie skale chunków — nie mylić pojęć

| Skala | Rozmiar | Zadanie | Status |
|---|---|---|---|
| Makrosektor S00–S23 | prostokąt 6×6 komórek planu, 12 sztuk | odpowiedzialność level designera, karta biomu, plan produkcji | propozycja |
| Komórka streamingu | 1×1 kratka abstrakcyjnej siatki, 24×18 = 432 adresy | dane terenu, kolizji, AI i dekoracji | podział logiczny do prototypu |

**Nie przyjmujemy jeszcze wymiarów w metrach.** Pomiary D (średnica postaci), B (obrys bossa), U (pełen unik), A (zasięg ataku), V (widok kamery) będą wykonane w grywalnym prototypie. Dopiero wtedy dobierzemy wymiar komórki i promień strumieniowania. Punkty JSON są pozycjami na planie, nie zatwierdzonymi współrzędnymi gameplayu.

## 3. Minimalny przepływ strumieniowania

1. **Always-on:** stan kampanii, postaci, rozliczenia jednorazowych zadań, zajętości drzwi, pokonanych bossów i zasobów; mała warstwa danych niezależna od sceny.
2. **Active:** fizyka, nawigacja, animacje i pełne AI w komórkach przy bohaterze oraz w aktywnej walce.
3. **Warm:** sąsiednie komórki przygotowane z wyprzedzeniem; niezależnie od kierunku i możliwego uniku.
4. **Visible LOD:** dalsze drzewa, skały, palisada i światło jako tańsze reprezentacje, aby nie widać było wyskakiwania.
5. **Dormant:** poza obszarem aktywnym zapisane są niezmienne identyfikatory, flagi, stany przeciwników, przedmiotów i obiektów; bez pełnej symulacji, jeśli nie jest potrzebna.

Bieżący aktywny obszar powinien obejmować kamerę, dystans ruchu podczas wczytania i dodatkowy margines na pełen unik U. Ładowanie wzdłuż przewidywanego kierunku ruchu jest dodatkiem, a nie zamiennikiem pełnego pierścienia bezpieczeństwa.

## 4. Granice komórek i ciągłość systemów

- **Nawigacja:** wspólny graf portali sektorów; komórki mają zapisane połączenia przejść, nie domyślają się ich ze sprite'a. Szwów navmesha / siatki nawigacyjnej nie można wykorzystywać jako niewidzialnych ścian.
- **Kolizje:** obiekty przecinające granicę komórki mają jednego właściciela logicznego i instancję kontaktową widoczną dla obu stron. Nie duplikujemy pickupów.
- **AI:** podczas aktywnej walki gracz i przeciwnik przypinają (pin) komórki wymagane do wykonania akcji i wycofania. AI nie może zniknąć przy przekroczeniu linii sektora.
- **Pociski i zasięgi:** obliczane w globalnym świecie; nie znikają w szwie. Osłony, np. wóz i stos drewna, blokują również linię strzału.
- **Audio:** woda, las, pochodnie i głosy przechodzą przez płynny crossfade strefowy, bez nagłego restartu pętli na granicy.
- **Oświetlenie:** subtelne przejście wolumetryczne, żar pochodni bez zmiany globalnego modelu światła w momencie zmiany sektora.
- **Roślinność i dachy:** wysoka korona, dach albo ściana przed kamerą staje się przezroczysta bądź otwierana warstwowo, bez ujawniania podłoża przez błędną maskę.

## 5. Wnętrza i komora pod ziemią

- Gospoda, kuźnia i strażnica osady w pierwszej wersji mają zewnętrzne bryły i interakcje w progu; wnętrza dopiero jeśli służą zadaniom.
- Jeśli wnętrze jest grywalne, leży fizycznie za drzwiami tej samej budowli. Dach przygasa / znika warstwowo, gdy kamera ma przecięcie z bohaterem.
- Komora latarni leży na poziomie `z<0` w tym samym globalnym świecie. Dochodzi się schodami od ruin; geometria wierzchnia musi przysłonić otoczenie komory z zewnątrz, ale odsłonić ją podczas zejścia.
- **Nie używamy teleportu dla ukrycia innego levelu.** Każdy podziemny zakręt ma geometrię, nie czarną planszę.

## 6. Fabularna anomalia i odsłonięty trakt

- **Pętla przy wozie:** dwie różne, ciągłe ścieżki zataczają rzeczywisty łuk, a druga wraca na ten sam plac pod innym kątem. Z perspektywy gracza daje poczucie dezorientacji; znak na drzewie i wóz pozostają tymi samymi obiektami.
- Ten kompromis **nie wyjaśnia** nadprzyrodzoności fabularnej. Jeśli autor zechce prawdziwej niemożliwej geometrii, opracować to jako osobny efekt z nieprzerwanym obrazem i bez utraty stanu, nie zakładać potajemnego teleportu.
- **Latarnia:** fizyczny trakt jest w świecie od początku, lecz przed `village_lamp_lit` nie ma dostępnego przejścia (korzenie, skarpa, ciemna mgła). Gdy latarnia zostaje zapalona w osadzie, bramka udostępnia ścieżkę; bez podmieniania całej lokacji w kadrze gracza.
- **Skrót obozu:** początkowo zamknięty od strony rozstaju; otwierany na miejscu, od obozu. Potem obie strony są fizycznie drożne.

## 7. Savegame i spójność odległych sektorów

Każdy trwały obiekt ma `world_id`, `owner_cell`, `state_version`. Odmienny wygląd tego samego obiektu po odwrocie wynika z flag, nie ze spawnów nowej kopii. Zachować:

- Jednorazowe pakunki, księgę i rozliczenie zadania.
- Stan trzech słupów niezależnie od kolejności oglądania.
- Ukończenie walki z Dźwigaczem + lampę jako jeden spójny wynik zapisu.
- Wspólną latarnię Niemiru i flagę nowego traktu.
- Otwarcie skrótu obozowego.
- Pokonanie Stróża i dostępność suchej drogi.
- Wrogów pokonanych na stałe oraz wrogów żywych w stanie sprzed wyłączenia sektora (zgodnie z regułami zapisu).

## 8. Zakres testów wydajności i QA

To **cele do pomiaru, nie uzyskane wyniki**:

1. Przejście brama→rozstaj→wóz, bez wstrzymania sterowania.
2. Bieg / seria uników przez granicę 4 komórek; brak pustej ziemi, zanikających kolizji i pojawiających się obiektów.
3. Walka przeciwnika na szwie; pocisk trafia prawidłowo w osłonę po drugiej stronie granicy.
4. Szybki nawrót przy skrócie; brak podwójnych przeciwników i powtórnie zebranych pakunków.
5. Zejście do komory i powrót schodami; nie pojawia się „obca” scena.
6. Zapis/odczyt tuż przed i po zgaszeniu/włączeniu flag; brak utraty widoczności traktu.
7. Po pokonaniu bossa, oddaleniu się o wiele sektorów i powrocie: poprawna trwałość stanu.
8. Zmiana kamery i widoczności dachów podczas płynnego przejścia przez bramę.
9. Profilowanie czasu klatki i skoków alokacji w chwili doczytu. Wstępne aspiracje: 60 FPS na docelowym PC, bez zauważalnych pauz przy granicach — wartości do zatwierdzenia po pomiarach sprzętu.
10. Test obciążeniowy niska pamięć i przerwanie pobierania danych; bez cichej utraty savegame.

Żaden z tych testów nie został jeszcze wykonany w silniku gry.