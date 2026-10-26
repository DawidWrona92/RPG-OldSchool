# Karta stylu Welesza — sprite'y jednostek (seria 01)

Podstawa: `retro-rts-sprites` tryb DARK FANTASY (`pixelcraft.py`), reguły `references/art-direction.md`.
Zakres: pierwsi zwykli przeciwnicy z `docs/bestiariusz-demo.md`. Nie jest to zatwierdzony styl całej gry — to seria porównawcza do oceny autora.

## Płaszczyzna i kamera

- Widok: pseudotop-down 3/4 jak w Diablo 2, jednostka pionowo, lekki boczny przesuw ramion i sprzętu zależny od kierunku.
- Canvas jednostki: 96×116 px, kotwica stóp (48, 104), identyczna dla wszystkich klatek i kierunków.
- Cień podłoża: płaski owal w warstwie `shadow`, kolor `#1c242b`, twarda alfa — bez rozmycia.

## Paleta (nazwana, wspólna dla wszystkich jednostek serii)

Cień/podłoże `#1c242b`; futro `#241d1a`, `#4a3527`, `#6d5138`, `#8a6a4a`, jasna łatka `#c9b08a`;
tkanina wyblakła `#3a3b33`, `#57584a`, `#7d7a5c`; pas tkaniny `#9a8560`;
skóra blada `#6e5a4c`, `#9b8266`, `#b59a77`;
drewno/stal narzędzi `#2b2f36`, `#4c5560`, `#75828c`, `#a3b0b8`;
kontur: `#17171f` (nie czysta czerń), 1 px, selektywny — rozjaśniany po stronie światła.

## Światło

- Jedno źródło: lewy górny. Strona bliska jaśniejsza, dalsza ciemniejsza; brak „pillow shading".
- Metal: ostre skupione refleksy 2–3 px; tkanina: duże miękkie płaszczyzny bez ditheringu; futro: 3 tony + charakterystyczna jasna łatka.

## Sylwetki (rozróżnialne bez barw)

- **ENM-zdziczaly-pies**: niski (ok. 40 px wys.), wychudzony, głowa nisko, zerwany rzemień obroży, jasna łatka na grzbiecie.
- **ENM-powrotnik**: pochylony człowiek (ok. 78 px wys.), worek na plecach, ręka na węźle, wyblakły pas przy nadgarstku.
- **ENM-drwal**: szerokie barki (ok. 84 px wys.), długi topór, ciemny fartuch z jednym jasnym szwem.

## Bramka jakości

1. Sylwetka czytelna na ciemnym `#191922` i zielonkawym `#394e38` tle, bez barw.
2. 8 kierunków × 2 fazy idle: stały canvas, kotwica i tryb RGBA; `frame_checks` bez błędów.
3. Detal: najpierw skupiska 2–4 px, pojedyncze piksele tylko jako refleksy.
4. Ocena w 1× na dwóch podłożach + powiększenie 4× nearest; minimum dwie iteracje po pierwszym renderze.
5. Eksport: PNG 1× na jednostkę, atlas 8 kierunków × 2 klatki, JSON z metadanymi, generator `.py` jako źródło.

## Ograniczenia

- Bez broni palnej, bez świecących run, bez makabry. Łatka psa i szew fartucha to sygnały fabularne, nie dekoracja.
- Wartości liczbowe bestiariusza pozostają robocze; sprite nie rozstrzyga AI ani balansu.
