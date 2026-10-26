# Welesza — podstawy mechanik

Data: 26 października 2026 r.
Status: zapis decyzji autora oraz osobno oznaczona propozycja do dalszego omówienia. Nie jest to gotowa specyfikacja implementacji ani zatwierdzony balans.

Powiązania: [fabuła demo](demo-fabula.md), [kolejność prac](przed-prototypem.md).

## 1. Decyzje autora

| Obszar | Ustalenie |
|---|---|
| Platforma | PC, mysz i klawiatura; możliwość późniejszego dodania obsługi pada. |
| Kamera i sterowanie | Jak w Diablo 2: perspektywa izometryczna i sterowanie myszą. Szczegółowe przypisanie nowych akcji wymaga ustalenia. |
| Tryb | Wyłącznie single player. |
| Walka | Mniejsza liczba groźnych przeciwników, uniki, precyzyjne wyczucie momentu ataku. |
| Zagrożenie | Inspiracja WFRP: walka przeciw trzem przeciwnikom naraz ma być bardzo niebezpieczna. Nie ustalono automatycznej porażki ani konkretnej szansy przeżycia. |
| Rozwój | Inspiracja WFRP; doświadczenie prowadzi do awansów, awanse dają Punkty Nauki (PN), a PN wydajemy u nauczycieli, na wzór Gothic. |
| Łupy | Rzadkie, bardzo cenne, dające wyraźne poczucie zwycięstwa i postępu. |
| Wyprawa | Przygotowanie w osadzie → eksploracja → starcie → nagroda → powrót po nagrodę lub naganę. |
| Zasoby | Wyprawa wymagająca; zasoby na wyczerpaniu około 90–95% jej przebiegu, aby skłaniać do kreatywności. Rodzaje zasobów i metoda oceny przebiegu wyprawy nie są jeszcze określone. |

WFRP stanowi inspirację dla zagrożenia i rozwoju. Nie zatwierdzono przeniesienia rzutów kośćmi, losowego pudłowania, profesji, trwałych ran ani śmierci permanentnej. Gothic stanowi inspirację dla roli nauczycieli, nie automatyczne przyjęcie wszystkich jego zasad.

## 2. Proponowane przełożenie na rozgrywkę — do omówienia

### Walka

Podstawą starcia może być odczytanie zamiaru przeciwnika, ustawienie się poza jego atakiem, wykorzystanie krótkiej okazji i świadome wycofanie. Trafienia oraz porażki powinny mieć czytelną przyczynę.

Proponuję, żeby przewaga liczebna była groźna przez oskrzydlanie i nakładanie się zagrożeń. Rozdzielenie grupy, wykorzystanie przejścia i rezygnacja ze starcia powinny być sposobami na poprawę sytuacji. Sama liczba przeciwników nie powinna uruchamiać sztucznego mnożnika obrażeń.

Do wyboru pozostaje, czy unik oznacza osobną akcję, czy przede wszystkim zejście z linii ataku ruchem postaci. Osobny unik wymaga ustalenia kierunku, ograniczenia użycia, możliwości przerwania ataku oraz ewentualnej nietykalności. Żadna z tych reguł nie jest obecnie przyjęta.

### Zasoby i końcówka wyprawy

Proponuję traktować 90–95% jako cel dla testowanej, typowej trasy przy określonym przygotowaniu. Świat nie powinien potajemnie odbierać zapasów ani dokładać przeciwników tylko dlatego, że gracz radzi sobie lepiej niż oczekiwano.

Przed balansowaniem należy określić, co się kończy: leczenie, amunicja, przedmioty pomocnicze czy inny zasób. Chwilowa zdolność do wykonania ataku lub uniku to inny problem niż zapasy na całą wyprawę.

Kreatywność wymaga działających alternatyw. Przykłady do rozważenia: obejście przeciwnika, rozdzielenie grupy, wykorzystanie terenu lub rezygnacja z dodatkowego łupu. Nie należy najpierw wymagać zużywalnego zasobu do każdej walki, a potem odbierać go przed obowiązkowym finałem bez innej drogi.

### Rozwój i nauczyciele

Potwierdzony przebieg rozwoju: zdobywanie doświadczenia → awans → otrzymanie PN → wydanie PN u nauczyciela. Otwarte pozostają źródła doświadczenia, tempo awansów, liczba PN, warunki dostępu do szkolenia, ewentualne dodatkowe opłaty i możliwość zmiany wcześniejszych wyborów.

