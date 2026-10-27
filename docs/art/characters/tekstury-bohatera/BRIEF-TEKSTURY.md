# Brief: unikatowe tekstury bohatera

**Zleceniobiorca:** GPT 6 · **Status: [ZLECENIE PM]**, 27 października 2026 r. · **Plan nadrzędny:** [plan naprawy bohatera](../PLAN-NAPRAWY-BOHATERA.md) (faza F4).

Część **A** (skóra i oko) zaczynasz od razu. Część **B** (strój) dopiero po przekazaniu P2 od Sola — UV stroju jeszcze nie istnieje.

## 1. Kontekst

Welesza to mroczne action RPG w duchu Diablo 2, osadzone w słowiańskim, wilgotnym borze. Bohater to **zwykły podróżnik**, nie rycerz ani wybraniec. Postać jest modelowana w Blenderze i renderowana do sprite'ów kamerą z góry (30°), w skali 60 px/m — w grze cały człowiek ma ok. 105 px, a twarz ok. 12 px. Tekstury służą więc trzem celom:

1. **czytelnym walorom i kolorom w małej skali** (twarz, dłonie i przedramiona muszą czytać się jak skóra, nie jak plama),
2. **zbliżeniom** — portrety 768 px i duże rendery,
3. **wzorowi** dla innych ludzkich postaci (ta sama siatka i UV).

Obecny model wygląda jak plastikowy manekin, bo skóra ma jednolitą, kafelkowaną próbkę bez cech twarzy. Zobacz, czego unikać: [review — twarz](../review-bohater-01-twarz.jpg), [review](../REVIEW-BOHATER-01.md).

## 2. Materiały źródłowe

| Co | Gdzie (gałąź `main`) | Jak używać |
|---|---|---|
| Koncept bohatera | [`docs/koncepty/17-bohater-i-woz.jpg`](../../../koncepty/17-bohater-i-woz.jpg) — górny rząd: przód, tył, bok | **główne odniesienie** wyglądu: wiek, karnacja, zarost, brud, kolory stroju |
| Opis konceptu | [`docs/koncepty/17-bohater-i-woz.md`](../../../koncepty/17-bohater-i-woz.md) | czego koncept nie przesądza |
| Kierunek artystyczny | [`docs/art/niemir/NIEMIR_ART_DIRECTION.md`](../../niemir/NIEMIR_ART_DIRECTION.md), rozdz. 03 | paleta: zgaszone, ziemiste, wilgotne; bez nasyconych barw |
| Szablon UV ciała | [`uv-cialo-siatka-2048.png`](uv-cialo-siatka-2048.png) (siatka na przezroczystym tle) | warstwa nakładki przy malowaniu; skaluj do 4096 |
| Mapa obszarów UV | [`uv-cialo-obszary-2048.png`](uv-cialo-obszary-2048.png) | kolory płaskie: czerwony = głowa, pomarańczowy = szyja, niebieski = dłonie, zielony = przedramiona, szary = reszta |
| Opis UV z punktami | [`uv-cialo-opis.jpg`](uv-cialo-opis.jpg) | **głowa leży bokiem**: czubek w lewo, podbródek w prawo, uszy u góry i u dołu wyspy; oczy to dwie małe wyspy po lewej stronie atlasu |
| Siatka 3D | `assets/sprites/player/source/third_party/base.obj` na gałęzi `vibe/sprite-bohater-codex` (MakeHuman, CC0, grupa `body`) | jeśli masz podgląd 3D — maluj lub sprawdzaj na niej |
| Biblioteka materiałów | [`assets/textures/characters/hero/`](../../../../assets/textures/characters/hero/README.md) | mikrodetal (pory skóry, splot tkanin, skóra) — **wolno** użyć jako warstwę szczegółu |

Kolory widoczne na koncepcie (mediana próbek, **ze światłem ilustracji** — albedo zwykle o 10–25% jaśniejsze):

| Element | Koncept | Element | Koncept |
|---|---|---|---|
| skóra twarzy (policzek) | `#5E4539` | kaftan skórzany | `#251A13` |
| skóra przedramienia | `#886654` | płaszcz, wełna | `#281F1A` |
| len koszuli (rękaw) | `#9C8B7E` | spodnie | `#110C09` |
| włosy | `#281F1A` | buty | `#312620` |
| posłanie | `#4D4138` | plecak | `#362A24` |

