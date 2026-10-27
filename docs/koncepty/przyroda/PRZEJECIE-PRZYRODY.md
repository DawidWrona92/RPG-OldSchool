# Przejęcie zakresu „przyroda i teren”

**Status: [DECYZJA AUTORA, 27.10.2026] dotychczasowy wykonawca (GLM 5.3) wstrzymany; zakres czeka na następcę.** Dokument przygotował PM zamiast `HANDOFF.md`, którego poprzedni wykonawca nie zostawił. Rejestr: [WYKONAWCY.md](../../WYKONAWCY.md).

## Punkt startu

| | |
|---|---|
| Gałąź poprzednika | `vibe/environment-stones-mistral` |
| Ostatni commit | `6882bad` (27.10.2026, 18:20) — grupa A (kamienie) + poprawki + grupa B (krzewy) |
| Katalog | `assets/environment/stones-mistral-01/` |
| Następca pracuje na | **nowej gałęzi** od `6882bad`, np. `vibe/environment-przyroda-<wykonawca>` (AGENTS.md, zasada 6) |
| Czytać najpierw | [kontrakt renderu](../../art/KONTRAKT-RENDERU.md) (w tym „Duże obiekty” i warianty obrotu), [plan assetów przyrody](PLAN-ASSETOW.md), [arkusze przyrody](README.md), [przewodnik Niemiru](../../art/niemir/NIEMIR_ART_DIRECTION.md) rozdz. 03 |

## Co działa — zachować

Sprawdzone przez PM na `6882bad`:

- **Kontrakt renderu:** Blender 4.3, kamera i trzy światła 1:1 z bohaterem (kształt DISK, obroty), AgX, 64 próbki, seed 1703, render 2× i zmniejszenie z premultiplikowaną alfą, cień jako sama alfa (RGB = 0).
- **Odtwarzalność:** scenę można zbudować od nowa skryptem z tekstur w repozytorium, a render z odbudowanej sceny jest **identyczny co do piksela** z eksportem (48/48 plików). Źródłem są więc skrypty i `textures_src/`, nie plik `.blend`.
- **Metadane:** `export/env_01.json` — `frame_size`, kotwica liczona rzutem kamery (`world_to_camera_view`), wymiary 3D, `visible_height_m`, obrys kolizji w świecie.
- **Duże klatki:** głazy 256 i 512 px, kotwica (N/2; N/2 + 62,354), cień w rozmiarze obrazu.
- **Szczelne bryły:** 0 otwartych krawędzi nad ziemią we wszystkich kamieniach, głazach, płytach i żwirze.
- **Rośliny:** otwarte karty z alfą (jak włosy postaci) — właściwa technika do prerenderu.

## Odtworzenie

Środowisko: `bpy==4.3.0` na Pythonie 3.11 (kontrakt, „Wersja Blendera i środowisko”) + `numpy<2`, `pillow`.

```bash
cd assets/environment/stones-mistral-01
# 1. Budowa sceny ze skryptu (zapisuje .blend; tekstury z textures_src/)
WELESZA_TEX=$PWD/textures_src WELESZA_BLEND=/tmp/env.blend python source/build_env_v43.py
# 2. Render wszystkich assetów + audyt SHA-256
WELESZA_BLEND=/tmp/env.blend WELESZA_OUT=/tmp/env_out python source/render_env_v43.py
# 3. Metadane env_01.json
WELESZA_OUT=/tmp/env_out python source/make_env_json.py
# 4. Kontrola (z katalogu głównego repozytorium)
python tools/art/check_env_export.py assets/environment/stones-mistral-01/export \
  --fresh /tmp/env_out --blend /tmp/env.blend
```

[`tools/art/check_env_export.py`](../../../tools/art/check_env_export.py) sprawdza rozmiary klatek i cieni względem JSON, krawędzie klatek, kotwice, identyczność ze świeżym renderem i szczelność brył. Kod wyjścia 1 przy błędzie.

## Długi techniczne do spłacenia na start

1. `source/build_env_v43.py` ma **wpisane ścieżki** `/workspace/github__…` i `/workspace/envwork` — zastąp ścieżkami względnymi do katalogu skryptu.
2. W tym samym skrypcie sekcje „GRUPA B: krzewy niskie” i „RUNO: trawa, paprocie, chrust” są **zdublowane** (druga definicja nadpisuje pierwszą) — zostaw jedną.
3. `source/make_env_json.py` ma domyślny katalog `/workspace/envwork/renders_v43` — ustaw domyślnie `export/`.
4. **Repozytorium:** poprzednik commitował `.blend` (dziś 98 MB) w każdej iteracji, a `textures_src/` (32 MB) dubluje tekstury spakowane w `.blend`. Ponieważ scena odtwarza się ze skryptu co do piksela, **nie commituj `.blend` w ogóle** (albo tylko przy zamknięciu grupy, na sygnał PM).

## Otwarte uwagi z ostatniego review (wygląd)

| # | Asset | Problem | Oczekiwane |
|---|---|---|---|
| a | `krzew_a`, `krzew_b` | kilka płaskich ciemnozielonych wycinanek na czarnych patykach — „skrawki papieru” | gęsta, zaokrąglona bryła: rozgałęziony szkielet, dziesiątki–setki małych kart liści w kępach, jaśniejsze końce od strony światła, ciemniejsze wnętrze; gałązki szarobrązowe. Wysokości: 0,4–0,6 / 0,5–0,7 m + nowy `krzew_c` 0,7–0,9 m |
| b | `glaz`, `glaz_duzy`, kamienie | cała bryła jednolicie zielona i gładka, kilka wielkich płaskich ścian — „zielony plastik”; `glaz` ma 0,67 m nad ziemią | skała szara (chłodna, z ciepłym przełamaniem), mech tylko na górnych powierzchniach z przerwami, porosty jako jaśniejsze plamy; mniejsze, nieregularne płaszczyzny z fazami; `glaz` 1,0–1,4 m nad ziemią |
| c | `paproc_a`, `paproc_b` | wyglądają jak małe świerczki | frondy szeroko w rozetę, łukiem opadające na boki, listki po obu stronach osi; 0,6–1,0 m |
| d | `chrust_a`, `chrust_b` | neutralnie szare jak aluminiowe rurki | ciepła, szarobrązowa kora, zmienność między gałązkami, ciemniejsze końce |
| e | `plyta_kamienna_b` | pionowe pasy rozciągniętej tekstury na bokach | poprawne mapowanie boków (box projection z blendem) |

Odniesienie wyglądu: [arkusze przyrody a–d](README.md). Zasada autora: zapisane wymagania są nadrzędne wobec konceptów.

## Pierwsze zadanie następcy

1. Spłać długi techniczne 1–3.
2. Zrób **dwa assety wzorcowe**: jeden krzew i jeden głaz według uwag a i b. Oddaj planszę 3× na `assets/textures/environment/ground/forest_litter_mixed.png` z cieniem oraz test skali 1× z klatką bohatera.
3. Po akceptacji PM i autora — poprawki c–e, reszta grupy B, potem grupy C (pniak z korzeniami, korzenie wystające) i D (jedna sosna wzorcowa do decyzji autora) według [planu](PLAN-ASSETOW.md).
4. Na koniec każdej sesji: `HANDOFF.md` w katalogu roboczym (AGENTS.md, zasada 8).
