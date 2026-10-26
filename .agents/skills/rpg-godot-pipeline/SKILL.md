---
name: rpg-godot-pipeline
description: Weryfikuje i importuje sprite'y do Godot 4 dla izometrycznej gry ARPG w duchu Diablo 1/2; stałe kotwice, osiem kierunków, czas klatek, osobne warstwy cieni i wyposażenia, poprawna kolejność animacji oraz zewnętrzny atlas PNG+JSON.
---

# RPG Godot Pipeline

1. Odczytaj rzeczywistą konwencję istniejącego projektu: `Iso.iso` jest 96×48, yaw `0,45,...315` i `Sheet.build_sprite_frames` tworzy animacje `<prefix>_<directionIndex>`; **nie zmieniaj jej bez jawnej migracji**. W całej grze nazwa `direction` oznacza indeks w przestrzeni świata, nie obrót wyglądu arkusza.
2. Preferuj assety w istniejącym formacie `frame_size`, `anchor`, `frames[]` (x, y, view_angle_deg), rozszerzone o `duration_ms`. Każdy kierunek ma tyle samo klatek, uporządkowanych kierunek→faza. Kadr/kotwica stałe na wszystkich 8×N klatkach i wszystkich warstwach postaci. `sourceGenerator` zapisuj osobno.
3. Przed importem uruchom `python scripts/verify_atlas.py <sheet.png> <sheet.json>`. Błędy eksportu blokują użycie. Duplikaty kierunków to ostrzeżenia w wypadku obiektów symetrycznych; zawsze obejrzyj atlas.
4. Używaj `scripts/RpgAtlas.gd` jako *opcjonalnego* adaptera Godot 4 (obsługuje czas klatek). Nie nadpisuj obecnego `Sheet.gd` projektu. Metoda `make_sprite` ustawia filtr nearest i offset punktu zakotwiczenia zgodny z `Sprite2D.centered`.
5. Sprite `pixel-art`: filtr nearest i integer scaling; render `painted/prerender`: filtr liniowy tylko po sprawdzeniu krawędzi i jasności (nie narzucaj retro zasady). Nie wymuszaj kwantyzacji kolorów ani twardej alfy na renderach 3D.
6. Sortowanie Y i kolizje to osobne systemy. Jednostki o wysokich bryłach mogą wymagać warstw foreground/occluder; sortowanie po samym y nie zastępuje prawidłowej nawigacji i kolizji.
7. Warstwowy bohater: dopasowanie wymiarów i kotwicy między cape/base/blade/shield/helmet; zmieniaj kolejność warstw zależnie od widoku, gdy geometrię zasłania błędnie. Timing sprite'a podstawowego synchronizuje pozostałe warstwy. Przy wariancie FPS≠stałe, synchronizuj też czas fazy.

## Nie obiecuj

Przy braku zainstalowanego Godota nie deklaruj, że uruchomiono scenę lub zwalidowano kompatybilność GDScript runtime. `verify_atlas.py` sprawdza format i obraz, nie rozwiązuje kolizji, pathfindingu i animacji w grze.

Kompatybilne przykłady: `../demo/arpg/output/dark_knight_walk_8dir.png` oraz `skeleton_walk_8dir.png`.
