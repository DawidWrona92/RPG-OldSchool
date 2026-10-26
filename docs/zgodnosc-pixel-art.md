# junyudev/pixel-art — przegląd zgodności i instalacja

Źródło: https://github.com/junyudev/pixel-art
Wersja: `d3374bd93d56a0834704d7643496b7ebf07b9fda`.
Data: 26 października 2026 r.

## Wynik

Zainstalowano jako dodatkowy warsztat prawdziwego pixel-artu w `.agents/skills/pixel-art`. Nie ma kolizji nazwy skilla, plików ani wymaganych wersji środowiska z istniejącym zestawem. Nie należy stosować jego reguł stylistycznych globalnie do wszystkich assetów.

Zachowano 30 plików pakietu `skills/pixel-art/` oraz główny `LICENSE`. Nie instalowano strony benchmarkowej, jej obrazów, fontów ani konfiguracji Vercela. Kod źródłowy pakietu pozostaje niezmieniony; dodano lokalne [AGENTS.md](../.agents/skills/pixel-art/AGENTS.md) opisujące zasady integracji.

## Porównanie

| Obszar | Ocena | Reguła integracji |
|---|---|---|
| Nazwa `pixel-art` | Unikalna wśród wcześniejszych 24 skilli | Instalacja obok, bez nadpisania |
| Python i zależności | Pillow, NumPy, SciPy są dostępne | Nie zmieniano globalnych pakietów ani ich wersji |
| Lokalny moduł `kit` | Brak konfliktu przy zalecanym uruchamianiu izolowanym | `python3 -I -B`; bez globalnego `PYTHONPATH` |
| Pokrycie z `retro-rts-sprites` | Częściowo podobne zastosowanie, ale inny warsztat | Wybór jednego wykonania dla danego assetu, zachowanie źródła |
| Twarda alfa i ograniczona paleta | Pasuje do pixel-artu, różni się od Painted i pre-renderów | Reguła lokalna dla pixel-artu, bez konwersji istniejących renderów |
| Światło i perspektywa | Nowy skill domyślnie światło z lewej góry i widok z góry/przodu; poprzednie narzędzia mają inne domyślne ustawienia | Jawna karta stylu Weleszy przed wspólnym zestawem |
| Eastward | Dołączony przykład stylu, nie przyjęty kierunek naszej gry | Nie narzuca palety, proporcji ani gotowych fragmentów postaci |
| Sprite text | Dodatkowe, odtwarzalne źródło PNG | Zachować tekst i generator; nie zastępuje JSON atlasu |
| Eksport do silnika | Sam skill nie zapewnia zgodności z kontraktem ARPG/Godot | Potrzebne mapowanie kotwicy, ramki, kierunków i czasów; brak deklaracji zweryfikowanego importu |
| Codex CLI / Concept | Opcjonalna ścieżka, zależna od dostępnych narzędzi | Nie instalowano CLI ani nie zmieniano logowania; nie uruchamiano generowania obrazów |

## Rzeczywiste próby

Zainstalowana kopia działa w Python 3.12.14 z Pillow 12.3.0, NumPy 2.3.5 i SciPy 1.17.0. Nie było potrzeby doinstalowywania zależności.

1. **Grid:** wygenerowano techniczny obraz 16×16 z palety i siatki tekstowej. Sprawdzono rozmiar i twardą alfę.
2. **Odtworzenie źródła:** PNG → sprite text → PNG zachowało dokładne piksele RGBA.
3. **Błędne wiersze:** renderer odrzucił siatkę z nierówną długością wierszy.
4. **Błędna paleta:** renderer odrzucił niezdefiniowany znak koloru.
5. **Błędny rozmiar:** renderer odrzucił siatkę niezgodną z zamówionym rozmiarem.
6. **Construct:** uruchomiono dołączony przykład postaci. Po użyciu wspieranej konfiguracji `shadow=None` wynik miał 48×64 px, 15 nieprzezroczystych kolorów, alfę wyłącznie 0/255 oraz dokładną zgodność PNG → tekst → PNG.

Próby wykonano narzędziami `tools/grid.py` i `tools/render_figure.py` z katalogu zainstalowanego skilla. Pliki próbne powstały w `/tmp`, nie w katalogu assetów gry. To testy funkcjonalne narzędzi, nie ocena jakości artystycznej i nie pełny zestaw testów upstream.

## Wykryta niespójność i jej obsługa

Oryginalny `examples/mechanic_idle.py` ma skonfigurowany cień podłoża. Wynik zawiera alfę 90 oprócz 0 i 255, więc nie spełnia ścisłej reguły pixel-perfect z głównej instrukcji. Pierwsza kontrola twardej alfy tego przykładu poprawnie zakończyła się niepowodzeniem.

Sprawdzono także, że `grid.py` akceptuje kolor z częściową alfą i jedynie ostrzega — kod zakończenia 0 nie wystarcza do potwierdzenia twardych krawędzi.

Wspierane rozwiązanie dla pracy bez zamówionego cienia: `dataclasses.replace(figure, shadow=None)` przed renderowaniem lub ustawienie `shadow=None` we własnym generatorze. Powtórzona kontrola tak przygotowanego przykładu przeszła. Nie zmieniano przykładu upstream ani nie usuwano cienia z istniejących renderów Painted/3D.

## Granice sprawdzenia

Nie uruchomiono trasy Concept, konwersji obrazów modelu, pełnej animacji ośmiokierunkowej ani Godota. Nie wybrano za autora stylu gry i nie stworzono docelowych assetów Weleszy.

Licencja kodu: MIT, z zachowaną informacją o Jun Yu. Dołączone dane Eastward mają osobny status wskazany w `LICENSE`; nie opisujemy ich jako objętych licencją MIT kodu. Pozostają referencją w pakiecie, nie assetami do automatycznego użycia w grze.
