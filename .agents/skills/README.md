# RTS / ARPG Sprite Skills v4

Zestaw **pięciu umiejętności** do proceduralnych sprite'ów izometrycznych dla Godot 4 i gier RTS / ARPG. Zawiera silniki JavaScript, warsztat pixel-art Python, generatory, narzędzia analizy stylu, walidatory oraz przykładowe wyniki renderowania.

## Struktura

- [retro-rts-sprites](retro-rts-sprites/SKILL.md) — `spritekit.js` i `pixelcraft.py`, pixel-art, styl retro, analiza referencji
- [painted-rts-sprites](painted-rts-sprites/SKILL.md) — `painter.js`, malarskie sprite'y 2D, atlasy kierunków
- [rts-prerender-3d](rts-prerender-3d/SKILL.md) — `rtcore.js`, pre-render 3D, `meshkit.js`
- [rts-sprite-router](rts-sprite-router/SKILL.md) — wybór stylu i silnika, wspólne reguły
- [rpg-godot-pipeline](rpg-godot-pipeline/SKILL.md) — metadane PNG/JSON i adapter `RpgAtlas.gd`
- [shared](shared/) — kontrakty assetów i bramki QA
- [tests](tests/) — testy Python oraz JS i zapisane wyniki
- [demo](demo/) — generatory i przykładowe wyjściowe rendery

## Uruchomienie testów

W katalogu głównym:

```bash
node tests/test_tools.js
node tests/test_integrated.js
python tests/test_arpg.py
```

Narzędzia Python mogą wymagać pakietu Pillow. Bazowe silniki JS działają w Node bez zewnętrznych bibliotek.

## Dla innych LLM-ów

Zacznij od [rts-sprite-router/SKILL.md](rts-sprite-router/SKILL.md), wybierz backend, przeczytaj jego `SKILL.md` i odpowiednie materiały `references/`. Zawsze udostępniaj plik źródłowy generatora, sprite w natywnej rozdzielczości, metadane oraz wynik walidacji. Nie utożsamiaj wizualizacji celu z rzeczywistym renderem silnika.

## Wersja

Import pełnego zestawu plików v4 (2026-10-26), z wyłączeniem automatycznie generowanych katalogów `__pycache__`. Wybrane starsze dokumenty w repozytorium są zachowane jako archiwum historyczne (`*-original.md`).

## Pochodzenie

Trzy silniki JS dostarczył właściciel repo i potwierdził ich autorstwo wspólnie z narzędziem Vibe. Informacje o metodologicznych inspiracjach w [LICENSE-INSPIRATIONS.md](LICENSE-INSPIRATIONS.md). Repo nie deklaruje automatycznie licencji open-source dla wszystkich komponentów.
