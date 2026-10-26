# QA assetów v2 — kontrola i testy

**Gate 1 — pliki:** kompletność, import kodu, deterministyczne testy, niepusty alpha-bbox, brak NaN, zgodne wymiary i metadane.

**Gate 2 — geometra:** normalne skierowane na zewnątrz, brak samoprzecięć, triangulacja wielokątów wklęsłych, brak cullingowych dziur, cienie nie są przycinane, emblemat drużyny widoczny wyłącznie na zdefiniowanej stronie.

**Gate 3 — animacje:** wszystkie pary kierunków, asymetryczny obiekt diagnostyczny, ruch stóp i osi tułowia, stała kotwica, płynne przejścia faz, poprawna kolejność kierunków, brak teleportacji wyposażenia, brak wielokrotnych obrotów.

**Gate 4 — styl:** podgląd 1× na docelowej teksturze terenu. 0.5× i 2× służą ocenie czytelności i artefaktów. Obejrzyj osobno alpha, team i shadow. Ocena estetyczna wymaga człowieka lub modelu wizyjnego.

**Gate 5 — integracja:** render w silniku gry, jedna plansza z różnymi typami obiektów, prawidłowe depth-ordering i clipping przy ruchu kamery.

Raport zawiera `PASS/WARN/FAIL`, faktyczne pomiary, reprodukowalne przykłady i listę znanych ograniczeń. Wszystkie progi zależne od skali kalibruj na zestawie referencyjnym, nie z jednego bohatera.
