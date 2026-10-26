# Sprite'y postaci — prerender SDF

Metoda i zasady dla autorów postaci: [welesza-sprites](../../../.agents/skills/welesza-sprites/SKILL.md).
Ten plik opisuje **format wyniku** dla osoby, która wpina postacie do gry.

## Pliki postaci

`output/<postać>/` (wariant: `output/<postać>-<litera>/`):

| Plik | Zawartość |
|---|---|
| `<postać>_<animacja>.png` | atlas RGBA: **kolumny = klatki animacji, wiersze = 8 kierunków**; każda komórka 192×192 px |
| `<postać>.json` | metadane wszystkich animacji postaci |
| `<postać>_<animacja>.gif` | podgląd: 8 kierunków obok siebie w ruchu, na tle lasu (nie do gry) |

## Klatka

- 192×192 px, wygładzone krawędzie, cień na ziemi jako półprzezroczysta czerń w tej samej klatce.
- **Kotwica** (`anchor_px`, ≈ 96, 158): punkt pod stopami postaci = jej pozycja w świecie gry. Taka sama w każdej klatce, kierunku, animacji i wariancie.
- Skala: `pixels_per_meter` = 60. Człowiek ≈ 105 px wysokości.
- Kamera ortogonalna, 30° nad horyzontem, jak w Diablo 2. Światło stałe w świecie (z lewej góry ekranu), więc cień nie obraca się z postacią.

## Kierunki

Wiersz atlasu = indeks w `directions`: `S, SW, W, NW, N, NE, E, SE`. S = postać zwrócona do kamery (w dół ekranu); kolejne co 45° zgodnie z ruchem wskazówek zegara na ekranie (SW = w lewo-dół). Każdy kierunek to osobny render, nie lustrzane odbicie.

## Animacje w JSON

```json
"rozlupanie": {
  "file": "drwal_rozlupanie.png",
  "frames": 10,
  "durations_ms": [100, 140, 220, 240, 60, 90, 260, 260, 160, 140],
  "loop": false,
  "events": {
    "parowalny": false,
    "zapowiedz": [1, 2, 3],
    "sygnal": [2, 3, 4, 5],
    "aktywne": [4, 5],
    "trafienie": 5,
    "okazja": [6, 7, 8]
  }
}
```

- `durations_ms` — czas każdej klatki osobno (zapowiedzi są celowo dłuższe, ciosy krótkie).
- `loop` — spoczynek i chód zapętlone; ataki, trafienie i śmierć jednorazowe (ostatnia klatka śmierci zostaje jako zwłoki).
- `root_speed_mps` (chód) — prędkość przesuwania postaci w grze, przy której stopy nie ślizgają się po ziemi.
- `events` — okna walki z [bestiariusza](../../../docs/bestiariusz-demo.md): `zapowiedz` (telegraf), `aktywne` (klatki, w których cios może trafić), `trafienie` (klatka kontaktu), `okazja` (bezpieczne okno na kontrę gracza), `parowalny`, `sygnal` (klatki z czerwonym zarzewiem ataku nieparowalnego). Dokładne okna czasowe i hitboxy są do dostrojenia w testach gry.

## Drwal (ENM-drwal)

Ożywieniec z wygasłego obozu. Animacje: `spoczynek`, `chod`, `ciecie` (parowalne cięcie z boku), `rozlupanie` (nieparowalne, ostrze grzęźnie w ziemi), `trafienie`, `smierc`.

Warianty wyglądu (te same animacje, czasy i zasięg): `drwal` (długie włosy, broda), `drwal-b` (łysy, krępy, bez rękawów, sakwa), `drwal-c` (wyższy, chudy, w kapturze, węższa siekiera), `drwal-d` (kołpak z futrem, krótka broda, jeden rękaw oderwany). W grze losuj wariant przy rozmieszczaniu przeciwników.

Ponowne wygenerowanie: `python3 drwal.py anim all [--wariant=b]` (ok. 25 min na wariant na 4 rdzeniach).
