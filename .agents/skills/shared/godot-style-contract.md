# ARPG Godot Style Contract v4

- Aktualny projekt użytkownika: kafel rombowy 96×48, `Iso.iso(gx,gy) = ((gx+gy)*48,(gx-gy)*24)`; `Iso.dir_index` mapuje atan2 ruchu w **przestrzeni siatki** na indeks `0..7` co 45°.
- Standard `Sheet.gd`: `frame_size`, `frames:[{x,y,view_angle_deg}]`, `anchor:[px,py]` i odtwarzanie `<prefix>_<direction>`. Rozszerzenie `duration_ms` jest opcjonalne.
- Wysokość postaci nie jest automatycznie równa `tilePx`; wyrównanie następuje przez `anchor` (stopy/punkt podłoża) i dobraną skalę renderowania w świecie. Co do stylu referencyjnego, gęstości detali oraz klatek: zobacz `retro-rts-sprites/references/art-direction.md`.
- Dla ataku szerszy/fixed canvas niż dla chodu jest dopuszczalny **pod warunkiem stałego anchor w świecie**, a nie automatycznego centrowania alfa-bbox w każdej klatce. Zamiana warstw nie może powodować drgania ciała.
- Stosuj nearest i integer scaling tylko dla pixel-art; w ARPG z 3D pre-renderem można użyć tekstury liniowej oraz dynamicznego zoomu (wtedy antialiasing z kontrolą halo).
- Wyrównanie świateł: nie wolno mieszać stylistyk przez samą zmianę kierunku cienia; oceniaj w grze, gdzie obowiązuje CanvasModulate i dodatkowe światła.
- Assety wejściowe są tylko wizualne; kolizje, zasięg ataku, warstwa przesłaniania i pathfinding muszą być skonstruowane w osobnych zasobach Godot.
