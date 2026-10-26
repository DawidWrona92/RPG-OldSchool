# Rzemioslo detalu: od kapsul do zbroi (katalog z projektu "rzemioslo detalu")

Zasada nadrzedna: postac najpierw musi byc czytelna jako SYLWETKA (czarny kontur bez kolorow), dopiero potem dostaje kolor i detal. Kapsuly i owale daja manekina, nie czlowieka w zbroi. Liczy sie: staw jako osobna bryla, przerwa miedzy segmentami konczyny, dlon i stopa jako kity z wyraznym kierunkiem, detal siedzacy na KRAWEDZI sylwetki (zasada D2: naramiennik, grzbiet napier snika, krawedz tarczy).

## Anatomia v2: skeleton2

Szkielet v2 opakowuje zwykly szkielet (stad dziedziczy pelna animacje: pozy, chod, zamach, smierc). Kluczowe punkty: kulki stawow na poziomie kolana i lokcia z przerwa 0.012*S w konczynie, nadgarstnik, piesc blizej konca przedramienia, pietownik i palcowka stopy z noskiem, kark, pas, biodra jako kotwice sprzetu.

```js
// stawy i kotwice sprzetu (pelny listing nie jest dołączony)
sk.arms.forEach(function (A) {
  var dirU = norm2(A.elbow, A.hand); // zachowaj oryginalną dłoń PRZED zmianą A.hand
  A.wrist = lerpv(A.elbow, A.hand, 0.82);     // nadgarstnik
  A.hand = lerpv(A.elbow, A.hand, 0.94);       // piesc blizej konca
  A.elbowBall = lerpv(A.elbow, A.hand, 0.06); // obecnie liczone do przesuniętej dłoni; preferowane: oblicz do originalHand // kulka stawu
  A.fistDir = dirU;
  A.fistAxis = [dirU[0], 0, dirU[2]];         // rzut na x-z: dlon grzbietem do przodu
});
sk.legs.forEach(function (Lg, i) {
  var side = i === 0 ? 1 : -1;
  Lg.kneeBall = lerpv(Lg.knee, Lg.ankle, 0.06);
  Lg.toe = addv(Lg.ankle, [0.095 * S, side * 0.010 * S, -0.028 * S]);  // palcowka
  Lg.heel = addv(Lg.ankle, [-0.020 * S, 0, -0.030 * S]);              // pietownik
});
sk.neck = lerpv(sk.pivot, sk.head, 0.42);
sk.waist = [sk.pivot[0], 0, sk.pivot[2] - 0.055 * S];
sk.belt = [sk.pivot[0], 0, sk.pivot[2] - 0.035 * S];
sk.hipFront = [sk.pivot[0] + 0.05 * S, 0, sk.pivot[2] - 0.06 * S];
```

Proporcje mierzone, nie z oczu: glowa jako jednostka (0.076*S), barki 2.2 szerokosci glowy, wzrost ~6.5 glowy z helmem. Asercję proporcji kalibruj do pozy i definicji S; sam sztywny przedział 0.5–0.95*S nie może zastąpić testu geometrii.

## Katalog sprzetu D2

Kazda funkcja sprzetu przyjmuje `(P, o, p, sk, M)` jak warstwa bohatera: sprzet podmienia sie warstwami bez ruszania szkieletu ani animacji. Wzorzec (napier snik):

