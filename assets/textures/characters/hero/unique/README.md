# Bohater — skóra v4 według konceptu twarzy 19 v2

**PROTOTYPE_NOT_APPROVED**, część A do przeglądu autora i integracji Sola. Baza: `35df59f4c19b473530fd3fe316b35fc7b1739327`. Część B czeka na przekazanie P2.

Wymagania autora i brief mają pierwszeństwo; koncept 19 v2 ma pierwszeństwo przed twarzą z planszy 17. Użyto briefu rozdz. 2–4 i konceptu 19 z `main` @ `eb3a2ec6282855e8b659970b10a677b4232d68fe`. Oryginalny koncept, bez przemalowania, zachowano do porównania w `podglad/v4/reference/concept19.jpg`.

## Zmiany

- Różowoczerwone, wygojone blizny z ciemniejszym środkiem, nierówną szerokością, lekko wypukłymi brzegami i drobnymi śladami szycia. **Lewa strona postaci:** skośna przez czoło nad brwią i krótsze krzyżujące cięcie oraz skośna blizna pod okiem. **Prawa strona:** trzy drobne zadrapania. +X natywnego OBJ to lewa strona postaci (+Y po transformacji renderera). Nie przypisujemy bliznom fabuły.
- Usunięto poprzednie jasne, wklęsłe blizny i długie czerwone kreski naczynek przy nosie. Nowa tkanka blizn ma dodatni relief względem 0,5, gładszą odpowiedź materiału (roughness dąży do 0,43), bez otwartych ran i krwi.
- Nieregularne, przerywane bruzdy czoła, najgłębsze nisko nad brwiami; pionowy relief gniewny między brwiami, kurze łapki, worki i chłodniejsze cienie pod oczami. Bruzdy nosowo-wargowe zachowano.
- Drobne piegi/plamki na czole, nosie i policzkach; cieplejszy, czerwieniejący nos i policzki, widoczne pory. Dotychczasowe pieprzyki pozostają.
- Gęstsza baza krótkiej brody i wąsa, nieregularne policzki. Siwe mieszki są losowo rozłożone, nie tworzą sinusoidalnych pasów; najwięcej na podbródku, pojedyncze na policzkach. Skóra głowy ma ciemną bazę z siwymi mieszkami. Włosy średniej długości do żuchwy i geometria brody pozostają zadaniem Sola.
- Tęczówka A2: **szarozielona / szaroorzechowa**, z cieplejszym oliwkowo-brązowym pierścieniem przy źrenicy, ciemnym limbusem i radialnymi włóknami. Bez namalowanego refleksu. Białko jest niezmienione.

## Zachowanie dłoni i szyi

Dłonie i szyja są chronione danymi z `35df59f`: po eksporcie przywracane są dokładne próbki bazowe poza edytowanym wnętrzem czerwonej wyspy głowy. Walidator porównuje **każdy piksel pomarańczowego obszaru szyi i niebieskiego obszaru dłoni** we wszystkich pięciu mapach 4K i pięciu mapach 2K. SSS i sclera są identyczne w całości.

Polecenie „bez zmian szyja” potraktowano dosłownie: zachowano także jej dotychczasową pigmentację, zamiast dodawać na niej nowe piegi. Nie przywrócono poziomych bruzd szyi ani kresek/żył dłoni. Zapisane nazwy, rozdzielczości, formaty i UV ciała są niezmienione.

## Podłączenie

**Normal strength: 0,45** we wszystkich porównaniach. Basecolor/iris/sclera: sRGB. Roughness, normal_opengl, height, sss_mask: Non-Color. Basecolor i normalna RGB 8 bit, roughness/SSS grayscale 8 bit, height grayscale 16 bit. Ciało 4096 i pochodne 2048, oczy 512; iris zachowuje dotychczasowy RGBA 8 bit i alfę poza okręgiem 80% obrazu. Źrenica ma około 30% średnicy tęczówki.

Normalna OpenGL +Y, węzeł Normal Map z bazą MikkTSpace. Neutralny height 0,5; umowny pełny zakres 0,002 m, bez zmiany sylwetki. Nie nakładać jednocześnie pełnego bump i normalnej. SSS jest względną maską, nie pomiarem tkanki; w diagnostyce mnoży wagę SSS przez 0,30.

