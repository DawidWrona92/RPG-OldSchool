# Welesza — tekstury środowiskowe v1

**15 tekstur PNG, 1024 × 1024 px**. Biblioteka obrazów koloru bazowego do prototypów w Blenderze, inspirowana chłodnym, wilgotnym borem Weleszy.

## Katalog

- `ground/` — ściółka, gleba, ubity trakt, mokre błoto, trawy, opadłe liście, igliwie, wystające korzenie, mech (9 map).
- `rock/` — spękane i omszałe skały, mieszanki kamieni, mchu i porostów (3 mapy).
- `bark/` — stara kora, kora sosny, kora brzozy (3 mapy).

Każda nazwa jednoznacznie opisuje motyw. Szczegółowa tabela i dane źródłowe w [`manifest.json`](manifest.json).

## Blender — użycie

1. Dodaj `Image Texture`; ustaw `Color Space: sRGB` dla koloru.
2. Podłącz `Color` do `Base Color` w `Principled BSDF`.
3. Współrzędne i gęstość powtarzania dostosuj do rzeczywistej skali obiektu; nie ma jeszcze zatwierdzonej skali UV.
4. Roughness/normal/bump/height komponuj i testuj osobno. Pliki PNG nie są pomiarowymi zestawami PBR.
5. Używaj masek i mieszania warstw do łagodnych przejść między trawą, błotem i ściółką.

## Ograniczenia i jakość

- Materiały są **generowane**, nie skanowane; nie posiadają mierzonej informacji o właściwościach powierzchni.
- Obrazy **nie mają zweryfikowanej bezszwowości** mimo niektórych historycznych nazw plików; sprawdź łączenia przed powielaniem.
- Wersje repozytoryjne zostały zmniejszone do 1024 px i zindeksowane paletą 256 barw, bez zmian semantycznych; oryginalne PNG zachowano w paczce przekazanej autorowi.
- Tekstura koloru nie zastępuje geometrii korzeni, kamieni, traw i drzew.
- Różnice oświetlenia powinny wynikać także z renderingu sceny, a nie samego przyciemniania albedo.

**Status: [DECYZJA AUTORA] zaakceptowana do produkcji** (27 października 2026 r.). Tekstury wygenerowane przez AI zostają, bo autor ocenił ich jakość jako wysoką; ograniczenia wyżej (brak pomiarowego PBR i potwierdzonej bezszwowości) nadal obowiązują. Kierunek artystyczny Niemiru: `docs/art/niemir/NIEMIR_ART_DIRECTION.md`.
