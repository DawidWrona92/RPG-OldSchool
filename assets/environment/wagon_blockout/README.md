# Wóz — roboczy blockout

Ten model to uproszczona bryła do oceny skali, nie asset produkcyjny. Geometria: deski, rama, cztery koła szprychowe, osie i dwa dyszle. Układ X wzdłuż wozu, Y w poprzek, Z w górę; wymiary wyłącznie orientacyjne, nie zatwierdzona skala gry. Budowa zaprzęgu wymaga weryfikacji z koniem. Bez tekstur, materiałów PBR, lin, zawieszenia, uszkodzeń, kolizji, osobnego cienia i prawidłowego oświetlenia.

`python build.py` wymaga Pythona 3 i Pillow; generuje OBJ oraz poglądowy PNG za pomocą uproszczonego rysowania wielokątów. PNG nie jest renderem Blendera, ma orientacyjną projekcję i może mieć błędy kolejności powierzchni. OBJ zawiera jedną siatkę bez materiałów; nie jest gotowym sprite’em. Skala, geometria kół i montaż dyszli wymagają sprawdzenia w Blenderze oraz w scenie gry.

Dwukrotne uruchomienie w tym samym środowisku dało identyczne sumy SHA-256 dla OBJ i PNG. Nie przeprowadzono testów kolizji, kamery w grze ani renderu w Blenderze. Punkt odniesienia: [koncepcja i plan](../../../docs/koncepty/18-woz-i-trakt.md).
