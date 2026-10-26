---
name: rts-sprite-router
description: Wybiera jeden z trzech faktycznie dołączonych backendów tworzenia sprite'ów izometrycznych RTS (pixel-art retro, malarski 2.5D, pre-render 3D) i pilnuje zgodności stylu, skali, kierunków i formatów.
---

# RTS Sprite Router

Dla zamówienia sprite'a RTS sprawdź, czy istnieje już zestaw assetów użytkownika. Istniejący zestaw ma pierwszeństwo przed domyślnymi stylami. W przypadku nowego zestawu:

| Styl | Skill | Silnik | Typowe zastosowanie |
|---|---|---|---|
| 16–64 px, sylwetkowy pixel-art | `retro-rts-sprites` | `scripts/spritekit.js` | surowce, teren, niewielkie jednostki |
| tekstury malarskie, budynki i stylizowane postacie | `painted-rts-sprites` | `scripts/painter.js` | stylizowane RTS 2.5D, wielu kierunków |
| modelowane obiekty 3D z bogatszym oświetleniem | `rts-prerender-3d` | `scripts/rtcore.js` | wieże, domy, machiny, drzewa |

Nie obiecuj jednego spójnego atlasu złożonego z różnych backendów bez świadomej normalizacji światła, rozmiaru kafli, filtracji, kotwic i gradingu. Przeprowadź bramki: walidacja -> podgląd w 1× -> zgodność kierunków -> kontrola artefaktów -> eksport metadanych. Zachowaj generator jako źródło edytowalne.

Wspólny kontrakt: `../shared/asset-contract.md`. Realne demonstracje wszystkich trzech silników: `../demo/real/render-real.js`, wynik `../demo/real/output/real_engine_comparison.png`.

Inspiracja estetyczna Diablo, Age of Empires czy Stronghold nie oznacza odtwarzania konkretnych chronionych assetów 1:1.

## Specjalizacja ARPG / Godot (v4)

Jeżeli cel jest Diablo-like, a nie RTS, nie wybieraj na ślepo 24×32 pseudo-ASCII. `retro-rts-sprites` oferuje teraz dwa wykonania: historyczne `spritekit.js` i bardziej artystyczny warsztat `pixelcraft.py` na Pillow. Do statycznych szczegółowych budynków nadal częściej wybieraj Painted lub 3D. Ośmiokierunkowe animacje importuj wspólnym kontraktem `rpg-godot-pipeline`.

Gdy użytkownik przesyła aktualny projekt Godot, jego `Iso.iso`, `Iso.dir_index` i `Sheet.build_sprite_frames` determinują rzeczywistą kolejność kierunków, punkt kotwicy i metadane. Nie niszcz kompatybilności tylko po to, by użyć innego standardu (np. LPC 4-dir); konwersję wykonaj jawnie i przetestuj 8 widoków.

Uruchamiaj procedurę: referencja/style-card → próbka native 1× na tle gry → poprawki → QA wszystkich klatek → eksport PNG+JSON + source → weryfikator Godot. Celowy pixel cleanup tylko dla rzeczywistego pixel artu. Przy kolorach, skali, estetyce i animacji postaci wydawaj osobne oceny techniczną oraz wizualną.
