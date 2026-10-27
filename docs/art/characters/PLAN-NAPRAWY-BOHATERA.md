# Plan naprawy bohatera — wzór postaci ludzkiej

**Status: [PLAN PM] w realizacji**, 27 października 2026 r. Podstawa: [review detale-01](REVIEW-BOHATER-01.md), [koncept 17](../../koncepty/17-bohater-i-woz.md), [kontrakt renderu](../KONTRAKT-RENDERU.md).

> **Stan po [review v2](REVIEW-BOHATER-02.md) (27.10.2026):** F0–F3 wykonane przez Sola (`c51bc52`). **B1 przyjęte** — ciało, szkielet 163 kości, natywne UV. **B2 odrzucone** — głowa, włosy i strój. Wygląd przejmuje **Claude** na `vibe/bohater-claude` w etapach G1–G3 (sekcja „Przejęcie wyglądu” na końcu). Tam, gdzie niżej występuje „Sol”, wykonawcą jest teraz Claude.

Bohater ma być **wzorem dla wszystkich ludzkich postaci** (Drwal, Powrotnik, Stróż, cywile). Dlatego naprawiamy nie tylko wygląd, ale i fundament: ciało, szkielet, UV i sposób teksturowania, tak aby kolejne postacie powstawały z tego samego rdzenia.

## Role

| Kto | Zakres | Gałąź |
|---|---|---|
| **Claude** (model 3D, od 27.10.2026) | głowa, włosy, strój, UV stroju, wypalone mapy, shading, render, animacje, eksport | `vibe/bohater-claude` |
| *Sol* (do 27.10.2026) | F0–F3: ciało, szkielet, UV, strój v2, P1/P2 | `vibe/sprite-bohater-codex` (`c51bc52`) |
| **GPT 6** (tekstury) | malowane tekstury skóry, oka i — po przekazaniu UV — części stroju | `vibe/hero-textures-gpt6` |
| **PM** | review każdej bramki, pomiary (`tools/art/check_intersections.py`), porównania z konceptem | `main` (dokumentacja) |
| **Autor** | decyzje D1–D3, akceptacja bramek B1–B4 | — |

Wykonawcy nie zmieniają cudzych gałęzi. Przekazanie między Solem a GPT 6 odbywa się wyłącznie przez pliki opisane w sekcji „Przekazania”.

## Decyzje autora przed startem

| # | Pytanie | Propozycja PM |
|---|---|---|
| D1 | Miecz w eksploracji | w pochwie przy lewym biodrze, jak na koncepcie; dobyty tylko w animacjach walki |
| D2 | Ciało bazowe | siatka MakeHuman CC0 z natywnym UV (jest już w `source/third_party/base.obj`); kształt przez targety lub rzeźbę **bez zmiany topologii i UV** |
| D3 | Szkielet | pełny szkielet MakeHuman `default.mhskel` (163 kości, CC0, już w repozytorium) z wagami `default_weights.mhw`; do animacji można ukryć kości twarzy |

D2 jest warunkiem równoległej pracy: tekstura skóry GPT 6 powstaje na natywnym UV MakeHuman, więc Sol nie może tego UV zmienić.

## Kolejność zleceń

1. **GPT 6 — część A briefu** (skóra całego ciała i oko na natywnym UV MakeHuman); nie zależy od nowego modelu.
2. **Sol — F0–F3 i F5 dla skóry**, z teksturami z kroku 1; na końcu F3 przekazanie P2 (UV i wypalenia stroju).
3. **GPT 6 — część B briefu** (strój) na podstawie P2.
4. **Sol — integracja stroju, bramka B2**, potem F6–F7.

## Fazy i bramki

### F0 — Porządek źródeł (Sol)
- Zamrozić `bohater.blend` (rewizja 08) i `bohater_detale.blend` jako archiwum; nowa praca w **jednym** pliku `source/bohater_v2.blend`.
- Zachować bez zmian: renderer tylko do odczytu, audyt SHA, kontrakt renderu, Blender 4.3.

