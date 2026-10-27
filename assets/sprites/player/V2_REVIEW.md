# Bohater v2 — F0–F3, do oceny autora

Gałąź `vibe/sprite-bohater-codex`. Commit zapisujący model: `ad5f69d0095317310f17f463616904488474b13a`. SHA-256 źródła: `6947b81d85b8b358483bd221e8f196da77a023454fa09d82956e55ff260015e5`. Rewizja: `v2-F3-equipment-review-16`; Blender 4.3.2.

**To statyczne źródło i przekazanie do teksturowania, przed B1/B2. Nie jest zatwierdzonym wzorem produkcyjnym.** Nie rozpoczęto animacji ani atlasów v2. Oczekiwane są tekstury stroju F4 i szarozielona tęczówka v4.

[Przegląd HTML](reviews/v2-f0-f3/index.html) · [model](source/bohater_v2.blend) · [manifest źródła](source/bohater_v2.source.json) · [P1](handoff/p1/manifest.json) · [P2](handoff/p2/manifest.json)

## Plansze i pliki do oceny

- [Koncept 17 ↔ model: przód, tył, bok](reviews/v2-f0-f3/koncept17-model.png), materiały tymczasowe; źródłowe kadry 768 w `reviews/v2-f0-f3/model/`.
- [Koncept 19 ↔ portret](reviews/v2-f0-f3/koncept19-portret.png) i [nieprzeskalowany portret 768](reviews/v2-f0-f3/portrait19/portrait_0.png), skóra GPT 6 v3.
- [Osiem kierunków 1× na tle lasu](reviews/v2-f0-f3/osiem-kierunkow-1x.png), [ciemne tło 1×](reviews/v2-f0-f3/osiem-kierunkow-ciemne-1x.png), osobne RGBA w `reviews/v2-f0-f3/native/` i osobne cienie w `native/shadows/`.
- [Ciało z natywnym UV](reviews/v2-f0-f3/p1-cialo-uv.png) i [sześć pojedynczych póz diagnostycznych](reviews/v2-f0-f3/p1-szesc-poz.png). To testy statyczne, nie animacje.
- [P2 — opis map](handoff/p2/README.md), [manifest z pełną listą 154 PNG i SHA](handoff/p2/manifest.json).

Koncepty 17 i 19 są **ilustracjami koncepcyjnymi, nie sceną gry ani renderem źródła**. Plansza porównawcza ma diagnostycznie dopasowane kadry. W próbie 1× użyto niezmienionego wycinka 17: skala tła nie jest pewna, przyjęto dla postaci 60 px/m. Postaci nie powiększano względem wycinka. Plik `.blend` i osobne PNG zachowują przezroczystość.

## Co zmieniono

**F0:** `bohater.blend` rev08 i `bohater_detale.blend` pozostają nienaruszonym archiwum, z sumami w `source/archive-sources.json`. Ich stare atlasy/rendery nie przedstawiają v2. Nowa praca ma jedno nadrzędne źródło `bohater_v2.blend`; aktualne instrukcje w README/HANDOFF, stare w `README-ARCHIVE-PROTOTYPE.md`.

**F1:** pełna grupa `body` MakeHuman CC0, 19158 indeksów OBJ, 13378 ścian i 53512 narożników natywnego UV. Mężczyzna 1,8 m, stary i silny, targety CC0 na tej samej topologii. Szkielet `default.mhskel`: **163 kości**, pełne wagi `default_weights.mhw`, bez remapowania do starego rigu 17 kości. Utrwalono neutralną pozę: opuszczone ramiona, luźniejsze przedramiona i dłonie. To dopasowany rig, nie obietnica gotowego ruchu.

**F2:** po nowej decyzji autora podstawą twarzy jest 19, a nie 17. Cofnięto zapadnięcie policzków, wzmocniono pełną żuchwę i łuki brwiowe, dodano makrobruzdy czoła/glabelli i worki pod oczami. Blizny i pieprzyki pozostają w teksturze. **65 000 natywnych włókien Curves**: średniej długości włosy, broda, wąs i brwi, ciemnobrązowe z siwizną, więcej siwych na podbródku. Groom dostał warstwy, falowanie i nierówne końce po odrzuceniu zbyt równej kurtyny. Oczy mają osobne kule, tęczówki i rogówki IOR 1,376. Tęczówka v3 jest nadal brązowa — szarozielona oczekuje v4.