Albedo jest pigmentem proceduralnym bez świateł, AO i okluzji. Mikrodetal korzysta z pasa ochronnego UV 32–56 px; nowe regionalne kolory łagodnie mieszają się z bazą przy brzegu obszaru edycji. Niezmienione piksele tła i brzegów zachowują istniejącą dylatację, bez czarnych krawędzi. Oryginalna geometria i UV grupy `body` nie są modyfikowane.

## Podglądy i ograniczenia

`podglad/v4/before/`: mapy v3 z `35df59f`; `podglad/v4/after/`: v4. Po cztery kadry: przód, profil, zbliżenie twarzy, oko. `porownanie.png` zestawia je bez skalowania i korekcji kolorów, a `koncept19-v4.png` pokazuje koncept obok zbliżenia v4. **Koncept ma własne światło ilustracji**; nie jest pomiarowym albedo ani renderem tej samej rzeźby.

Obie wersje: identyczny OBJ, kamera 768×768, normal 0,45, światła kontraktu, AgX Medium High Contrast, exposure −0,2, Cycles 64 próbki, seed 1703, 4 wątki, brak denoise. Dla oceny tęczówki w obu wersjach włączono **te same pomocnicze siatki oczu z OBJ**, z płaskim rzutem A2. To dodatkowa diagnostyka: nie są docelowymi gałkami z rogówką ani zmienionym UV ciała. Bieżące pełne podglądy v4 są w `podglad/skin_*.png`.

Neutralna baza hm08 nie ma ciężkich łuków brwiowych, żuchwy, rzeźby wieku ani włosów z konceptu. Tekstury nie zastępują tej pracy Sola; nie deklarujemy identycznych rysów ani sylwetki. Nie sprawdzono docelowego `.blend`, włókien, rogówki, skali gry 1×, animacji i integracji ze strojem. Podglądy są diagnostyką materiału, nie eksportem sprite'ów. Height/normal nie są wypaleniem high-poly, a SSS nie jest pomiarem fizycznym. Proceduralna interpretacja wymaga oceny autora na modelu docelowym.

## Odtwarzanie

Python 3 + NumPy 2.3.5, SciPy 1.17.0, Pillow 12.3.0; Blender 4.3.2. Kilka–kilkanaście GB RAM. Korzystamy z istniejącego checkoutu, bez dodatkowego worktree. Generator wymaga dostępnego w historii Git commita bazowego `35df59f`, ponieważ z niego odtwarza chronione dane.

```bash
# Z katalogu repozytorium:
git show 421c7e895e6a029181dcb7c63ab277ad7bab4ca0:assets/sprites/player/source/third_party/base.obj > /tmp/hero-base.obj
cd assets/textures/characters/hero/unique
OPENBLAS_NUM_THREADS=1 python3 source/build_maps.py --mesh /tmp/hero-base.obj
python3 source/build_eye.py
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --eyes
python3 source/validate.py --mesh /tmp/hero-base.obj
```

Rdzeń eksportu: `source/build_maps.py`; baza chronionych pól v3: `aging_v2.py`; nowa twarz: `face_v4.py`; tęczówka: `build_eye.py`. MakeHuman hm08, przypięty OBJ, grupa body, CC0 według nagłówka. Nie kopiowano koloru ani światła z konceptu do albedo, nie używano zewnętrznych fotografii.

Porównania można odtworzyć, odczytując stare mapy przez `git show 35df59f:assets/textures/characters/hero/unique/NAZWA_MAPY` do `/tmp/hero-v3-final-snapshot`, następnie:

```bash
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --texture-dir /tmp/hero-v3-final-snapshot --output-dir podglad/v4/before --eyes --view front profile face_close eye
blender -b -t 4 -P source/render_check.py -- /tmp/hero-base.obj --output-dir podglad/v4/after --eyes --view front profile face_close eye
python3 source/compare_v4.py
```

Po świadomej regeneracji odświeżyć manifest (`source/write_manifest.py`) i raport (`source/validate.py --write-report`), a potem ponownie manifest oraz zwykłą walidację SHA. Manifest nie hashuje sam siebie. `qa/validation.json` obejmuje formaty, skalowanie, normalne, szwy, pierścienie tęczówki, chronione regiony. `qa/v4_material_checks.json` zapisuje kotwice i stronę blizn oraz dodatni relief ich rdzeni. Starsze `podglad/v2/`, `v3/` oraz `source/README-v*.md` są archiwum. Podsumowanie dla następnego wykonawcy: `HANDOFF.md`.
