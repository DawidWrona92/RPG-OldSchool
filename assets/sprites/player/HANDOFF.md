# Bohater v2 — HANDOFF

**Aktywne źródło: [source/bohater_v2.blend](source/bohater_v2.blend).** Stan: F0–F3 / przekazanie do F4, przed oceną B1/B2. Bez animacji i atlasów v2.

Gałąź `vibe/sprite-bohater-codex`. Commit modelu `ad5f69d0095317310f17f463616904488474b13a`. SHA-256 `6947b81d85b8b358483bd221e8f196da77a023454fa09d82956e55ff260015e5`, rewizja `v2-F3-equipment-review-16`. Wszystkie bieżące podglądy i P2 odnoszą się do tego źródła.

[Przegląd](reviews/v2-f0-f3/index.html) · [raport](V2_REVIEW.md) · [P1](handoff/p1/manifest.json) · [P2](handoff/p2/manifest.json) · [opis P2](handoff/p2/README.md).

## Decyzje obowiązujące

- Wymagania pisemne i decyzje autora przed konceptami. Głowa według 19; strój według 17. Starszy, ogorzały podróżnik, pełne policzki i mocna żuchwa, ciężkie brwi, zmęczony surowy wyraz.
- Włosy średniej długości do linii żuchwy, ciemnobrązowe z siwizną, potargane; gęsty zarost i wąs, więcej siwizny na podbródku. Blizny/pieprzyki tylko z tekstury.
- D1 miecz w pochwie przy lewym biodrze. D2 pełna grupa body MakeHuman z nietkniętym natywnym UV. D3 default.mhskel, 163 kości, default_weights.mhw.
- Nie animować i nie eksportować atlasów przed B2. Sześć statycznych póz diagnostycznych nie jest produkcją animacji.

## Co jest gotowe do przekazania

- Pełne ciało, native UV, 163 kości; P1: przód/bok/¾ z siatką UV i sześć prób deformacji. Ocenę B1 wykonuje autor/PM, nie automat.
- F2 według 19 i **skóra v3** z `bc1da517031a63dabad00380e95566f32f2f3c65`: 51 plików zgodnych z manifestem, 7 używanych obrazów spakowanych i zgodnych bajtowo. Normal 0,45, maska SSS ×0,30, height niepodłączony obok normalnej.
- F3: 22 części, własne UV ~1024 px/m, trzy utrwalone drapowania Cloth z późniejszymi poprawkami artystycznymi. Plecak i posłanie dopasowane do kontaktu, paski/sprzączki butów i pasy posłania są geometrią.
- **P2 kompletne: 154 PNG**, siedem na część, 2K + podgląd 768, manifest SHA, `complete: true`. Normal/AO/curvature/height/ID/UV mają opis metod i ograniczeń. Obecne materiały stroju są tymczasowe, oczekują F4 od GPT 6.
- Narzędzie z main: neutralna klatka 1, 0 niedozwolonych przecięć po jawnych wyjątkach oczu i głowicy/rękojeści. Brak wyjątków dla stroju. Nie obejmuje Curves, samoprzenikania jednej siatki ani ruchu.
- Powtórzony S/body+shadow z zapisanego pliku: identyczne zdekodowane piksele `True`. Nie powtarzano wszystkich map P2 ani całych ośmiu kierunków.

## Co jest otwarte

**Tęczówka v3 jest brązowa. Szarozielona oczekuje v4 od GPT 6.** Nie przemalowano jej zastępczo. Głowa/groom wymagają oceny z 19; włosy i linia zarostu mogą być nadal zbyt regularne. Strój czeka na unikatowe tekstury, zużycie, wilgoć i błoto F4. B2 nie jest zatwierdzone, kontrola statyki nie dowodzi jakości ruchu. Wagi/deformacje stroju wymagają oceny przy przyszłym B3.

## Wznowienie i podmiana tekstur

1. Pracować na bieżącym `.blend`, sprawdzić `git status`, często commitować i pushować. Recepty `v2_*.py` są zapisem kolejnych poprawek z guardami rewizji, nie krokiem renderu i nie regeneracją ręcznie poprawionego źródła.
2. `v2_render_static.py` czyta model, nie zapisuje go. `--mode game` zachowuje kamerę kontraktu; `portrait`, `model`, `p1` to diagnostyka. Audyt zawiera źródło/renderer/obrazy SHA. Przy zmienionym źródle nie przepisywać starych audytów.
3. Po otrzymaniu v4 skopiować tylko paczkę `unique/` z podanego commitu, bez scalania gałęzi. `v2_refresh_textures.py -- --version 4 --commit <pełny SHA>` w Blenderze na aktywnym źródle weryfikuje manifest, przeładowuje/packuje obrazy pod tymi samymi nazwami i sprawdza nienaruszenie geometrii, UV, rigu i Curves. **Przygotowany skrypt skompilowano, nie wykonywano go z nieotrzymaną v4.** Nowe źródło wymaga nowych podglądów/SHA; starszych manifestów nie aktualizować po cichu.
4. P2 regenerować tylko z właściwego zapisanego źródła. `v2_bake_p2.py -- --resume` sprawdza zgodność źródła/bakera i gotowych plików; po zmianie modelu zachować starszą paczkę osobno i wykonać świeże wypalenia. `v2_finish_p2.py` weryfikuje kompletność i generuje szablony UV.
5. Po F4 zintegrować tekstury stroju bez zmiany kamery/światła/skali, ponowić podglądy i pełny audyt main, przekazać B2 autorowi. Dopiero po zgodzie B2 wrócić do spoczynku/chodu, prędkości, każdej klatki kolizji i atlasów.

Archiwum rev08/detale, ich atlasy i podglądy pozostały bez zmian. Sumy w `source/archive-sources.json`; nie są aktualnym eksportem v2. Pochodzenie/CC0 MakeHuman i targetów w `source/third_party/`, pochodzenie i ograniczenia tekstur w `unique/manifest.json` i `README.md`.
