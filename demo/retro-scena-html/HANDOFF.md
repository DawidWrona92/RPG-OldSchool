# Retro scena HTML — Niemir (brama nocą)

Interaktywna mini-scena w czystym HTML/CSS/JS, odtwarzająca kadry bramy osady nocą
w konwencji skilla `retro-rts-sprites` (styl PIXELART: sylwetka + trzy tony + ciemny
kontur, światło z lewej-górnej, kotwica u stóp, kaflowa przestrzeń).

## Zawartość

- `index.html` — powłoka scenki (canvas 480x200, skalowany pikselowo).
- `style.css` — rama, HUD sterowania, pixelated rendering.
- `game.js` — świat, postacie, para z ust, sterowanie.

## Jak odpalić

- **Najprościej**: pobierz `niemir-scena.html` i otwórz dwuklikiem w przeglądarce — to samodzielny plik (CSS/JS wbudowane), nie wymaga serwera ani zależności.
- Alternatywnie otwórz `index.html` (używa `style.css` + `game.js` z katalogu) — działa też z dysku lub przez `python3 -m http.server`.

## Sterowanie

- `W A S D` lub strzałki — chodzenie.
- `Shift` — bieg.

## Elementy

- Kamera podąża za bohaterem (świat 960 px, widok 480 px, paralaksa: niebo/księżyc/las).
- Boazeria: wieża bramna z palisadą, dwie chaty (światła okien migoczą, komin dymi),
  wóz, latarnie z poświatą, mostek nad strumieniem.
- NPC: strażnik z włócznią przy bramie oraz wieśniak z koszykiem — obaj oddychają
  (animacja torsu/głowy) i mają parę z ust.
- Bohater sterowany klawiaturą: animacja chodu (nogi + kołysanie torsu), oddech,
  para z ust zależna od kierunku. Kolizje z budynkami, wozem i latarniami.
- Zasięg chodu ograniczony do pasa drogi; strumień nieprzejezdny.

## Stan / handoff

- Ostatni commit: patrz `git log -1` na gałęzi roboczej.
- Scena jest samodzielna (bez zależności); nie jest kontraktem produkcyjnym
  (produkcja sprite'ów: Blender/Cycles wg `docs/art/KONTRAKT-RENDERU.md`).
- Otwarte: dźwięki, wchodzenie na mostek, dodatkowe NPC, interakcja (E — rozmowa).
