# Pakiet 04 — brief do późniejszych obrazów

Status: propozycja briefu, nie zatwierdzony styl graficzny. Ilustracji kadrów jeszcze nie wykonano. Sprite'y postaci powstają metodą [welesza-sprites](../.agents/skills/welesza-sprites/SKILL.md).

Podstawa: [mapa](pakiet-04-mapa.md), [początek](pakiet-04-poczatek.md), [bestiariusz](bestiariusz-demo.md). Obraz ma pokazywać konkretne miejsce albo decyzję gracza, nie tylko dekoracyjny nastrój.

## Wspólne wytyczne

- Las zamyka widok. Niemir jest mały, użytkowy, naprawiany przez mieszkańców; nie wygląda jak gotowy park atrakcji grozy.
- Smutek pokazują zużyte przedmioty, nieobecni ludzie i czynności, które przestały mieć sens. Nie dodajemy zwłok w każdym kadrze.
- Światło w osadzie jest skromne i lokalne. Ciepło nie oznacza bezpieczeństwa całego świata; chłód lasu nie oznacza całkowitego braku czytelności.
- Magia nie ma stale świecących run na każdej powierzchni. Zapalona latarnia i odsłonięty trakt powinny być wyjątkowym wydarzeniem.
- Nazewnictwo słowiańskie nie wymaga dekorowania wszystkiego takim samym zestawem symboli. Rekwizyty wynikają z funkcji domu, pracy lub konkretnego obyczaju.
- Materiał i epoka są umowne: drewno, stary kamień, żelazo, wełna, len, skóra. Unikamy nieuzgodnionej broni palnej i architektury monumentalnego miasta.
- Proponowana relacja barw: ziemia, zgaszona zieleń, mokry kamień i oszczędne ciepłe światło. Dokładną paletę, styl 2D/3D i stopień malarskości wybierzemy na obrazach porównawczych.

## Pierwsza seria obrazów

| Kadr | Co musi pokazać | Ograniczenia i kryterium oceny |
|---|---|---|
| ART-01 — Niemir z góry pod kątem | Jedną bramę, palisadę, skałę ze źródłem, plac, małą strażnicę, drogę do gospody | Bez pól i wielkiego miasta. Widać, gdzie gracz wejdzie i wróci; bryły odpowiadają mapie, nie są dowolną panoramą |
| ART-02 — Pierwszy widok bramy | Światło między pniami, Żegotę, rzemienie i ptasie kości pod dachem, wąskie podejście otwierające się przed wejściem | Nie wyjaśnia, co stoi w ciemności. Kierunek ruchu czytelny bez strzałki |
| ART-03 — Wóz przed nocą i rano | Ten sam układ wozu, butów i konia w dwóch stanach światła | Porównanie potwierdza, że to to samo miejsce. Poranny kontekst nie tworzy drugiego identycznego wozu |
| ART-04 — Plac pierwszej walki | Ujęcie z docelowego kierunku kamery, Pies przygotowujący skok, bohater, wolny bok na unik, obie drogi przy wozie | Sylwetka i zasięg zagrożenia nie giną w trawie. Nie udajemy znanej skali metrycznej |
| ART-05 — Strażnice obok siebie | Małą osadową strażnicę ze wspólnym światłem oraz niskie, ciężkie leśne ruiny z piecem | Gracz nie powinien mylić tych miejsc. Obrazy nie rozstrzygają wspólnego pochodzenia |
| ART-06 — Piec Dźwigacza | Nosidło, mokre drewno, zimny piec i człowieczą sylwetkę wykonującą bezsensowną pracę | Smutek przed spektaklem potwora; zostawić przestrzeń na obejście w walce |
| ART-07 — Trakt Stróża | Słupy, zamknięte przejście, drzewce w poprzek, pakunki na zbroi; ścieżkę powrotu | Bez armii, magicznej ściany ognia i nowej kosmologii. To jeden nieustępliwy przeciwnik |

Najpierw warto obejrzeć ART-01–04, bo ustalają skalę człowieka, przestrzeń osady, las i czytelność kamery. Bossowie korzystają potem z tego samego języka wizualnego.

## Co obrazy mają pomóc wybrać

Styl wykonania i stopień uproszczenia, proporcje postaci do budynków, gęstość lasu, paletę, sposób odróżniania interaktywnych obiektów oraz sylwetki w izometrii. Porównania powinny utrzymywać ten sam układ sceny; zmiana jednocześnie stylu i całej architektury utrudnia decyzję.

Obraz koncepcyjny nie jest finalnym assetem gry, dowodem przechodniości areny ani specyfikacją kolizji. Docelowe formaty, rozdzielczości, siatki animacji i eksporty ustalimy po wyborze technologii oraz sposobu tworzenia grafiki.

## Przekazanie do kolejnego etapu

Autor przyjął prerender SDF jako metodę sprite'ów postaci (pierwszy wynik: Drwal, `assets/sprites/prerender/`). Kadry ART-01–07 można wykonać tym samym rendererem i tą samą kamerą, żeby zachować skalę i światło; zakres i kolejność ustala autor. Nie zmieniamy przy tym zatwierdzonej fabuły.
