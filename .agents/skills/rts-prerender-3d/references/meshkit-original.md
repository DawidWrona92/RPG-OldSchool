# Meshkit: bryly z dowolnego konturu (OBJ generowany w locie)

Rdzen ma gotowe bryly (cylinder, box, blob, lathe), ale zbroja i sprzet potrzebuja pryzm z WLASNYCH konturow: tarcza heater, czasza helmu, ostrza. Przybornik generuje tekst OBJ i wstawia go przez `Model.addObj`.

## polyPrismObj i taperPrismObj

```js
// Kontur w plaszczyznie lokalnej (x, y), grzbiet wzdluz lokalnego z.
function ccw(pts) {                       // wymuszenie nawinienia CCW patrząc z +z
  var n = pts.length, area2 = 0;
  for (var i = 0; i < n; i++) {
    var a = pts[i], b = pts[(i + 1) % n];
    area2 += a[0] * b[1] - b[0] * a[1];
  }
  return area2 >= 0 ? pts : pts.slice().reverse();
}
function polyPrismObj(pts, thickness) {  // pryzma z konturu: przednia pokrywa, tylna, sciany boczne
  var p = ccw(pts), n = p.length, t = thickness / 2, lines = [];
  function fmt(x) { return (+x).toFixed(4); }
  for (var i = 0; i < n; i++) lines.push('v ' + fmt(p[i][0]) + ' ' + fmt(p[i][1]) + ' ' + fmt(-t));
  for (var j = 0; j < n; j++) lines.push('v ' + fmt(p[j][0]) + ' ' + fmt(p[j][1]) + ' ' + fmt(t));
  var front = [], back = [];
  for (var k = 0; k < n; k++) { front.push(k + 1); back.push(n + k + 1); }
  lines.push('f ' + front.join(' '));
  lines.push('f ' + back.slice().reverse().join(' '));
  for (var q = 0; q < n; q++) {
    var a = q, b = (q + 1) % n;
    lines.push('f ' + (a + 1) + ' ' + (b + 1) + ' ' + (b + 1 + n) + ' ' + (a + 1 + n));
  }
  return lines.join('\n');
}
// taperPrismObj(pts0, pts1): graniastoslup zwiezany, kontury dolny i gorny (ta sama liczba punktow, wspolrzedne 3D); analogicznie.
```

## Lekcje z produkcji (bohater plytowy)

1. NAWINIENIA. `addObj` liczy normalna z `cross(v1-v0, v2-v0)`, a rasteryzer odrzuca sciany odwrocone od kamery. Kontur musi byc CCW patrzc z +z: przednia pokrywa ma wtedy normalna +z, tylna -z, a sciany boczne na zewnatrz. Zle nawinienie = sciana znika (albo w wychodzi czarna).
2. Maska druzyny a backfacing. Tarcza heater ma emblemat druzyny na PRZEDNIEJ pokrywie; przy obrotach widoku tylna pokrywa nie moze "przebija" maska. Osobne sciany z roznymi materialami (team: true tylko na przedniej) zamiast jednej bryly.
3. Kontury gotowe: `heaterOutline(s)` (plaska gora, boki z zalaniem, dol w punkt) i `greatHelmProfile()` (promien, z wzgledem srodka glowy).
4. Kamera: film bohatera ~84 px przy tilePx 96; `Camera({ tilePx: 96, halfExtent: 0.95, target: [0,0,0.45], supersample: 2 })` po ZMIARZENIU cienia (cien siega ~0.9 jednostki; halfExtent dobierany po pomiarse, nie z glowy). 8 widokow: 4.8 s, zero przycietych klatek.
5. Model twarza w +x, os z do gory; widoki przez `renderSprite(viewAngleDeg)` (kamera i swiatlo obracaja rdzen, cien na ekranie zawsze po tej samej stronie).

Pelne listingi bohatera i przybornika: kanwa "rzemioslo-detalu-etap-4b".