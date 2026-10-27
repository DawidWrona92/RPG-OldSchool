# Wynik eksperymentu bohatera Weleszy

27 października 2026. **Nie osiągnięto jakości dostarczonego concept artu.**
Powstał odtwarzalny model i zestaw animowanych sprite'ów, ale materiały,
twarz, włosy i konstrukcja ubioru nadal wyglądają zbyt prosto. Sprawność
eksportu nie jest uznana za odbiór artystyczny ani gotowość produkcyjną.

## 1. Technologia

Blender 4.3.2 / Cycles CPU, organiczna baza człowieka MakeHuman CC0, osobne
wykroje ubrań, 17-kościowy szkielet, IK i deformacja wtórna płaszcza.
Wybrano siatkę, żeby zapewnić anatomię twarzy, ciągłą powierzchnię człowieka
i standardowy plik do dalszej pracy. Nie modyfikowano SDF ani innych postaci.

Nie wykonano porównania wydajności tego samego modelu w dwóch rendererach,
więc nie deklarujemy wykazanej przewagi jakościowej Blendera nad SDF.
Obejrzano istniejące rendery i klatki GIF Drwala. Psa nie ma na gałęzi bazowej.

## 2. Obrazy i eksport

- [Osiem kierunków 1:1](previews/osiem-kierunkow-1x.png).
- [Źródłowe rendery 384 px](previews/osiem-kierunkow-render-384.png), bez powiększania obrazu 192 px.
- [Próba w świecie, bez zmiany skali tła](previews/bohater-w-swiecie-1x.png).
- [Atlasy i JSON](atlas/bohater.json), [wariant poprzedniego formatu](atlas/compat/bohater.json).
- [Model `.blend`](source/bohater.blend), [generator](source/build_player.py), [odtworzenie](README.md).

Klatka 192×192 RGBA, 60 px/m, kamera ortograficzna 30°, kotwica
(96, 158.353829). Kierunki S, SW, W, NW, N, NE, E, SE są oddzielnymi
obrotami tego samego modelu. Postać i fizyczny cień są osobnymi atlasami;
kontaktowy cień ma jawne ograniczenie zasięgu opisane w README.

## 3. Zgodność z referencją

Obejrzano nowy arkusz autora w rozmowie: przód, tył i profil podróżnika oraz
scenę z rozbitym wozem. Zmieniono płaszcz na dłuższy i brązowy, rękawy na
podwinięte, odsłonięto przedramiona, poszerzono spodnie, dodano wyraźniejsze
pasma włosów i pochwę. Miecz pozostaje dobyty na potrzeby próby animacji;
w koncepcie znajduje się w pochwie. To interpretacja do oceny, nie nowy kanon.

**Brakuje** nieregularnego układu tkanin, wiarygodnych śladów zużycia,
charakterystycznej twarzy i włosów, szycia oraz przestrzennego detalu skóry
wyprawionej. W 1:1 część elementów zlewa się w jednolite powierzchnie.
Przyczyną jest niedostateczne dopracowanie modelu i tekstur, a nie brak
Blendera czy konieczność powiększenia bohatera. Więcej próbek renderowania
nie naprawi tych wad.

Kompozyty wykorzystują rzeczywistą scenę 12 z repozytorium. Nowy arkusz
z rozmowy nie jest dostępny jako lokalny plik, więc nie deklarujemy montażu
na jego dokładnych pikselach. Warianty chłodu i pochodni wyrenderowano
oddzielnie; pochodnia nie została wypieczona w atlasach bazowych.

## 4. Animacje

- [Spoczynek GIF](previews/bohater_spoczynek.gif): 8 klatek, cykl 3,2 s.
- [Chód GIF](previews/bohater_chod.gif): 12 klatek, cykl 0,96 s.
- [Chód bez stratnego indeksowania GIF](previews/bohater_chod.webp).
- [Próba podparcia na ruchomym podłożu](previews/chod-kontakt-stop.gif).
- [Wszystkie klatki W](previews/chod-klatki-W-1x.png), [wszystkie klatki NW](previews/chod-klatki-NW-1x.png).

