# Welesza — zasady dla współtwórców i agentów LLM

W pierwszej kolejności przeczytaj [README](README.md), [indeks dokumentacji](docs/INDEX.md), [fabułę](docs/demo-fabula.md) i właściwy dokument zakresowy.

1. **`main` jest źródłem prawdy dla fabuły, mechanik, topologii świata, zatwierdzonej stylistyki i ilustracji referencyjnych.**
2. Odróżniaj ustalenia autora od propozycji i testów. Nie dopisuj faktów o świecie ani zasad gry wyłącznie na podstawie grafiki koncepcyjnej.
3. Aktualny kierunek wizualny Niemiru opisuje [art direction](docs/art/niemir/NIEMIR_ART_DIRECTION.md); postacie i otoczenie mają [bibliotekę referencji](docs/koncepty/README.md).
4. **Sprite'y renderujemy w Blenderze (Cycles) według [kontraktu renderu](docs/art/KONTRAKT-RENDERU.md)** — ta sama kamera, skala, kierunki, kotwica, światło i format eksportu dla postaci i otoczenia. Wzorzec techniczny: bohater z gałęzi `vibe/sprite-bohater-codex`. Historyczne generatory i skille graficzne (pixel-art, SDF, router RTS) nie są kontraktem produkcyjnym. Silnik gry: Godot 4.7.2 — [decyzja warunkowa](docs/SILNIK.md); projekt Godota powstaje na gałęziach roboczych.
5. Nie przenoś na `main` plików źródłowych generatorów grafiki, silnika, atlasów, animacji ani renderów testowych w ramach porządkowania dokumentacji.
6. Pracę implementacyjną prowadź na własnym branchu. Nie nadpisuj aktywnych branchy innych wykonawców; najpierw porównaj zmiany.
7. Podczas redagowania dokumentacji zachowaj linki względne oraz wersje Markdown i PDF tego samego przewodnika w zgodzie.
8. Kto prowadzi który zakres i kto go przejmuje — [rejestr wykonawców](docs/WYKONAWCY.md). Na końcu każdej sesji aktualizuj `HANDOFF.md` w swoim katalogu roboczym (ostatni commit, stan, otwarte problemy, następny krok).

Ten plik ustala współpracę i hierarchię dokumentów. Specyfikacją obrazu jest kontrakt renderu, a wyboru silnika — [SILNIK.md](docs/SILNIK.md); grywalnej implementacji jeszcze nie ma.