Propozycja: nowe umiejętności powinny rozszerzać dostępne decyzje, a nie wyłącznie zwiększać liczby. Nie przydzielamy jeszcze nauczycieli do obsady; wymaga to zgodności z ich rolami fabularnymi.

### Łupy i nagrody

Proponuję rozróżnić istotną zdobycz zmieniającą wyposażenie od drobnych zapasów. Rzadkość cennej broni nie musi oznaczać, że eksploracja długo nie daje żadnego rezultatu: nagrodą mogą być również informacja, przejście lub dostęp do szkolenia.

To propozycja do omówienia, zwłaszcza w zakresie tego, czy rzadkie mają być wszystkie przedmioty, czy przede wszystkim ulepszenia wyposażenia. Nie wybrano systemu jakości, losowych właściwości ani tabel wypadania łupów.

## 3. Propozycja pętli na różnych skalach

Poniższe czasy są skalami opisu, nie zatwierdzonym czasem trwania walki lub demo.

| Skala | Cel gracza | Przeszkoda | Informacja zwrotna | Nagroda |
|---|---|---|---|---|
| Pojedyncza wymiana, około 30 sekund | Zadać obrażenia i uniknąć odpowiedzi | Zasięg ataku, pozycja, kolejny wróg | Zapowiedź ruchu, trafienie, reakcja przeciwnika | Bezpieczniejsza pozycja i postęp w starciu |
| Fragment wyprawy, około 5 minut | Przejść przez niebezpieczne miejsce | Grupa wrogów, teren, koszt użycia zapasów | Stan zasobów, odkryta droga, rozpoznane zagrożenie | Dostęp do celu, wskazówki lub zdobyczy |
| Sesja | Zrealizować cel i powrócić | Długość trasy, trudne starcia, ograniczone zapasy | Postęp zadania i stan przygotowania do powrotu | Rozliczenie zadania i odczuwalny postęp |
| Dłuższa gra | Rozwinąć bohatera i znaleźć drogę z Niemiru | Groźniejsze obszary i niepełna wiedza | Nowe możliwości, reakcje mieszkańców | Dostęp do dalszych zadań i rozwiązanie lokalnego problemu |

Awans zapewnia PN, a nauczyciele pozwalają je wydać. Pętla nie przesądza jeszcze, które działania nagradzane są doświadczeniem.

## 4. Ryzyka do sprawdzenia w prototypie

- Klikanie przeciwnika i ruch korzystające z tego samego przycisku mogą powodować niezamierzony atak zamiast ucieczki. Sprawdzić rozróżnienie intencji i reakcję na polecenie ruchu.
- Sprawdzić, czy sterowanie myszą pozwala wykonać precyzyjny unik w tłoku i przy przeszkodach.
- Nieograniczone wycofywanie i pojedynczy atak mogą stać się najlepszą odpowiedzią na każde zagrożenie. Testować zachowania przeciwników i teren, zanim doda się kolejne ograniczenia gracza.
- Ograniczenie leczenia połączone z trudną walką może zmienić końcówkę w powtarzanie beznadziejnej próby. Potrzebne są zrozumiałe warunki odwrotu, śmierci i ponownego podejścia.
- Rzadkie łupy mogą opóźnić poczucie postępu. Sprawdzić, czy gracz rozpoznaje wartość nagrody i czy może z niej skorzystać.
- Nauczyciel lub usługa nie mogą stać się przypadkowo niedostępne po naganie, jeśli bez nich nie da się kontynuować głównego zadania.

To analiza projektu, nie wyniki testów gry. Nie uruchomiono prototypu ani symulacji balansu.

## 5. Kolejne decyzje

Źródło PN zostało doprecyzowane przez autora. Następnie omówić wspólnie:

1. Wykonanie uniku i to, czy atak można przerwać.
2. Dostępne zasoby, leczenie oraz konsekwencje śmierci i odwrotu.
3. Pierwszy styl walki, zakres umiejętności i funkcję wyposażenia w demie.
4. Minimalny zestaw sytuacji bojowych do sprawdzenia sterowania i zagrożenia liczebnego.

Przed wyborem silnika ustalić prezentację 2D/3D oraz doświadczenie i zasoby zespołu. Przed implementacją zadań opracować ich stany i wewnętrzną logikę tajemnicy. Nie jest konieczne wcześniejsze rozpisanie całej Weleszy.
