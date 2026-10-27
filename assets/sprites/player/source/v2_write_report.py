"""Raport i HANDOFF z rzeczywiście zakończonego przeglądu/P2, bez zmiany źródła."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'reviews/v2-f0-f3'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=read(OUT/'source-validation.json');frames=read(OUT/'frame-validation.json');collision=read(OUT/'intersection-validation.json');repro=read(OUT/'reproduction-validation.json');p2=read(ROOT/'handoff/p2/manifest.json');package=read(OUT/'p2-validation.json');p1=read(ROOT/'handoff/p1/body-validation.json');source=read(ROOT/'source/bohater_v2.source.json');poses=read(ROOT/'handoff/p1/poses/manifest.json');digest=sha(ROOT/'source/bohater_v2.blend')
assert all(m['source_blend_sha256']==digest for m in [s,frames,collision,repro,p2,package,p1,source,poses]);assert p2['complete'] and source['skin']['version']==3
branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();modelcommit=subprocess.check_output(['git','log','-1','--format=%H','--','assets/sprites/player/source/bohater_v2.blend'],text=True).strip();names=list(p2['parts']);normalout=sum(p['normal_unit_length_outliers'] for p in package['parts']);normalsample=sum(p['normal_sampled_interior_pixels'] for p in package['parts']);boneerror=max(p['max_bone_length_error_m'] for p in p1['poses']);shadows_clipped=[p['direction'] for p in frames['frames'] if p['shadow_border_max_alpha']>0];identical=all(f['identical_decoded_rgba_pixels'] for f in repro['frames'])
links='[Przegląd HTML](reviews/v2-f0-f3/index.html) · [model](source/bohater_v2.blend) · [manifest źródła](source/bohater_v2.source.json) · [P1](handoff/p1/manifest.json) · [P2](handoff/p2/manifest.json)'
text=f'''# Bohater v2 — F0–F3, do oceny autora

Gałąź `{branch}`. Commit zapisujący model: `{modelcommit}`. SHA-256 źródła: `{digest}`. Rewizja: `{s['revision']}`; Blender {s['blender']}.

**To statyczne źródło i przekazanie do teksturowania, przed B1/B2. Nie jest zatwierdzonym wzorem produkcyjnym.** Nie rozpoczęto animacji ani atlasów v2. Oczekiwane są tekstury stroju F4 i szarozielona tęczówka v4.

{links}

## Plansze i pliki do oceny

- [Koncept 17 ↔ model: przód, tył, bok](reviews/v2-f0-f3/koncept17-model.png), materiały tymczasowe; źródłowe kadry 768 w `reviews/v2-f0-f3/model/`.
- [Koncept 19 ↔ portret](reviews/v2-f0-f3/koncept19-portret.png) i [nieprzeskalowany portret 768](reviews/v2-f0-f3/portrait19/portrait_0.png), skóra GPT 6 v3.
- [Osiem kierunków 1× na tle lasu](reviews/v2-f0-f3/osiem-kierunkow-1x.png), [ciemne tło 1×](reviews/v2-f0-f3/osiem-kierunkow-ciemne-1x.png), osobne RGBA w `reviews/v2-f0-f3/native/` i osobne cienie w `native/shadows/`.
- [Ciało z natywnym UV](reviews/v2-f0-f3/p1-cialo-uv.png) i [sześć pojedynczych póz diagnostycznych](reviews/v2-f0-f3/p1-szesc-poz.png). To testy statyczne, nie animacje.
- [P2 — opis map](handoff/p2/README.md), [manifest z pełną listą 154 PNG i SHA](handoff/p2/manifest.json).

Koncepty 17 i 19 są **ilustracjami koncepcyjnymi, nie sceną gry ani renderem źródła**. Plansza porównawcza ma diagnostycznie dopasowane kadry. W próbie 1× użyto niezmienionego wycinka 17: skala tła nie jest pewna, przyjęto dla postaci 60 px/m. Postaci nie powiększano względem wycinka. Plik `.blend` i osobne PNG zachowują przezroczystość.

## Co zmieniono

**F0:** `bohater.blend` rev08 i `bohater_detale.blend` pozostają nienaruszonym archiwum, z sumami w `source/archive-sources.json`. Ich stare atlasy/rendery nie przedstawiają v2. Nowa praca ma jedno nadrzędne źródło `bohater_v2.blend`; aktualne instrukcje w README/HANDOFF, stare w `README-ARCHIVE-PROTOTYPE.md`.

**F1:** pełna grupa `body` MakeHuman CC0, {s['body']['vertices']} indeksów OBJ, {s['body']['faces']} ścian i {s['body']['uv_loop_count']} narożników natywnego UV. Mężczyzna 1,8 m, stary i silny, targety CC0 na tej samej topologii. Szkielet `default.mhskel`: **163 kości**, pełne wagi `default_weights.mhw`, bez remapowania do starego rigu 17 kości. Utrwalono neutralną pozę: opuszczone ramiona, luźniejsze przedramiona i dłonie. To dopasowany rig, nie obietnica gotowego ruchu.

**F2:** po nowej decyzji autora podstawą twarzy jest 19, a nie 17. Cofnięto zapadnięcie policzków, wzmocniono pełną żuchwę i łuki brwiowe, dodano makrobruzdy czoła/glabelli i worki pod oczami. Blizny i pieprzyki pozostają w teksturze. **65 000 natywnych włókien Curves**: średniej długości włosy, broda, wąs i brwi, ciemnobrązowe z siwizną, więcej siwych na podbródku. Groom dostał warstwy, falowanie i nierówne końce po odrzuceniu zbyt równej kurtyny. Oczy mają osobne kule, tęczówki i rogówki IOR 1,376. Tęczówka v3 jest nadal brązowa — szarozielona oczekuje v4.

Skóra v3 z `{source['skin']['commit']}`: zweryfikowano **51 plików** manifestu, skopiowano katalog bez scalania gałęzi. Siedem używanych obrazów jest spakowanych; ich bajty ponownie porównano z plikami paczki. Albedo/oczy sRGB, dane Non-Color, normal OpenGL strength 0,45; maska SSS × 0,30, promienie R > G > B. Height pozostaje niepodłączony obok normalnej, aby nie dublować reliefu; umowny zakres mikrodetalu do 0,002 m. Brak osobnej geometrii blizn/pieprzyków.

**F3:** {len(names)} osobne części z własnym UV, średnio 1024 px/m, 2K na część. Koszula/kaftan/spodnie mają szwy paneli, tkaniny otwarty rozkrój. Ciało pozostaje pod ubraniem. Scena ma **{len(s['actor_meshes'])} renderowanych siatek postaci** i 8 obiektów Curves, zamiast 207 osobnych siatek starego passu.

Kaptur, peleryna i płaszcz przeszły rzeczywiste drapowania Cloth z kolizjami i self-collision, utrwalone w siatkach. Pierwsze niestabilne drapowanie odrzucono; drugie użyło 16 klatek, 6 kroków jakości i grawitacji ×0,35. **Finalna geometria jest po późniejszych poprawkach artystycznych i dopasowaniu kontaktów**, nie jest niezmienionym wynikiem solvera. Wolny brzeg peleryny opuszczono po ocenie dużego renderu; skorygowano jej luzy względem płaszcza. Nie ma zależności od cache symulacji.

Kaftan ma osobne panele, otwarty przód i brzegi zachodzące na spodnie; rękawy kończą się przy łokciach. Płaszcz ma pionowe fałdy i nierówny dolny brzeg. Duży plecak ma ukształtowaną klapę/kieszenie i sprzączki; jego wyściółkę dopasowano do ubrania, posłanie osadzono na górze i dodano dwa pasy. Buty mają wysokie cholewy, wywinięcia, podeszwy oraz rzeczywiste paski i metalowe sprzączki. **D1: miecz w pochwie przy lewym biodrze**, z otwartym wlotem. Nie produkowano wersji dobytej ani ruchów walki.

## P2 — wydanie do GPT 6

**{len(names)} części, 154 PNG, `complete: true`**, ta sama rewizja źródła co powyższe rendery. Każda część: `_uv`, `_ao`, `_curvature`, `_normal_sculpt`, `_height_ground`, `_id`, `_preview`.

{', '.join('`'+n+'`' for n in names)}.

AO jest rzeczywistym wypaleniem Cycles z otoczeniem stroju i zasięgiem 0,15 m; może być ciemne pod innymi warstwami. Curvature to podpisany lokalny Laplacian geometrii, nie skan. Normalna powstaje z ewaluowanych fałd/Subsurf/Solidify do bazowego UV — nie opisujemy jej jako ręcznie rzeźbionego high-poly. Height ground to Z / 1,8 m, do błota/wilgoci, nie displacement. Scalar maps są liniowe 16-bit, normal/ID RGB 8-bit, UV RGBA, podglądy szare 768 RGBA. AO nie należy wpisywać na stałe do koloru albedo.

Kontrola [P2](reviews/v2-f0-f3/p2-validation.json) odczytała i zweryfikowała SHA, formaty oraz wymiary wszystkich 154 PNG. Długość wektorów normalnych sprawdzono na {normalsample:,} pikselach wewnątrz wysp UV; odchyłki powyżej 0,012: **{normalout:,}**. Liczby i ewentualne ubytki dla każdej części są jawne w raporcie, nie zastępują oceny malarskiej.

## Faktycznie wykonane kontrole

| Zakres | Wynik |
|---|---|
| Kamera, światła, AgX, ekspozycja, Blender | Odczyt zapisanej sceny: zgodne z kontraktem; [raport źródła](reviews/v2-f0-f3/source-validation.json) |
| UV ciała / topologia | Te same indeksy i kolejność pętli; maks. różnica UV {s['body']['native_uv_max_float_error']:.3g}, wynik reprezentacji float32 |
| Kości / wagi | 163 nazwy zgodne z `mhskel`; suma wag {p1['body_weight_sum_range'][0]:.9f}–{p1['body_weight_sum_range'][1]:.9f} |
| Sześć prób deformacji | Skończone współrzędne i rzeczywiste przemieszczenia; maks. zmiana długości kości {boneerror:.3g} m; osobne obrazy do oceny zapadnięć |
| Przenikania, neutralna klatka 1 | **0 niedozwolonych par / 0 par trójkątów**; [pełny zakres i wyjątki](reviews/v2-f0-f3/intersection-validation.json) |
| Rzeczywiście dopuszczone styki | 6 par osadzenia oczu pod powiekami i `glowica~rekojesc`; łącznie 7 par / 974 pary trójkątów przed odjęciem. Żadnego wyjątku dla ubrania, plecaka, butów lub płaszcza |
| Widoczność w audycie | Ciało i wszystkie 22 części włączone do renderu; nic nie ukryto dla uzyskania zera |
| Kierunki / alfa / granice | 8 różnych renderów, bez odbić; RGBA postać i cień, postać nie dotyka brzegu; [klatki](reviews/v2-f0-f3/frame-validation.json) |
| Brzeg cienia | {('Bez przycięcia w ośmiu kierunkach.' if not shadows_clipped else 'Alfa na brzegu w: '+', '.join(shadows_clipped)+'. Cień może być przycięty zgodnie z kontraktem.')} |
| Powtórzenie z zapisanych źródeł | Ponowny osobny proces Blendera: S, klatka 1, postać i cień; identyczne zdekodowane piksele: **{identical}**; [pomiar różnic](reviews/v2-f0-f3/reproduction-validation.json) |
| Archiwum / atlas | Sumy obu starych `.blend` bez zmian. Nie wygenerowano atlasów ani animacji v2; stare eksporty są archiwum |

Narzędzie PM bada **wszystkie renderowane MESH po modyfikatorach**, również warstwy stroju. Nie bada Curves, samoprzenikania jednej siatki, całkowitego zawierania jednej bryły w drugiej ani ruchu. Nie deklarujemy pełnej kontroli kolizji ani naturalności animacji. Kontakty włosów z ubraniem oceniano wizualnie w dużych widokach; nie ma automatycznej walidacji wszystkich włókien.

## Kontrakt i ograniczenia do dalszej oceny

192×192 RGBA, supersampling 384→192 przez premultiplikowany Lanczos; osobny cień; 60 px/m. Kamera 30°, ortho 3,2 m, kotwica nominalna (96; 158,353829), rzeczywisty rzut zapisany w raporcie źródła. Kierunki S, SW, W, NW, N, NE, E, SE, obroty −45°. Nie zmieniono światła ani ekspozycji i nie powiększano postaci w świecie. Większe widoki mają osobne kamery diagnostyczne.

Nie ma w v2 animacji spoczynku/chodu, prędkości chodu ani nowych atlasów. Te parametry będą ustalane i mierzone w B3/B4 po zgodzie B2; dane ruchu starego rev08 nie są przedstawiane jako wynik v2.

**Otwarte:** szarozielona tęczówka v4, unikatowe tekstury stroju F4 oraz ocena artystyczna głowy i sylwetki. Włosy i przejście zarostu nadal mogą czytać się zbyt regularnie wobec 19; nie zakładamy ich akceptacji. Plecak, fałdy i wykończenie stroju pozostają interpretacją roboczą do oceny w 1× i zbliżeniach. Kontrast tymczasowych, płaskich materiałów nie jest oceną końcowych tkanin/skór. Sześć póz nie zastępuje pełnego zakresu deformacji, a statyka nie dowodzi gotowości stroju do ruchu.

Źródła MakeHuman/targetów: CC0, przypięta rewizja i SHA w `source/third_party/`. Skóra GPT 6 jest autorską interpretacją proceduralną, nie skanem. Oczy zachowują pochodzenie repozytoryjne i ograniczenie nieudokumentowanego oryginalnego generatora opisane w paczce autora. Nie dodano zewnętrznych fotografii ani assetów z niejasnych źródeł.
'''
(ROOT/'V2_REVIEW.md').write_text(text)
handoff=f'''# Bohater v2 — HANDOFF

**Aktywne źródło: [source/bohater_v2.blend](source/bohater_v2.blend).** Stan: F0–F3 / przekazanie do F4, przed oceną B1/B2. Bez animacji i atlasów v2.

Gałąź `{branch}`. Commit modelu `{modelcommit}`. SHA-256 `{digest}`, rewizja `{s['revision']}`. Wszystkie bieżące podglądy i P2 odnoszą się do tego źródła.

[Przegląd](reviews/v2-f0-f3/index.html) · [raport](V2_REVIEW.md) · [P1](handoff/p1/manifest.json) · [P2](handoff/p2/manifest.json) · [opis P2](handoff/p2/README.md).

## Decyzje obowiązujące

- Wymagania pisemne i decyzje autora przed konceptami. Głowa według 19; strój według 17. Starszy, ogorzały podróżnik, pełne policzki i mocna żuchwa, ciężkie brwi, zmęczony surowy wyraz.
- Włosy średniej długości do linii żuchwy, ciemnobrązowe z siwizną, potargane; gęsty zarost i wąs, więcej siwizny na podbródku. Blizny/pieprzyki tylko z tekstury.
- D1 miecz w pochwie przy lewym biodrze. D2 pełna grupa body MakeHuman z nietkniętym natywnym UV. D3 default.mhskel, 163 kości, default_weights.mhw.
- Nie animować i nie eksportować atlasów przed B2. Sześć statycznych póz diagnostycznych nie jest produkcją animacji.

## Co jest gotowe do przekazania

- Pełne ciało, native UV, 163 kości; P1: przód/bok/¾ z siatką UV i sześć prób deformacji. Ocenę B1 wykonuje autor/PM, nie automat.
- F2 według 19 i **skóra v3** z `{source['skin']['commit']}`: 51 plików zgodnych z manifestem, 7 używanych obrazów spakowanych i zgodnych bajtowo. Normal 0,45, maska SSS ×0,30, height niepodłączony obok normalnej.
- F3: 22 części, własne UV ~1024 px/m, trzy utrwalone drapowania Cloth z późniejszymi poprawkami artystycznymi. Plecak i posłanie dopasowane do kontaktu, paski/sprzączki butów i pasy posłania są geometrią.
- **P2 kompletne: 154 PNG**, siedem na część, 2K + podgląd 768, manifest SHA, `complete: true`. Normal/AO/curvature/height/ID/UV mają opis metod i ograniczeń. Obecne materiały stroju są tymczasowe, oczekują F4 od GPT 6.
- Narzędzie z main: neutralna klatka 1, 0 niedozwolonych przecięć po jawnych wyjątkach oczu i głowicy/rękojeści. Brak wyjątków dla stroju. Nie obejmuje Curves, samoprzenikania jednej siatki ani ruchu.
- Powtórzony S/body+shadow z zapisanego pliku: identyczne zdekodowane piksele `{identical}`. Nie powtarzano wszystkich map P2 ani całych ośmiu kierunków.

## Co jest otwarte

**Tęczówka v3 jest brązowa. Szarozielona oczekuje v4 od GPT 6.** Nie przemalowano jej zastępczo. Głowa/groom wymagają oceny z 19; włosy i linia zarostu mogą być nadal zbyt regularne. Strój czeka na unikatowe tekstury, zużycie, wilgoć i błoto F4. B2 nie jest zatwierdzone, kontrola statyki nie dowodzi jakości ruchu. Wagi/deformacje stroju wymagają oceny przy przyszłym B3.

## Wznowienie i podmiana tekstur

1. Pracować na bieżącym `.blend`, sprawdzić `git status`, często commitować i pushować. Recepty `v2_*.py` są zapisem kolejnych poprawek z guardami rewizji, nie krokiem renderu i nie regeneracją ręcznie poprawionego źródła.
2. `v2_render_static.py` czyta model, nie zapisuje go. `--mode game` zachowuje kamerę kontraktu; `portrait`, `model`, `p1` to diagnostyka. Audyt zawiera źródło/renderer/obrazy SHA. Przy zmienionym źródle nie przepisywać starych audytów.
3. Po otrzymaniu v4 skopiować tylko paczkę `unique/` z podanego commitu, bez scalania gałęzi. `v2_refresh_textures.py -- --version 4 --commit <pełny SHA>` w Blenderze na aktywnym źródle weryfikuje manifest, przeładowuje/packuje obrazy pod tymi samymi nazwami i sprawdza nienaruszenie geometrii, UV, rigu i Curves. **Przygotowany skrypt skompilowano, nie wykonywano go z nieotrzymaną v4.** Nowe źródło wymaga nowych podglądów/SHA; starszych manifestów nie aktualizować po cichu.
4. P2 regenerować tylko z właściwego zapisanego źródła. `v2_bake_p2.py -- --resume` sprawdza zgodność źródła/bakera i gotowych plików; po zmianie modelu zachować starszą paczkę osobno i wykonać świeże wypalenia. `v2_finish_p2.py` weryfikuje kompletność i generuje szablony UV.
5. Po F4 zintegrować tekstury stroju bez zmiany kamery/światła/skali, ponowić podglądy i pełny audyt main, przekazać B2 autorowi. Dopiero po zgodzie B2 wrócić do spoczynku/chodu, prędkości, każdej klatki kolizji i atlasów.

Archiwum rev08/detale, ich atlasy i podglądy pozostały bez zmian. Sumy w `source/archive-sources.json`; nie są aktualnym eksportem v2. Pochodzenie/CC0 MakeHuman i targetów w `source/third_party/`, pochodzenie i ograniczenia tekstur w `unique/manifest.json` i `README.md`.
'''
(ROOT/'HANDOFF.md').write_text(handoff)
checks={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='checksums.json'};(OUT/'checksums.json').write_text(json.dumps({'source_blend_sha256':digest,'files':checks},indent=2)+'\n')
print('V2_REPORT_AND_HANDOFF_READY',digest,'review files',len(checks))
