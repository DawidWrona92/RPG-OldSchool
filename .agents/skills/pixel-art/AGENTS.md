# Użycie pixel-art w Weleszy

To lokalne zasady integracji. Pliki upstream pozostają niezmienione. Pełny przegląd zgodności: [dokument projektu](../../../docs/zgodnosc-pixel-art.md).

- Ten skill wybieramy do prawdziwego pixel-artu, nie automatycznie do każdego sprite'a, ilustracji lub pre-renderu. `rts-sprite-router` nadal jest punktem wyboru narzędzia.
- Styl Weleszy ma pierwszeństwo przed przykładami Eastward. Nie przyjmuj automatycznie jego palety, proporcji, kamery, progów statystycznych ani szablonów twarzy. Przykłady są referencją narzędzia, nie assetami naszej gry.
- Twarda alfa i nazwana paleta obowiązują wynik tego skilla; nie zmieniaj na ich podstawie grafik Painted lub pre-renderów 3D ani ich osobnych cieni.
- Dla wyniku bez zamówionego cienia buduj `Figure` z `shadow=None`. Przykład `mechanic_idle.py` dodaje cień z półprzezroczystością, mimo ogólnej reguły pixel-perfect.
- `grid.py` ostrzega o częściowej przezroczystości, ale nie kończy błędem. Przed zatwierdzeniem czystego pixel-artu sprawdź osobno, że wszystkie wartości alfa należą do `{0, 255}`, rozmiar jest zgodny, kolory należą do ustalonej palety, a zapis tekstowy odtwarza PNG bez zmian. Nie naprawiaj automatycznie przez kwantyzację plików z innych narzędzi.
- Źródło pixel-artu to sprite text oraz generator albo koncept. Import gry dodatkowo potrzebuje metadanych zgodnych z wybranym później kontraktem. Pojedynczy PNG nie jest automatycznie gotowym atlasem ośmiokierunkowym.
- Uruchamiaj narzędzia przez `python3 -I -B tools/...`, bez dodawania `kit` do globalnego `PYTHONPATH`. Nazwa `kit` jest lokalna dla tego pakietu.
- Trasa Concept jest opcjonalna. Sprawdź faktycznie dostępne narzędzie generowania obrazów w sesji; przykłady upstream z Codex CLI nie oznaczają konieczności instalowania CLI, ponownego logowania ani uruchamiania dodatkowych agentów.
- Zachowuj licencję i osobny status dołączonych danych stylu opisany w `LICENSE`. Nie eksportuj przykładów Eastward jako oryginalnych assetów Weleszy.
