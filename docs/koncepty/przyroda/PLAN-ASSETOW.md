# Plan assetów przyrody dla Weleszy — v0.1

Status: **propozycja do oceny autora**, przygotowana po analizie koncepcji przyrody
(`docs/koncepty/przyroda/`). Nic tutaj nie zmienia ustaleń fabularnych; lista wynika
wprost z elementów widocznych na koncepcjach i potrzeb pierwszej lokacji
(trakt przy wozie → Niemir → bór).

## Założenia produkcyjne

- Pipeline: Blender 4.3 (Cycles CPU, headless) → prerender RGBA + osobna warstwa cienia,
  zgodnie z [kontraktem renderu](../../art/KONTRAKT-RENDERU.md): kamera ortograficzna 30°,
  60 px/m, te same trzy światła co bohater.
- Geometria proceduralna lub modelowana ręcznie. Tekstury z biblioteki
  [`assets/textures/environment/`](../../../assets/textures/environment/README.md)
  (wygenerowane przez AI) są **dozwolone** — decyzja autora z 27 października 2026 r.
  Inne zewnętrzne zasoby tylko z jasną licencją i zapisanym źródłem.
- Każdy asset: warianty rotacji, punkt osadzenia, uproszczona kolizja (dane
  orientacyjne), metadane JSON.

### Do poprawy w `stones-mistral-01` (stan gałęzi z 27 października 2026 r.)

Odczytano z `welesza_env_01.blend` i `source/build_env.py` na gałęzi `vibe/environment-stones-mistral`:

| Parametr | Na gałęzi | Wymaga kontrakt |
|---|---|---|
| Wersja Blendera pliku | 5.0 (nie otworzy się w 4.3) | 4.3 |
| Kamera | perspektywiczna, obiektyw 50 mm | ortograficzna, skala 3,2 m, obrót (60°; 0; 90°) |
| Klatka | 512×512 (asset), 960×540 (scena) | 384 → 192×192, większa tylko dla dużych obiektów, z kotwicą w JSON |
| Światło | słońce 6,5 + powierzchniowe 320 W | trzy światła powierzchniowe z kontraktu |
| Kolor | AgX „Base Contrast”, ekspozycja 0 | AgX „Medium High Contrast”, ekspozycja −0,2 |
| Próbki | 256 | 64 (cień 16), seed 1703 |

Modele i materiały można zachować. Blender 4.3 nie otworzy pliku z 5.0, więc scenę trzeba odtworzyć skryptem `build_env.py` uruchomionym w 4.3, z kamerą i światłem z kontraktu.

## Priorytet 1 — lokacja przy wozie (wioska → trakt)

### Skały (rozszerzenie paczki stones-mistral-01)
1. **Kamień mokry** — wilgotna powierzchnia, po deszczu (mocniejszy specular,
   ciemniejszy albedo).
2. **Kamień z mchem** — trwałe plamy mchu od strony północnej/zacienionej.
3. **Kamień z porostami** — porosty + drobne spękania.
4. **Skała spękana** — większa forma z pęknięciami/erozją (variation dla głazu).
5. **Kamienie drobne / żwir** — rozsypcze, do wypełniania krawędzi traktu.
6. **Płyty kamienne** — zwietrzałe płyty (dawniejsze konstrukcje przy osadzie —
   zgodne z fabułą starszej strażnicy w Niemiru).

### Roślinność runa i przydroża
7. **Trawa kępowa** — 2–3 warianty (sucha/wilgotna), do nakładania w klastrach.
8. **Paprocie** — 2 warianty (młoda/rozwinięta), charakterystyczne dla boru.
9. **Krzewy niskie** — 2 warianty, głównie przy krawędzi traktu.
10. **Suche gałęzie i chrust** — rozrzucone przy drodze.
11. **Pniak ze korzeniami** — stary pniak (potencjalny element sceny przy wozie).
12. **Korzenie wystające** — do okalania drzew i skalnego źródła.

### Podłoża (rozszerzenie materiałów)
13. **Tekstura: kałuża/błoto z wodą stojącą** — wariant traktu z wodą (deszcz
    pada trzy dni wg fabuły otwarcia).
14. **Tekstura: gleba z korzeniami** — wariant ściółki przeciętej korzeniami.
15. **Przejście trakt↔ściółka w 3 wariantach** (krawędź równa/kępowa/z korzeniami).

## Priorytet 2 — bór i podejście do Niemiru

### Drzewa (draft do decyzji autora — duży nakład)
16. **Sosna** (pień + korona do prerenderu w płaszczyznach).
17. **Świerk**, **Brzoza**, **Dąb martwy/złamany** — wg koncepcji drzew boru
    słowiańskiego.
18. **Drzewo powalone** — do komponowania barier nieprzechodnich.

### Skały formacji większych
19. **Ostra skała** — surowe formy (klify, skarpa przy źródle).
20. **Skarpa/zbocze** — modułowe krawędzie terenu.

## Priorytet 3 — osada (materiały, nie modele)
21. **Tekstury kory**: sosna, dąb, brzoza, świerk — pod przyszłe modele drzew
    i palisadę (plansza [03_drewno_kora_korzenie](tekstury-referencje/03_drewno_kora_korzenie.png) wymienia je wprost).
22. **Tekstury mchu i porostów** — przejściowe mapy do nakładania na kamienie
    i pniaki.

## Czego świadomie NIE planuję na tym etapie

- Pełnych modeli drzew z liśćmi geometrycznymi (koszt renderu vs zysk —
  najpierw decyzja o stylu koron).
- Wody płynącej / strumieni (osobny system materiałowy, po decyzji o silniku).
- Zależności od płatnych modeli AI (Trompe/fal) — do odrębnej decyzji autora,
  patrz raport z oceny Trompe.

## Kolejność proponowana dla najbliższej iteracji

Kamienie mokry/z mchem/porosty (1–3) → trawa i paprocie (7–8) → kałuże (13) —
bo bezpośrednio wzmacniają scenę przy wozie, która jest pierwszym kadrem gry.
