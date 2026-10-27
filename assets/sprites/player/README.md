# Bohater Weleszy — eksperyment Blender / Codex

Status: praca eksperymentalna do oceny autora, nie zatwierdzony asset produkcyjny.
Gałąź bazowa: `vibe/welesza-sprites-03` (`fc8f657d393af195ddcd900602cc849dde1fffc0`).
Gałąź pracy: `vibe/sprite-bohater-codex`; istniejącej gałęzi Sol nie zmieniamy.

Metoda: organiczna siatka człowieka, osobne modelowane ubrania i ekwipunek,
szkielet animacyjny oraz prerender ortograficzny w Blenderze. Wspólny renderer
SDF i cudze generatory pozostają bez zmian. Alternatywną metodę dopuszcza
bezpośrednio zlecenie autora.

Kontrakt bazowy: klatka 192×192 RGBA, 60 px/m, kamera 30° nad horyzontem,
kotwica (96, 158.35), kierunki S, SW, W, NW, N, NE, E, SE. Cień będzie
eksportowany osobno; atlas zgodny ze starszym układem może zawierać jego kopię.

## Źródła i licencje

`source/third_party/` zawiera bazową siatkę i dane szkieletu MakeHuman,
przypięte do wersji `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`.
Pliki danych są udostępnione przez autorów na CC0-1.0; tekst licencji,
adres każdego źródła oraz SHA-256 zachowano obok danych. Nie kopiujemy kodu
aplikacji MakeHuman (AGPL) ani zewnętrznych assetów społeczności.

Referencje projektu: `docs/koncepty/03-arkusz-cywile-niemiru.jpg` oraz
`docs/koncepty/12-scena-postac-z-porozem-i-toporem.jpg`. Służą do testów
kompozycji, nie są częścią przezroczystych sprite'ów.

## Kolejne zapisy pracy

1. Źródła CC0 i izolacja eksperymentu.
2. Model, rig i próbne rendery; ocena oraz poprawki.
3. Spoczynek i chód we wszystkich ośmiu kierunkach.
4. Atlasy, podglądy, kontrola techniczna i raport ograniczeń.

Blender 4.3.2, Python 3.12, NumPy i Pillow są dostępne w środowisku.
Instrukcje odtworzenia i rzeczywiste wyniki zostaną dopisane po uruchomieniu.