```js
function drawBreastplate(P, o, p, sk, M) {
  var S = sk.S, ang = p.torsoPitch, dx = Math.sin(ang), dz = Math.cos(ang);
  var chest = sk.chest;
  P.ellipsoid([chest[0] + 0.018*S*dx, 0, chest[2] + 0.006*S], [0.104*S, 0.136*S, 0.118*S], M.armor, { pitch: ang }); // plyta gorna
  P.rod(addv(chest, [0.108*S*dx, 0, 0.052*S*dz + 0.012*S]), addv(chest, [0.108*S*dx, 0, -0.052*S*dz]), 0.008*S, M.steel, { shadow: false }); // grzbiet chwyta swiatlo
  var belly = [chest[0] + 0.012*S*dx, 0, sk.pivot[2] - 0.085*S];
  P.ellipsoid(belly, [0.092*S, 0.126*S, 0.062*S], M.armor, { pitch: ang + 10*RAD }); // plastron dolny z PRZERWA: przegub zbroi
  for (var i = 0; i < 3; i++) { // fartuch: 3 lamele z przerwami
    var z = sk.pivot[2] - 0.155*S - i * 0.030*S;
    P.ellipsoid([belly[0], 0, z], [0.088*S - i*0.004*S, 0.122*S - i*0.006*S, 0.012*S], i % 2 ? M.armorDark : M.armor, { pitch: ang });
  }
  // dalej: gorset (obroza szyjna), pasy na barki, pas biodrowy z klamra, nity na krawedzi plyty
}
```

Katalog deklarowany w oryginale (NIEDOŁĄCZONY w całości): napier snik z grzbietem, naramienniki (kopula + kielich + zebra), napforemniki, nagolenniki, buty, tarcza heater z emblematem druzyny, helm wielki z kita, miecz. Ta sama konwencja dla innego gatunku: karabin z magazynkiem czyta sie jako PRZEKATNA bryly z wyraznym magazynkiem (bohater SF dostaje inny sprzet, ten sam szkielet).

## Bramka jakości: sylwetka — wersja v1 (DO NIEUŻYWANIA jako jedynej bramki)

Bramka liczona na masce alfa sprite'a: liczba komponentow spojnosci, dziury, stopa, wypelnienie bboxa, pole. Slyszalny cel: czy czytelnik rozpozna "czlowiek w zbroi z mieczem" bez kolorow.

```js
function silhouetteTest(sprite, label, opts) {
  var relaxed = opts && opts.relaxed;   // klatki akcji: rozciagniecie w zamachu to cel, nie wada
  var mask = maskOf(sprite);            // alfa > 0.5
  var comp = components(mask), hole = holes(mask, comp.labels, comp.count), ft = feetCount(mask);
  var r = { label: label, components: comp.count, holes: hole, feet: ft.feet, fill: ft.fill, area: ft.area, relaxed: !!relaxed };
  r.pass = relaxed
    ? r.components <= 9 && r.fill >= 0.20 && r.area >= 550   // miecz i kita ODRYWAJA sie od bryly w zamachu
    : r.components <= 3 && r.fill >= 0.35 && r.area >= 350;  // zwarta bryla
  return r;
}
```

WAZNE: prog `area` skaluje sie z kwadratem skali postaci. 350 bylo kalibracja dla S=0.78; dla mniejszej postaci licz `350 * (S / 0.78)^2` (militia S=0.72: 298). Bez skalowania bramka odrzuca prawidlowe, chudsze widoki z boku (bryla sama sie zaslania, pole spada o ~20%). Pełny listing oryginalnej bramki nie został dołączony. Użyj testowanej alternatywy `scripts/silhouette-check.js`.

Pomiary z produkcji (caly bohater, 64 klatki, 5 warstw): NU 0 odrzuconych sylwetek, fill 0.55-0.62; zbroja plytowa z przegubami nie zwieksza liczby komponentow (przerwy czyta sie jako linie zbroi, nie jak rozpad bryly).

## Nowa bramka v2

`../scripts/silhouette-check.js` liczy liczbę spójnych komponentów, całkowite pole, wypełnienie bbox, liczbę otworów i znormalizowane pole (`area/(width*height)`). Progi ustawiane jawnie w profilu assetu; `holes` i `feet` z wersji demonstracyjnej **nie były w niej używane**. Nie używaj arbitralnego `350*(S/0.78)^2` bez kontroli tilePx, bbox i odległości kamery. Komponenty 4-connectivity i otwory muszą być liczone w rozdzielczości docelowej; szczegóły w `../shared/qa.md`. Wymagane też oględziny sylwetki na tle i test faz.
