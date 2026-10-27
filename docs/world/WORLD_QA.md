# Kontrola spójności mapy v0.1

Automatyczne sprawdzenie modelu planistycznego (nie test silnika):

- Węzłów: 28; dróg: 30; sektorów: 12.
- Każda droga kończy się w istniejącym węźle; brak nieznanych flag: PASS.
- Punkty i polilinie mieszczą się w obrysie świata: PASS.
- Niemir → wóz, kamienie, obóz i dojście do areny Dźwigacza bez latarni: PASS.
- Komora, arena Stróża i suchy szlak przed ich fabularnym odblokowaniem: zablokowane zgodnie z flagami (PASS).
- Po wszystkich odblokowaniach wszystkie 28 węzły są osiągalne: PASS.
- Fizyczna pętla wozu: różne geometrycznie drogi wyjścia i powrotu, bez teleportu (model: PASS).

**Tego NIE potwierdzają testy grafu:** przechodniości terenu, kolizji, czytelności widoku, czasu przejścia, jakości streamingu, logicznej spójności nadprzyrodzonego zjawiska w finalnej geometrii.