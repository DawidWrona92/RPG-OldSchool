# Referencja i decyzje dopracowania

Plansza `docs/koncepty/17-bohater-i-woz.jpg` oraz opis pobrane z aktualnego
`main` (7ce5c4b), bez przełączania i zmiany tej gałęzi. To ten sam koncept
przesłany wcześniej w rozmowie; teraz dostępne są również jego dokładne piksele.
To ilustracja, nie scena gry ani potwierdzenie skali tła.

Autor zaakceptował kierunek poprzedniego prototypu jako podstawę. Kontynuujemy
jego 17-kościowy model, proporcje, strój i pipeline. Brak ataków, uników,
śmierci i innych postaci. Baza porównawcza a0a6c27 / `baseline/`.

Zachowano płaszcz, miecz, plecak, posłanie, praktyczny kaftan i odkryte
przedramiona. Poprawiono istniejące wykroje i materiały, nie odtworzono postaci
od początku. Tekstury chunk01 (main 7ce5c4b) i chunk02 (c6c1a67) skopiowano
wyłącznie do biblioteki, a nie przez merge cudzej gałęzi lub reset shaderów.

## Broń i otwarta decyzja

Pierwotna poza prowadziła ostrze do przodu i w dół, z małą składową boczną.
W dopracowaniu wypróbowano niższe niesienie na zewnątrz: oś w przestrzeni
spoczynkowej (0.40,-0.40,-0.82), znormalizowana. Po pilocie prowadzącym broń zbyt mocno w bok wybrano bardziej neutralną pozycję dłoni przy biodrze (0.01,-0.40,1.07 m). Poprzednia próba poprawiała N, lecz pogarszała W. Długość głowni 0,70 m i
szerokość 0,044 m pozostają bez zmian. Obrócono razem broń, rękawicę i palce,
zachowując punkt chwytu; dodano fizyczny szlif 0,8 mm.

Porównanie przed/po pokazuje propozycję pozy, nie rozstrzygnięcie stałego
noszenia broni w eksploracji. Osobny podgląd przekłada istniejący miecz do
pochwy, bez zmiany źródła i atlasów bazowych. Nie jest gotową akcją chowania
ani ukończoną pracą palców swobodnej dłoni. Decyzja do autora.

N/NW nadal wymagają oceny wizualnej na ciemnym i zróżnicowanym podłożu; liczba
pikseli maski nie jest kryterium akceptacji artystycznej. Wyniki pełnego testu
i konkretne słabe fazy zapisuje REPORT.md oraz render-validation.json.

## Korekta po uwadze autora

Jasna łata między nogawkami była źle zakrytym, zbyt długim dołem tuniki, nie
osią rigu. Koszulę wpuszczono pod pas i spodnie. Włosy dostały grzywkę,
nieregularne boki/kark i drobne włókna. Zarost skorygowano według faktycznych
punktów ust/nosa/żuchwy; stary fragment leżał za wysoko na twarzy. Oczy
osadzono wewnątrz powiek. To nadal ten sam model i rig, bez nowej koncepcji.

Dołączono też całą dostawę Chunk03 (ff74eb7): materiały metali, rzemieni, skóry
człowieka i włosów oraz lokalne maski i trim. Obrazy są zapakowane w .blend.