## 3. Kanon i ograniczenia

- **[DECYZJA AUTORA, 27.10.2026] Stary, mocno ogorzały podróżnik** — postać wygląda starzej niż na koncepcie 17: głębokie zmarszczki czoła, kurze łapki, bruzdy nosowo-wargowe, zwiotczała skóra pod oczami, przebarwienia od słońca. Jasna, środkowoeuropejska karnacja **ogorzała od wiatru i słońca**: twarz, szyja, dłonie i przedramiona cieplejsze i ciemniejsze niż ciało pod ubraniem.
- **Kilkudniowy, ciemnobrązowy zarost** na policzkach, żuchwie, podbródku, nad wargą i pod żuchwą; włosy ciemne (model dostanie włókna — Twoja tekstura daje pod nimi ciemniejszą skórę głowy i cień zarostu).
- Brud i zmęczenie drogą: brud w zagłębieniach dłoni, przy paznokciach i na kostkach; lekkie zaczerwienienia nosa, policzków i uszu od chłodu.
- **[DECYZJA AUTORA, 27.10.2026] Ślady życia w drodze są dozwolone:** kilka starych, wygojonych blizn (np. przecięcie brwi lub policzka, drobne blizny na dłoniach i knykciach) i jeden–dwa pieprzyki na twarzy lub szyi. Blizny są jaśniejsze i gładsze od skóry, bez świeżych ran i zaczerwienień. To wygląd postaci, nie nowe fakty fabularne — nie wymyślaj ich historii.
- **Nadal nie dodawaj** tatuaży, malunków, biżuterii ani świeżych ran.
- **Bez wpieczonego światła:** albedo nie ma cieni, połysków, okluzji ani kierunku światła. Model oświetla Blender według [kontraktu renderu](../../KONTRAKT-RENDERU.md).
- Nie kopiuj fotografii ani tekstur o niejasnej licencji. Narzędzia i modele, których użyłeś, zapisz w manifeście. Tekstury tworzone przez AI są dopuszczone decyzją autora.

## 4. Część A — skóra i oko (start od razu)

### A1. Atlas skóry całego ciała — natywne UV MakeHuman

| Mapa | Plik | Format |
|---|---|---|
| kolor (albedo) | `hero_skin_body_basecolor.png` | sRGB, 8 bit |
| szorstkość | `hero_skin_body_roughness.png` | liniowa (Non-Color), 8 bit |
| normalna | `hero_skin_body_normal_opengl.png` | tangent space, OpenGL (+Y w górę), MikkTSpace |
| wysokość | `hero_skin_body_height.png` | 16 bit, szarość, 0,5 = brak przesunięcia |
| maska SSS | `hero_skin_body_sss_mask.png` | jaśniej w cienkich miejscach: uszy, skrzydełka nosa, palce |

Rozdzielczość **4096×4096**, plus wersje 2048 przeskalowane z 4096. Priorytet szczegółu według obszarów:

1. **Twarz i głowa** (czerwony): pory; zmarszczki czoła, kurze łapki, bruzdy nosowo-wargowe; usta naturalne, lekko spierzchnięte, nie czerwone; oczodoły odrobinę ciemniejsze i chłodniejsze; cień zarostu; skóra głowy pod włosami ciemna w kolorze włosów, żeby prześwity między włóknami nie świeciły; delikatna baza brwi.
2. **Dłonie** (niebieski): zgrubienia, linie dłoni, zmarszczki na knykciach, krótkie paznokcie z brudem, wnętrze dłoni jaśniejsze; ślady pracy, nie rany.
3. **Szyja i przedramiona** (pomarańczowy, zielony): opalenizna z delikatnym przejściem ku jaśniejszej skórze ramion; lekkie owłosienie przedramion w teksturze.
4. **Reszta ciała** (szary): jednolita, spójna skóra bez cech — jest pod ubraniem, ale nie może mieć dziur ani skoków koloru.

**Szwy UV:** sąsiednie wyspy stykają się w 3D. Pas ok. 32 px przy brzegu każdej wyspy zostaw w tonie bazowym danego obszaru, bez cech, i nie zostawiaj tła. Wypełnij też tło poza wyspami kolorem sąsiedniej skóry (dilation ≥ 16 px), żeby mipmapy nie dawały czarnych krawędzi.