### F1 — Ciało i szkielet (Sol)
- Pełne ciało z `base.obj` (grupa `body`), natywne UV MakeHuman nietknięte.
- Proporcje z konceptu: mężczyzna 1,80 m, **stary i mocno ogorzały** (decyzja autora 27.10.2026 — starszy niż na koncepcie), wciąż silny i żylasty, szerokie barki, wyprostowana postawa. Targety MakeHuman (CC0, ta sama przypięta rewizja repozytorium MakeHuman) albo MPFB — wynik zapisany jako kształt, nie nowa siatka.
- Szkielet `default.mhskel` + `default_weights.mhw`; sprawdzić deformację barków, łokci, nadgarstków, palców i kolan w pozach testowych.
- **Wydanie dla GPT 6 (przekazanie P1):** render siatki ciała w pozie spoczynkowej (przód, profil, ¾) z nałożonym szablonem UV, aby potwierdzić, że UV jest natywne.

### F2 — Głowa (Sol, równolegle z F3; tekstury GPT 6 równolegle)
- Rzeźba twarzy według [konceptu twarzy 19](../../koncepty/19-bohater-twarz.md) (strój nadal według 17), postarzona zgodnie z decyzją autora: ciężkie łuki brwiowe, pionowa zmarszczka gniewna, głębokie bruzdy czoła i nosowo-wargowe, worki pod oczami, mocna, pełna żuchwa i prosty nos (policzki **nie** zapadnięte); wyraz zmęczony i surowy. Blizny i pieprzyki są w teksturze — nie modeluj ich osobno.
- Oczy: **szarozielone** jak w koncepcie 19; kula oka z rogówką i osobną teksturą tęczówki od GPT 6; powieki nachodzą na oko bez przenikania na zewnątrz.
- Włosy **średniej długości, do linii żuchwy**, potargane, pasma opadają na czoło i uszy (długość według konceptu 19, decyzja autora 27.10.2026); ciemnobrązowe i **przyprószone siwizną** (decyzja autora); krzywe. Zarost gęsty, kilkudniowy do krótkiej brody, z wąsem; brwi gęste. Brwi i zarost z krótkich włókien z domieszką siwych **oraz** w teksturze skóry (cień zarostu).
- Skóra: Principled BSDF z teksturami GPT 6, SSS 0,2–0,3, promienie czerwień > zieleń > niebieski.

### F3 — Strój od nowa, warstwami (Sol)
Kolejność warstw (od ciała): koszula lniana → spodnie → kaftan skórzany → pasy, rzemienie, sakwy, pochwa → kaptur z krótką peleryną → płaszcz → plecak z posłaniem i manierką → buty.

- Każda część **jedną siatką** z grubością (Solidify), zamiast dziesiątek kawałków.
- Kaptur, peleryna i płaszcz: symulacja tkaniny Blendera na ciele z kolizjami, potem rzeźba fałd; płaszcz układa się w pionowe fałdy od barków, brzeg poszarpany na całej długości dołu.
- Zgodność z konceptem: rękawy podwinięte do łokci, rozpięty kołnierz, kaftan z panelami i przeszyciami, dwa skrzyżowane rzemienie, dwa pasy z sakwami, wysokie buty z paskami i wywiniętą cholewą, duży plecak z klapami i sprzączkami.
- UV rozłożone dla każdej części, gęstość ok. 1024 px na metr, szwy w miejscach niewidocznych lub na szwach krawieckich.
- **Wypalenia dla GPT 6 (przekazanie P2):** dla każdej części AO, krzywizna, normalna z rzeźby, gradient wysokości nad ziemią, maska ID elementów (np. szwy, sprzączki), szablon UV i render 768 px w szarym materiale.

### F4 — Tekstury (GPT 6)
- **F4a, od razu:** skóra całego ciała i tęczówka — [brief](tekstury-bohatera/BRIEF-TEKSTURY.md), część A.
- **F4b, po przekazaniu P2:** części stroju — ten sam brief, część B.

### F5 — Integracja i shading (Sol)
- Podłączenie tekstur, kalibracja pod światło kontraktu (bez zmiany świateł).
- Walory w skali 1×: najjaśniejsza ma być koszula na piersi i rękawach; posłanie i owijki nie mogą przyciągać wzroku bardziej niż twarz i miecz.

### Bramki akceptacji