Skóra v3 z `bc1da517031a63dabad00380e95566f32f2f3c65`: zweryfikowano **51 plików** manifestu, skopiowano katalog bez scalania gałęzi. Siedem używanych obrazów jest spakowanych; ich bajty ponownie porównano z plikami paczki. Albedo/oczy sRGB, dane Non-Color, normal OpenGL strength 0,45; maska SSS × 0,30, promienie R > G > B. Height pozostaje niepodłączony obok normalnej, aby nie dublować reliefu; umowny zakres mikrodetalu do 0,002 m. Brak osobnej geometrii blizn/pieprzyków.

**F3:** 22 osobne części z własnym UV, średnio 1024 px/m, 2K na część. Koszula/kaftan/spodnie mają szwy paneli, tkaniny otwarty rozkrój. Ciało pozostaje pod ubraniem. Scena ma **29 renderowanych siatek postaci** i 8 obiektów Curves, zamiast 207 osobnych siatek starego passu.

Kaptur, peleryna i płaszcz przeszły rzeczywiste drapowania Cloth z kolizjami i self-collision, utrwalone w siatkach. Pierwsze niestabilne drapowanie odrzucono; drugie użyło 16 klatek, 6 kroków jakości i grawitacji ×0,35. **Finalna geometria jest po późniejszych poprawkach artystycznych i dopasowaniu kontaktów**, nie jest niezmienionym wynikiem solvera. Wolny brzeg peleryny opuszczono po ocenie dużego renderu; skorygowano jej luzy względem płaszcza. Nie ma zależności od cache symulacji.

Kaftan ma osobne panele, otwarty przód i brzegi zachodzące na spodnie; rękawy kończą się przy łokciach. Płaszcz ma pionowe fałdy i nierówny dolny brzeg. Duży plecak ma ukształtowaną klapę/kieszenie i sprzączki; jego wyściółkę dopasowano do ubrania, posłanie osadzono na górze i dodano dwa pasy. Buty mają wysokie cholewy, wywinięcia, podeszwy oraz rzeczywiste paski i metalowe sprzączki. **D1: miecz w pochwie przy lewym biodrze**, z otwartym wlotem. Nie produkowano wersji dobytej ani ruchów walki.

## P2 — wydanie do GPT 6

**22 części, 154 PNG, `complete: true`**, ta sama rewizja źródła co powyższe rendery. Każda część: `_uv`, `_ao`, `_curvature`, `_normal_sculpt`, `_height_ground`, `_id`, `_preview`.

`koszula`, `spodnie`, `kaftan`, `plaszcz`, `peleryna`, `kaptur`, `but_lewy`, `but_prawy`, `pas_gorny`, `pas_dolny`, `rzemien_1`, `rzemien_2`, `plecak`, `poslanie`, `manierka`, `sakwa_lewa`, `sakwa_prawa`, `pochwa`, `rekojesc`, `jelec`, `glowica`, `sprzaczki`.

AO jest rzeczywistym wypaleniem Cycles z otoczeniem stroju i zasięgiem 0,15 m; może być ciemne pod innymi warstwami. Curvature to podpisany lokalny Laplacian geometrii, nie skan. Normalna powstaje z ewaluowanych fałd/Subsurf/Solidify do bazowego UV — nie opisujemy jej jako ręcznie rzeźbionego high-poly. Po filtrowaniu bake wektory renormalizowano; rzadkie wektory bliskie zeru po zniesieniu kierunków na krawędzi zastąpiono neutralnym +Z. Manifest zachowuje SHA surowego bake, liczby, metodę i SHA finalizera. Height ground to Z / 1,8 m, do błota/wilgoci, nie displacement. Scalar maps są liniowe 16-bit, normal/ID RGB 8-bit, UV RGBA, podglądy szare 768 RGBA. AO nie należy wpisywać na stałe do koloru albedo.

Kontrola [P2](reviews/v2-f0-f3/p2-validation.json) odczytała i zweryfikowała SHA, formaty oraz wymiary wszystkich 154 PNG. Długość wektorów normalnych sprawdzono na 5,796,388 pikselach wewnątrz wysp UV; odchyłki powyżej 0,012: **0**. Liczby i ewentualne ubytki dla każdej części są jawne w raporcie, nie zastępują oceny malarskiej.

## Faktycznie wykonane kontrole

