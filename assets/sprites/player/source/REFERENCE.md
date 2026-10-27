# Referencje i decyzje wykonawcze

Podstawa projektu: arkusz cywilów `docs/koncepty/03-*`, kierunek Niemiru i scena
`docs/koncepty/12-*`. Nie kopiujemy anatomii, poroża ani topora potwora.

W trakcie pracy autor dostarczył w rozmowie dodatkowy obraz: trzy widoki
tego samego podróżnika oraz izometryczną scenę z uszkodzonym wozem i latarnią.
Obraz obejrzano bezpośrednio w rozmowie. Nie jest dostępny jako plik w lokalnym
systemie, więc nie deklarujemy kompozytu wykonanego na jego dokładnych pikselach.
Testy kompozycji używają istniejącej, nieprzeskalowanej sceny 12 z repozytorium.

## Różnice wprowadzone po nowej referencji

- Płaszcz: ciemnobrązowa wełna, dłuższy dół z wyraźniejszymi fałdami i nieregularnym brzegiem.
- Lniane rękawy: podwinięte przy łokciach, odsłonięte anatomiczne przedramiona.
- Spodnie: luźniejsze, bez zmiany długości kończyn szkieletu.
- Włosy: większe, nieregularne pasma, mniej równy obrys.
- Plecak: większy i mniej kulisty; zachowane posłanie oraz nośne rzemienie.
- Pochwa: osobna, po lewej stronie. Dla demonstracji miecz pozostaje w prawej
  dłoni, zgodnie z pierwotnym zleceniem; szkic pokazuje broń schowaną.

## Wykryta wada kierunku NW

Test Object Index pierwszej wersji wykazał tylko **2 widoczne piksele miecza**
w rzucie NW, przy progu odbioru 4 px. Ten test zakończył się błędem, mimo że
atlas RGBA, geometria i pozostałe kontrole były poprawne. Samo istnienie broni
w modelu nie było uznane za zaliczenie.

Zmieniono sposób niesienia ostrza na ukośny, na zewnątrz sylwetki. Nie
powiększono broni, nie zmieniono progu ani nie zastąpiono brakującego widoku
lustrzanym odbiciem. Wynik poprawki zapisuje `previews/render-validation.json`.

To interpretacja do oceny autora, a nie automatyczne zatwierdzenie wyposażenia
startowego, fabuły lub wyglądu produkcyjnego.