| Bramka | Kiedy | Kryteria | Akceptuje |
|---|---|---|---|
| **B1 — ciało** | po F1 | proporcje zgodne z konceptem (przód, bok), deformacja w 6 pozach testowych bez zapadnięć, UV natywne | PM, autor |
| **B2 — statyka** | po F2–F5 | plansza koncept ↔ render (przód, tył, bok), 8 kierunków 1× na tle lasu, portret 768 px; **0 przenikań** między warstwami stroju w spoczynku (`check_intersections.py`, dozwolone styki jawnie w `--allow`); tekstury bez wpieczonego światła | autor |
| **B3 — ruch** | po animacjach | spoczynek i chód: 0 przenikań w **każdej** klatce, stopy bez ślizgu (`root_speed_mps`), płaszcz bez przebić przez nogi | PM, autor |
| **B4 — eksport** | po atlasach | atlas, cień, JSON i podglądy z tej samej rewizji `bohater_v2.blend`; test w Godocie (gałąź `vibe/godot-test-silnika`) | PM |

Animacji (F6) i eksportu (F7) nie zaczynamy przed B2.

### F6–F7 — Animacje i eksport (Sol)
Spoczynek, chód, potem walka według [bestiariusza](../../bestiariusz-demo.md) i [walki](../../walka-i-trafienia.md); okna walki w `events`. Eksport zgodnie z kontraktem renderu.

## Przekazania między Solem a GPT 6

| ID | Od → do | Pliki | Miejsce |
|---|---|---|---|
| P0 | PM → GPT 6 | szablony UV ciała i obszarów (już gotowe) | `docs/art/characters/tekstury-bohatera/` na `main` |
| P1 | Sol → GPT 6 | potwierdzenie natywnego UV: rendery ciała z szablonem | `assets/sprites/player/handoff/p1/` na gałęzi Sola |
| P2 | Sol → GPT 6 | dla każdej części stroju: `<czesc>_uv.png`, `_ao.png`, `_curvature.png`, `_normal_sculpt.png`, `_height_ground.png`, `_id.png`, `_preview.png` + `manifest.json` (rozdzielczość, gęstość, opis części) | `assets/sprites/player/handoff/p2/` |
| T1 | GPT 6 → Sol | skóra i tęczówka | `assets/textures/characters/hero/unique/` na gałęzi GPT 6 |
| T2 | GPT 6 → Sol | tekstury części stroju | jw. |

Każde przekazanie ma `manifest.json` z SHA-256 plików i rewizją źródła. Odbiorca kopiuje pliki do siebie, nie scala cudzej gałęzi w całości.

## Co zostaje bez zmian
Kontrakt renderu (kamera, skala, światło, eksport), Blender 4.3, renderer tylko do odczytu, audyt SHA, zapakowane obrazy w `.blend`, uczciwe raporty ograniczeń.

## Przejęcie wyglądu (od 27.10.2026)

Bazą jest `bohater_v2.blend` z `c51bc52`: ciało, szkielet, natywne UV, skóra GPT 6 i narzędzia kontroli zostają. Metoda: po każdym etapie plansza obok konceptu i pomiar sylwetki (skill [`donth77/blender-game-skills`](https://github.com/donth77/blender-game-skills), MIT, zgoda autora).

| Etap | Zakres | Dowód do akceptacji autora |
|---|---|---|
| **G1 — głowa** | wyraz surowy (brwi w dół, zmarszczka gniewna), szersza żuchwa, włosy w kosmykach do żuchwy z siwizną, gęsta krótka broda z siwym podbródkiem, kaptur bez grud przy żuchwie | portret 768 i zbliżenie 1× obok konceptu 19 |
| **G2 — sylwetka stroju** | koszula, kaftan z panelami, pasy i sakwy, buty z kostką i wywinięciem, kaptur z peleryną, płaszcz, plecak — z wykrojów zszywanych symulacją tkaniny | przód, bok, tył obok konceptu 17; 8 kierunków 1× na tle lasu; 0 przenikań |
| **G3 — przekazanie** | nowe P2 dla GPT 6 (część B briefu), potem F5 i bramka B2 | manifest P2 z SHA |

Do czasu G2 GPT 6 nie maluje stroju — UV części się zmienią.