| Zakres | Wynik |
|---|---|
| Kamera, światła, AgX, ekspozycja, Blender | Odczyt zapisanej sceny: zgodne z kontraktem; [raport źródła](reviews/v2-f0-f3/source-validation.json) |
| UV ciała / topologia | Te same indeksy i kolejność pętli; maks. różnica UV 2.98e-08, wynik reprezentacji float32 |
| Kości / wagi | 163 nazwy zgodne z `mhskel`; suma wag 0.999999955–1.000000045 |
| Sześć prób deformacji | Skończone współrzędne i rzeczywiste przemieszczenia; maks. zmiana długości kości 7.45e-08 m; osobne obrazy do oceny zapadnięć |
| Przenikania, neutralna klatka 1 | **0 niedozwolonych par / 0 par trójkątów**; [pełny zakres i wyjątki](reviews/v2-f0-f3/intersection-validation.json) |
| Rzeczywiście dopuszczone styki | 6 par osadzenia oczu pod powiekami i `glowica~rekojesc`; łącznie 7 par / 974 pary trójkątów przed odjęciem. Żadnego wyjątku dla ubrania, plecaka, butów lub płaszcza |
| Widoczność w audycie | Ciało i wszystkie 22 części włączone do renderu; nic nie ukryto dla uzyskania zera |
| Kierunki / alfa / granice | 8 różnych renderów, bez odbić; RGBA postać i cień, postać nie dotyka brzegu; [klatki](reviews/v2-f0-f3/frame-validation.json) |
| Brzeg cienia | Alfa na brzegu w: S, SW, W, NW, N, NE, E, SE. Cień może być przycięty zgodnie z kontraktem. |
| Powtórzenie z zapisanych źródeł | Ponowny osobny proces Blendera: S, klatka 1, postać i cień; identyczne zdekodowane piksele: **True**; [pomiar różnic](reviews/v2-f0-f3/reproduction-validation.json) |
| Wznowienie P2 / finalizer | 22 części pominiętych, 0 nowych wypaleń; finalizer nie zmienił manifestu |
| Archiwum / atlas | Sumy obu starych `.blend` bez zmian. Nie wygenerowano atlasów ani animacji v2; stare eksporty są archiwum |

Narzędzie PM bada **wszystkie renderowane MESH po modyfikatorach**, również warstwy stroju. Nie bada Curves, samoprzenikania jednej siatki, całkowitego zawierania jednej bryły w drugiej ani ruchu. Nie deklarujemy pełnej kontroli kolizji ani naturalności animacji. Kontakty włosów z ubraniem oceniano wizualnie w dużych widokach; nie ma automatycznej walidacji wszystkich włókien.

## Kontrakt i ograniczenia do dalszej oceny

192×192 RGBA, supersampling 384→192 przez premultiplikowany Lanczos; osobny cień; 60 px/m. Kamera 30°, ortho 3,2 m, kotwica nominalna (96; 158,353829), rzeczywisty rzut zapisany w raporcie źródła. Kierunki S, SW, W, NW, N, NE, E, SE, obroty −45°. Nie zmieniono światła ani ekspozycji i nie powiększano postaci w świecie. Większe widoki mają osobne kamery diagnostyczne.

Nie ma w v2 animacji spoczynku/chodu, prędkości chodu ani nowych atlasów. Te parametry będą ustalane i mierzone w B3/B4 po zgodzie B2; dane ruchu starego rev08 nie są przedstawiane jako wynik v2.

**Otwarte:** szarozielona tęczówka v4, unikatowe tekstury stroju F4 oraz ocena artystyczna głowy i sylwetki. Włosy i przejście zarostu nadal mogą czytać się zbyt regularnie wobec 19; nie zakładamy ich akceptacji. Plecak, fałdy i wykończenie stroju pozostają interpretacją roboczą do oceny w 1× i zbliżeniach. W N/NW pochwa i część rękojeści są przesłonięte płaszczem; czytelność w wariancie D1 wymaga oceny, bez technicznego progu pikseli i bez powiększania broni. Kontrast tymczasowych, płaskich materiałów nie jest oceną końcowych tkanin/skór. Sześć póz nie zastępuje pełnego zakresu deformacji, a statyka nie dowodzi gotowości stroju do ruchu.

Źródła MakeHuman/targetów: CC0, przypięta rewizja i SHA w `source/third_party/`. Skóra GPT 6 jest autorską interpretacją proceduralną, nie skanem. Oczy zachowują pochodzenie repozytoryjne i ograniczenie nieudokumentowanego oryginalnego generatora opisane w paczce autora. Nie dodano zewnętrznych fotografii ani assetów z niejasnych źródeł.
