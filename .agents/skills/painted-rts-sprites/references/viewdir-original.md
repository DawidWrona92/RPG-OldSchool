# Kierunki jednostki: kamera wirtualna i test rozroznalnosci

## Bug, ktory wyglada dobrze

`pt.renderFrames` podaje `dir.yaw` do `build`, ale `render()` NIE obraca modelu: `viewAngleDeg` trafia wylacznie do metadanych wyniku i arkusza. Zestawy wbudowane (`pt.humanoid(P, { yaw })`, `pt.house(P, { rot })`) obracaja sie same. Ale wlasny rysunek w `build` (wlasne warstwy zbroi, broni, pozy) trzeba obracic recznie. Bez tego 8 kierunkow to 8 kopii jednego widoku. Arkusz wyglada poprawnie, walidator milczy, a w grze postac chodzi zawsze tylem albo zawsze przodem. Ten bug przechodzi przez wszystkie automatyczne bramki; zlapano go dopiero porownujac maski alfa klatek roznych kierunkow.

## Kamera wirtualna: applyView

```js
// plik viewdir.js (przenosny; zero zaleznosci poza painter.js)
function applyView(P, yawDeg, draw) {
  P.at(null, -yawDeg, draw);   // obrot modelu o -yaw; swiatlo i slonce cienia zostaja
}
```

W `build` klatki:

```js
build: function (P, dir, phase, phaseIndex) {
  applyView(P, dir.yaw, function () {
    // rysunek ZAWSZE twarza w +x (yaw 0 = patrzy SE, jak kierunek 0 pt.directions(8))
    drawMyUnit(P, pose(phaseIndex));
  });
}
```

Dlaczego to dziala i czemu niczego wiecej nie trzeba: w painter.js zarowno `SUN_DIR` (rzut cienia na ziemie), jak i `light.dir` (swiatlo cieniujace bryly) sa stale w przestrzeni RYSOWANIA (ekranu), a punkty i normalne bryl przechodza przez wewnetrzna transformacje. Sam obrot modelu daje wiec pelna konwencje kamery orbitujacej: cien pada zawsze w lewo-dol ekranu, strona oswietlona zawsze z prawej, jak w AoE2/D2, niezaleznie od kierunku. NIE rotuj swiatla ani cienia "zeby nadazaly za modelem": probowano, walidator lapal "cien pada w prawo" przy kierunkach 3-7.

## Bramka: checkDirections

Test rozroznalnosci kierunkow po renderze (maski alfa klatek roznych kierunkow musza sie roznic):

```js
// frames: uklad renderFrames (kierunek po kierunku, w kazdym framesPerDirection klatek)
function checkDirections(frames, opts) {
  var o = opts || {}, fpd = o.framesPerDirection || 1, sever = o.strict === undefined ? true : o.strict, findings = [];
  if (!frames || frames.length < fpd * 2) return [['WARN', 'za malo klatek do testu kierunkow']];
  var nd = Math.floor(frames.length / fpd);
  for (var d = 1; d < nd; d++) for (var q = 0; q < fpd; q++) {
    var f0 = frames[q], fd = frames[d * fpd + q], diff = 0, n = f0.sprite.width * f0.sprite.height;
    for (var i = 0; i < n; i++) if (Math.abs(f0.sprite.data[i * 4 + 3] - fd.sprite.data[i * 4 + 3]) > 8) diff++;
    if (diff === 0) findings.push([sever ? 'ERR' : 'WARN', 'kierunek ' + d + ' klatka ' + q +
      ' identyczny z kierunkiem 0: kierunki to kopie (albo obiekt osiowo symetryczny)']);
  }
  if (!findings.length) findings.push(['INFO', 'kierunki ' + nd + ' x ' + fpd + ': wszystkie rozne od kierunku 0']);
  return findings;
}
```

Przy walidacji: obiekt osiowo symetryczny (beczka, wieza) zasadnie daje identyczne kierunki; wtedy uzywaj `strict: false` albo nie renderuj 8 kierunkow.

## Kadr przy obrotach

Pelny obrot 360 stopni ma wiekszy bbox niz pojedynczy widok: przy wlasnych warstwach jednostki mierz bbox alfa (i cienia) po calym zbiorze klatek i ustaw ramke przed renderem. `frameClipped` liczy dotyk krawedzi kadru PRZED rozmyciem cienia, wiec cień wystajacy poza ramke tez go podnosi. Przyklad z praktyki: militia przy obrotach potrzebuje ramki 144x112 zamiast domyslnej 128x96 dla pojedynczego widoku. Weryfikuj kazda warstwe z osobna: cień plytszej warstwy moze wystawac dalej niz bryla.