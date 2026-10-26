# Zainstalowane skille graficzne

Źródło: `DawidWrona92/skills`, wersja `1527a5173886e3b66b63296cb4d2483d4d3bb6a1`. Instalacja i weryfikacja: 26 października 2026 r.

| Skill | Zastosowanie |
|---|---|
| [rts-sprite-router](../.agents/skills/rts-sprite-router/SKILL.md) | Punkt wejścia: wybór narzędzia i wspólnego kontraktu assetów |
| [retro-rts-sprites](../.agents/skills/retro-rts-sprites/SKILL.md) | Pixel-art; `spritekit.js` oraz warsztat Python/Pillow `pixelcraft.py` |
| [painted-rts-sprites](../.agents/skills/painted-rts-sprites/SKILL.md) | Malarskie sprite'y, budynki, rekwizyty i atlasy |
| [rts-prerender-3d](../.agents/skills/rts-prerender-3d/SKILL.md) | Proceduralne modele renderowane do sprite'ów, przede wszystkim obiekty statyczne |
| [rpg-godot-pipeline](../.agents/skills/rpg-godot-pipeline/SKILL.md) | Walidacja atlasów PNG/JSON i opcjonalny adapter Godot 4 |

Wspólne katalogi `shared`, `demo` i `tests` zainstalowano obok skilli, zachowując odwołania względne. Źródła i informacje licencyjne są zachowane, a wcześniejsze 19 skilli projektowych nie zostało zastąpionych.

## Wykonana weryfikacja

Polecenia uruchomiono z zainstalowanej kopii w `.agents/skills`, a nie na podstawie dołączonych historycznych wyników:

```bash
cd .agents/skills
node tests/test_tools.js
node tests/test_integrated.js
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_arpg.py
```

- Narzędzia JS: 9 testów zaliczonych.
- Integracja silników JS: 5 testów zaliczonych.
- Narzędzia Python i format atlasów: 16 testów zaliczonych.
- Wszystkie trzy polecenia zakończyły się kodem 0.

Środowisko weryfikacji: Node 24.19.0, Python 3.12.14, Pillow 12.3.0. Zależności były już dostępne; nie wykonywano dodatkowej instalacji pakietów.

Testy sprawdzają m.in. geometrię, kodowanie PNG, duplikaty kierunków, kotwice, obcięcie klatek oraz odczyt przykładowych atlasów. Nie potwierdzają jakości artystycznej ilustracji dla Niemiru. Nie uruchamiano edytora Godot ani adaptera w jego środowisku wykonawczym.

## Użycie w projekcie

Punktem wejścia jest `rts-sprite-router/SKILL.md`; następnie należy przeczytać wybrany skill i wymagane przez niego referencje. Instrukcje można czytać bezpośrednio z repozytorium również w bieżącej sesji; nie zakładamy automatycznego przeładowania katalogu skilli przez klienta.

Zestaw służy głównie do proceduralnych sprite'ów i atlasów. Nie stanowi obietnicy automatycznej jakości gotowych postaci Diablo 2 ani zastępstwa pełnego warsztatu ilustracji koncepcyjnej. Dobór narzędzia do [briefu obrazów](pakiet-04-obrazy.md) wymaga próbki oraz osobnej oceny wizualnej.

Skalę, światło, projekcję, kotwicę i filtrację trzeba uzgodnić przed łączeniem wyników różnych narzędzi. Eksport ma zawierać źródło generatora, obraz natywny, wymagane metadane i raport kontroli.

Instalacja adaptera Godot nie zatwierdza wyboru silnika. Podane w jego instrukcji przykładowe konwencje projektu nie są automatycznie konwencjami Weleszy — projekt silnika gry jeszcze nie istnieje.

Na tym etapie nie wygenerowano nowych ilustracji ani assetów Weleszy; obrazy w `demo/` są przykładami dostarczonymi przez repozytorium źródłowe.
