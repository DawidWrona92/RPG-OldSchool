# Kierunki i animacje — corrected v2

**Istotne:** `pt.renderFrames` przekazuje `dir.yaw` do `build`, ale renderowane samodzielnie warstwy NIE obracają się bez wywołania transformacji. Własną jednostkę buduj wokół stałej osi +x i stosuj obrot `-yaw`. Nie stosuj jednocześnie `applyView` i ręcznej rotacji geometrii z `pt.humanoid(...,{yaw})` — to powoduje podwójny obrót.

```js
function applyView(P, yawDeg, draw) {
  if (!Number.isFinite(yawDeg) || typeof draw !== 'function') throw new TypeError('yaw/draw');
  return P.at(null, -yawDeg, draw);
}
```

`pt.renderFrames` i `pt.render()` mają semantykę specyficzną dla niedostarczonego `painter.js`. Zanim uznasz kierunki za poprawne, przetestuj jednostkę z niesymetryczną tarczą i bronią (0,90,180,270°, następnie przekątne). Obszary alfa mogą być identyczne dla dwóch prawidłowych orientacji — jest to co najwyżej ostrzeżenie. Kontroluj też kolor, ramkę, kotwicę, stronę tarczy i kolejność kierunków.

## Kod w tym pakiecie

`../scripts/direction-check.js` udostępnia `checkDirections(frames,{framesPerDirection,strict})`:
- waliduje liczbę klatek, szerokość/wysokość, długość RGBA oraz równy rozmiar dla wszystkich klatek;
- porównuje **wszystkie pary kierunków** dla odpowiadających sobie faz;
- sprawdza duplikaty maski alfa i duplikaty obrazu RGBA; całkowicie identyczne obrazy są błędem albo ostrzeżeniem wg `strict`;
- nierozróżnialne alfa przy innym RGBA traktuje jako WARN, nie ERR;
- nie twierdzi, że dowodzi poprawności orientacji — to wymaga wizualnej bramki testowej.

## Kadr, stopy i osie

Ustal wspólną ramkę i kotwicę dla wszystkich kierunków i faz. Mierz bbox sprite'a **oraz cienia po rozmyciu** i sprawdź margines co najmniej 1–2 px. Testuj odchylenie stóp od pozycji bazowej, ale świadomie dopuszczaj fazy lotu i ataku. Cień jest nieruchomy względem światła świata, a nie przypięty do osi tułowia; przetestuj to na jednostce asymetrycznej.
