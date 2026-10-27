# P2 — unikatowe mapy stroju bohatera v2

Stan produkcyjny określa `manifest.json`: `complete: true` oznacza pełną, zweryfikowaną paczkę. W czasie wypalania część może mieć `uv_layout_pending` i nie jest jeszcze gotowa do pracy.

Każda z 22 części otrzymuje siedem plików: `uv`, `ao`, `curvature`, `normal_sculpt`, `height_ground`, `id`, `preview`. Nazwy, rozdzielczość, średnia gęstość i SHA są w manifeście. Źródłem jest **jedna rewizja `source/bohater_v2.blend`** wskazana SHA; po zmianie jej geometrii/UV nie mieszać wypaleń.

- **UV:** RGBA 2048, unikatowe wyspy. Ubrania mają szwy paneli krawieckich, tkaniny otwarty rozkrój, drobne wyposażenie Smart Project. Średnio 1024 px/m na bazowej powierzchni; lokalna gęstość może się różnić w fałdach.
- **AO:** liniowe 16-bit grayscale, rzeczywisty Cycles Ambient Occlusion z odległością 0,15 m, z całym złożonym strojem i ciałem. Pod kaftanem/płaszczem koszula jest mocno przesłonięta. To mapa kontaktu montażu, nie oświetlenie ani samodzielna tekstura koloru. **Nie wpisywać jej na stałe w albedo.**
- **Curvature:** liniowe 16-bit grayscale, podpisany lokalny Laplacian powierzchni: 0 wklęsłe, 0,5 płaskie, 1 wypukłe. Przydatny do masek zużycia; to przybliżenie z geometrii, nie pomiar krzywizny skanu.
- **Normal sculpt:** RGB 8 bit, tangent OpenGL +Y, Cycles selected-to-active z ewaluowanych fałd/Subsurf/Solidify do bazowej siatki UV. Nie przedstawiamy tego jako ręcznie wyrzeźbionego high-poly ani skanu. Dane Non-Color.
- **Height ground:** liniowe 16-bit grayscale, **światowe Z / 1,8 m**, a nie mikrodisplacement. 0 oznacza poziom ziemi, 1 wysokość 1,8 m. Do kierunkowego błota i wilgoci od dołu.
- **ID:** RGB 8 bit, płaskie kolory regionów opisane przy części. Domyślnie czerwony to materiał główny, zielony dolny brzeg/podeszwa, niebieski panel/zapięcie/łata, żółty podwinięcie. To pomocnicze regiony geometrii; nie udają kompletnego ręcznego malowania wszystkich szwów i sprzączek.
- **Preview:** 768 RGBA, szary materiał i światła kontraktu, kamera dopasowana do części. To podgląd diagnostyczny, nie skala gry.

Docelowy strój nadal według konceptu 17 i planu naprawy. Potrzebne są unikatowe len/wełna/skóra, konstrukcyjne przeszycia, paski butów i posłania, sensowne przetarcia krawędzi, wilgoć i błoto od ziemi. Obecne materiały w modelu są **tymczasowe**. Głowa według 19, z nadrzędnością decyzji pisemnych; nie przenosić malowanych świateł konceptu do map koloru.

Licencje/pochodzenie: geometria stroju autorska w repozytorium; ciało i wagi MakeHuman CC0 według `source/third_party/manifest.json`. Wypalenia geometryczne z Blendera 4.3.2; bez zewnętrznych zdjęć i bez nowych materiałów z niejasnych źródeł. To przekazanie do teksturowania, **nie akceptacja B2**.
