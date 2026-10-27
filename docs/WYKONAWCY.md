# Wykonawcy i przekazywanie pracy

**Rejestr prowadzi PM; stan na 27 października 2026 r.** Kto prowadzi który zakres, na jakiej gałęzi, od czego zależy i kto go przejmie, jeśli wykonawca się zmieni. Zasady współpracy są w [AGENTS.md](../AGENTS.md).

Autorstwo commitów nie identyfikuje wykonawcy (część pracuje z konta autora), dlatego obowiązuje ten rejestr i nazwa gałęzi.

## Aktywni

| Wykonawca | Rola | Gałąź | Zakres teraz | Wejście (czytać najpierw) | Zależy od / przekazuje |
|---|---|---|---|---|---|
| **Claude** (Anthropic) | PM: dokumentacja na `main`, review, decyzje do autora, narzędzia kontroli | `main` przez krótkie gałęzie `porzadki/*` | review i koordynacja; [test silnika](SILNIK.md) na `vibe/godot-test-silnika` | ten plik, [INDEX](INDEX.md), ostatnie review w `docs/art/` | akceptuje bramki razem z autorem |
| **GPT Sol** (OpenAI) | bohater — wzór postaci ludzkiej: model, szkielet, strój, render, animacje | `vibe/sprite-bohater-codex` | fazy F0–F3 [planu naprawy](art/characters/PLAN-NAPRAWY-BOHATERA.md) | [plan naprawy](art/characters/PLAN-NAPRAWY-BOHATERA.md), [review](art/characters/REVIEW-BOHATER-01.md), [kontrakt](art/KONTRAKT-RENDERU.md) | bierze tekstury od GPT 6; oddaje P1/P2 dla GPT 6 |
| **GPT 6** (OpenAI) | unikatowe tekstury bohatera | `vibe/hero-textures-gpt6` | skóra i oko — v3 (`bc1da51`); część B (strój) czeka na P2 od Sola | [brief tekstur](art/characters/tekstury-bohatera/BRIEF-TEKSTURY.md) | oddaje tekstury Solowi (T1, T2) |
| *wakat* | przyroda i teren: kamienie, runo, pniaki, drzewa | następca: nowa gałąź od `6882bad` | **do przejęcia** — [pakiet przejęcia](koncepty/przyroda/PRZEJECIE-PRZYRODY.md) | [pakiet przejęcia](koncepty/przyroda/PRZEJECIE-PRZYRODY.md), [plan przyrody](koncepty/przyroda/PLAN-ASSETOW.md) | niezależny; test skali z klatką bohatera |

## Zamknięte i archiwalne

| Gałąź / zakres | Kto | Stan |
|---|---|---|
| Materiały bohatera, paczki 01–03 | GPT 6 | scalone z `main` (`assets/textures/characters/hero/`) |
| Walidator mapy świata i 16 testów | GPT 6 | scalone z `main` (`tools/world/`) |
| Przewodnik artystyczny Niemiru | GPT 6, potem aktualizacje PM | na `main`, v1.2 |
| Plan przyrody i arkusze konceptów | GLM 5.3 | scalone z `main` |
| `vibe/environment-stones-mistral` — przyroda: kamienie, głazy, żwir, płyty, runo, krzewy | GLM 5.3 | **wstrzymany 27.10.2026** (decyzja autora); stan `6882bad`, przejęcie: [pakiet](koncepty/przyroda/PRZEJECIE-PRZYRODY.md) |
| `obsolete-sprites` — sprite'y dawną metodą (pixel-art, SDF) | Claude i inni | archiwum, bez dalszej pracy |
| `vibe/environment-forest-prototype-gpt6` — prototyp skraju lasu | GPT 6 | archiwum przed kontraktem renderu |
| `vibe/environment-wagon-blockout` — bryła wozu | *do uzupełnienia przez autora* | prototyp; wóz wymaga nowej realizacji według kontraktu |
| `vibe/godot-test-silnika` — test Godota | Claude | wynik w [SILNIK.md](SILNIK.md); gałąź zostaje jako wzór importu |

## Zmiana wykonawcy — co przejmuje następca

1. **Gałąź:** następca kontynuuje na tej samej gałęzi dopiero wtedy, gdy poprzednik przestał na niej pracować; w razie wątpliwości zakłada nową gałąź od ostatniego commita poprzednika (AGENTS.md, zasada 6).
2. **Stan:** czyta `HANDOFF.md` w katalogu roboczym zakresu (np. `assets/sprites/player/HANDOFF.md`) — ostatni commit, co działa, otwarte problemy, następny krok, polecenia odtworzenia.
3. **Wejście:** dokumenty z kolumny „Wejście” i ostatnie review PM.
4. **Kontrola przed zmianami:** odtwarza ostatni eksport poprzednika i porównuje sumy SHA z audytem — dopiero potem zmienia źródła.
5. **Rejestr:** PM wpisuje zmianę do tabeli „Aktywni”.

| Zakres | Proponowany zastępca (decyduje autor) |
|---|---|
| Bohater i postacie ludzkie (Blender, rig, strój) | Claude Opus 5.5 na wysokim poziomie wysiłku albo Claude Fable 5.1 do najtrudniejszych etapów |
| Tekstury postaci | GPT Sol (zna model i UV) albo inny wykonawca z briefem tekstur |
| Przyroda i teren | GPT Sol lub Claude Sonnet 5.5 — pipeline GLM jest odtwarzalny skryptami |
| PM | nowa sesja Claude: ten plik, INDEX i ostatnie review |

## Obowiązek każdego wykonawcy

Na końcu każdej sesji pracy aktualizuj `HANDOFF.md` w swoim katalogu roboczym: hash ostatniego wypchniętego commita, co zrobiono i sprawdzono, otwarte problemy, następny krok i polecenia odtworzenia. Bez tego zakres nie może zostać przekazany.