**Szorstkość, wskazówki:** strefa T czoła i nosa ok. 0,40–0,50; policzki 0,55–0,65; zarost i skóra głowy 0,70; dłonie 0,60–0,70; usta 0,45.

### A2. Oko

| Plik | Opis |
|---|---|
| `hero_eye_iris_basecolor.png` | 512×512; tęczówka ciemnobrązowa jako okrąg o średnicy 80% obrazu, wyśrodkowana, z ciemniejszym brzegiem (limbus) i źrenicą o średnicy ok. 30% tęczówki |
| `hero_eye_sclera_basecolor.png` | 512×512; białko lekko ciepłe, nie czysto białe, z delikatnymi żyłkami przy kącikach |

Sol rzutuje je płasko na kulę oka; nie potrzeba szablonu UV.

### A3. Kontrola przed oddaniem

Jeśli masz podgląd 3D, wyrenderuj `base.obj` z teksturą: przód, profil, tył i dłonie. Jeśli nie — dołącz atlas z nałożonym szablonem UV, który pokaże, że cechy leżą we właściwych miejscach. Ostateczną kontrolę w świetle gry robi Sol; po jego renderze możesz dostać poprawki.

## 5. Część B — strój (po przekazaniu P2)

Sol dostarczy w `assets/sprites/player/handoff/p2/` (gałąź `vibe/sprite-bohater-codex`) dla każdej części stroju: szablon UV, wypalone AO, krzywiznę, normalną z rzeźby, gradient wysokości nad ziemią, maskę ID elementów, podgląd 768 px i `manifest.json`.

Części: koszula lniana, spodnie, kaftan, pasy i rzemienie, sakwy, pochwa, kaptur z peleryną, płaszcz, plecak, posłanie, manierka, buty.

Dla każdej części: `hero_<czesc>_basecolor.png`, `_roughness.png`, `_normal_opengl.png` (detal, który Sol połączy z normalną z rzeźby), `_height.png`; rozdzielczość jak w manifeście P2 (zwykle 2048). Zasady:

- **Zużycie według map, nie losowo:** przetarcia i jaśniejsze krawędzie skóry według krzywizny; brud i ciemniejsze zagłębienia według AO; **błoto od ziemi**: mocne na butach, słabnące do kolan na nogawkach, na dolnym brzegu płaszcza; wilgoć — ciemniejszy, mniej szorstki dół płaszcza i buty.
- Szwy krawieckie i przeszycia według maski ID (kaftan, plecak, buty, łaty).
- Kolory i walory według konceptu (tabela wyżej): len jasny tylko na piersi i rękawach, cała reszta ciemna i ziemista; posłanie **nie** może być jaśniejsze od koszuli.
- Mikrodetal z biblioteki (`linen_shirt_worn`, `wool_cloak_dark_brown`, `leather_vest_weathered_brown` itd.) wolno użyć jako warstwę splotu i porów.

## 6. Oddanie

- Gałąź: `vibe/hero-textures-gpt6` (od aktualnego `main`); pliki w `assets/textures/characters/hero/unique/`.
- `assets/textures/characters/hero/unique/manifest.json`: dla każdego pliku nazwa, mapa, przestrzeń barw, rozdzielczość, SHA-256, sposób powstania (narzędzia, modele, źródła) i status `PROTOTYPE_NOT_APPROVED`.
- `README.md` w tym katalogu: co zrobiono, czego nie sprawdzono, znane wady.
- Commit z opisem po polsku; nie zmieniaj innych gałęzi ani plików poza `unique/`.

## 7. Kryteria akceptacji (sprawdza PM i autor po renderze Sola)

1. Portret 768 px: twarz starego, ogorzałego podróżnika (zgodnie z decyzją autora), rysy zgodne z konceptem; zarost czytelny; usta, oczodoły i uszy naturalne.
2. Brak widocznych szwów w ujęciach przód, profil, tył, dłonie.
3. Brak wpieczonego światła i powtórzeń kafelka.
4. W skali gry (1×) twarz i przedramiona czytają się jako ogorzała skóra, a nie jako jednolita beżowa plama.
5. Pliki, nazwy, formaty i manifest zgodne z tym briefem.
