# Pochodzenie pakietów skilli

## Projektowanie gier — 19 skilli

Źródło: https://github.com/gamesdesigners-source/agent-game-design-skills

Wersja zainstalowana: `8f9d79adf52444c4ca1ee114efa4b85c09f4f48f`.

Zainstalowano 19 skilli z katalogu `skills/`, pomijając `_template`, razem z ich skryptami i referencjami. Pliki skilli pozostają niezmienione względem tej wersji. Zostały dodane do Git, aby instrukcje projektowe towarzyszyły repozytorium.

Licencja MIT i oryginalna informacja o autorach: [SKILLS-LICENSE](SKILLS-LICENSE). Licencja dotyczy tego pakietu; nie ustanawia licencji całej gry.

Część instrukcji pakietu odwołuje się do pełnej struktury GDD upstream. Nasz projekt korzysta obecnie z dokumentów w `docs/`, z rozróżnieniem decyzji i propozycji. Nie utworzono automatycznie kompletnego rejestru kanonu ani wszystkich szablonów upstream.

## Grafika — 5 skilli z repozytorium autora

Źródło: https://github.com/DawidWrona92/skills

Wersja zainstalowana: `1527a5173886e3b66b63296cb4d2483d4d3bb6a1` (pakiet v4).

Skille: `retro-rts-sprites`, `painted-rts-sprites`, `rts-prerender-3d`, `rts-sprite-router`, `rpg-godot-pipeline`.

Zachowano układ katalogów źródłowych wewnątrz `skills/`, w tym `shared/`, `demo/` i `tests/`, ponieważ instrukcje oraz skrypty korzystają ze względnych odwołań. Zaimportowano 89 śledzonych plików bez zmian; pominięto wyłącznie niezwiązany z narzędziami plik `Help`. Nie kopiowano metadanych `.git`. Wcześniejszy pakiet projektowania gier pozostaje nienaruszony.

Zachowane informacje o pochodzeniu: [LICENSE-NOTICE.md](skills/LICENSE-NOTICE.md) i [LICENSE-INSPIRATIONS.md](skills/LICENSE-INSPIRATIONS.md). Licencja MIT pierwszego pakietu nie jest przypisywana temu zestawowi.

Instrukcje upstream: [README](skills/README.md). Bieżące wyniki weryfikacji: [instalacja skilli graficznych](../docs/skills-graficzne.md). Pliki `STATUS.json` i `tests/RESULTS_*` są niezmienionymi zapisami dostarczonymi przez źródłowe repozytorium.

## Dodatkowy pixel-art — 1 skill

Źródło: https://github.com/junyudev/pixel-art

Wersja: `d3374bd93d56a0834704d7643496b7ebf07b9fda`. Zainstalowano 30 plików z `skills/pixel-art/` oraz główny `LICENSE`. Pliki upstream pozostają niezmienione; dodano lokalny `AGENTS.md` z regułami integracji. Nie kopiowano strony benchmarkowej ani jej assetów.

Licencja i wyjątki: [pixel-art/LICENSE](skills/pixel-art/LICENSE). Wynik sprawdzenia zgodności oraz prób funkcjonalnych: [zgodność pixel-art](../docs/zgodnosc-pixel-art.md). Nowy warsztat uzupełnia zestaw jako osobny wariant pixel-artu; nie zastępuje pre-renderów ani nie narzuca stylu Eastward.