Prędkość przesuwania w grze: 0,9027777778 m/s. Kontakt stopy jest obliczony
dla tej prędkości. Ruch górnej części ciała pozostaje zbyt sztywny; nie ma
pełnego rolowania stopy pięta–palce ani symulacji tkaniny. Jest to wstępny
cykl chodu, nie zaakceptowana animacja o jakości zlecenia premium.

## 5. Ocena wzrokowa i kontrole

Oceny są samokrytyczną oceną przedstawionych obrazów, nie benchmarkiem:

| Obszar | Ocena | Uzasadnienie |
|---|---:|---|
| Anatomia | 6/10 | Spójna baza i długości kończyn; twarz i dłonie wymagają indywidualnego dopracowania. |
| Materiały | 4/10 | Osobne właściwości odbicia, lecz zbyt gładkie powierzchnie i za mało przekonującego zużycia. |
| Animacja | 5/10 | Pętle i podparcie działają; barki, dłonie i przenoszenie ciężaru są nadal mechaniczne. |
| Czytelność | 6/10 | Ubiór i wyposażenie są rozpoznawalne; broń w NW/N pozostaje słaba wizualnie. |
| Zgodność z referencją | 4/10 | Zbliżony zestaw ubioru i paleta, wyraźnie niższa jakość geometrii i materiałów. |
| Gotowość do gry | 4/10 | Poprawny pakiet techniczny; brak odbioru artystycznego, integracji w silniku i animacji walki. |

Rzeczywiście wykonane kontrole:

- **160 klatek**: odczyt PNG, SHA-256 źródła i obrazów, alfa, granice postaci/cienia, atlas/JSON, osiem różnych kierunków.
- **242 pozy** szkieletu, **22 klucze** zapisanych akcji i zamknięcie obu cykli; błędy stawów/długości poniżej 0,000001 m.
- **13 próbek podparcia**: maksymalny błąd kompensacji ruchu ok. 0,0000000043 m. To kontrola matematyczna, nie dowód naturalności ruchu.
- **32 renderowane maski broni**: spoczynek oraz chód 0/4/8 w każdym kierunku, minimum 7 widocznych pikseli przy niezmienionym progu 4. Pierwotne niepowodzenia opisuje `source/REFERENCE.md`.
- **Ponowny render z `.blend`**: obraz pierwszej klatki S identyczny piksel po pikselu z dostarczonym PNG.
- **5 grafów** dokumentacji projektu: poprawne.

Szczegóły: `previews/technical-report.json`, `blend-validation.json`,
`render-validation.json`; test wznowienia: `resume-validation.json`.
Nie wykonano pełnej detekcji kolizji ubrania, importu w docelowym silniku,
walki ani walidacji odtworzenia w nowym zadaniu chmurowym.

## 6. Repozytorium i licencje

Gałąź: `vibe/sprite-bohater-codex`. Pełny punkt kontrolny wyników po nowej
referencji: `49742e1`. Kolejne drobne commity zawierają raport i kontrole;
aktualny pełny SHA pokazuje `git log -1`. Praca jest wysyłana na GitHub;
nie utworzono PR i nie zmieniono cudzych gałęzi.

Całość mieści się w `assets/sprites/player/`. Baza MakeHuman jest CC0-1.0;
zachowano licencję, przypiętą wersję i sumy źródeł. Nie korzystano
z assetów o niejasnej licencji ani z kodu aplikacji MakeHuman.

## 7. Decyzja produkcyjna

**Nie rekomenduję jeszcze migracji pozostałych postaci.** Przydatny wynik
to powtarzalny eksport, standardowy model, kontrola szkieletu i oddzielne
obrazy/cienie. Nie wykazano osiągnięcia zakładanego poziomu artystycznego.

Dalsza próba powinna dopracować twarz, włosy, modelowanie fałd i tekstury
ubioru, po czym ponownie przejść ocenę 1:1 w ośmiu kierunkach. Przed pracą
ręczną warto oddzielić autorstwo modelu od generatora, żeby regeneracja
nie nadpisywała poprawek artysty. Dopiero po akceptacji wyglądu ma sens
rozbudowa o ataki, uniki i kolejne postacie.

Raportowany czas renderowania 160 par postać/cień wyniósł łącznie około
573 s na czterech wątkach CPU, bez etapu modelowania i walidacji. Nie
przeprowadzono pomiaru GPU ani automatycznej produkcji dużej obsady.
