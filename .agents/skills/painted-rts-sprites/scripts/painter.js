/* painter.js - przenosny silnik "painted 2D" do sprite'ow RTS (czysty JavaScript, ZERO zaleznosci: bez fs, Buffer, process, DOM, sieci).
 * WYGENEROWANY z src/*.js przez build.js - nie edytuj recznie. Typy: painter.d.ts.
 * Dziala w Node, Bun, Deno, przegladarce i w piaskownicach, ktore wykonuja zwykly JS. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  root.painter = api;
})(typeof globalThis !== 'undefined' ? globalThis : typeof self !== 'undefined' ? self : this, function () {
'use strict';
// ===== 01_math.js =====
// ---------------------------------------------------------------- matematyka, losowanie, szum 3D, rzut izometryczny
// Konwencje wspolne z rts-prerender-3d: kafel 96 px, jednostka swiata = 1 kafel, z = gora, kamera 2:1 (elewacja 30, azymut 45),
// widoczne sciany +x (prawa, jasniejsza), -y (lewa, ciemniejsza) i gora. Ekran: sx = (x+y)*T/2, sy = (x-y)*T/4 - z*ZPX.
var TILE_PX = 96;
var SUN_DIR = [-0.45, -1.35, -1.5];                // kierunek PROMIENI (jak w prerenderze): cien pada w lewo-dol ekranu
var Z_PER_TILE = 0.6123724356957945;               // piksele na jednostke wysokosci = tilePx * Z_PER_TILE (cos 30 / sqrt 2)
var TO_CAMERA = [0.6123724356957945, -0.6123724356957945, 0.5];   // wersor od sceny do kamery (rzut ortograficzny)
var LUMA = [0.2126, 0.7152, 0.0722];

function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function mul(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function length(a) { return Math.sqrt(dot(a, a)); }
function normalize(a) { var l = length(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }
function clamp(x, lo, hi) { return x < lo ? lo : x > hi ? hi : x; }
function mix(a, b, t) { return a + (b - a) * t; }
function smoothstep(e0, e1, x) { var t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); }
function mix3(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
// rampa kolorow: stops = [[r,g,b], ...] rownomiernie na 0..1
function ramp(stops, t) {
  t = clamp(t, 0, 1) * (stops.length - 1);
  var i = Math.min(Math.floor(t), stops.length - 2);
  return mix3(stops[i], stops[i + 1], t - i);
}

// deterministyczny generator mulberry32 (identyczny jak w rts-prerender-3d)
function makeRng(seed) {
  var state = (seed | 0) + 0x6D2B79F5 | 0;
  var next = function () {
    state = (state + 0x6D2B79F5) | 0;
    var t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  next.uniform = function (lo, hi) { return lo + (hi - lo) * next(); };
  next.normal = function () { var u = Math.max(next(), 1e-12), w = next(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * w); };
  next.int = function (lo, hi) { return lo + Math.floor(next() * (hi - lo)); };
  next.next = next;
  next.pick = function (list) { return list[Math.floor(next() * list.length) % list.length]; };
  return next;
}

// hash calkowitoliczbowy -> 0..1 (do szumu 3D i komorek lisci)
function hash3(ix, iy, iz, seed) {
  var h = Math.imul(ix | 0, 374761393) ^ Math.imul(iy | 0, 668265263) ^ Math.imul(iz | 0, 2147483647) ^ Math.imul((seed | 0) + 1, 1274126177);
  h = Math.imul(h ^ (h >>> 13), 1274126177); h = h ^ (h >>> 16);
  return (h >>> 0) / 4294967296;
}
// szum wartosciowy 3D 0..1 (gladki)
function noise3(x, y, z, seed) {
  var ix = Math.floor(x), iy = Math.floor(y), iz = Math.floor(z), fx = x - ix, fy = y - iy, fz = z - iz;
  fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy); fz = fz * fz * (3 - 2 * fz);
  var a = hash3(ix, iy, iz, seed), b = hash3(ix + 1, iy, iz, seed), c = hash3(ix, iy + 1, iz, seed), d = hash3(ix + 1, iy + 1, iz, seed);
  var e = hash3(ix, iy, iz + 1, seed), f = hash3(ix + 1, iy, iz + 1, seed), g = hash3(ix, iy + 1, iz + 1, seed), h = hash3(ix + 1, iy + 1, iz + 1, seed);
  return mix(mix(mix(a, b, fx), mix(c, d, fx), fy), mix(mix(e, f, fx), mix(g, h, fx), fy), fz);
}
function fbm3(x, y, z, seed, octaves) {
  var sum = 0, amp = 0.5, norm = 0, freq = 1;
  for (var i = 0; i < (octaves || 3); i++) { sum += amp * noise3(x * freq, y * freq, z * freq, seed + i * 17); norm += amp; amp *= 0.5; freq *= 2.03; }
  return sum / norm;
}
// szum komorkowy 3D (Worley): zwraca { f1, f2, id, dx, dy, dz } - odleglosci do najblizszych punktow cech (w jednostkach komorki), id komorki 0..1, wektor do punktu cechy
var _cell = { f1: 0, f2: 0, id: 0, dx: 0, dy: 0, dz: 0 };
function cellular3(x, y, z, seed) {
  var ix = Math.floor(x), iy = Math.floor(y), iz = Math.floor(z), f1 = 9, f2 = 9, id = 0, bx = 0, by = 0, bz = 0;
  for (var k = -1; k <= 1; k++) for (var j = -1; j <= 1; j++) for (var i = -1; i <= 1; i++) {
    var cx = ix + i, cy = iy + j, cz = iz + k, h = hash3(cx, cy, cz, seed);
    var px = cx + hash3(cx, cy, cz, seed + 101) * 0.9 + 0.05, py = cy + hash3(cx, cy, cz, seed + 211) * 0.9 + 0.05, pz = cz + hash3(cx, cy, cz, seed + 307) * 0.9 + 0.05;
    var dx = px - x, dy = py - y, dz = pz - z, d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (d < f1) { f2 = f1; f1 = d; id = h; bx = dx; by = dy; bz = dz; } else if (d < f2) f2 = d;
  }
  _cell.f1 = f1; _cell.f2 = f2; _cell.id = id; _cell.dx = bx; _cell.dy = by; _cell.dz = bz;
  return _cell;
}

// macierze 3x3 [[...],[...],[...]]
function identity() { return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]; }
function matVec(m, v) { return [m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2], m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2], m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]]; }
function rotZ(angle) { var c = Math.cos(angle), s = Math.sin(angle); return [[c, -s, 0], [s, c, 0], [0, 0, 1]]; }

// rzut: swiat -> piksele wzgledem kotwicy (0,0,0). sx w prawo, sy w dol
function isoX(x, y, tile) { return (x + y) * tile / 2; }
function isoY(x, y, z, tile) { return (x - y) * tile / 4 - z * tile * Z_PER_TILE; }
function srgbToLinear(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }

// ===== 02_textures.js =====
// ---------------------------------------------------------------- tekstury proceduralne (kafelkowalne z definicji)
// Tekstura: { size, data: Float32Array(size*size*3) } w wartosciach sRGB 0..1, jak plik PNG.

// Szum okresowy: losowa siatka interpolowana kubicznym B-splajnem z zawinieciem. Cechy rzedu 2.4*sigma pikseli, std znormalizowane do 1.
function periodicNoise(size, seed, sigmaY, sigmaX) {
  var rng = makeRng(seed);
  var cellsY = clamp(Math.round(size / (sigmaY * 2.4)), 2, size), cellsX = clamp(Math.round(size / (sigmaX * 2.4)), 2, size);
  var lattice = new Float32Array(cellsY * cellsX);
  for (var i = 0; i < lattice.length; i++) lattice[i] = rng.normal();
  var spline = function (f) { var f2 = f * f, f3 = f2 * f; return [(1 - f) * (1 - f) * (1 - f) / 6, (3 * f3 - 6 * f2 + 4) / 6, (-3 * f3 + 3 * f2 + 3 * f + 1) / 6, f3 / 6]; };
  var prep = function (cells) {
    var idx = new Int32Array(size * 4), wts = new Float32Array(size * 4);
    for (var p = 0; p < size; p++) {
      var t = p * cells / size, base = Math.floor(t), w = spline(t - base);
      for (var k = 0; k < 4; k++) { idx[p * 4 + k] = (((base - 1 + k) % cells) + cells) % cells; wts[p * 4 + k] = w[k]; }
    }
    return { idx: idx, wts: wts };
  };
  var py = prep(cellsY), px = prep(cellsX), out = new Float32Array(size * size), sum = 0, sum2 = 0;
  for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
    var value = 0;
    for (var a = 0; a < 4; a++) {
      var row = py.idx[y * 4 + a] * cellsX, wy = py.wts[y * 4 + a];
      for (var b = 0; b < 4; b++) value += lattice[row + px.idx[x * 4 + b]] * wy * px.wts[x * 4 + b];
    }
    out[y * size + x] = value; sum += value; sum2 += value * value;
  }
  var n = size * size, mean = sum / n, std = Math.sqrt(Math.max(sum2 / n - mean * mean, 1e-12));
  for (var j = 0; j < n; j++) out[j] = (out[j] - mean) / std;
  return out;
}
// fbm: suma oktaw / (indeks + 1), znormalizowana do std 1. sigmaXY = [sy, sx] daje szum anizotropowy (slój drewna, zacieki).
function fbm(size, seed, sigmas, sigmaXY) {
  sigmas = sigmas || [2, 4, 8, 16];
  var out = new Float32Array(size * size);
  for (var i = 0; i < sigmas.length; i++) {
    var noise = periodicNoise(size, seed * 131 + i * 7919 + 17, sigmaXY ? sigmaXY[0] : sigmas[i], sigmaXY ? sigmaXY[1] : sigmas[i]);
    for (var j = 0; j < out.length; j++) out[j] += noise[j] / (i + 1);
  }
  var sum = 0, sum2 = 0;
  for (var k = 0; k < out.length; k++) { sum += out[k]; sum2 += out[k] * out[k]; }
  var mean = sum / out.length, std = Math.sqrt(Math.max(sum2 / out.length - mean * mean, 1e-12));
  for (var m = 0; m < out.length; m++) out[m] = (out[m] - mean) / std;
  return out;
}
function newTexture(size) { return { size: size, data: new Float32Array(size * size * 3) }; }
// zapis piksela z mnozeniem kanalow; wartosci obcinane do 0..1
function putPixel(tex, i, r, g, b) { var d = tex.data; d[i * 3] = clamp(r, 0, 1); d[i * 3 + 1] = clamp(g, 0, 1); d[i * 3 + 2] = clamp(b, 0, 1); }

function texShingle(size, seed, rows, cols, base) {
  rows = rows || 16; cols = cols || 12; base = base || [0.60, 0.26, 0.16];
  var rng = makeRng(seed), tones = [], hues = [];
  for (var i = 0; i < rows * cols; i++) { tones.push(rng.uniform(0.72, 1.22)); hues.push([rng.uniform(-0.035, 0.035), rng.uniform(-0.035, 0.035), rng.uniform(-0.035, 0.035)]); }
  var n1 = fbm(size, seed + 1, [3, 6, 14]), n2 = fbm(size, seed + 2, [0.7, 1.4]), tex = newTexture(size);
  for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
    var yy = y / size, xx = x / size, row = Math.floor(yy * rows), fy = yy * rows - row;
    var shifted = xx * cols + (row % 2) * 0.5, colIdx = Math.floor(shifted), fx = shifted - colIdx, cell = (row % rows) * cols + (colIdx % cols);
    var tone = tones[cell], hue = hues[cell], k = 1;
    k *= 1 + 0.22 * clamp(1 - fy / 0.10, 0, 1);
    k *= 1 - 0.60 * Math.pow(clamp((fy - 0.78) / 0.22, 0, 1), 1.5);
    k *= 1 - 0.50 * clamp((0.06 - Math.min(fx, 1 - fx)) / 0.06, 0, 1);
    k *= (1 + 0.12 * n1[y * size + x]) * (1 + 0.05 * n2[y * size + x]);
    // przeksztalcenie jak w Pythonie: kolor = baza * ton + odcien, potem mnozniki
    putPixel(tex, y * size + x, (base[0] * tone + hue[0]) * k, (base[1] * tone + hue[1]) * k, (base[2] * tone + hue[2]) * k);
  }
  return tex;
}
function texPlaster(size, seed, base) {
  base = base || [0.80, 0.74, 0.60];
  var a = fbm(size, seed, [4, 10, 24]), streaks = fbm(size, seed + 1, [1], [26, 2]), c = fbm(size, seed + 2, [0.7, 1.4]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var k = (1 + 0.07 * a[i]) * (1 - 0.10 * Math.max(streaks[i], 0)) * (1 + 0.03 * c[i]);
    putPixel(tex, i, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}
function texTimber(size, seed, base) {
  base = base || [0.27, 0.17, 0.09];
  var grain = fbm(size, seed, [1], [1.1, 40]), streak = fbm(size, seed + 1, [1], [3, 90]), c = fbm(size, seed + 2, [6, 14]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var k = (1 + 0.32 * grain[i] + 0.25 * streak[i]) * (1 + 0.08 * c[i]);
    putPixel(tex, i, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}
function texPlanks(size, seed, count, base) {
  count = count || 8; base = base || [0.42, 0.28, 0.15];
  var rng = makeRng(seed), tones = [];
  for (var i = 0; i < count; i++) tones.push(rng.uniform(0.78, 1.18));
  var grain = fbm(size, seed + 1, [1], [60, 1.0]), c = fbm(size, seed + 2, [4, 10]), tex = newTexture(size);
  for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
    var xx = x / size, idx = Math.floor(xx * count), frac = xx * count - idx, side = Math.min(frac, 1 - frac), j = y * size + x;
    var k = tones[idx % count] * (1 + 0.28 * grain[j]) * (1 - 0.75 * clamp((0.05 - side) / 0.05, 0, 1)) * (1 + 0.08 * c[j]);
    putPixel(tex, j, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}
function texStone(size, seed, rows) {
  rows = rows || 8;
  var rng = makeRng(seed), heights = [], total = 0, i;
  for (i = 0; i < rows; i++) { var h = rng.uniform(0.7, 1.3); heights.push(h); total += h; }
  var edges = [0], acc = 0;
  for (i = 0; i < rows; i++) { acc += heights[i] / total; edges.push(acc); }
  var rowData = [];
  for (i = 0; i < rows; i++) {
    var widths = [], sum = 0;
    while (sum < 1) { var w = rng.uniform(0.10, 0.24); widths.push(w); sum += w; }
    widths = widths.map(function (v) { return v / sum; });
    var offset = rng.uniform(0, 1), bounds = [0], a2 = 0;
    widths.forEach(function (v) { a2 += v; bounds.push(a2); });
    var tonesRow = widths.map(function () { return rng.uniform(0.62, 0.95); }), warm = widths.map(function () { return [rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)]; });
    rowData.push({ widths: widths, bounds: bounds, offset: offset, tones: tonesRow, warm: warm });
  }
  var n1 = fbm(size, seed + 1, [3, 7, 16]), n2 = fbm(size, seed + 2, [0.7, 1.4]), tex = newTexture(size);
  for (var y = 0; y < size; y++) {
    var yy = y / size, r = 0;
    while (r < rows - 1 && yy >= edges[r + 1]) r++;
    var rd = rowData[r], y0 = edges[r], y1 = edges[r + 1], ly = (yy - y0) / (y1 - y0);
    for (var x = 0; x < size; x++) {
      var shifted = (x / size - rd.offset) % 1; if (shifted < 0) shifted += 1;
      var b = 0; while (b < rd.widths.length - 1 && shifted >= rd.bounds[b + 1]) b++;
      var lx = (shifted - rd.bounds[b]) / rd.widths[b];
      var edge = Math.min(Math.min(lx, 1 - lx) * rd.widths[b] * 14, Math.min(ly, 1 - ly) * (y1 - y0) * 14), bevel = clamp(edge, 0, 1);
      var k = (0.62 + 0.38 * bevel) * (1 + 0.10 * (0.5 - ly) * clamp(1 - bevel, 0, 1)), tone = rd.tones[b], warm = rd.warm[b], j = y * size + x;
      var m = (1 + 0.10 * n1[j]) * (1 + 0.05 * n2[j]);
      putPixel(tex, j, (0.56 * tone + warm[0]) * k * m, (0.53 * tone + warm[1]) * k * m, (0.47 * tone + warm[2]) * k * m);
    }
  }
  return tex;
}
// Krotkie kreski (zdzbla) rysowane z zawinieciem: zwraca [warstwa jasnych, warstwa ciemnych] (Float32Array size*size), lekko rozmyte
function strokeLayers(size, seed, count, lengthRange, lightShare) {
  var rng = makeRng(seed), light = new Float32Array(size * size), dark = new Float32Array(size * size), steps = Math.floor(lengthRange[1] * 2) + 1;
  for (var n = 0; n < count; n++) {
    var sx = rng.uniform(0, size), sy = rng.uniform(0, size), angle = rng.uniform(0, Math.PI), len = rng.uniform(lengthRange[0], lengthRange[1]);
    var isLight = rng.uniform(0, 1) < lightShare, strength = rng.uniform(0.5, 1.0), layer = isLight ? light : dark, dx = Math.cos(angle) * len, dy = Math.sin(angle) * len;
    for (var step = 0; step < steps; step++) {
      var f = step / Math.max(steps - 1, 1), px = ((Math.floor(sx + dx * f) % size) + size) % size, py = ((Math.floor(sy + dy * f) % size) + size) % size;
      layer[py * size + px] += strength;
    }
  }
  return [blurWrap(light, size, 0.6), blurWrap(dark, size, 0.6)];
}
function blurWrap(data, size, sigma) {
  var radius = Math.max(1, Math.floor(4 * sigma + 0.5)), kernel = [], sum = 0, i;
  for (i = -radius; i <= radius; i++) { var w = Math.exp(-i * i / (2 * sigma * sigma)); kernel.push(w); sum += w; }
  kernel = kernel.map(function (w) { return w / sum; });
  var tmp = new Float32Array(data.length), out = new Float32Array(data.length);
  for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) { var acc = 0; for (i = -radius; i <= radius; i++) acc += data[y * size + ((x + i) % size + size) % size] * kernel[i + radius]; tmp[y * size + x] = acc; }
  for (var y2 = 0; y2 < size; y2++) for (var x2 = 0; x2 < size; x2++) { var acc2 = 0; for (var j = -radius; j <= radius; j++) acc2 += tmp[(((y2 + j) % size + size) % size) * size + x2] * kernel[j + radius]; out[y2 * size + x2] = acc2; }
  return out;
}
// Trawa w stylu gier z 2000 r.: jasna, zoltawozielona, niski kontrast. Miekkie plamy (suche zoltawe i gestsze zielone) + krotkie kreski zdzbel.
// detail: mnoznik widocznosci kresek i drobnej plamistosci (0 = gladko); patches: mnoznik duzych plam koloru
function texGrass(size, seed, detail, patches) {
  detail = detail === undefined ? 1 : detail; patches = patches === undefined ? 1 : patches;
  var patch = fbm(size, seed, [30, 60, 110]), strokes = strokeLayers(size, seed + 1, Math.floor(size * size / 26), [3, 7], 0.5), mottling = fbm(size, seed + 2, [3, 6]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var dry = Math.max(patch[i], 0) * 0.15 * patches, lush = Math.max(-patch[i], 0) * 0.35 * patches, l = clamp(strokes[0][i], 0, 1.2) * 1.25 * detail, d = clamp(strokes[1][i], 0, 1.2) * 1.25 * detail, k = 1 + 0.05 * detail * mottling[i];
    putPixel(tex, i, (0.37 + 0.16 * dry - 0.05 * lush + 0.10 * l - 0.07 * d) * k, (0.47 + 0.10 * dry - 0.05 * lush + 0.10 * l - 0.08 * d) * k, (0.18 - 0.06 * dry - 0.02 * lush + 0.02 * l - 0.04 * d) * k);
  }
  return tex;
}
// paleta ciemny -> sredni -> jasny dla pola 0..1
function paletteTexture(size, field, dark, middle, light, speckle, detail) {
  var tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var f = clamp(field[i], 0, 1), a = clamp(f / 0.5, 0, 1), b = clamp((f - 0.5) / 0.5, 0, 1), k = 1 + detail * speckle[i], c = [0, 0, 0];
    for (var j = 0; j < 3; j++) c[j] = (dark[j] + (middle[j] - dark[j]) * a + (light[j] - middle[j]) * b) * k;
    putPixel(tex, i, c[0], c[1], c[2]);
  }
  return tex;
}
// Paleta lisci: kazdy lisc probkuje maly wycinek, wiec liczy sie rozklad kolorow, nie wzor. detail: mnoznik drobnej plamistosci
function texLeaf(size, seed, detail) {
  detail = detail === undefined ? 1 : detail;
  var field = fbm(size, seed, [14, 28, 48]).map(function (v) { return 0.42 + 0.22 * v; }), speckle = fbm(size, seed + 1, [2, 4]).map(function (v) { return 0.06 * v; });
  return paletteTexture(size, field, [0.10, 0.23, 0.07], [0.26, 0.43, 0.11], [0.50, 0.62, 0.17], speckle, detail);
}
// Paleta igliwia: ciemna niebieskawa zielen z rzadkimi jasniejszymi czubkami
function texNeedle(size, seed, detail) {
  detail = detail === undefined ? 1 : detail;
  var field = fbm(size, seed, [14, 28, 48]).map(function (v) { return 0.40 + 0.20 * v; }), speckle = fbm(size, seed + 1, [2, 4]).map(function (v) { return 0.05 * v; });
  return paletteTexture(size, field, [0.12, 0.27, 0.14], [0.26, 0.46, 0.24], [0.45, 0.62, 0.32], speckle, detail);
}
function texCloth(size, seed, base) {
  base = base || [0.05, 0.14, 0.72];
  var n = fbm(size, seed, [2, 6]), tex = newTexture(size);
  for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
    var weave = 0.5 + 0.5 * Math.sin(x * 2 * Math.PI / 4) * Math.sin(y * 2 * Math.PI / 4), k = 0.88 + 0.12 * weave + 0.06 * n[y * size + x];
    putPixel(tex, y * size + x, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}
function texThatch(size, seed, base) {
  base = base || [0.62, 0.50, 0.24];
  var strands = fbm(size, seed, [1], [28, 0.9]), clumps = fbm(size, seed + 1, [3, 8, 18]), fine = fbm(size, seed + 2, [0.7, 1.4]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var k = (1 + 0.26 * strands[i] + 0.14 * clumps[i]) * (1 + 0.06 * fine[i]);
    putPixel(tex, i, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}
function texBark(size, seed, base) {
  base = base || [0.32, 0.25, 0.18];
  var ridges = fbm(size, seed, [1], [30, 1.6]), cracks = fbm(size, seed + 1, [1], [18, 1.0]), c = fbm(size, seed + 2, [4, 12]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var k = (1 + 0.30 * ridges[i] - 0.12 * Math.max(-clamp(cracks[i], -3, 3), 0)) * (1 + 0.08 * c[i]);
    putPixel(tex, i, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}
function texDirt(size, seed, base) {
  base = base || [0.46, 0.34, 0.21];
  var a = fbm(size, seed, [2, 6, 20]), b = fbm(size, seed + 1, [0.8, 1.6]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) { var k = 1 + 0.10 * a[i] + 0.06 * b[i]; putPixel(tex, i, base[0] * k, base[1] * k, base[2] * k); }
  return tex;
}
function texMetal(size, seed, base) {
  base = base || [0.30, 0.30, 0.32];
  var a = fbm(size, seed, [1], [1.2, 30]), b = fbm(size, seed + 1, [3, 8]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) { var k = 1 + 0.14 * a[i] + 0.06 * b[i]; putPixel(tex, i, base[0] * k, base[1] * k, base[2] * k); }
  return tex;
}

// ---- tekstury dodatkowe dla stylu "painted": sucha ziemia, jesienna trawa, adobe, deski poziome (clapboard)
// Sucha ziemia (pomaranczowo-brazowa jak w westernowych RTS): plamy jasniejsze i ciemniejsze, drobne ziarno, kamyki
function texSoil(size, seed, base) {
  base = base || [0.70, 0.44, 0.21];
  var large = fbm(size, seed, [28, 60]), mid = fbm(size, seed + 1, [5, 12]), fine = fbm(size, seed + 2, [0.7, 1.5]), tex = newTexture(size), rng = makeRng(seed + 9);
  for (var i = 0; i < size * size; i++) {
    var field = clamp(0.5 + 0.20 * large[i] + 0.10 * mid[i], 0, 1), light = Math.max(field - 0.5, 0) * 2, dark = Math.max(0.5 - field, 0) * 2;
    var k = 1 + 0.07 * fine[i];
    putPixel(tex, i, (base[0] + 0.12 * light - 0.14 * dark) * k, (base[1] + 0.12 * light - 0.11 * dark) * k, (base[2] + 0.08 * light - 0.07 * dark) * k);
  }
  var pebbles = Math.floor(size * size / 110);
  for (var n = 0; n < pebbles; n++) {
    var px = Math.floor(rng.uniform(0, size)), py = Math.floor(rng.uniform(0, size)), tone = rng.uniform(0.05, 0.16), j = py * size + px, j2 = ((py + 1) % size) * size + px;
    for (var c = 0; c < 3; c++) { tex.data[j * 3 + c] = clamp(tex.data[j * 3 + c] + tone, 0, 1); tex.data[j2 * 3 + c] = clamp(tex.data[j2 * 3 + c] - tone * 0.8, 0, 1); }
  }
  return tex;
}
// Jesienna trawa: zoltozielona z pomaranczowymi, wyschnietymi plamami i kreskami zdzbel
function texAutumnGrass(size, seed, dryness) {
  dryness = dryness === undefined ? 0.5 : dryness;
  var patch = fbm(size, seed, [26, 52, 90]), strokes = strokeLayers(size, seed + 1, Math.floor(size * size / 24), [3, 8], 0.5), mott = fbm(size, seed + 2, [2.5, 6]), tex = newTexture(size);
  for (var i = 0; i < size * size; i++) {
    var dry = clamp(0.5 + 0.45 * patch[i] * 1.0 + (dryness - 0.5), 0, 1), l = clamp(strokes[0][i], 0, 1.2), d = clamp(strokes[1][i], 0, 1.2), k = 1 + 0.06 * mott[i];
    var r = 0.43 + 0.20 * dry + 0.08 * l - 0.06 * d, g = 0.50 - 0.03 * dry + 0.08 * l - 0.08 * d, b = 0.20 - 0.02 * dry + 0.02 * l - 0.04 * d;
    putPixel(tex, i, r * k, g * k, b * k);
  }
  return tex;
}
function texAdobe(size, seed, base) { return texPlaster(size, seed, base || [0.84, 0.80, 0.70]); }
// Deski poziome (siding): kazdy rzad ma jasna gorna krawedz, cien pod spodem i rozne tony odcinkow
function texClapboard(size, seed, rows, base) {
  rows = rows || 14; base = base || [0.68, 0.64, 0.56];
  var rng = makeRng(seed), segs = 3, tones = [], i;
  for (i = 0; i < rows * segs; i++) tones.push(rng.uniform(0.86, 1.10));
  var grain = fbm(size, seed + 1, [1], [0.9, 40]), mott = fbm(size, seed + 2, [4, 12]), tex = newTexture(size);
  for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
    var yy = y / size * rows, row = Math.floor(yy), f = yy - row, xs = x / size * segs + row * 0.37, seg = Math.floor(xs), fx = xs - seg, tone = tones[(row % rows) * segs + ((seg % segs) + segs) % segs], j = y * size + x;
    var k = tone * (1 + 0.20 * clamp(1 - f / 0.12, 0, 1)) * (1 - 0.50 * Math.pow(clamp((f - 0.80) / 0.20, 0, 1), 1.2)) * (1 - 0.45 * clamp((0.025 - Math.min(fx, 1 - fx)) / 0.025, 0, 1)) * (1 + 0.07 * grain[j]) * (1 + 0.04 * mott[j]);
    putPixel(tex, j, base[0] * k, base[1] * k, base[2] * k);
  }
  return tex;
}

var TEXTURE_FUNCTIONS = {
  roof: function () { return texShingle(512, 1); }, plaster: function () { return texPlaster(512, 2); }, timber: function () { return texTimber(512, 3); },
  planks: function () { return texPlanks(512, 4); }, stone: function () { return texStone(512, 5); }, grass: function () { return texGrass(512, 6); },
  leaf: function () { return texLeaf(256, 7); }, needle: function () { return texNeedle(256, 13); }, thatch: function () { return texThatch(512, 8); }, bark: function () { return texBark(512, 9); },
  dirt: function () { return texDirt(512, 10); }, soil: function () { return texSoil(512, 14); }, autumnGrass: function () { return texAutumnGrass(512, 15); }, adobe: function () { return texAdobe(512, 16); }, clapboard: function () { return texClapboard(512, 17); }, metal: function () { return texMetal(256, 11); }, cloth: function () { return texCloth(256, 12); },
};
// Korekta stylu gotowej tekstury (kopia): kontrast wokol sredniej jasnosci, nasycenie, jasnosc; 1.0 nic nie zmienia. Odpowiednik adjust_texture w Pythonie.
function adjustTexture(tex, options) {
  options = options || {};
  var contrast = options.contrast === undefined ? 1 : options.contrast, saturation = options.saturation === undefined ? 1 : options.saturation, brightness = options.brightness === undefined ? 1 : options.brightness;
  var n = tex.size * tex.size, out = newTexture(tex.size), mean = 0, i, c;
  for (i = 0; i < n; i++) mean += tex.data[i * 3] * LUMA[0] + tex.data[i * 3 + 1] * LUMA[1] + tex.data[i * 3 + 2] * LUMA[2];
  mean /= n;
  for (i = 0; i < n; i++) {
    var v = [0, 0, 0];
    for (c = 0; c < 3; c++) v[c] = mean + (tex.data[i * 3 + c] - mean) * contrast;
    var l = v[0] * LUMA[0] + v[1] * LUMA[1] + v[2] * LUMA[2];
    putPixel(out, i, (l + (v[0] - l) * saturation) * brightness, (l + (v[1] - l) * saturation) * brightness, (l + (v[2] - l) * saturation) * brightness);
  }
  return out;
}
// Komplet standardowych tekstur (slownik nazwa -> tekstura); names: opcjonalna lista nazw do wygenerowania;
// style: opcjonalnie { nazwa: { contrast, saturation, brightness } } - korekta wybranych tekstur, np. spokojniejszy grunt { grass: { contrast: 0.7, saturation: 0.8 } }
function standardTextures(names, style) {
  var out = {};
  Object.keys(TEXTURE_FUNCTIONS).forEach(function (name) {
    if (names && names.indexOf(name) < 0) return;
    var tex = TEXTURE_FUNCTIONS[name]();
    out[name] = style && style[name] ? adjustTexture(tex, style[name]) : tex;
  });
  return out;
}
// Tekstura -> obraz RGB (do zapisu jako PNG przez encodePng)
function textureToImage(tex) {
  var data = new Uint8Array(tex.size * tex.size * 3);
  for (var i = 0; i < data.length; i++) data[i] = Math.round(tex.data[i] * 255);
  return { width: tex.size, height: tex.size, channels: 3, data: data };
}

// ===== 03_canvas.js =====
// ---------------------------------------------------------------- Painter: bufory probek (kolor, alfa, glebia, druzyna, cien), transformacje, rzut, material, swiatlo
// Obraz powstaje w buforze o rozdzielczosci supersample x docelowej. Kazda probka ma kolor, alfa 0..1 i glebie (im wieksza, tym blizej kamery),
// wiec kolejnosc rysowania nie ma znaczenia dla przeslaniania. Cienie to osobna warstwa (rzut sylwetek na ziemie wzdluz SUN_DIR).

var DEFAULT_LIGHT = {
  dir: normalize([0.5, -0.25, 0.83]),               // kierunek DO swiatla uzywany do cieniowania scian (zgodny: prawa sciana jasna, lewa ciemna)
  sunTint: [1.14, 1.05, 0.86], shadeTint: [0.56, 0.61, 0.78],   // cieple swiatlo, chlodny cien
  power: 2.4,                                        // im wiecej, tym ostrzejszy kontrast miedzy gora / prawa / lewa sciana
  aoHeight: 0.38, aoStrength: 0.34,                  // przyciemnienie przy ziemi
  rimWidth: 1.4, rimLight: 0.20, rimDark: 0.30,      // fazowanie krawedzi (w pikselach wyjsciowych)
  screenLight: normalize([0.5, -0.85, 0]),           // kierunek do swiatla na ekranie (prawo-gora)
};

function Painter(options) {
  options = options || {};
  this.width = options.width || 320; this.height = options.height || 320;
  this.anchor = options.anchor ? [options.anchor[0], options.anchor[1]] : [this.width / 2, this.height * 0.74];
  this.tilePx = options.tilePx || TILE_PX; this.ss = options.supersample || 3; this.seed = options.seed || 1;
  this.fw = this.width * this.ss; this.fh = this.height * this.ss;
  var n = this.fw * this.fh;
  this.rgb = new Float32Array(n * 3); this.alpha = new Float32Array(n); this.depth = new Float32Array(n).fill(-1e9); this.team = new Float32Array(n); this.shadowBuf = new Float32Array(n);
  this.light = {}; for (var k in DEFAULT_LIGHT) this.light[k] = DEFAULT_LIGHT[k];
  if (options.light) for (var k2 in options.light) this.light[k2] = options.light[k2];
  this.tf = { c: 1, s: 0, o: [0, 0, 0] };            // biezaca transformacja: p' = Rz(theta) p + o
  this.shadows = []; this.shadowAlpha = options.shadowAlpha === undefined ? 0.55 : options.shadowAlpha;
  this.stats = { samples: 0 };
  this._ctx = { P: this, px: 0, py: 0, pz: 0, nx: 0, ny: 0, nz: 1, u: 0, v: 0, lx: 0, ly: 0, lz: 0, s: 0, ao: 1, alpha: 1, depth: 0, kind: '', fx: 0, fy: 0 };
  this._out = [0, 0, 0, 1, 0];   // r, g, b, alfa, flaga druzyny (shader moze ustawic out[4] = 1)
}

// ---- transformacje: at(offset, rotDeg, fn) wykonuje fn w ukladzie przesunietym o offset i obroconym wokol z
Painter.prototype.at = function (offset, rotDeg, fn) {
  var prev = this.tf, a = (rotDeg || 0) * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
  var o = offset || [0, 0, 0];
  var po = this.tf.o, pc = this.tf.c, ps = this.tf.s;
  this.tf = { c: pc * c - ps * s, s: ps * c + pc * s, o: [pc * o[0] - ps * o[1] + po[0], ps * o[0] + pc * o[1] + po[1], o[2] + po[2]] };
  try { fn(this); } finally { this.tf = prev; }
};
Painter.prototype.tp = function (p) { var t = this.tf; return [t.c * p[0] - t.s * p[1] + t.o[0], t.s * p[0] + t.c * p[1] + t.o[1], p[2] + t.o[2]]; };
Painter.prototype.tn = function (n) { var t = this.tf; return [t.c * n[0] - t.s * n[1], t.s * n[0] + t.c * n[1], n[2]]; };
// punkt swiata (po transformacji) -> piksele wyjsciowe [x, y]
Painter.prototype.project = function (p) { return [this.anchor[0] + isoX(p[0], p[1], this.tilePx), this.anchor[1] + isoY(p[0], p[1], p[2], this.tilePx)]; };
Painter.prototype._film = function (p) { var q = this.project(p); return [q[0] * this.ss, q[1] * this.ss]; };

// ---- tekstury: probkowanie dwuliniowe z zawinieciem (sRGB)
function sampleTex(tex, u, v, out) {
  var s = tex.size, d = tex.data, x = u * s - 0.5, y = v * s - 0.5, x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
  var xa = ((x0 % s) + s) % s, xb = (xa + 1) % s, ya = ((y0 % s) + s) % s, yb = (ya + 1) % s;
  var i00 = (ya * s + xa) * 3, i10 = (ya * s + xb) * 3, i01 = (yb * s + xa) * 3, i11 = (yb * s + xb) * 3;
  var w00 = (1 - fx) * (1 - fy), w10 = fx * (1 - fy), w01 = (1 - fx) * fy, w11 = fx * fy;
  out[0] = d[i00] * w00 + d[i10] * w10 + d[i01] * w01 + d[i11] * w11;
  out[1] = d[i00 + 1] * w00 + d[i10 + 1] * w10 + d[i01 + 1] * w01 + d[i11 + 1] * w11;
  out[2] = d[i00 + 2] * w00 + d[i10 + 2] * w10 + d[i01 + 2] * w01 + d[i11 + 2] * w11;
}

// ---- oswietlenie: albedo (sRGB 0..1) + normalna -> kolor. Maluje cieplo w swietle i chlodno w cieniu.
Painter.prototype.lit = function (ctx, albedo, out, mat) {
  var L = this.light, h = 0.5 + 0.5 * (ctx.nx * L.dir[0] + ctx.ny * L.dir[1] + ctx.nz * L.dir[2]);
  var k = Math.pow(clamp(h, 0, 1), L.power), ao = ctx.ao;
  var r = albedo[0] * (L.shadeTint[0] + (L.sunTint[0] - L.shadeTint[0]) * k) * ao;
  var g = albedo[1] * (L.shadeTint[1] + (L.sunTint[1] - L.shadeTint[1]) * k) * ao;
  var b = albedo[2] * (L.shadeTint[2] + (L.sunTint[2] - L.shadeTint[2]) * k) * ao;
  if (mat && mat.spec) {   // polysk: odbicie wzgledem kamery (ortograficznej)
    var nd = ctx.nx * TO_CAMERA[0] + ctx.ny * TO_CAMERA[1] + ctx.nz * TO_CAMERA[2];
    var rx = 2 * nd * ctx.nx - TO_CAMERA[0], ry = 2 * nd * ctx.ny - TO_CAMERA[1], rz = 2 * nd * ctx.nz - TO_CAMERA[2];
    var sp = Math.pow(Math.max(0, rx * L.dir[0] + ry * L.dir[1] + rz * L.dir[2]), mat.shin || 24) * mat.spec;
    r += sp; g += sp * 0.97; b += sp * 0.9;
  }
  out[0] = r; out[1] = g; out[2] = b;
};

// ---- material: { texture, size, color, tint, grain, team, spec, shin, unlit, shader, offset }
// Standardowy shader: albedo z tekstury lub koloru, drobna plamistosc 3D (grain), potem swiatlo. shader: function (ctx, out) -> pelny wlasny kolor (out[0..2]) i alfa (out[3]).
function material(def) {
  var m = { texture: def.texture || null, size: def.size || 2, color: def.color || [0.6, 0.6, 0.6], tint: def.tint || null, grain: def.grain === undefined ? 0.05 : def.grain,
    grainScale: def.grainScale || 7, team: !!def.team, spec: def.spec || 0, shin: def.shin || 24, unlit: !!def.unlit, shader: def.shader || null,
    offset: def.offset || [0, 0], seed: def.seed || 1, name: def.name || '', rim: def.rim, ao: def.ao, flip: !!def.flip };
  var rgb = [0, 0, 0];
  m.shade = function (ctx, out) {
    if (m.shader) { m.shader(ctx, out); return; }
    if (m.texture) sampleTex(m.texture, ctx.u / m.size + m.offset[0], ctx.v / m.size + m.offset[1], rgb);
    else { rgb[0] = m.color[0]; rgb[1] = m.color[1]; rgb[2] = m.color[2]; }
    if (m.tint) { rgb[0] *= m.tint[0]; rgb[1] *= m.tint[1]; rgb[2] *= m.tint[2]; }
    if (m.grain > 0) {
      var q = (fbm3(ctx.px * m.grainScale, ctx.py * m.grainScale, ctx.pz * m.grainScale, m.seed, 2) - 0.5) * 2 * m.grain, f = 1 + q;
      rgb[0] *= f; rgb[1] *= f; rgb[2] *= f;
    }
    if (m.unlit) { out[0] = rgb[0]; out[1] = rgb[1]; out[2] = rgb[2]; } else ctx.P.lit(ctx, rgb, out, m);
    out[3] = 1;
  };
  return m;
}

// ---- zapis probki z testem glebi i mieszaniem alfa
Painter.prototype._put = function (i, depth, r, g, b, a, team) {
  if (depth < this.depth[i]) return;
  var A = this.alpha[i], rgb = this.rgb, j = i * 3;
  if (a >= 0.999) { rgb[j] = r; rgb[j + 1] = g; rgb[j + 2] = b; this.alpha[i] = 1; }
  else {
    var oa = a + A * (1 - a);
    rgb[j] = (r * a + rgb[j] * A * (1 - a)) / oa; rgb[j + 1] = (g * a + rgb[j + 1] * A * (1 - a)) / oa; rgb[j + 2] = (b * a + rgb[j + 2] * A * (1 - a)) / oa;
    this.alpha[i] = oa;
  }
  if (a > 0.5) this.depth[i] = depth;
  this.team[i] = (team ? 1 : 0) * a + this.team[i] * (1 - a);
  this.stats.samples++;
};

// ---- skanowanie wielokata (parzysto-nieparzyste) po srodkach probek; pts w pikselach bufora
function scanPolygon(pts, width, height, cb) {
  var n = pts.length, minY = Infinity, maxY = -Infinity, i;
  for (i = 0; i < n; i++) { if (pts[i][1] < minY) minY = pts[i][1]; if (pts[i][1] > maxY) maxY = pts[i][1]; }
  var y0 = Math.max(0, Math.ceil(minY - 0.5)), y1 = Math.min(height - 1, Math.floor(maxY - 0.5)), xs = [];
  for (var y = y0; y <= y1; y++) {
    var yc = y + 0.5; xs.length = 0;
    for (i = 0; i < n; i++) {
      var a = pts[i], b = pts[(i + 1) % n];
      if ((a[1] <= yc && b[1] > yc) || (b[1] <= yc && a[1] > yc)) xs.push(a[0] + (yc - a[1]) * (b[0] - a[0]) / (b[1] - a[1]));
    }
    xs.sort(function (p, q) { return p - q; });
    for (var k = 0; k + 1 < xs.length; k += 2) {
      var xa = Math.max(0, Math.ceil(xs[k] - 0.5)), xb = Math.min(width - 1, Math.floor(xs[k + 1] - 0.5));
      for (var x = xa; x <= xb; x++) cb(x, y);
    }
  }
}
function convexHull(points) {
  var p = points.slice().sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
  if (p.length < 3) return p;
  function turn(o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }
  var lower = [], upper = [], i;
  for (i = 0; i < p.length; i++) { while (lower.length >= 2 && turn(lower[lower.length - 2], lower[lower.length - 1], p[i]) <= 0) lower.pop(); lower.push(p[i]); }
  for (i = p.length - 1; i >= 0; i--) { while (upper.length >= 2 && turn(upper[upper.length - 2], upper[upper.length - 1], p[i]) <= 0) upper.pop(); upper.push(p[i]); }
  lower.pop(); upper.pop();
  return lower.concat(upper);
}

// ---- cienie: punkty 3D (po transformacji) -> rzut na z=0 wzdluz SUN_DIR -> otoczka wypukla; wypelniana na koncu
Painter.prototype.groundShadow = function (points) {
  var ground = [];
  for (var i = 0; i < points.length; i++) {
    var p = points[i], t = Math.max(p[2], 0) / -SUN_DIR[2];
    ground.push(this._film([p[0] + SUN_DIR[0] * t, p[1] + SUN_DIR[1] * t, 0]));
  }
  var hull = convexHull(ground);
  if (hull.length >= 3) this.shadows.push(hull);
};
// recznie: wielokat leżący na ziemi (kontur plamy, np. cien chmury lub zacieniona kępa) we wspolrzednych swiata (xy) - bez rzutowania
Painter.prototype.groundPatch = function (xyPoints, z) {
  var pts = xyPoints.map(function (p) { return this._film(this.tp([p[0], p[1], z || 0])); }, this);
  this.shadows.push(pts);
};
// miekki cien kontaktowy pod obiektem (elipsa na ziemi): rx, ry w kaflach
Painter.prototype.contactShadow = function (center, rx, ry) {
  var pts = [];
  for (var k = 0; k < 28; k++) { var a = 2 * Math.PI * k / 28; pts.push(this._film(this.tp([center[0] + rx * Math.cos(a), center[1] + ry * Math.sin(a), 0]))); }
  this.shadows.push(pts);
};

// ---- pomocnik: pozycja punktu terenu pod probka (film px -> swiat z=0)
Painter.prototype._ground = function (fx, fy, out) {
  var sx = (fx + 0.5) / this.ss - this.anchor[0], sy = (fy + 0.5) / this.ss - this.anchor[1], T = this.tilePx;
  out[0] = sx / T + 2 * sy / T; out[1] = sx / T - 2 * sy / T;
};

// ===== 04_shapes.js =====
// ---------------------------------------------------------------- prymitywy: wielokat plaski, elipsoida, scieta bryla obrotowa (walec, stozek, kapsula), prostopadloscian, sciana (Surface), dach
// Wszystkie wspolrzedne w kaflach, z = gora. Przeslanianie rozwiazuje bufor glebi, wiec kolejnosc wywolan nie ma znaczenia.

function newell(pts) {
  var nx = 0, ny = 0, nz = 0;
  for (var i = 0; i < pts.length; i++) {
    var a = pts[i], b = pts[(i + 1) % pts.length];
    nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1]);
  }
  return normalize([nx, ny, nz]);
}
Painter.prototype._aoAt = function (z, opts) {
  if (opts && opts.ao === false) return 1;
  var L = this.light, h = (opts && opts.aoHeight) || L.aoHeight, s = (opts && opts.aoStrength !== undefined) ? opts.aoStrength : L.aoStrength;
  return 1 - s * (1 - smoothstep(0, h, z - ((opts && opts.aoBase) || 0)));
};

// fazowanie krawedzi: dystans (px wyjsciowe) do najblizszej krawedzi wielokata i kierunek na zewnatrz
function makeRim(fp, ss, rimW, light, dark, lightDir) {
  var n = fp.length;
  return function (x, y, mult) {
    var best = 1e9, ox = 0, oy = 0;
    for (var i = 0; i < n; i++) {
      var a = fp[i], b = fp[(i + 1) % n], ex = b[0] - a[0], ey = b[1] - a[1], l2 = ex * ex + ey * ey, t = l2 > 0 ? clamp(((x - a[0]) * ex + (y - a[1]) * ey) / l2, 0, 1) : 0;
      var qx = a[0] + ex * t - x, qy = a[1] + ey * t - y, d = qx * qx + qy * qy;
      if (d < best) { best = d; ox = qx; oy = qy; }
    }
    var dist = Math.sqrt(best) / ss;
    if (dist >= rimW) return 1;
    var len = Math.sqrt(ox * ox + oy * oy) || 1, facing = (ox * lightDir[0] + oy * lightDir[1]) / len, w = Math.pow(1 - dist / rimW, 1.5);
    return 1 + mult * w * (facing > 0 ? light * facing : dark * facing);
  };
}

// poly(points, mat, opts): plaski wielokat w przestrzeni. opts: normal, uAxis (os tekstury), bias, cull, rim (mnoznik, 0 = bez), ao (false), aoBase, shadow (true/false), worldUV
Painter.prototype.poly = function (points, mat, opts) {
  opts = opts || {};
  var self = this, tf = this.tf, pts = points.map(function (p) { return this.tp(p); }, this);
  var n = opts.normal ? normalize(this.tn(opts.normal)) : newell(pts), nc = dot(n, TO_CAMERA);
  if (nc < 0) { if (opts.cull) return; n = mul(n, -1); nc = -nc; }
  if (nc < 1e-3) return;
  if (opts.shadow !== false) { var elevated = false; for (var q = 0; q < pts.length; q++) if (pts[q][2] > 0.02) elevated = true; if (elevated) this.groundShadow(pts); }
  var d0 = dot(n, pts[0]), tAxis;
  if (opts.uAxis) tAxis = normalize(this.tn(opts.uAxis));
  else { var t0 = cross([0, 0, 1], n); tAxis = length(t0) < 1e-3 ? [tf.c, tf.s, 0] : normalize(t0); }
  var bAxis = cross(n, tAxis), fp = pts.map(function (p) { return this._film(p); }, this), ctx = this._ctx, out = this._out, G = [0, 0], fw = this.fw, bias = opts.bias || 0;
  var rimMult = opts.rim !== undefined ? opts.rim : (mat.rim !== undefined ? mat.rim : 1), L = this.light;
  var rim = rimMult > 0 ? makeRim(fp, this.ss, L.rimWidth, L.rimLight, L.rimDark, L.screenLight) : null, ox = opts.worldUV ? 0 : tf.o[0], oy = opts.worldUV ? 0 : tf.o[1], oz = opts.worldUV ? 0 : tf.o[2];
  ctx.kind = 'poly'; ctx.s = 0;
  scanPolygon(fp, this.fw, this.fh, function (x, y) {
    self._ground(x, y, G);
    var gx = G[0], gy = G[1], t = (d0 - (n[0] * gx + n[1] * gy)) / nc, px = gx + t * TO_CAMERA[0], py = gy + t * TO_CAMERA[1], pz = t * TO_CAMERA[2];
    ctx.px = px; ctx.py = py; ctx.pz = pz; ctx.nx = n[0]; ctx.ny = n[1]; ctx.nz = n[2];
    var rx = px - ox, ry = py - oy, rz = pz - oz;
    ctx.u = rx * tAxis[0] + ry * tAxis[1] + rz * tAxis[2]; ctx.v = -(rx * bAxis[0] + ry * bAxis[1] + rz * bAxis[2]);
    ctx.lx = rx; ctx.ly = ry; ctx.lz = rz; ctx.ao = self._aoAt(pz, opts); ctx.fx = x; ctx.fy = y; ctx.alpha = 1; out[3] = 1; out[4] = 0;
    mat.shade(ctx, out);
    if (out[3] <= 0.004) return;
    if (opts.post) opts.post(ctx, out);
    var m = rim ? rim(x + 0.5, y + 0.5, rimMult) : 1;
    self._put(y * fw + x, TO_CAMERA[0] * gx + TO_CAMERA[1] * gy + t + bias, out[0] * m, out[1] * m, out[2] * m, out[3], mat.team || out[4] > 0.5);
  });
};

// castShadow(points): rzuca cien bryly o podanych wierzcholkach (wspolrzedne lokalne, jak w at()); do zlozonych obiektow, ktorych czesci maja shadow:false
Painter.prototype.castShadow = function (points) { this.groundShadow(points.map(function (p) { return this.tp(p); }, this)); };

// card(base, shape, mat, opts): pionowa karta zwrocona do kamery; shape = [[w, h], ...] w kaflach (w w prawo na ekranie, h w gore); base = punkt oparcia
Painter.prototype.card = function (base, shape, mat, opts) {
  var R = [Math.SQRT1_2, Math.SQRT1_2, 0], pts = shape.map(function (s) { return [base[0] + R[0] * s[0], base[1] + R[1] * s[0], base[2] + s[1]]; });
  var o = {}; for (var k in (opts || {})) o[k] = opts[k];
  o.normal = o.normal || [Math.SQRT1_2, -Math.SQRT1_2, 0]; o.uAxis = o.uAxis || [R[0], R[1], 0];
  this.poly(pts, mat, o);
};

// ellipsoid(center, radii, mat, opts): analityczny impostor. opts: yaw, pitch (stopnie), axes, discard (func ctx -> true gdy pominac), shadow
function rotationFromAngles(yawDeg, pitchDeg, rollDeg) {
  var y = (yawDeg || 0) * Math.PI / 180, p = (pitchDeg || 0) * Math.PI / 180, r = (rollDeg || 0) * Math.PI / 180;
  var cy = Math.cos(y), sy = Math.sin(y), cp = Math.cos(p), sp = Math.sin(p), cr = Math.cos(r), sr = Math.sin(r);
  // R = Rz(yaw) * Ry(pitch) * Rx(roll); kolumny to osie lokalne w swiecie
  var rz = [[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], ry = [[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], rx = [[1, 0, 0], [0, cr, -sr], [0, sr, cr]];
  function mm(a, b) { var o = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]; for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) for (var k = 0; k < 3; k++) o[i][j] += a[i][k] * b[k][j]; return o; }
  return mm(mm(rz, ry), rx);
}
Painter.prototype.ellipsoid = function (center, radii, mat, opts) {
  opts = opts || {};
  var self = this, c = this.tp(center), r = radii, fw = this.fw, ctx = this._ctx, out = this._out, bias = opts.bias || 0;
  var R = rotationFromAngles(opts.yaw, opts.pitch, opts.roll);
  var tr = this.tf, wr = [[tr.c, -tr.s, 0], [tr.s, tr.c, 0], [0, 0, 1]];
  var M = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) for (var k = 0; k < 3; k++) M[i][j] += wr[i][k] * R[k][j];   // lokalne -> swiat
  var corners = [], sx, sy, sz, hull = [];
  for (sx = -1; sx <= 1; sx += 2) for (sy = -1; sy <= 1; sy += 2) for (sz = -1; sz <= 1; sz += 2) {
    var lc = [sx * r[0], sy * r[1], sz * r[2]], w = matVec(M, lc); corners.push([c[0] + w[0], c[1] + w[1], c[2] + w[2]]);
  }
  var minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
  corners.forEach(function (p) { var f = self._film(p); minX = Math.min(minX, f[0]); maxX = Math.max(maxX, f[0]); minY = Math.min(minY, f[1]); maxY = Math.max(maxY, f[1]); });
  if (opts.shadow !== false) {   // punkty na elipsoidzie (siatka 7 x 14) do otoczki cienia
    for (var a = 0; a <= 6; a++) for (var b = 0; b < 14; b++) {
      var th = Math.PI * a / 6, ph = 2 * Math.PI * b / 14, lp = [r[0] * Math.sin(th) * Math.cos(ph), r[1] * Math.sin(th) * Math.sin(ph), r[2] * Math.cos(th)], w2 = matVec(M, lp);
      hull.push([c[0] + w2[0], c[1] + w2[1], c[2] + w2[2]]);
    }
    this.groundShadow(hull);
  }
  var Mt = [[M[0][0], M[1][0], M[2][0]], [M[0][1], M[1][1], M[2][1]], [M[0][2], M[1][2], M[2][2]]];   // swiat -> lokalne (obrot)
  var cl = matVec(Mt, TO_CAMERA), dl = [cl[0] / r[0], cl[1] / r[1], cl[2] / r[2]], aa = dot(dl, dl), G = [0, 0];
  var x0 = Math.max(0, Math.floor(minX) - 1), x1 = Math.min(this.fw - 1, Math.ceil(maxX) + 1), y0 = Math.max(0, Math.floor(minY) - 1), y1 = Math.min(this.fh - 1, Math.ceil(maxY) + 1);
  var rimMult = opts.rim !== undefined ? opts.rim : 0;
  var nw = [0, 0, 0];
  for (var y = y0; y <= y1; y++) for (var x = x0; x <= x1; x++) {
    this._ground(x, y, G);
    var gx = G[0], gy = G[1], d = matVec(Mt, [gx - c[0], gy - c[1], -c[2]]), q0 = d[0] / r[0], q1 = d[1] / r[1], q2 = d[2] / r[2];
    var bb = q0 * dl[0] + q1 * dl[1] + q2 * dl[2], cc = q0 * q0 + q1 * q1 + q2 * q2 - 1, disc = bb * bb - aa * cc;
    if (disc < 0) continue;
    var t = (-bb + Math.sqrt(disc)) / aa, p0 = q0 + t * dl[0], p1 = q1 + t * dl[1], p2 = q2 + t * dl[2];
    var gl = [p0 / r[0], p1 / r[1], p2 / r[2]], nn = matVec(M, gl), nl = Math.sqrt(dot(nn, nn)) || 1;
    var px = gx + t * TO_CAMERA[0], py = gy + t * TO_CAMERA[1], pz = t * TO_CAMERA[2];
    ctx.kind = 'ellipsoid'; ctx.px = px; ctx.py = py; ctx.pz = pz; ctx.nx = nn[0] / nl; ctx.ny = nn[1] / nl; ctx.nz = nn[2] / nl;
    ctx.lx = p0; ctx.ly = p1; ctx.lz = p2; ctx.s = 0.5 + 0.5 * p2;
    ctx.u = Math.atan2(p1, p0) * (r[0] + r[1]) * 0.5; ctx.v = -p2 * r[2];
    ctx.ao = this._aoAt(pz, opts); ctx.fx = x; ctx.fy = y; out[3] = 1; out[4] = 0;
    if (opts.discard && opts.discard(ctx)) continue;
    mat.shade(ctx, out);
    if (out[3] <= 0.004) continue;
    this._put(y * fw + x, TO_CAMERA[0] * gx + TO_CAMERA[1] * gy + t + bias, out[0], out[1], out[2], out[3], mat.team || out[4] > 0.5);
  }
};

// frustum(p0, p1, r0, r1, mat, opts): walec / stozek sciety / kapsula miedzy punktami. opts: caps (domyslnie true), capMat, discard, shadow
Painter.prototype.frustum = function (p0w, p1w, r0, r1, mat, opts) {
  opts = opts || {};
  var self = this, p0 = this.tp(p0w), p1 = this.tp(p1w), axisV = sub(p1, p0), L = length(axisV);
  if (L < 1e-6) return;
  var a = mul(axisV, 1 / L), k = (r1 - r0) / L, fw = this.fw, ctx = this._ctx, out = this._out, bias = opts.bias || 0, caps = opts.caps !== false, capMat = opts.capMat || mat;
  var ref = Math.abs(a[2]) > 0.9 ? [1, 0, 0] : [0, 0, 1], e1 = normalize(cross(ref, a)), e2 = cross(a, e1);
  var minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9, ring = [];
  for (var end = 0; end < 2; end++) for (var m = 0; m < 16; m++) {
    var ang = 2 * Math.PI * m / 16, rad = end ? r1 : r0, base = end ? p1 : p0;
    var pt = [base[0] + rad * (e1[0] * Math.cos(ang) + e2[0] * Math.sin(ang)), base[1] + rad * (e1[1] * Math.cos(ang) + e2[1] * Math.sin(ang)), base[2] + rad * (e1[2] * Math.cos(ang) + e2[2] * Math.sin(ang))];
    ring.push(pt); var f = this._film(pt); minX = Math.min(minX, f[0]); maxX = Math.max(maxX, f[0]); minY = Math.min(minY, f[1]); maxY = Math.max(maxY, f[1]);
  }
  if (opts.shadow !== false) this.groundShadow(ring);
  var x0 = Math.max(0, Math.floor(minX) - 1), x1 = Math.min(this.fw - 1, Math.ceil(maxX) + 1), y0 = Math.max(0, Math.floor(minY) - 1), y1 = Math.min(this.fh - 1, Math.ceil(maxY) + 1);
  var da = dot(TO_CAMERA, a), w = [TO_CAMERA[0] - a[0] * da, TO_CAMERA[1] - a[1] * da, TO_CAMERA[2] - a[2] * da], ww = dot(w, w), Gp = [0, 0], rMean = (r0 + r1) / 2;
  for (var y = y0; y <= y1; y++) for (var x = x0; x <= x1; x++) {
    this._ground(x, y, Gp);
    var gx = Gp[0], gy = Gp[1], qx = gx - p0[0], qy = gy - p0[1], qz = -p0[2], qa = qx * a[0] + qy * a[1] + qz * a[2];
    var ux = qx - a[0] * qa, uy = qy - a[1] * qa, uz = qz - a[2] * qa, R0 = r0 + k * qa;
    var A = ww - k * k * da * da, B = ux * w[0] + uy * w[1] + uz * w[2] - k * da * R0, C = ux * ux + uy * uy + uz * uz - R0 * R0;
    var best = -1e18, kind = 0;
    if (Math.abs(A) > 1e-9) {
      var disc = B * B - A * C;
      if (disc >= 0) {
        var sq = Math.sqrt(disc), t1 = (-B + sq) / A, t2 = (-B - sq) / A;
        var s1 = qa + t1 * da, s2 = qa + t2 * da;
        if (s1 >= 0 && s1 <= L && t1 > best) { best = t1; kind = 1; }
        if (s2 >= 0 && s2 <= L && t2 > best) { best = t2; kind = 1; }
      }
    }
    if (caps && Math.abs(da) > 1e-6) {
      var tc0 = -qa / da, hx0 = ux + tc0 * w[0], hy0 = uy + tc0 * w[1], hz0 = uz + tc0 * w[2];
      if (hx0 * hx0 + hy0 * hy0 + hz0 * hz0 <= r0 * r0 && tc0 > best) { best = tc0; kind = 2; }
      var tc1 = (L - qa) / da, hx1 = ux + tc1 * w[0], hy1 = uy + tc1 * w[1], hz1 = uz + tc1 * w[2];
      if (hx1 * hx1 + hy1 * hy1 + hz1 * hz1 <= r1 * r1 && tc1 > best) { best = tc1; kind = 3; }
    }
    if (kind === 0) continue;
    var t = best, px = gx + t * TO_CAMERA[0], py = gy + t * TO_CAMERA[1], pz = t * TO_CAMERA[2], s = qa + t * da;
    var hx = px - p0[0], hy = py - p0[1], hz = pz - p0[2], ex = hx - a[0] * s, ey = hy - a[1] * s, ez = hz - a[2] * s, el = Math.sqrt(ex * ex + ey * ey + ez * ez) || 1, nx, ny, nz, cm = mat;
    if (kind === 1) { nx = ex / el - k * a[0]; ny = ey / el - k * a[1]; nz = ez / el - k * a[2]; var nl = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1; nx /= nl; ny /= nl; nz /= nl; }
    else { var sg = kind === 2 ? -1 : 1; nx = a[0] * sg; ny = a[1] * sg; nz = a[2] * sg; cm = capMat; }
    ctx.kind = 'frustum'; ctx.px = px; ctx.py = py; ctx.pz = pz; ctx.nx = nx; ctx.ny = ny; ctx.nz = nz; ctx.s = s / L;
    if (kind === 1) { ctx.u = Math.atan2(ex * e2[0] + ey * e2[1] + ez * e2[2], ex * e1[0] + ey * e1[1] + ez * e1[2]) * rMean; ctx.v = -s; }
    else { ctx.u = hx * e1[0] + hy * e1[1] + hz * e1[2]; ctx.v = hx * e2[0] + hy * e2[1] + hz * e2[2]; }
    ctx.lx = hx; ctx.ly = hy; ctx.lz = hz; ctx.ao = this._aoAt(pz, opts); ctx.fx = x; ctx.fy = y; out[3] = 1; out[4] = 0;
    if (opts.discard && opts.discard(ctx)) continue;
    cm.shade(ctx, out);
    if (out[3] <= 0.004) continue;
    this._put(y * fw + x, TO_CAMERA[0] * gx + TO_CAMERA[1] * gy + t + bias, out[0], out[1], out[2], out[3], cm.team || out[4] > 0.5);
  }
};
// beam / pole / rope: cienki walec (kapsula) o promieniu r miedzy p0 i p1
Painter.prototype.rod = function (p0, p1, r, mat, opts) { this.frustum(p0, p1, r, r, mat, opts); };
Painter.prototype.sphere = function (center, radius, mat, opts) { this.ellipsoid(center, [radius, radius, radius], mat, opts); };

// box(center, size, mat | { top, side, east, west, north, south }, opts): prostopadloscian (srodek bryly). opts: rot (stopnie wokol z), uvOffset
Painter.prototype.box = function (center, size, mats, opts) {
  opts = opts || {};
  var hx = size[0] / 2, hy = size[1] / 2, hz = size[2] / 2, isMat = typeof mats.shade === 'function';
  function pick(name) { return isMat ? mats : (mats[name] || mats.side || mats.top); }
  var faces = [
    ['east', [1, 0, 0], [[hx, -hy, -hz], [hx, hy, -hz], [hx, hy, hz], [hx, -hy, hz]]],
    ['west', [-1, 0, 0], [[-hx, hy, -hz], [-hx, -hy, -hz], [-hx, -hy, hz], [-hx, hy, hz]]],
    ['north', [0, 1, 0], [[hx, hy, -hz], [-hx, hy, -hz], [-hx, hy, hz], [hx, hy, hz]]],
    ['south', [0, -1, 0], [[-hx, -hy, -hz], [hx, -hy, -hz], [hx, -hy, hz], [-hx, -hy, hz]]],
    ['top', [0, 0, 1], [[-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]]],
  ];
  var self = this, off = opts.uvOffset;
  if (opts.shadow !== false) {
    var all = []; for (var sx = -1; sx <= 1; sx += 2) for (var sy = -1; sy <= 1; sy += 2) for (var sz = -1; sz <= 1; sz += 2) all.push([sx * hx, sy * hy, sz * hz]);
    this.at(center, opts.rot || 0, function () { self.groundShadow(all.map(function (p) { return self.tp(p); })); });
  }
  this.at(center, opts.rot || 0, function () {
    faces.forEach(function (f) {
      var m = pick(f[0]);
      if (!m) return;
      self.poly(f[2], m, { normal: f[1], cull: true, shadow: false, rim: opts.rim, ao: opts.ao, aoBase: center[2] - hz, aoHeight: opts.aoHeight, aoStrength: opts.aoStrength, bias: opts.bias });
    });
  });
};

// ---- Surface: plaszczyzna z lokalnymi wspolrzednymi (u wzdluz, v w gore); normalna = u x v musi wskazywac na zewnatrz
function Surface(painter, origin, uVec, vVec) {
  this.P = painter; this.o = origin; this.u = uVec; this.v = vVec;
  this.n = normalize(cross(uVec, vVec)); this.uLen = length(uVec); this.vLen = length(vVec);
}
// punkt na powierzchni; off = odsuniecie wzdluz normalnej (kafle)
Surface.prototype.pt = function (u, v, off) {
  var o = this.o, a = this.u, b = this.v, n = this.n;
  return [o[0] + a[0] * u + b[0] * v + n[0] * (off || 0), o[1] + a[1] * u + b[1] * v + n[1] * (off || 0), o[2] + a[2] * u + b[2] * v + n[2] * (off || 0)];
};
function surfaceOpts(s, opts, bias) { var o = {}; for (var k in (opts || {})) o[k] = opts[k]; o.normal = s.n; o.uAxis = s.u; o.shadow = false; if (o.bias === undefined) o.bias = bias || 0; return o; }
// u, v w jednostkach 0..uLen / 0..vLen - tu w kaflach, gdy wektory u, v sa jednostkowe (Painter.wall tworzy je jednostkowe)
Surface.prototype.polygon = function (uv, mat, opts) {
  var self = this, off = (opts && opts.off) || 0.004;
  this.P.poly(uv.map(function (p) { return self.pt(p[0], p[1], off); }), mat, surfaceOpts(this, opts, off * 0.5));
};
Surface.prototype.quad = function (u0, v0, u1, v1, mat, opts) { this.polygon([[u0, v0], [u1, v0], [u1, v1], [u0, v1]], mat, opts); };
// plyta wystajaca z powierzchni o depth (parapet, rama, okiennica, deska, schodek)
Surface.prototype.slab = function (u0, v0, u1, v1, depth, mat, opts) {
  opts = opts || {};
  var self = this, P = this.P, n = this.n, u = normalize(this.u), v = normalize(this.v), d0 = opts.off || 0.002;
  var c = function (uu, vv, dd) { return self.pt(uu, vv, dd); };
  var front = depth + d0, so = { cull: true, shadow: false, bias: 0, rim: opts.rim, ao: opts.ao };
  var sides = [
    [n, [c(u0, v0, front), c(u1, v0, front), c(u1, v1, front), c(u0, v1, front)]],
    [v, [c(u0, v1, d0), c(u1, v1, d0), c(u1, v1, front), c(u0, v1, front)]],
    [mul(v, -1), [c(u0, v0, front), c(u1, v0, front), c(u1, v0, d0), c(u0, v0, d0)]],
    [u, [c(u1, v0, front), c(u1, v1, front), c(u1, v1, d0), c(u1, v0, d0)]],
    [mul(u, -1), [c(u0, v1, front), c(u0, v0, front), c(u0, v0, d0), c(u0, v1, d0)]],
  ];
  sides.forEach(function (s, idx) {
    var m = idx === 0 ? mat : (opts.sideMat || mat), o = { cull: true, shadow: false, normal: s[0], rim: opts.rim, ao: opts.ao, uAxis: idx === 3 || idx === 4 ? n : self.u };
    P.poly(s[1], m, o);
  });
  if (opts.shadow) P.groundShadow([c(u0, v0, 0), c(u1, v0, 0), c(u1, v1, 0), c(u0, v1, 0), c(u0, v0, front), c(u1, v0, front), c(u1, v1, front), c(u0, v1, front)].map(function (p) { return P.tp(p); }));
};
// sciana pionowa od A do B (x, y), od z0 do z1; obrys przeciwnie do ruchu wskazowek zegara => normalna na zewnatrz. Zwraca Surface, u in [0, dlugosc] w kaflach, v in [0, z1-z0]
Painter.prototype.surface = function (origin, uVec, vVec) { return new Surface(this, origin, uVec, vVec); };
Painter.prototype.wall = function (a, b, z0, z1, mat, opts) {
  opts = opts || {};
  var dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy), u = [dx / len, dy / len, 0], s = new Surface(this, [a[0], a[1], z0], u, [0, 0, 1]);
  s.uLen = len; s.vLen = z1 - z0; s.z0 = z0; s.z1 = z1;
  var o = { normal: s.n, uAxis: u, cull: true, shadow: false, aoBase: z0, rim: opts.rim, ao: opts.ao, post: opts.post };
  if (mat) {
    this.poly([[a[0], a[1], z0], [b[0], b[1], z0], [b[0], b[1], z1], [a[0], a[1], z1]], mat, o);
  }
  return s;
};

// ---- dach: gable (dwuspadowy), hip (czterospadowy), shed (jednospadowy), pyramid
// roof({ x0, y0, x1, y1, z, rise, overhang, type, ridge: 'x'|'y', mat, gableMat, edgeMat, thickness, ridgeMat })
Painter.prototype.roof = function (o) {
  var x0 = o.x0, y0 = o.y0, x1 = o.x1, y1 = o.y1, z = o.z, rise = o.rise, oh = o.overhang === undefined ? 0.12 : o.overhang, type = o.type || 'gable', ridge = o.ridge || (x1 - x0 >= y1 - y0 ? 'x' : 'y');
  var th = o.thickness === undefined ? 0.05 : o.thickness, mat = o.mat, edgeMat = o.edgeMat || mat, self = this, hullPts = [];
  var cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  function panel(pts, m) { self.poly(pts, m, { cull: true, shadow: false, rim: o.rim === undefined ? 1 : o.rim, ao: false }); pts.forEach(function (p) { hullPts.push(self.tp(p)); }); }
  function edge(a, b, m) {   // pionowy pas grubosci dachu pod krawedzia a-b (okap); normalna na zewnatrz z kierunku a->b
    var pts = [[a[0], a[1], a[2] - th], [b[0], b[1], b[2] - th], [b[0], b[1], b[2]], [a[0], a[1], a[2]]];
    var nx = b[1] - a[1], ny = -(b[0] - a[0]), nl = Math.hypot(nx, ny) || 1;
    self.poly(pts, m, { normal: [nx / nl, ny / nl, 0], cull: true, shadow: false, ao: false });
  }
  var X0 = x0 - oh, X1 = x1 + oh, Y0 = y0 - oh, Y1 = y1 + oh;
  if (type === 'gable') {
    if (ridge === 'x') {
      var half = (y1 - y0) / 2, slope = rise / half, ze = z - oh * slope;
      var A = [X0, Y0, ze], B = [X1, Y0, ze], C = [X1, cy, z + rise], D = [X0, cy, z + rise], E = [X1, Y1, ze], F = [X0, Y1, ze];
      panel([A, B, C, D], mat); panel([D, C, E, F], mat);
      edge(A, B, edgeMat); edge(E, F, edgeMat);
      if (o.gableMat) { self.poly([[x1, y0, z], [x1, y1, z], [x1, cy, z + rise]], o.gableMat, { normal: [1, 0, 0], cull: true, shadow: false, uAxis: [0, 1, 0] }); self.poly([[x0, y1, z], [x0, y0, z], [x0, cy, z + rise]], o.gableMat, { normal: [-1, 0, 0], cull: true, shadow: false, uAxis: [0, -1, 0] }); }
      if (o.ridgeMat !== null) self.rod([X0, cy, z + rise], [X1, cy, z + rise], 0.035, o.ridgeMat || edgeMat, { shadow: false, caps: true });
    } else {
      var halfX = (x1 - x0) / 2, slopeX = rise / halfX, zeX = z - oh * slopeX;
      var A2 = [X1, Y0, zeX], B2 = [X1, Y1, zeX], C2 = [cx, Y1, z + rise], D2 = [cx, Y0, z + rise], E2 = [X0, Y1, zeX], F2 = [X0, Y0, zeX];
      panel([A2, B2, C2, D2], mat); panel([D2, C2, E2, F2], mat);
      edge(A2, B2, edgeMat);
      if (o.gableMat) { self.poly([[x1, y0, z], [x0, y0, z], [cx, y0, z + rise]], o.gableMat, { normal: [0, -1, 0], cull: true, shadow: false, uAxis: [1, 0, 0] }); }
      if (o.ridgeMat !== null) self.rod([cx, Y0, z + rise], [cx, Y1, z + rise], 0.035, o.ridgeMat || edgeMat, { shadow: false, caps: true });
    }
  } else if (type === 'hip' || type === 'pyramid') {
    var inset = Math.min(x1 - x0, y1 - y0) / 2, top = z + rise, slopeH = rise / inset, zh = z - oh * slopeH, r0p, r1p;
    var square = type === 'pyramid' || Math.abs((x1 - x0) - (y1 - y0)) < 1e-6;
    if (square) { r0p = r1p = [cx, cy, top]; }
    else if (ridge === 'x') { r0p = [x0 + inset, cy, top]; r1p = [x1 - inset, cy, top]; }
    else { r0p = [cx, y0 + inset, top]; r1p = [cx, y1 - inset, top]; }
    var P00 = [X0, Y0, zh], P10 = [X1, Y0, zh], P11 = [X1, Y1, zh], P01 = [X0, Y1, zh];
    var near = function (c) { return Math.hypot(c[0] - r0p[0], c[1] - r0p[1]) <= Math.hypot(c[0] - r1p[0], c[1] - r1p[1]) ? r0p : r1p; };
    var hipPanel = function (c0, c1) { var n0 = near(c0), n1 = near(c1); panel(n0 === n1 ? [c0, c1, n0] : [c0, c1, n1, n0], mat); };
    hipPanel(P00, P10); hipPanel(P10, P11); hipPanel(P11, P01); hipPanel(P01, P00);
    edge(P00, P10, edgeMat); edge(P10, P11, edgeMat);
  } else if (type === 'shed') {   // jednospad: wyzsza krawedz przy +y (ridge x) lub +x (ridge y)
    if (ridge === 'x') {
      var s2 = rise / (y1 - y0), zz = z - oh * s2;
      var a1 = [X0, Y0, zz], b1 = [X1, Y0, zz], c1 = [X1, Y1, z + rise + oh * s2], d1 = [X0, Y1, z + rise + oh * s2];
      panel([a1, b1, c1, d1], mat); edge(a1, b1, edgeMat);
    } else {
      var s3 = rise / (x1 - x0), zy = z - oh * s3;
      var a3 = [X0, Y0, zy], b3 = [X0, Y1, zy], c3 = [X1, Y1, z + rise + oh * s3], d3 = [X1, Y0, z + rise + oh * s3];
      panel([a3, b3, c3, d3], mat);
    }
  }
  if (o.shadow !== false) this.groundShadow(hullPts);
};

// ===== 05_render.js =====
// ---------------------------------------------------------------- render: zmniejszenie probek, obrobka "malarska", cien, maska druzyny, podglad, przyciecie
function makeImage(width, height, channels) { return { width: width, height: height, channels: channels, data: new Uint8Array(width * height * channels) }; }
function to8(x) { return Math.max(0, Math.min(255, Math.round(x * 255))); }

function blurPlane(src, w, h, sigma) {   // rozmycie gaussowskie jednego kanalu (Float32Array w*h), brzeg przedluzony
  var radius = Math.max(1, Math.ceil(sigma * 3)), kernel = [], sum = 0, i;
  for (i = -radius; i <= radius; i++) { var wt = Math.exp(-i * i / (2 * sigma * sigma)); kernel.push(wt); sum += wt; }
  kernel = kernel.map(function (v) { return v / sum; });
  var tmp = new Float32Array(src.length), out = new Float32Array(src.length);
  for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) { var acc = 0; for (i = -radius; i <= radius; i++) acc += src[y * w + clamp(x + i, 0, w - 1)] * kernel[i + radius]; tmp[y * w + x] = acc; }
  for (var y2 = 0; y2 < h; y2++) for (var x2 = 0; x2 < w; x2++) { var acc2 = 0; for (var j = -radius; j <= radius; j++) acc2 += tmp[clamp(y2 + j, 0, h - 1) * w + x2] * kernel[j + radius]; out[y2 * w + x2] = acc2; }
  return out;
}

var _defaultGround = null;
function defaultGround() { if (!_defaultGround) _defaultGround = texGrass(256, 6, 0.8, 0.8); return _defaultGround; }

// render(options) -> { sprite (RGBA), shadow (RGBA czarny), team (1 kanal), preview (RGB), anchor, tilePx, frameClipped, viewAngleDeg }
// options: trim (true), pad (2), sharpen (0.45), edgeDark (0.22), contrast (1.04), saturation (1.06), shadowBlur (0.7), shadowAlpha, ground (tekstura podgladu), groundGain, viewAngleDeg
Painter.prototype.render = function (options) {
  options = options || {};
  var ss = this.ss, w = this.width, h = this.height, n = w * h, fw = this.fw, s2 = ss * ss, i, c, self = this;
  // cienie -> bufor
  for (i = 0; i < this.shadows.length; i++) scanPolygon(this.shadows[i], fw, this.fh, function (x, y) { self.shadowBuf[y * fw + x] = 1; });
  var rgb = new Float32Array(n * 3), alpha = new Float32Array(n), team = new Float32Array(n), shadow = new Float32Array(n);
  for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
    var sa = 0, sr = 0, sg = 0, sb = 0, st = 0, ssd = 0;
    for (var yy = 0; yy < ss; yy++) for (var xx = 0; xx < ss; xx++) {
      var si = (y * ss + yy) * fw + x * ss + xx, a = this.alpha[si];
      ssd += this.shadowBuf[si];
      if (a <= 0) continue;
      sa += a; sr += this.rgb[si * 3] * a; sg += this.rgb[si * 3 + 1] * a; sb += this.rgb[si * 3 + 2] * a; st += this.team[si] * a;
    }
    var pi = y * w + x;
    shadow[pi] = ssd / s2;
    if (sa > 0) { alpha[pi] = sa / s2; rgb[pi * 3] = sr / sa; rgb[pi * 3 + 1] = sg / sa; rgb[pi * 3 + 2] = sb / sa; team[pi] = st / sa; }
  }
  // ocena ucieca (przed przycieciem)
  var frameClipped = false, e;
  for (e = 0; e < w && !frameClipped; e++) if (alpha[e] > 0.05 || alpha[(h - 1) * w + e] > 0.05 || shadow[e] > 0.25 || shadow[(h - 1) * w + e] > 0.25) frameClipped = true;
  for (e = 0; e < h && !frameClipped; e++) if (alpha[e * w] > 0.05 || alpha[e * w + w - 1] > 0.05 || shadow[e * w] > 0.25 || shadow[e * w + w - 1] > 0.25) frameClipped = true;
  // obrobka: ostrzenie (unsharp na kolorze), przyciemnienie krawedzi, korekta tonalna
  var sharpen = options.sharpen === undefined ? 0.45 : options.sharpen, edgeDark = options.edgeDark === undefined ? 0.22 : options.edgeDark;
  var contrast = options.contrast === undefined ? 1.04 : options.contrast, saturation = options.saturation === undefined ? 1.06 : options.saturation;
  if (sharpen > 0) {
    var pm = [new Float32Array(n), new Float32Array(n), new Float32Array(n)];
    for (i = 0; i < n; i++) for (c = 0; c < 3; c++) pm[c][i] = rgb[i * 3 + c] * alpha[i];
    var bp = pm.map(function (pl) { return blurPlane(pl, w, h, 0.9); }), ba = blurPlane(alpha, w, h, 0.9);
    for (i = 0; i < n; i++) if (alpha[i] > 0.5 && ba[i] > 0.05) for (c = 0; c < 3; c++) {
      var blurred = bp[c][i] / ba[i];
      rgb[i * 3 + c] = rgb[i * 3 + c] + sharpen * (rgb[i * 3 + c] - blurred);
    }
  }
  if (edgeDark > 0) {
    var darker = new Float32Array(n);
    for (var ey = 0; ey < h; ey++) for (var ex = 0; ex < w; ex++) {
      var a0 = alpha[ey * w + ex]; if (a0 <= 0) continue;
      var mn = a0;
      for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) { var qx = ex + dx, qy = ey + dy; var aq = (qx < 0 || qy < 0 || qx >= w || qy >= h) ? 0 : alpha[qy * w + qx]; if (aq < mn) mn = aq; }
      darker[ey * w + ex] = a0 - mn;
    }
    for (i = 0; i < n; i++) if (darker[i] > 0) for (c = 0; c < 3; c++) rgb[i * 3 + c] *= 1 - edgeDark * darker[i];
  }
  for (i = 0; i < n; i++) {
    if (alpha[i] <= 0) continue;
    var l = rgb[i * 3] * LUMA[0] + rgb[i * 3 + 1] * LUMA[1] + rgb[i * 3 + 2] * LUMA[2];
    for (c = 0; c < 3; c++) { var v = l + (rgb[i * 3 + c] - l) * saturation; v = (v - 0.5) * contrast + 0.5; rgb[i * 3 + c] = clamp(v, 0, 1); }
  }
  // cien
  var shadowBlur = options.shadowBlur === undefined ? 0.7 : options.shadowBlur, shadowAlpha = options.shadowAlpha === undefined ? this.shadowAlpha : options.shadowAlpha;
  if (shadowBlur > 0) shadow = blurPlane(shadow, w, h, shadowBlur);
  // przyciecie
  var x0 = 0, y0 = 0, x1 = w, y1 = h;
  if (options.trim !== false) {
    x0 = w; y0 = h; x1 = 0; y1 = 0;
    for (var ty = 0; ty < h; ty++) for (var tx = 0; tx < w; tx++) {
      var pj = ty * w + tx;
      if (alpha[pj] > 0.02 || shadow[pj] * shadowAlpha > 0.05) { if (tx < x0) x0 = tx; if (tx + 1 > x1) x1 = tx + 1; if (ty < y0) y0 = ty; if (ty + 1 > y1) y1 = ty + 1; }
    }
    var pad = options.pad === undefined ? 2 : options.pad;
    if (x1 <= x0) { x0 = 0; y0 = 0; x1 = w; y1 = h; } else { x0 = Math.max(0, x0 - pad); y0 = Math.max(0, y0 - pad); x1 = Math.min(w, x1 + pad); y1 = Math.min(h, y1 + pad); }
  }
  var ow = x1 - x0, oh = y1 - y0, sprite = makeImage(ow, oh, 4), shadowImg = makeImage(ow, oh, 4), teamImg = makeImage(ow, oh, 1), preview = makeImage(ow, oh, 3);
  var anchor = [this.anchor[0] - x0, this.anchor[1] - y0];
  var gl = groundLayer(ow, oh, anchor, this.tilePx, options.ground || defaultGround(), { gain: options.groundGain });
  for (var oy = 0; oy < oh; oy++) for (var ox = 0; ox < ow; ox++) {
    var src = (oy + y0) * w + ox + x0, dst = oy * ow + ox, al = alpha[src], sh = clamp(shadow[src] * shadowAlpha, 0, 1);
    var a8 = al < 0.02 ? 0 : to8(al);
    sprite.data[dst * 4] = to8(rgb[src * 3]); sprite.data[dst * 4 + 1] = to8(rgb[src * 3 + 1]); sprite.data[dst * 4 + 2] = to8(rgb[src * 3 + 2]); sprite.data[dst * 4 + 3] = a8;
    shadowImg.data[dst * 4 + 3] = to8(sh);
    teamImg.data[dst] = al < 0.02 ? 0 : to8(clamp(team[src], 0, 1));
    for (c = 0; c < 3; c++) preview.data[dst * 3 + c] = to8(gl.data[dst * 3 + c] * (1 - sh) * (1 - al) + rgb[src * 3 + c] * al);
  }
  return { sprite: sprite, shadow: shadowImg, team: teamImg, preview: preview, anchor: anchor, tilePx: this.tilePx, frameClipped: frameClipped, viewAngleDeg: options.viewAngleDeg || 0 };
};

// swapTeamColor(sprite, teamMask, color): przemalowanie obszaru maski z zachowaniem jasnosci (jak w rts-prerender-3d)
function swapTeamColor(sprite, teamMask, color) {
  color = color || [0.80, 0.12, 0.12];
  var n = sprite.width * sprite.height, out = makeImage(sprite.width, sprite.height, 4), sum = 0, count = 0, i, c;
  for (i = 0; i < n; i++) if (teamMask.data[i] > 127) { sum += (sprite.data[i * 4] * LUMA[0] + sprite.data[i * 4 + 1] * LUMA[1] + sprite.data[i * 4 + 2] * LUMA[2]) / 255; count++; }
  var reference = count ? sum / count : 0.30;
  for (i = 0; i < n; i++) {
    var m = teamMask.data[i] / 255, rgb = [sprite.data[i * 4] / 255, sprite.data[i * 4 + 1] / 255, sprite.data[i * 4 + 2] / 255];
    var luma = rgb[0] * LUMA[0] + rgb[1] * LUMA[1] + rgb[2] * LUMA[2];
    for (c = 0; c < 3; c++) { var tinted = Math.min(1, luma / Math.max(reference, 1e-3) * color[c]); out.data[i * 4 + c] = Math.floor(Math.min(1, rgb[c] * (1 - m) + tinted * m) * 255); }
    out.data[i * 4 + 3] = sprite.data[i * 4 + 3];
  }
  return out;
}

// sprite(options): fabryka. options: width, height, anchor, tilePx (96), supersample (3; 2 = szkic), seed, light, shadowAlpha
function sprite(options) { return new Painter(options); }

// renderFrames({ frame: { width, height, anchor, supersample, tilePx }, directions (liczba kierunkow, domyslnie 8), phases (liczba klatek animacji, domyslnie 1), build: function (P, dir, phase, phaseIndex), render })
// Zwraca tablice klatek (trim: false, ta sama ramka i kotwica) gotowa do packSheet. Kolejnosc: kierunek po kierunku, w kazdym phases klatek.
// build rysuje obiekt w P; dir = { index, yaw, name }, phase = 0..1 (ulamek cyklu).
function renderFrames(options) {
  var frame = options.frame || {}, dirs = directions(options.directions || 8), phases = options.phases || 1, frames = [];
  dirs.forEach(function (dir) {
    for (var p = 0; p < phases; p++) {
      var P = new Painter(frame), phase = p / phases;
      options.build(P, dir, phase, p);
      var res = P.render(Object.assign({}, options.render || {}, { trim: false, viewAngleDeg: dir.yaw }));
      res.direction = dir.name; res.phaseIndex = p;
      frames.push(res);
    }
  });
  return frames;
}

// ===== 06_nature.js =====
// ---------------------------------------------------------------- material pomocniczy, roslinnosc, kamienie, ziemia
// Funkcje zestawu przyjmuja Painter jako pierwszy argument: tree(P, [x, y], opts). Wszystko rysowane w biezacym ukladzie P.at(...).

var PALETTE = {
  wood: [0.42, 0.28, 0.15], darkWood: [0.26, 0.17, 0.09], oldWood: [0.46, 0.40, 0.32], plaster: [0.84, 0.80, 0.70], whitewash: [0.90, 0.88, 0.82], brick: [0.58, 0.28, 0.20],
  iron: [0.22, 0.22, 0.24], rust: [0.46, 0.24, 0.12], cloth: [0.70, 0.62, 0.48], red: [0.62, 0.12, 0.10], blue: [0.15, 0.25, 0.60], green: [0.20, 0.40, 0.16],
  skin: [0.80, 0.58, 0.42], skinDark: [0.62, 0.42, 0.30], leather: [0.36, 0.22, 0.12], denim: [0.22, 0.30, 0.46], black: [0.10, 0.10, 0.11], white: [0.88, 0.88, 0.85],
};
function solid(color, opts) {
  var d = { color: color, grain: 0.04 }; for (var k in (opts || {})) d[k] = opts[k];
  return material(d);
}

var _texCache = {};
function stdTex(name) { if (!_texCache[name]) _texCache[name] = TEXTURE_FUNCTIONS[name](); return _texCache[name]; }

var FOLIAGE = {
  summer: [[0.06, 0.15, 0.05], [0.15, 0.29, 0.08], [0.31, 0.45, 0.13], [0.55, 0.64, 0.22]],
  olive: [[0.09, 0.13, 0.06], [0.22, 0.28, 0.09], [0.40, 0.46, 0.15], [0.64, 0.67, 0.28]],
  autumn: [[0.24, 0.08, 0.04], [0.52, 0.20, 0.06], [0.79, 0.41, 0.10], [0.95, 0.68, 0.26]],
  red: [[0.22, 0.05, 0.04], [0.50, 0.12, 0.07], [0.75, 0.26, 0.10], [0.93, 0.50, 0.20]],
  gold: [[0.28, 0.15, 0.04], [0.60, 0.36, 0.08], [0.86, 0.62, 0.16], [0.97, 0.85, 0.40]],
  spruce: [[0.04, 0.11, 0.07], [0.10, 0.23, 0.13], [0.21, 0.39, 0.21], [0.40, 0.56, 0.32]],
  spruceAutumn: [[0.17, 0.09, 0.04], [0.38, 0.21, 0.07], [0.59, 0.35, 0.10], [0.80, 0.56, 0.21]],
  dry: [[0.20, 0.17, 0.07], [0.40, 0.34, 0.12], [0.62, 0.54, 0.22], [0.80, 0.72, 0.38]],
};
function paletteStops(p, fallback) { return typeof p === 'string' ? FOLIAGE[p] : (p || FOLIAGE[fallback]); }

// Material lisci: mozaika kopulastych "kep lisci" (komorki Worleya w przestrzeni swiata), kolor z rampy wg swiatla, ao korony i ciemne szczeliny.
// state (mutowany przez budowniczego drzewa): { cx, cy, cz, R, depth } - srodek i promien korony, glebokosc kepy (0 = wnetrze, 1 = zewnatrz)
function foliageMaterial(def) {
  def = def || {};
  var pal = paletteStops(def.palette, 'summer'), cell = def.cell || 0.14, fineCell = def.fineCell || 0.045, dome = def.dome === undefined ? 0.55 : def.dome, seed = def.seed || 3, ragged = def.ragged === undefined ? 0.8 : def.ragged;
  var state = def.state || { cx: 0, cy: 0, cz: 1, R: 1, depth: 1 };
  var m = material({ name: 'foliage', shader: function (ctx, out) {
    var nd = ctx.nx * TO_CAMERA[0] + ctx.ny * TO_CAMERA[1] + ctx.nz * TO_CAMERA[2];
    var f = cellular3(ctx.px / fineCell, ctx.py / fineCell, ctx.pz / fineCell, seed + 31), fid = f.id, ff1 = f.f1;
    if (ragged > 0 && nd < 0.5 && fid < smoothstep(0.5, 0.0, nd) * ragged) { out[3] = 0; return; }
    var c = cellular3(ctx.px / cell, ctx.py / cell, ctx.pz / cell, seed);
    var tx = ctx.nx - c.dx * dome, ty = ctx.ny - c.dy * dome, tz = ctx.nz - c.dz * dome, tl = Math.sqrt(tx * tx + ty * ty + tz * tz) || 1;
    var Ld = ctx.P.light.dir, h = 0.5 + 0.5 * (tx * Ld[0] + ty * Ld[1] + tz * Ld[2]) / tl, k = Math.pow(clamp(h, 0, 1), 1.55);
    var q = clamp((ctx.pz - state.cz) / state.R * 0.5 + 0.5, 0, 1), gap = smoothstep(0.0, 0.30, c.f2 - c.f1);
    var x = k * 0.86 + (c.id - 0.5) * 0.22 + (fid - 0.5) * 0.34 + (ff1 < 0.18 ? 0.04 : 0) + (q - 0.5) * 0.46 - (1 - state.depth) * 0.42 - (1 - gap) * 0.13 + 0.07;
    x *= ctx.ao;
    var col = ramp(pal, x), cool = 1 - smoothstep(0.05, 0.55, x);
    out[0] = col[0] * (1 - 0.14 * cool); out[1] = col[1] * (1 - 0.04 * cool); out[2] = col[2] * (1 + 0.16 * cool); out[3] = 1;
  } });
  m.state = state; m.palette = pal;
  return m;
}
// Material igliwia (stozek): zabkowany dolny brzeg (galazki zwisaja), smugi wzdluz spadku, ciemne szczeliny przy brzegu.
// state: { teeth, phase, rim } mutowane przez budowniczego
function needleMaterial(def) {
  def = def || {};
  var pal = paletteStops(def.palette, 'spruce'), seed = def.seed || 5, state = def.state || { teeth: 11, phase: 0, rim: 0.34 };
  var m = material({ name: 'needle', shader: function (ctx, out) {
    var ang = Math.atan2(ctx.ly, ctx.lx), tooth = Math.abs(Math.sin(ang * state.teeth * 0.5 + state.phase)), jit = noise3(ang * 3.1, ctx.s * 4, 0, seed);
    var cut = 0.02 + state.rim * Math.pow(tooth, 1.35) * (0.55 + 0.9 * jit);
    if (ctx.s < cut) { out[3] = 0; return; }
    var streak = noise3(ang * 12.0, ctx.s * 6.0, 0.5, seed + 3), fine = noise3(ang * 40.0, ctx.s * 26.0, 1.5, seed + 9);
    var Ld = ctx.P.light.dir, h = 0.5 + 0.5 * (ctx.nx * Ld[0] + ctx.ny * Ld[1] + ctx.nz * Ld[2]), k = Math.pow(clamp(h, 0, 1), 1.4);
    var edge = smoothstep(cut, cut + 0.08, ctx.s);
    var x = k * 0.80 + (streak - 0.5) * 0.34 + (fine - 0.5) * 0.30 + (ctx.s - 0.45) * 0.30 - 0.26 * (1 - smoothstep(0.0, 0.5, ctx.s)) - (1 - edge) * 0.30 + 0.10 - (state.shade || 0);
    x *= ctx.ao;
    var col = ramp(pal, x), cool = 1 - smoothstep(0.05, 0.5, x);
    out[0] = col[0] * (1 - 0.10 * cool); out[1] = col[1]; out[2] = col[2] * (1 + 0.14 * cool); out[3] = 1;
  } });
  m.state = state; m.palette = pal;
  return m;
}
function barkMaterial(tint) { return material({ texture: stdTex('bark'), size: 0.9, tint: tint || null, grain: 0.07, name: 'bark', ao: true }); }

// tree(P, [x, y], { height, crown, palette | palettes, seed, lean, trunk }) -> drzewo liściaste; ~2.4 kafla wysokosci
function tree(P, pos, o) {
  o = o || {};
  var H = o.height || 2.2, rng = makeRng((o.seed || 1) * 7 + 3), Rc = o.crown || H * 0.28, cz = H * 0.64, lean = o.lean === undefined ? 0.05 : o.lean;
  var pals = (o.palettes || [o.palette || 'summer']).map(function (p) { return foliageMaterial({ palette: p, seed: (o.seed || 1) + 4, cell: o.cell || 0.14 }); });
  var bark = barkMaterial();
  var lx = lean * rng.uniform(-1, 1), ly = lean * rng.uniform(-1, 1);
  P.at([pos[0], pos[1], 0], 0, function () {
    P.frustum([0, 0, 0], [0, 0, 0.18], 0.21, 0.15, bark, { caps: false });                       // zgrubienie u podstawy
    P.frustum([0, 0, 0.1], [lx, ly, cz + Rc * 0.1], 0.15, 0.085, bark, { caps: false });
    var nb = 4; for (var b = 0; b < nb; b++) {
      var a = b * 2 * Math.PI / nb + rng.uniform(0, 1), z0 = cz - Rc * 0.55 + b * 0.05;
      P.rod([lx * 0.7, ly * 0.7, z0], [Math.cos(a) * Rc * 0.55, Math.sin(a) * Rc * 0.55, cz + Rc * 0.05], 0.035, bark, { shadow: false });
    }
    var n = o.clumps || 26, golden = Math.PI * (3 - Math.sqrt(5)), hold = [];
    for (var i = 0; i < n; i++) {
      var y = 1 - 2 * (i + 0.5) / n, rr = Math.sqrt(Math.max(0, 1 - y * y)), th = i * golden + rng.uniform(0, 0.5), shell = (0.62 + 0.36 * rng.next()) * (0.82 + 0.36 * noise3(Math.cos(th) * 1.3 + pos[0], Math.sin(th) * 1.3 + pos[1], y * 1.5, 5));
      if (y < -0.72) shell *= 0.8;
      var px = Math.cos(th) * rr * Rc * shell, py = Math.sin(th) * rr * Rc * shell, pz = cz + y * Rc * 1.12 * shell, rad = Rc * (0.28 + 0.24 * rng.next() * rng.next() + 0.10);
      hold.push({ p: [lx + px, ly + py, pz], r: rad, depth: clamp((shell - 0.4) / 0.6, 0, 1), id: i });
    }
    for (var c0 = 0; c0 < 3; c0++) hold.push({ p: [lx + rng.uniform(-0.15, 0.15) * Rc, ly + rng.uniform(-0.15, 0.15) * Rc, cz + rng.uniform(-0.2, 0.25) * Rc], r: Rc * 0.45, depth: 0.12, id: 100 + c0 });
    hold.forEach(function (cl) {
      var pick = Math.min(pals.length - 1, Math.floor(noise3(cl.p[0] * 1.4 + pos[0] * 3, cl.p[1] * 1.4 + pos[1] * 3, cl.p[2] * 1.4, 11) * pals.length)), m = pals[pick];
      m.state.cx = lx; m.state.cy = ly; m.state.cz = cz; m.state.R = Rc; m.state.depth = cl.depth;
      P.ellipsoid(cl.p, [cl.r * 1.08, cl.r * 1.08, cl.r * 0.80], m, { aoBase: 0.0, aoHeight: 0.9, aoStrength: 0.25, yaw: cl.id * 47 });
    });
  });
}

// conifer(P, [x, y], { height, radius, tiers, palette, seed }) -> swierk / sosna z pietrami zwisajacych galezi; ~3 kafle wysokosci
function conifer(P, pos, o) {
  o = o || {};
  var H = o.height || 2.8, R0 = o.radius || 0.64, n = o.tiers || 7, rng = makeRng((o.seed || 1) * 11 + 5), pal = o.palette || 'spruce';
  var needle = needleMaterial({ palette: pal, seed: (o.seed || 1) + 2 }), bark = barkMaterial();
  P.at([pos[0], pos[1], 0], 0, function () {
    P.frustum([0, 0, 0], [0, 0, H * 0.82], 0.13, 0.04, bark, { caps: false });
    for (var i = 0; i < n; i++) {
      var t = i / (n - 1), z0 = H * (0.12 + 0.66 * Math.pow(t, 0.95)), hT = H * (0.34 - 0.14 * t), R = R0 * (1 - 0.86 * Math.pow(t, 0.9)) * rng.uniform(0.92, 1.08);
      needle.state.teeth = 9 + rng.int(0, 5); needle.state.phase = rng.uniform(0, 6.28); needle.state.rim = 0.30 + 0.12 * (1 - t); needle.state.shade = 0.06 * (1 - t);
      var ox = rng.uniform(-0.03, 0.03), oy = rng.uniform(-0.03, 0.03);
      P.frustum([ox, oy, z0], [ox, oy, z0 + hT], R, 0.02, needle, { caps: false, aoBase: 0, aoHeight: 0.8, aoStrength: 0.30 });
    }
  });
}

// bush(P, [x, y], { size, palette, seed })
function bush(P, pos, o) {
  o = o || {};
  var s = o.size || 0.55, rng = makeRng((o.seed || 1) * 5 + 1), m = foliageMaterial({ palette: o.palette || 'olive', seed: (o.seed || 1) + 8, cell: 0.10, fineCell: 0.035, dome: 0.55 }), n = o.clumps || 5;
  P.at([pos[0], pos[1], 0], 0, function () {
    for (var i = 0; i < n; i++) {
      var a = i * 2.4 + rng.uniform(0, 0.6), d = i === 0 ? 0 : s * rng.uniform(0.35, 0.6), r = s * rng.uniform(0.42, 0.58), z = r * 0.62;
      m.state.cx = 0; m.state.cy = 0; m.state.cz = s * 0.5; m.state.R = s; m.state.depth = i === 0 ? 0.4 : 0.9;
      P.ellipsoid([Math.cos(a) * d, Math.sin(a) * d, z], [r, r, r * 0.8], m, { aoHeight: 0.4, aoStrength: 0.3 });
    }
  });
}

// rock(P, [x, y], { size, palette: 'sand' | 'grey', seed })
function rockMaterial(kind, seed) {
  var pal = kind === 'grey' ? [[0.16, 0.16, 0.17], [0.36, 0.36, 0.37], [0.56, 0.56, 0.56], [0.76, 0.75, 0.72]] : [[0.30, 0.17, 0.09], [0.55, 0.34, 0.17], [0.76, 0.52, 0.28], [0.92, 0.72, 0.46]];
  return material({ name: 'rock', shader: function (ctx, out) {
    var c = cellular3(ctx.px * 3.2, ctx.py * 3.2, ctx.pz * 3.2, seed), fine = noise3(ctx.px * 22, ctx.py * 22, ctx.pz * 22, seed + 4);
    var tx = ctx.nx + (c.id - 0.5) * 0.9 - c.dx * 0.6, ty = ctx.ny + (hash3(c.id * 1000 | 0, 1, 2, seed) - 0.5) * 0.9 - c.dy * 0.6, tz = ctx.nz + (hash3(c.id * 1000 | 0, 3, 4, seed) - 0.5) * 0.5, tl = Math.sqrt(tx * tx + ty * ty + tz * tz) || 1;
    var Ld = ctx.P.light.dir, h = 0.5 + 0.5 * (tx * Ld[0] + ty * Ld[1] + tz * Ld[2]) / tl, k = Math.pow(clamp(h, 0, 1), 1.7);
    var x = (k * 0.95 + (fine - 0.5) * 0.18 + (c.id - 0.5) * 0.12) * ctx.ao, col = ramp(pal, x), cool = 1 - smoothstep(0.05, 0.5, x);
    out[0] = col[0] * (1 - 0.1 * cool); out[1] = col[1]; out[2] = col[2] * (1 + 0.14 * cool); out[3] = 1;
  } });
}
function rock(P, pos, o) {
  o = o || {};
  var s = o.size || 0.5, rng = makeRng((o.seed || 1) * 13 + 7), m = rockMaterial(o.palette || 'sand', (o.seed || 1) + 6), n = o.parts || 2;
  P.at([pos[0], pos[1], 0], 0, function () {
    for (var i = 0; i < n; i++) {
      var d = i === 0 ? 0 : s * rng.uniform(0.4, 0.7), a = rng.uniform(0, 6.28), r = s * (i === 0 ? 1 : rng.uniform(0.45, 0.7));
      P.ellipsoid([Math.cos(a) * d, Math.sin(a) * d, r * 0.42], [r * rng.uniform(0.9, 1.2), r * rng.uniform(0.7, 1.0), r * 0.55], m, { yaw: rng.uniform(0, 180), aoHeight: 0.25, aoStrength: 0.35 });
    }
  });
}

// tuft(P, [x, y], { blades, height, palette, seed }) -> kepka trawy z karteczek; do ozdabiania terenu
function tuft(P, pos, o) {
  o = o || {};
  var rng = makeRng((o.seed || 1) * 17 + 3), n = o.blades || 9, hgt = o.height || 0.16, cols = o.colors || [[0.30, 0.38, 0.12], [0.50, 0.58, 0.20], [0.62, 0.62, 0.26]];
  P.at([pos[0], pos[1], 0], 0, function () {
    for (var i = 0; i < n; i++) {
      var bx = rng.uniform(-0.07, 0.07), by = rng.uniform(-0.07, 0.07), hh = hgt * rng.uniform(0.55, 1.15), lean = rng.uniform(-0.05, 0.05), w = 0.018, pick = rng.int(0, cols.length), col = cols[pick];
      var m = material({ name: 'blade', shader: (function (c0) { return function (ctx, out) {
        var t = clamp(ctx.lz / hh, 0, 1), k = 0.55 + 0.6 * t; out[0] = c0[0] * k; out[1] = c0[1] * k; out[2] = c0[2] * k; out[3] = 1; }; })(col) });
      P.card([bx, by, 0], [[-w, 0], [w, 0], [lean * 0.4 + w * 0.5, hh * 0.6], [lean, hh]], m, { rim: 0, ao: false, shadow: false });
    }
  });
}

// pole uprawne: field(P, { x0, y0, x1, y1, rows, crop: 'wheat' | 'corn' | 'green', seed })
function field(P, o) {
  var soil = material({ texture: stdTex('soil'), size: 2.2, grain: 0.03, unlit: false }), rng = makeRng((o.seed || 1) * 3 + 1), rows = o.rows || 6;
  var cols = o.crop === 'green' ? [[0.22, 0.42, 0.14], [0.38, 0.58, 0.20]] : o.crop === 'corn' ? [[0.40, 0.46, 0.15], [0.70, 0.66, 0.26]] : [[0.62, 0.52, 0.20], [0.86, 0.74, 0.34]];
  P.poly([[o.x0, o.y0, 0], [o.x1, o.y0, 0], [o.x1, o.y1, 0], [o.x0, o.y1, 0]], soil, { normal: [0, 0, 1], shadow: false, rim: 0, ao: false, bias: -0.002 });
  for (var r = 0; r < rows; r++) {
    var yy = o.y0 + (r + 0.5) * (o.y1 - o.y0) / rows;
    for (var x = o.x0 + 0.04; x < o.x1 - 0.04; x += 0.075) {
      var hh = 0.13 + 0.07 * rng.next(), col = mix3(cols[0], cols[1], rng.next()), m = solid(col, { grain: 0.0 }), xx = x + rng.uniform(-0.015, 0.015);
      var ms = material({ name: 'crop', shader: (function (c0, h0) { return function (ctx, out) { var k = 0.7 + 0.5 * clamp(ctx.lz / h0, 0, 1); out[0] = c0[0] * k; out[1] = c0[1] * k; out[2] = c0[2] * k; out[3] = 1; }; })(col, hh) });
      P.card([xx, yy, 0], [[-0.02, 0], [0.02, 0], [0.012, hh], [-0.012, hh * 1.0]], ms, { rim: 0, ao: false, shadow: false });
    }
  }
}

function stump(P, pos, o) {
  o = o || {};
  var r = o.radius || 0.16, bark = barkMaterial();
  P.at([pos[0], pos[1], 0], 0, function () {
    P.frustum([0, 0, 0], [0, 0, 0.16], r * 1.15, r, bark, { capMat: material({ color: [0.62, 0.46, 0.28], grain: 0.1 }) });
  });
}

// deadTree(P, [x, y], { height, seed }) -> sucha kora i nagie gałezie
function deadTree(P, pos, o) {
  o = o || {};
  var H = o.height || 1.9, rng = makeRng((o.seed || 1) * 19 + 2), bark = barkMaterial([0.85, 0.82, 0.78]);
  P.at([pos[0], pos[1], 0], 0, function () {
    P.frustum([0, 0, 0], [0.04, 0.02, H], 0.09, 0.03, bark, { caps: false });
    for (var i = 0; i < 4; i++) {
      var a = rng.uniform(0, 6.28), z = H * (0.45 + 0.13 * i), len = 0.35 * (1 - 0.15 * i);
      P.rod([0.04 * z / H, 0.02 * z / H, z], [Math.cos(a) * len, Math.sin(a) * len, z + len * 0.8], 0.022, bark, {});
    }
  });
}

// cactus(P, [x, y], { height, seed })
function cactus(P, pos, o) {
  o = o || {};
  var H = o.height || 0.9, g = material({ name: 'cactus', shader: function (ctx, out) {
    var rib = 0.5 + 0.5 * Math.cos(Math.atan2(ctx.ly, ctx.lx) * 10), Ld = ctx.P.light.dir, h = 0.5 + 0.5 * (ctx.nx * Ld[0] + ctx.ny * Ld[1] + ctx.nz * Ld[2]), k = Math.pow(clamp(h, 0, 1), 1.6);
    var x = (0.08 + 0.88 * k) * (0.68 + 0.32 * rib) * ctx.ao, col = ramp([[0.06, 0.16, 0.08], [0.16, 0.34, 0.16], [0.36, 0.56, 0.28]], x); out[0] = col[0]; out[1] = col[1]; out[2] = col[2]; out[3] = 1; } });
  P.at([pos[0], pos[1], 0], 0, function () {
    P.frustum([0, 0, 0], [0, 0, H], 0.10, 0.09, g, { capMat: g });
    P.sphere([0, 0, H], 0.09, g, {});
    P.rod([0.0, 0.06, H * 0.42], [0.22, 0.06, H * 0.42], 0.065, g, {}); P.rod([0.22, 0.06, H * 0.42], [0.24, 0.06, H * 0.75], 0.06, g, {}); P.sphere([0.24, 0.06, H * 0.75], 0.06, g, {});
  });
}

// ===== 07_buildings.js =====
// ---------------------------------------------------------------- budynki i rekwizyty (ściany z oknami i drzwiami, dachy, wieża, beczki, płoty, namiot, ognisko)

var _matCache = {};
function cached(key, make) { if (!_matCache[key]) _matCache[key] = make(); return _matCache[key]; }
function copyOpts(o, defaults) { var r = {}, k; for (k in defaults) r[k] = defaults[k]; for (k in (o || {})) r[k] = o[k]; return r; }

// Szyba: ciemna u gory (cien nadproza), jasniejsza na dole (odbicie nieba), skosny refleks. v0 = wysokosc dolu szyby (z lokalne), h = wysokosc szyby
function windowGlass(v0, h, opts) {
  opts = opts || {};
  var top = opts.top || [0.05, 0.08, 0.11], bot = opts.bottom || [0.30, 0.42, 0.54];
  return material({ name: 'glass', shader: function (ctx, out) {
    var t = clamp((ctx.lz - v0) / h, 0, 1), col = mix3(bot, top, Math.pow(t, 0.85)), d = ctx.u * 1.7 - t * 0.5, streak = Math.sin(d * 9.0), k = 1 - 0.55 * smoothstep(0.72, 1.0, t);
    if (streak > 0.86) { var add = 0.10 * (streak - 0.86) / 0.14; col = [col[0] + add, col[1] + add, col[2] + add]; }
    var lit = [0, 0, 0]; ctx.P.lit(ctx, [col[0] * k, col[1] * k, col[2] * k], lit, null);
    out[0] = lit[0]; out[1] = lit[1]; out[2] = lit[2]; out[3] = 1;
  } });
}

// okno na scianie s (Surface): srodek (uc, vc), szerokosc w, wysokosc h. opts: frameMat, sillMat, shutterMat, frame
function windowOn(P, s, uc, vc, w, h, o) {
  o = o || {};
  var fw = o.frame || 0.035, frame = o.frameMat || solid(PALETTE.whitewash, { grain: 0.03 }), u0 = uc - w / 2, u1 = uc + w / 2, v0 = vc - h / 2, v1 = vc + h / 2, z0 = s.o[2];
  s.slab(u0 - fw, v0 - fw, u1 + fw, v1 + fw, 0.032, frame, { rim: 1 });
  s.quad(u0, v0, u1, v1, windowGlass(z0 + v0, h), { off: 0.036, rim: 0.3, ao: false });
  s.slab(uc - 0.009, v0, uc + 0.009, v1, 0.043, frame, { rim: 0.6 });
  s.slab(u0, vc - 0.009, u1, vc + 0.009, 0.043, frame, { rim: 0.6 });
  s.slab(u0 - fw - 0.03, v0 - fw - 0.035, u1 + fw + 0.03, v0 - fw, 0.075, o.sillMat || frame, { rim: 1 });
  if (o.shutterMat) {
    var sw = w * 0.42;
    s.slab(u0 - fw - sw - 0.01, v0 - fw, u0 - fw - 0.01, v1 + fw, 0.026, o.shutterMat, { rim: 1 });
    s.slab(u1 + fw + 0.01, v0 - fw, u1 + fw + sw + 0.01, v1 + fw, 0.026, o.shutterMat, { rim: 1 });
  }
}
// drzwi: srodek uc, szerokosc w, wysokosc h (od podlogi v0)
function doorOn(P, s, uc, w, h, o) {
  o = o || {};
  var fw = 0.04, frame = o.frameMat || solid(PALETTE.whitewash, { grain: 0.03 }), panel = o.doorMat || material({ texture: stdTex('planks'), size: 0.9, tint: [0.62, 0.5, 0.4], grain: 0.05 });
  var u0 = uc - w / 2, u1 = uc + w / 2, v0 = o.v0 || 0;
  s.slab(u0 - fw, v0, u1 + fw, v0 + h + fw, 0.03, frame, { rim: 1 });
  s.slab(u0, v0, u1, v0 + h, 0.036, panel, { rim: 0.7 });
  s.slab(uc - 0.01, v0 + h * 0.12, uc + 0.01, v0 + h * 0.9, 0.044, solid(PALETTE.darkWood), { rim: 0.4 });
  P.sphere(s.pt(u1 - 0.07, v0 + h * 0.48, 0.05), 0.02, solid([0.7, 0.55, 0.2], { grain: 0, spec: 0.5 }), { shadow: false });
}

var WALL_TINTS = {};
function wallTexture(style, tint) {
  var key = 'wall-' + style + '-' + (tint ? tint.join(',') : '');
  return cached(key, function () {
    var base = tint;
    if (style === 'clapboard') return texClapboard(512, 21, 14, base || [0.70, 0.66, 0.58]);
    if (style === 'adobe') return texAdobe(512, 22, base || [0.95, 0.88, 0.74]);
    if (style === 'planks') return texPlanks(512, 23, 9, base || [0.40, 0.30, 0.20]);
    if (style === 'stone') return texStone(512, 24, 9);
    return texClapboard(512, 21, 14, base);
  });
}
function roofTexture(tone) {
  var base = tone === 'gray' ? [0.34, 0.31, 0.28] : tone === 'brown' ? [0.34, 0.24, 0.16] : tone === 'tile' ? [0.66, 0.30, 0.20] : tone === 'slate' ? [0.26, 0.28, 0.32] : [0.58, 0.27, 0.17];
  return cached('roof-' + tone, function () { return adjustTexture(texShingle(512, tone === 'tile' ? 31 : 32, tone === 'tile' ? 12 : 18, tone === 'tile' ? 8 : 14, base), { contrast: 0.72, saturation: 0.88 }); });
}
// przyciemnienie przy ziemi i pod okapem (malowany cien dachu na scianie)
function wallShading(z0, z1, eave) {
  return function (ctx, out) {
    var g = 0.80 + 0.20 * smoothstep(0, 0.30, ctx.pz - z0), e = 1 - (eave === undefined ? 0.40 : eave) * smoothstep(z1 - 0.26, z1 - 0.02, ctx.pz), k = g * e;
    out[0] *= k; out[1] *= k; out[2] *= k * (e < 1 ? 1.04 : 1);
  };
}

// house(P, { pos, rot, w, d, h, floors, style: 'clapboard'|'adobe'|'planks'|'stone', wallTint, roof: 'gable'|'hip'|'flat'|'shed', roofTone: 'red'|'gray'|'brown'|'tile'|'slate',
//   rise, porch, chimney, door: 'south'|'east', windows, shutters, team, seed })
function house(P, o) {
  o = copyOpts(o, { w: 2.0, d: 1.5, h: 0.95, floors: 1, style: 'clapboard', roof: 'gable', roofTone: 'red', porch: false, chimney: true, door: 'south', shutters: false, team: false });
  var w = o.w, dp = o.d, floors = o.floors, wallH = o.h * floors, base = 0.12, x0 = -w / 2, x1 = w / 2, y0 = -dp / 2, y1 = dp / 2, zt = base + wallH;
  var wallMat = material({ texture: wallTexture(o.style, o.wallTint), size: o.style === 'stone' ? 1.6 : 1.7, grain: 0.04, name: 'wall' });
  var roofMat = material({ texture: roofTexture(o.roofTone), size: 1.5, grain: 0.05, name: 'roof' }), edgeMat = solid(o.style === 'adobe' ? [0.55, 0.26, 0.18] : PALETTE.darkWood, { grain: 0.05 });
  var stone = material({ texture: stdTex('stone'), size: 1.4, tint: [0.92, 0.9, 0.86], name: 'stone' }), trim = solid(o.style === 'adobe' ? [0.62, 0.36, 0.22] : PALETTE.whitewash, { grain: 0.03 });
  var team = material({ color: [0.62, 0.22, 0.20], team: true, grain: 0.05, name: 'team' }), shutterMat = o.team ? team : solid([0.20, 0.34, 0.24], { grain: 0.05 });
  var rise = o.rise || Math.min(w, dp) * 0.36;
  P.at(o.pos || [0, 0, 0], o.rot || 0, function () {
    P.castShadow([[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0], [x0, y0, zt], [x1, y0, zt], [x1, y1, zt], [x0, y1, zt]]);
    P.box([0, 0, base / 2], [w + 0.08, dp + 0.08, base], stone, { shadow: false, rim: 1 });
    var walls = [[[x0, y0], [x1, y0]], [[x1, y0], [x1, y1]], [[x1, y1], [x0, y1]], [[x0, y1], [x0, y0]]], surfaces = [];
    walls.forEach(function (ab) { surfaces.push(P.wall(ab[0], ab[1], base, zt, wallMat, { post: wallShading(base, zt, o.roof === 'flat' ? 0.15 : 0.40) })); });
    // slupki narozne
    [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].forEach(function (c) { P.box([c[0], c[1], base + (wallH - 0.09) / 2], [0.07, 0.07, wallH - 0.09], trim, { shadow: false, rim: 1 }); });
    if (floors > 1) walls.forEach(function (ab, i) { surfaces[i].slab(-0.03, o.h - 0.03, surfaces[i].uLen + 0.03, o.h + 0.03, 0.03, trim, { rim: 1 }); });
    // okna i drzwi
    var doorWall = o.door === 'east' ? 1 : 0, rngW = makeRng((o.seed || 1) * 3 + 2);
    [0, 1, 2, 3].forEach(function (wi) {
      var s = surfaces[wi], len = s.uLen, count = Math.max(1, Math.round(len / 0.68)), step = len / count;
      for (var f = 0; f < floors; f++) for (var k = 0; k < count; k++) {
        var uc = (k + 0.5) * step, isDoor = wi === doorWall && f === 0 && k === Math.floor(count / 2);
        if (isDoor) { doorOn(P, s, uc, 0.34, 0.62, { frameMat: trim }); continue; }
        if (o.windows === false) continue;
        windowOn(P, s, uc, f * o.h + o.h * 0.56, 0.22, 0.30, { frameMat: trim, shutterMat: o.shutters || o.team ? shutterMat : null });
      }
    });
    // dach
    if (o.roof === 'flat') {
      P.box([0, 0, zt + 0.03], [w + 0.1, dp + 0.1, 0.06], solid([0.62, 0.55, 0.44], { grain: 0.05 }), { shadow: false });
      var pw = 0.07, ph = 0.2;
      [[0, y0 - 0.02, w + 0.14, pw], [0, y1 + 0.02, w + 0.14, pw]].forEach(function (p) { P.box([p[0], p[1], zt + ph / 2 + 0.03], [p[2], p[3], ph], wallMat, { shadow: false, rim: 1 }); });
      [[x0 - 0.02, 0, pw, dp + 0.14], [x1 + 0.02, 0, pw, dp + 0.14]].forEach(function (p) { P.box([p[0], p[1], zt + ph / 2 + 0.03], [p[2], p[3], ph], wallMat, { shadow: false, rim: 1 }); });
    } else {
      P.roof({ x0: x0, y0: y0, x1: x1, y1: y1, z: zt, rise: rise, overhang: o.overhang === undefined ? 0.14 : o.overhang, type: o.roof, ridge: w >= dp ? 'x' : 'y', mat: roofMat, gableMat: wallMat, edgeMat: edgeMat, shadow: false });
    }
    if (o.chimney && o.roof !== 'flat') {
      var cx = o.chimneyAt ? o.chimneyAt[0] : x1 - 0.42, cy = o.chimneyAt ? o.chimneyAt[1] : (w >= dp ? 0.1 : y1 - 0.4), brick = material({ texture: stdTex('stone'), size: 0.7, tint: [1.0, 0.72, 0.62], name: 'brick' });
      var chH = rise + 0.5;
      P.box([cx, cy, zt + chH / 2 - 0.05], [0.2, 0.2, chH], brick, { shadow: true, rim: 1 });
      P.box([cx, cy, zt + chH - 0.05 + 0.03], [0.26, 0.26, 0.06], brick, { shadow: false, rim: 1 });
    }
    if (o.porch) {
      var pd = 0.46, s0 = surfaces[0], px0 = x0 + 0.12, px1 = x1 - 0.12;
      P.box([(px0 + px1) / 2, y0 - pd / 2, base + 0.03], [px1 - px0, pd, 0.06], material({ texture: stdTex('planks'), size: 1.0, name: 'deck' }), { shadow: true, rim: 1 });
      [[px0 + 0.04, y0 - pd + 0.04], [px1 - 0.04, y0 - pd + 0.04], [(px0 + px1) / 2, y0 - pd + 0.04]].forEach(function (p) { P.rod([p[0], p[1], base + 0.06], [p[0], p[1], base + o.h * 0.88 - 0.03], 0.028, trim, { shadow: true }); });
      P.roof({ x0: px0 - 0.04, y0: y0 - pd, x1: px1 + 0.04, y1: y0, z: base + o.h * 0.88, rise: 0.16, overhang: 0.06, type: 'shed', ridge: 'x', mat: roofMat, edgeMat: edgeMat, shadow: true });
      P.rod([px0 + 0.04, y0 - pd + 0.04, base + 0.30], [px1 - 0.04, y0 - pd + 0.04, base + 0.30], 0.02, trim, { shadow: false });
      for (var b = 0; b <= 9; b++) { var bx = px0 + 0.04 + (px1 - px0 - 0.08) * b / 9; P.rod([bx, y0 - pd + 0.04, base + 0.06], [bx, y0 - pd + 0.04, base + 0.30], 0.011, trim, { shadow: false }); }
    }
  });
}

// tower(P, { pos, radius, height, roofTone, team }) -> okragla wieza z kamienia ze stozkowym dachem
function tower(P, o) {
  o = copyOpts(o, { radius: 0.5, height: 1.9, roofTone: 'slate', team: false });
  var stone = material({ texture: cached('stone-hi', function () { return adjustTexture(stdTex('stone'), { contrast: 1.35, brightness: 1.12 }); }), size: 1.1, tint: [0.98, 0.95, 0.92], name: 'stone' }), roofMat = material({ texture: roofTexture(o.roofTone), size: 1.2, name: 'roof' }), dark = solid([0.04, 0.035, 0.03], { grain: 0 });
  var team = material({ color: [0.62, 0.22, 0.20], team: true, grain: 0.05 }), r = o.radius, H = o.height;
  P.at(o.pos || [0, 0, 0], o.rot || 0, function () {
    P.frustum([0, 0, 0], [0, 0, H], r * 1.08, r * 0.92, stone, { caps: false });
    P.frustum([0, 0, H - 0.02], [0, 0, H + 0.1], r * 1.12, r * 1.12, stone, { caps: false });
    P.frustum([0, 0, H + 0.08], [0, 0, H + o.height * 0.55], r * 1.2, 0.03, roofMat, { caps: false });
    [[0, -1, 0.62], [1, 0, 0.78]].forEach(function (d) { P.ellipsoid([d[0] * r * 0.92, d[1] * r * 0.92, H * d[2]], [0.035, 0.035, 0.12], dark, { shadow: false, rim: 0 }); });
    P.ellipsoid([r * 0.62, -r * 0.78, 0.3], [0.13, 0.13, 0.26], dark, { shadow: false });
    if (o.team) { P.rod([0, 0, H + o.height * 0.55], [0, 0, H + o.height * 0.55 + 0.4], 0.012, solid(PALETTE.darkWood), { shadow: false }); P.card([0, 0, H + o.height * 0.55 + 0.2], [[0, 0], [0.26, 0.04], [0.28, 0.12], [0, 0.16]], team, { rim: 0, ao: false, shadow: false }); }
  });
}

function barrel(P, pos, o) {
  o = o || {};
  var wood = material({ texture: stdTex('planks'), size: 0.5, tint: o.tint || [1.35, 1.2, 1.05], grain: 0.05, name: 'barrel' }), iron = solid(PALETTE.iron, { grain: 0.04, spec: 0.3 }), s = o.scale || 1;
  P.at([pos[0], pos[1], 0], o.rot || 0, function () {
    P.frustum([0, 0, 0], [0, 0, 0.2 * s], 0.15 * s, 0.19 * s, wood, { caps: false });
    P.frustum([0, 0, 0.2 * s], [0, 0, 0.4 * s], 0.19 * s, 0.15 * s, wood, { caps: true });
    [0.06, 0.2, 0.34].forEach(function (z) { var r = (0.15 + 0.04 * (1 - Math.abs(z / s - 0.2) / 0.2)) * s + 0.006; P.frustum([0, 0, (z - 0.012) * s], [0, 0, (z + 0.012) * s], r, r, iron, { caps: false, shadow: false }); });
  });
}
function crate(P, pos, o) {
  o = o || {};
  var s = o.size || 0.34, wood = material({ texture: stdTex('planks'), size: 0.6, tint: [1.4, 1.25, 1.1], grain: 0.05, name: 'crate' }), brace = solid(PALETTE.darkWood, { grain: 0.05 });
  P.at([pos[0], pos[1], 0], o.rot || 0, function () {
    P.box([0, 0, s / 2], [s, s, s], wood, { shadow: true, rim: 1 });
    [[s / 2, 0], [-s / 2, 0], [0, s / 2], [0, -s / 2]].forEach(function (c) { var vert = c[0] !== 0; P.box([c[0] * 1.0, c[1] * 1.0, s / 2], vert ? [0.012, s * 0.08 + 0.012, s * 1.002] : [s * 0.08 + 0.012, 0.012, s * 1.002], brace, { shadow: false }); });
    P.box([0, 0, s + 0.005], [s * 1.02, s * 1.02, 0.014], brace, { shadow: false });
  });
}
// plot z palikow i dwoch poprzeczek od a do b; gap: odstep palikow
function fence(P, a, b, o) {
  o = o || {};
  var len = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(len / (o.gap || 0.4))), hgt = o.height || 0.34, wood = material({ texture: stdTex('planks'), size: 0.5, tint: [1.3, 1.2, 1.1], name: 'fence' });
  for (var i = 0; i <= n; i++) {
    var t = i / n, x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t;
    P.box([x, y, hgt / 2], [0.045, 0.045, hgt], wood, { shadow: true, rim: 1 });
  }
  [0.62, 0.3].forEach(function (f) { P.rod([a[0], a[1], hgt * f], [b[0], b[1], hgt * f], 0.016, wood, { shadow: true }); });
}
// kolo wozu w pionowej plaszczyznie obroconej o yaw (stopnie)
function wagonWheel(P, center, radius, yaw) {
  var wood = solid(PALETTE.wood, { grain: 0.05 }), iron = solid(PALETTE.iron, { grain: 0.03 }), a = (yaw || 0) * Math.PI / 180, dx = Math.cos(a), dy = Math.sin(a), n = 16;
  function pt(ang, r) { return [center[0] + dx * Math.cos(ang) * r, center[1] + dy * Math.cos(ang) * r, center[2] + Math.sin(ang) * r]; }
  for (var i = 0; i < n; i++) { P.rod(pt(2 * Math.PI * i / n, radius * 0.1), pt(2 * Math.PI * i / n, radius * 0.95), 0.014, wood, { shadow: i % 2 === 0 }); P.rod(pt(2 * Math.PI * i / n, radius), pt(2 * Math.PI * (i + 1) / n, radius), 0.02, iron, { shadow: false }); }
  P.sphere(center, radius * 0.12, wood, { shadow: false });
}

// namiot / tipi: stozek ze skory z malowanym pasem (team = pas w kolorze druzyny), tyczki na szczycie
function tent(P, pos, o) {
  o = copyOpts(o, { height: 1.7, radius: 0.8, team: true, door: -50 });
  var hide = [0.80, 0.68, 0.48], dark = [0.17, 0.12, 0.09], bandCol = [0.18, 0.28, 0.58];
  var doorRad = o.door * Math.PI / 180, teamMat = material({ color: [0.62, 0.22, 0.20], team: true, grain: 0.05 });
  var m = material({ name: 'tipi', shader: function (ctx, out) {
    var ang = Math.atan2(ctx.ly, ctx.lx), da = Math.atan2(Math.sin(ang - doorRad), Math.cos(ang - doorRad)), col = hide.slice(), isTeam = false;
    var n = fbm3(ctx.px * 6, ctx.py * 6, ctx.pz * 6, 3, 2); col = [col[0] * (0.88 + 0.2 * n), col[1] * (0.88 + 0.2 * n), col[2] * (0.88 + 0.2 * n)];
    var zig = 0.035 + 0.03 * Math.abs(Math.sin(ang * 6)), band = ctx.s > 0.14 && ctx.s < 0.14 + zig * 2 ? 1 : 0;
    if (ctx.s > 0.14 + 0.10 && ctx.s < 0.14 + 0.10 + 0.02) col = [0.3, 0.2, 0.12];
    if (band) col = o.team ? [0.58, 0.22, 0.2] : bandCol;
    if (Math.abs(da) < 0.30 * (1 - ctx.s * 1.4) && ctx.s < 0.5) col = dark;
    ctx.P.lit(ctx, col, out, null); out[3] = 1;
    if (band && o.team) out[4] = 1;
  } });
  P.at([pos[0], pos[1], 0], o.rot || 0, function () {
    var H = o.height, r = o.radius;
    P.frustum([0, 0, 0], [0, 0, H], r, 0.05, m, { caps: false });
    for (var i = 0; i < 8; i++) { var a = i * Math.PI / 4; P.rod([Math.cos(a) * 0.03, Math.sin(a) * 0.03, H - 0.05], [Math.cos(a) * 0.14, Math.sin(a) * 0.14, H + 0.5], 0.012, solid(PALETTE.wood), { shadow: false }); }
  });
}
function haystack(P, pos, o) {
  o = o || {};
  var s = o.size || 0.42, straw = material({ texture: stdTex('thatch'), size: 0.7, tint: [1.12, 1.0, 0.72], grain: 0.05, name: 'straw' });
  P.at([pos[0], pos[1], 0], o.rot || 0, function () {
    P.frustum([0, 0, 0], [0, 0, s * 0.55], s * 0.92, s * 0.86, straw, { caps: false, aoHeight: 0.3 });
    P.ellipsoid([0, 0, s * 0.55], [s * 0.86, s * 0.86, s * 0.62], straw, { aoHeight: 0.3 });
  });
}
function well(P, pos, o) {
  o = o || {};
  var stone = material({ texture: stdTex('stone'), size: 0.8, name: 'stone' }), wood = solid(PALETTE.wood, { grain: 0.05 }), water = solid([0.07, 0.12, 0.16], { grain: 0 }), roofM = material({ texture: roofTexture('brown'), size: 1.0 });
  P.at([pos[0], pos[1], 0], o.rot || 0, function () {
    P.frustum([0, 0, 0], [0, 0, 0.34], 0.30, 0.27, stone, { capMat: water });
    P.rod([-0.26, 0, 0.3], [-0.26, 0, 0.95], 0.028, wood, {}); P.rod([0.26, 0, 0.3], [0.26, 0, 0.95], 0.028, wood, {}); P.rod([-0.26, 0, 0.82], [0.26, 0, 0.82], 0.022, wood, { shadow: false });
    P.roof({ x0: -0.34, y0: -0.2, x1: 0.34, y1: 0.2, z: 0.95, rise: 0.2, overhang: 0.05, type: 'gable', ridge: 'x', mat: roofM, edgeMat: wood, gableMat: null, shadow: true });
  });
}
function sign(P, pos, o) {
  o = copyOpts(o, { rot: 0 });
  var wood = solid(PALETTE.wood, { grain: 0.06 }), board = material({ texture: stdTex('planks'), size: 0.5, tint: [1.3, 1.15, 1.0] }), ink = solid([0.12, 0.08, 0.05], { grain: 0 });
  P.at([pos[0], pos[1], 0], o.rot, function () {
    P.rod([0, 0, 0], [0, 0, 0.8], 0.025, wood, {});
    P.box([0, 0, 0.66], [0.5, 0.05, 0.22], board, { rim: 1 });
    var s = P.wall([-0.22, -0.03], [0.22, -0.03], 0.56, 0.76, null);
    for (var i = 0; i < 3; i++) s.quad(0.05 + i * 0.12, 0.08 + (i % 2) * 0.02, 0.05 + i * 0.12 + 0.09, 0.11 + (i % 2) * 0.02, ink, { off: 0.0, rim: 0 });
  });
}
function campfire(P, pos, o) {
  o = o || {};
  var log = solid([0.24, 0.15, 0.08], { grain: 0.08 }), stone = rockMaterial('grey', 4), rng = makeRng((o.seed || 1) + 5);
  var flame = material({ name: 'flame', shader: function (ctx, out) { var t = clamp(ctx.lz / 0.26, 0, 1), col = ramp([[1.0, 0.95, 0.6], [1.0, 0.65, 0.12], [0.85, 0.22, 0.05]], t); out[0] = col[0]; out[1] = col[1]; out[2] = col[2]; out[3] = 1 - smoothstep(0.7, 1.0, t) * 0.0; } });
  P.at([pos[0], pos[1], 0], 0, function () {
    for (var i = 0; i < 8; i++) { var a = i * Math.PI / 4; P.ellipsoid([Math.cos(a) * 0.22, Math.sin(a) * 0.22, 0.04], [0.06, 0.05, 0.04], stone, { yaw: a * 57, shadow: false }); }
    for (var j = 0; j < 4; j++) { var b = j * Math.PI / 2 + 0.4; P.rod([Math.cos(b) * 0.16, Math.sin(b) * 0.16, 0.03], [-Math.cos(b) * 0.04, -Math.sin(b) * 0.04, 0.11], 0.03, log, { shadow: false }); }
    P.contactShadow([0, 0], 0.30, 0.22);
    [[0, 0, 0.26], [0.05, 0.02, 0.19], [-0.05, -0.03, 0.2]].forEach(function (f) { P.card([f[0], f[1], 0.06], [[-0.07, 0], [0.07, 0], [0.03, f[2] * 0.7], [0.0, f[2]]], flame, { rim: 0, ao: false, shadow: false }); });
  });
}

// ===== 08_export.js =====
// ---------------------------------------------------------------- PNG (bez kompresji), zapis sprite'ow i arkuszy, sceny, walidacja

var CRC_TABLE = (function () {
  var t = new Uint32Array(256);
  for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1); t[n] = c >>> 0; }
  return t;
})();
function crc32(bytes, start, end) {
  var c = 0xFFFFFFFF;
  for (var i = start; i < end; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function adler32(bytes) {
  var a = 1, b = 0;
  for (var i = 0; i < bytes.length; i++) { a = (a + bytes[i]) % 65521; b = (b + a) % 65521; }
  return ((b << 16) | a) >>> 0;
}
function putU32(arr, offset, v) { arr[offset] = (v >>> 24) & 255; arr[offset + 1] = (v >>> 16) & 255; arr[offset + 2] = (v >>> 8) & 255; arr[offset + 3] = v & 255; }

// ---- deflate: LZ77 (lancuchy hashy) + staly kod Huffmana (BTYPE=01); poprawny strumien zlib, ~3-5x mniejsze pliki niz "stored"
var LEN_BASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258];
var LEN_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
var DIST_BASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
var DIST_EXTRA = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];
function reverseBits(code, n) { var r = 0; for (var i = 0; i < n; i++) { r = (r << 1) | (code & 1); code >>= 1; } return r; }
var FIXED = (function () {   // kody stalego Huffmana dla symboli 0..287: [kod odwrocony, dlugosc]
  var codes = new Int32Array(288), lens = new Uint8Array(288);
  for (var sym = 0; sym < 288; sym++) {
    var code, len;
    if (sym < 144) { code = 0x30 + sym; len = 8; } else if (sym < 256) { code = 0x190 + sym - 144; len = 9; } else if (sym < 280) { code = sym - 256; len = 7; } else { code = 0xC0 + sym - 280; len = 8; }
    codes[sym] = reverseBits(code, len); lens[sym] = len;
  }
  return { codes: codes, lens: lens };
})();
function lengthSymbol(length) { var i = 28; while (LEN_BASE[i] > length) i--; return i; }
function distSymbol(dist) { var i = 29; while (DIST_BASE[i] > dist) i--; return i; }
function deflateFixed(raw) {
  var n = raw.length, out = new Uint8Array(Math.ceil(n * 1.2) + 64), op = 0, bitBuf = 0, bitCnt = 0;
  function put(value, count) { bitBuf |= value << bitCnt; bitCnt += count; while (bitCnt >= 8) { out[op++] = bitBuf & 255; bitBuf >>>= 8; bitCnt -= 8; } }
  put(1, 1); put(1, 2);                                  // BFINAL=1, BTYPE=01 (staly Huffman)
  var head = new Int32Array(32768).fill(-1), prev = new Int32Array(n), i = 0, MAXCHAIN = 40;
  function insert(pos) { if (pos + 2 < n) { var h = ((raw[pos] << 10) ^ (raw[pos + 1] << 5) ^ raw[pos + 2]) & 32767; prev[pos] = head[h]; head[h] = pos; } }
  while (i < n) {
    var bestLen = 0, bestDist = 0;
    if (i + 2 < n) {
      var h = ((raw[i] << 10) ^ (raw[i + 1] << 5) ^ raw[i + 2]) & 32767, cand = head[h], chain = 0, maxLen = Math.min(258, n - i);
      while (cand >= 0 && i - cand <= 32768 && chain++ < MAXCHAIN) {
        var l = 0; while (l < maxLen && raw[cand + l] === raw[i + l]) l++;
        if (l > bestLen) { bestLen = l; bestDist = i - cand; if (l === maxLen) break; }
        cand = prev[cand];
      }
    }
    if (bestLen >= 3) {
      var ls = lengthSymbol(bestLen), ds = distSymbol(bestDist);
      put(FIXED.codes[257 + ls], FIXED.lens[257 + ls]); if (LEN_EXTRA[ls]) put(bestLen - LEN_BASE[ls], LEN_EXTRA[ls]);
      put(reverseBits(ds, 5), 5); if (DIST_EXTRA[ds]) put(bestDist - DIST_BASE[ds], DIST_EXTRA[ds]);
      for (var k = 0; k < bestLen; k++) insert(i + k);
      i += bestLen;
    } else { put(FIXED.codes[raw[i]], FIXED.lens[raw[i]]); insert(i); i++; }
  }
  put(FIXED.codes[256], FIXED.lens[256]);
  if (bitCnt > 0) out[op++] = bitBuf & 255;
  return out.subarray(0, op);
}
function filterRows(data, w, h, ch) {   // filtr PNG wybierany per wiersz (None/Sub/Up/Average/Paeth) wg najmniejszej sumy |bajt|
  var stride = w * ch, out = new Uint8Array((stride + 1) * h), cand = [0, 1, 2, 3, 4].map(function () { return new Uint8Array(stride); });
  for (var y = 0; y < h; y++) {
    var row = y * stride;
    for (var x = 0; x < stride; x++) {
      var a = x >= ch ? data[row + x - ch] : 0, b = y > 0 ? data[row - stride + x] : 0, c = (x >= ch && y > 0) ? data[row - stride + x - ch] : 0, cur = data[row + x];
      var pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c), paeth = (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      cand[0][x] = cur; cand[1][x] = (cur - a) & 255; cand[2][x] = (cur - b) & 255; cand[3][x] = (cur - ((a + b) >> 1)) & 255; cand[4][x] = (cur - paeth) & 255;
    }
    var best = 0, bestScore = Infinity;
    for (var f = 0; f < 5; f++) { var score = 0, arr = cand[f]; for (var q = 0; q < stride; q++) score += arr[q] < 128 ? arr[q] : 256 - arr[q]; if (score < bestScore) { bestScore = score; best = f; } }
    out[y * (stride + 1)] = best; out.set(cand[best], y * (stride + 1) + 1);
  }
  return out;
}
// encodePng(image, { compress = true }) -> Uint8Array; image = { width, height, channels: 1|3|4, data }
// compress:false = deflate "stored" (bez kompresji, szybciej, ale ~5x wieksze pliki). Dalsza optymalizacja: oxipng/pngquant, jesli srodowisko je ma.
function encodePng(image, options) {
  var w = image.width, h = image.height, ch = image.channels, colorType = ch === 1 ? 0 : ch === 3 ? 2 : 6, compress = !(options && options.compress === false);
  var raw, z;
  if (compress) {
    raw = filterRows(image.data, w, h, ch);
    var body = deflateFixed(raw);
    if (body.length < raw.length) { z = new Uint8Array(2 + body.length + 4); z[0] = 0x78; z[1] = 0x9C; z.set(body, 2); putU32(z, 2 + body.length, adler32(raw)); }
    else compress = false;   // dane nieskompresowalne (szum): zapis "stored" jest krotszy
  }
  if (!compress) {
    var stride = w * ch; raw = new Uint8Array((stride + 1) * h);
    for (var y = 0; y < h; y++) { raw[y * (stride + 1)] = 0; raw.set(image.data.subarray(y * stride, (y + 1) * stride), y * (stride + 1) + 1); }
    var blocks = Math.max(1, Math.ceil(raw.length / 65535)), p = 0;
    z = new Uint8Array(2 + raw.length + blocks * 5 + 4); z[p++] = 0x78; z[p++] = 0x01;
    for (var b = 0; b < blocks; b++) {
      var start = b * 65535, len = Math.min(65535, raw.length - start), last = b === blocks - 1 ? 1 : 0;
      z[p++] = last; z[p++] = len & 255; z[p++] = (len >>> 8) & 255; z[p++] = (~len) & 255; z[p++] = ((~len) >>> 8) & 255;
      z.set(raw.subarray(start, start + len), p); p += len;
    }
    putU32(z, p, adler32(raw));
  }
  var parts = [], ihdr = new Uint8Array(13);
  putU32(ihdr, 0, w); putU32(ihdr, 4, h); ihdr[8] = 8; ihdr[9] = colorType; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  function chunk(type, data) {
    var out = new Uint8Array(12 + data.length);
    putU32(out, 0, data.length);
    for (var i = 0; i < 4; i++) out[4 + i] = type.charCodeAt(i);
    out.set(data, 8); putU32(out, 8 + data.length, crc32(out, 4, 8 + data.length));
    return out;
  }
  parts.push(new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', z), chunk('IEND', new Uint8Array(0)));
  var total = 0; parts.forEach(function (x) { total += x.length; });
  var png = new Uint8Array(total), o = 0; parts.forEach(function (x) { png.set(x, o); o += x.length; });
  return png;
}
function toBase64(bytes) {   // do hostow, ktore potrafia tylko wypisac tekst
  var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', out = '';
  for (var i = 0; i < bytes.length; i += 3) {
    var n = (bytes[i] << 16) | ((bytes[i + 1] || 0) << 8) | (bytes[i + 2] || 0);
    out += chars[(n >> 18) & 63] + chars[(n >> 12) & 63] + (i + 1 < bytes.length ? chars[(n >> 6) & 63] : '=') + (i + 2 < bytes.length ? chars[n & 63] : '=');
  }
  return out;
}
function round2(v) { return Math.round(v * 100) / 100; }

// saveSprite(result, name, extraMeta) -> { files: { 'name.png': Uint8Array, ..., 'name.json': string }, meta }
// Nic nie zapisuje na dysk: rdzen jest niezalezny od srodowiska. Zapis: for (k in files) host.write(k, files[k]).
function saveSprite(result, name, extraMeta) {
  var files = {};
  files[name + '.png'] = encodePng(result.sprite); files[name + '_shadow.png'] = encodePng(result.shadow);
  files[name + '_team.png'] = encodePng(result.team); files[name + '_preview.png'] = encodePng(result.preview);
  var meta = { name: name, size: [result.sprite.width, result.sprite.height], anchor: [round2(result.anchor[0]), round2(result.anchor[1])], tile_px: result.tilePx, frame_clipped: !!result.frameClipped,
    light: 'shadow falls to the lower-left of the screen', style: 'painted-2d', team_color: 'see *_team.png mask' };
  for (var k in (extraMeta || {})) meta[k] = extraMeta[k];
  files[name + '.json'] = JSON.stringify(meta, null, 2);
  return { files: files, meta: meta };
}

function checkFrames(frames) {   // kontrola wejscia arkusza; rzuca Error z opisem
  if (!frames || !frames.length) throw new Error('packSheet: pusta lista klatek');
  var w = frames[0].sprite && frames[0].sprite.width, h = frames[0].sprite && frames[0].sprite.height, base = frames[0].anchor;
  frames.forEach(function (f, index) {
    if (!f.sprite || !f.shadow || !f.team || !f.anchor || !f.tilePx) throw new Error('packSheet: klatka ' + index + ' nie jest wynikiem renderSprite');
    if (f.sprite.width !== w || f.sprite.height !== h) throw new Error('packSheet: klatka ' + index + ' ma inny rozmiar (' + f.sprite.width + 'x' + f.sprite.height + ' zamiast ' + w + 'x' + h + '); renderuj z trim:false i tymi samymi parametrami sprite()');
    if (f.shadow.width !== w || f.shadow.height !== h || f.team.width !== w || f.team.height !== h) throw new Error('packSheet: warstwy klatki ' + index + ' (sprite/shadow/team) maja rozne wymiary');
    var any = false;
    for (var i = 0; i < w * h && !any; i++) if (Math.max(f.sprite.data[i * 4 + 3], f.shadow.data[i * 4 + 3]) > 6) any = true;
    if (!any) throw new Error('packSheet: klatka ' + index + ' jest pusta (brak pikseli sprite\'a i cienia); sprawdz, czy obiekt miesci sie w kadrze (width, height, anchor)');
    if (Math.abs(f.anchor[0] - base[0]) > 0.5 || Math.abs(f.anchor[1] - base[1]) > 0.5) throw new Error('packSheet: klatka ' + index + ' ma inna kotwice niz klatka 0; uzyj tych samych parametrow sprite() (width, height, anchor) i trim:false');
  });
}
function unionBbox(frames, margin) {
  var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, w = frames[0].sprite.width, h = frames[0].sprite.height;
  frames.forEach(function (f) {
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
      var i = (y * w + x) * 4 + 3;
      if (Math.max(f.sprite.data[i], f.shadow.data[i]) > 6) { if (x < x0) x0 = x; if (x + 1 > x1) x1 = x + 1; if (y < y0) y0 = y; if (y + 1 > y1) y1 = y + 1; }
    }
  });
  return [Math.max(x0 - margin, 0), Math.max(y0 - margin, 0), Math.min(x1 + margin, w), Math.min(y1 + margin, h)];
}
// packSheet(frames, { columns, padding }) -> { rgba, keyed, shadow, team, meta }; klatki z trim:false
function packSheet(frames, options) {
  options = options || {};
  checkFrames(frames);
  var padding = options.padding === undefined ? 1 : options.padding, columns = options.columns || frames.length, rows = Math.ceil(frames.length / columns);
  var box = unionBbox(frames, 2), x0 = box[0], y0 = box[1], fw = box[2] - box[0], fh = box[3] - box[1];
  var sw = columns * (fw + padding), sh = rows * (fh + padding), rgba = makeImage(sw, sh, 4), shadow = makeImage(sw, sh, 4), team = makeImage(sw, sh, 1), entries = [];
  frames.forEach(function (f, index) {
    var cx = (index % columns) * (fw + padding), cy = Math.floor(index / columns) * (fh + padding);
    for (var y = 0; y < fh; y++) for (var x = 0; x < fw; x++) {
      var src = (y + y0) * f.sprite.width + x + x0, dst = (cy + y) * sw + cx + x;
      for (var c = 0; c < 4; c++) { rgba.data[dst * 4 + c] = f.sprite.data[src * 4 + c]; shadow.data[dst * 4 + c] = f.shadow.data[src * 4 + c]; }
      team.data[dst] = f.team.data[src];
    }
    entries.push({ index: index, x: cx, y: cy, view_angle_deg: f.viewAngleDeg || 0 });
  });
  var keyed = makeImage(sw, sh, 3);
  for (var i = 0; i < sw * sh; i++) {
    var solid = rgba.data[i * 4 + 3] > 127;
    keyed.data[i * 3] = solid ? rgba.data[i * 4] : 255; keyed.data[i * 3 + 1] = solid ? rgba.data[i * 4 + 1] : 0; keyed.data[i * 3 + 2] = solid ? rgba.data[i * 4 + 2] : 255;
  }
  var meta = { frame_size: [fw, fh], columns: columns, rows: rows, padding: padding, anchor: [round2(frames[0].anchor[0] - x0), round2(frames[0].anchor[1] - y0)],
    tile_px: frames[0].tilePx, key_color: [255, 0, 255], frames: entries };
  return { rgba: rgba, keyed: keyed, shadow: shadow, team: team, meta: meta };
}
function saveSheet(sheet, name) {
  var files = {};
  files[name + '_sheet.png'] = encodePng(sheet.rgba); files[name + '_sheet_magenta.png'] = encodePng(sheet.keyed);
  files[name + '_sheet_shadow.png'] = encodePng(sheet.shadow); files[name + '_sheet_team.png'] = encodePng(sheet.team);
  var meta = {}; for (var k in sheet.meta) meta[k] = sheet.meta[k]; meta.name = name;
  files[name + '_sheet.json'] = JSON.stringify(meta, null, 2);
  return { files: files, meta: meta };
}

// ---- sceny (rzut jak w Painter: sx = (x+y)*T/2, sy = (x-y)*T/4)
// groundLayer(width, height, originPx, tilePx, texture, { gain, tileWorld }) -> { width, height, data: Float32Array RGB 0..1 }; tekstura przyklejona do swiata
function groundLayer(width, height, originPx, tilePx, texture, options) {
  options = options || {};
  var gain = options.gain || [1, 1, 1], tile = options.tileWorld || 3.0, data = new Float32Array(width * height * 3), px = [0, 0, 0];
  for (var y = 0; y < height; y++) for (var x = 0; x < width; x++) {
    var sx = x + 0.5 - originPx[0], sy = y + 0.5 - originPx[1], wx = sx / tilePx + 2 * sy / tilePx, wy = sx / tilePx - 2 * sy / tilePx;
    sampleTex(texture, wx / tile, wy / tile, px);
    for (var c = 0; c < 3; c++) data[(y * width + x) * 3 + c] = clamp(px[c] * gain[c], 0, 1);
  }
  return { width: width, height: height, data: data };
}
// groundMix(width, height, originPx, tilePx, texA, texB, { seed, scale, bias, softness, gain, tileWorld }) -> jak groundLayer, ale teren to plamy texB na tle texA (maska: szum w przestrzeni swiata)
function groundMix(width, height, originPx, tilePx, texA, texB, options) {
  options = options || {};
  var tile = options.tileWorld || 3.0, scale = options.scale || 9, bias = options.bias === undefined ? 0 : options.bias, soft = options.softness === undefined ? 0.22 : options.softness, gain = options.gain || [1, 1, 1];
  var mask = fbm(128, (options.seed || 1) * 5 + 2, [10, 22, 40]), data = new Float32Array(width * height * 3), pa = [0, 0, 0], pb = [0, 0, 0];
  for (var y = 0; y < height; y++) for (var x = 0; x < width; x++) {
    var sx = x + 0.5 - originPx[0], sy = y + 0.5 - originPx[1], wx = sx / tilePx + 2 * sy / tilePx, wy = sx / tilePx - 2 * sy / tilePx;
    sampleTex(texA, wx / tile, wy / tile, pa); sampleTex(texB, wx / tile, wy / tile, pb);
    var mu = ((wx / scale) % 1 + 1) % 1 * 128 - 0.5, mv = ((wy / scale) % 1 + 1) % 1 * 128 - 0.5, mx0 = Math.floor(mu), my0 = Math.floor(mv), fx = mu - mx0, fy = mv - my0;
    var ia = ((mx0 % 128) + 128) % 128, ib = (ia + 1) % 128, ja = ((my0 % 128) + 128) % 128, jb = (ja + 1) % 128;
    var m = (mask[ja * 128 + ia] * (1 - fx) + mask[ja * 128 + ib] * fx) * (1 - fy) + (mask[jb * 128 + ia] * (1 - fx) + mask[jb * 128 + ib] * fx) * fy;
    var w = smoothstep(-soft, soft, m - bias);
    for (var c = 0; c < 3; c++) data[(y * width + x) * 3 + c] = clamp((pa[c] * (1 - w) + pb[c] * w) * gain[c], 0, 1);
  }
  return { width: width, height: height, data: data };
}
// groundTile(texture, i, j, { tilePx, tileWorld }) -> obraz RGBA rombu tilePx x tilePx/2 dla kafla (i, j); bezszwowy, bo tekstura przyklejona do swiata
function groundTile(texture, i, j, options) {
  options = options || {};
  var T = options.tilePx || TILE_PX, H = T / 2, tile = options.tileWorld || 3.0, img = makeImage(T, H, 4), px = [0, 0, 0], sub = 4;
  for (var y = 0; y < H; y++) for (var x = 0; x < T; x++) {
    var cover = 0, acc = [0, 0, 0];
    for (var a = 0; a < sub; a++) for (var b = 0; b < sub; b++) {
      var sx = x + (a + 0.5) / sub - T / 2, sy = y + (b + 0.5) / sub - H / 2;
      if (Math.abs(sx) / (T / 2) + Math.abs(sy) / (H / 2) > 1) continue;
      var wx = i + 0.5 + sx / T + 2 * sy / T, wy = j + 0.5 + sx / T - 2 * sy / T;
      sampleTex(texture, wx / tile, wy / tile, px); cover++; acc[0] += px[0]; acc[1] += px[1]; acc[2] += px[2];
    }
    if (cover) for (var c = 0; c < 3; c++) img.data[(y * T + x) * 4 + c] = to8(acc[c] / cover);
    img.data[(y * T + x) * 4 + 3] = Math.round(255 * cover / (sub * sub));
  }
  return img;
}
// composeScene(items, width, height, originPx, ground, tilePx) -> Image RGB; items: [{ res, x, y }] (x, y w kaflach); res = wynik render()
function composeScene(items, width, height, originPx, ground, tilePx) {
  tilePx = tilePx || TILE_PX;
  var canvas = new Float32Array(ground.data), placed = [];
  items.forEach(function (item) {
    var px = originPx[0] + isoX(item.x, item.y, tilePx), py = originPx[1] + isoY(item.x, item.y, 0, tilePx);
    placed.push({ order: item.x - item.y, left: px - item.res.anchor[0], top: py - item.res.anchor[1], res: item.res });
  });
  placed.sort(function (a, b) { return a.order - b.order; });
  function blend(img, left, top, shadowOnly) {
    var x0 = Math.round(left), y0 = Math.round(top);
    for (var y = 0; y < img.height; y++) {
      var cy = y0 + y; if (cy < 0 || cy >= height) continue;
      for (var x = 0; x < img.width; x++) {
        var cx = x0 + x; if (cx < 0 || cx >= width) continue;
        var s = (y * img.width + x) * 4, a = img.data[s + 3] / 255, d = (cy * width + cx) * 3;
        if (a === 0) continue;
        for (var c = 0; c < 3; c++) canvas[d + c] = shadowOnly ? canvas[d + c] * (1 - a) : canvas[d + c] * (1 - a) + img.data[s + c] / 255 * a;
      }
    }
  }
  placed.forEach(function (p) { blend(p.res.shadow, p.left, p.top, true); });
  placed.forEach(function (p) { blend(p.res.sprite, p.left, p.top, false); });
  var out = makeImage(width, height, 3);
  for (var i = 0; i < canvas.length; i++) out.data[i] = Math.floor(Math.min(1, Math.max(0, canvas[i])) * 255 + 0.5);
  return out;
}

// ---- kontrola jakosci (te same progi co validate.py)
function validateSprite(result, options) {
  options = options || {};
  var expectTeam = options.expectTeam !== false, kind = options.kind || 'building', shadowSide = options.shadowSide || 'left', findings = [];
  var TH = { building: { colors: 200, dark: 0.18, std: 0.08, soft: 0.18, team: 0.25, black: 0.08 }, foliage: { colors: 120, dark: 0.14, std: 0.06, soft: 0.22, team: 0.25, black: 0.10 }, unit: { colors: 60, dark: 0.14, std: 0.06, soft: 0.40, team: 0.40, black: 0.10 }, prop: { colors: 40, dark: 0.12, std: 0.05, soft: 0.55, team: 0.30, black: 0.16 } }[kind] || { colors: 200, dark: 0.18, std: 0.08, soft: 0.18, team: 0.25, black: 0.08 };   // shadowSide: 'left' | 'right' | 'any'
  function add(level, text) { findings.push([level, text]); }
  var sp = result.sprite, w = sp.width, h = sp.height, n = w * h, alpha = new Float32Array(n), opaqueCount = 0;
  for (var i = 0; i < n; i++) { alpha[i] = sp.data[i * 4 + 3] / 255; if (alpha[i] > 0.9) opaqueCount++; }
  if (!opaqueCount) { add('ERR', 'pusty sprite (brak pikseli o alfa > 0.9)'); return findings; }
  if (result.frameClipped) add('ERR', 'obiekt lub cien dotyka krawedzi kadru - uciety, zwieksz width/height lub przesun anchor (przy trim:true ta flaga zastepuje test krawedzi)');
  var borderMax = 0;
  for (var x = 0; x < w; x++) borderMax = Math.max(borderMax, alpha[x], alpha[(h - 1) * w + x]);
  for (var y = 0; y < h; y++) borderMax = Math.max(borderMax, alpha[y * w], alpha[y * w + w - 1]);
  if (borderMax > 0.05) add('ERR', 'sprite dotyka krawedzi kadru - obiekt uciety, zwieksz width/height lub przesun anchor');
  var seen = {}, colors = 0, lumaSum = 0, lumaSq = 0, dark = 0, soft = 0, visible = 0, minX = w, maxX = -1;
  for (var j = 0; j < n; j++) {
    if (alpha[j] > 0.02) { visible++; if (alpha[j] < 0.9) soft++; }
    if (alpha[j] <= 0.9) continue;
    var r = sp.data[j * 4], g = sp.data[j * 4 + 1], b = sp.data[j * 4 + 2], key = (r >> 3) * 1024 + (g >> 3) * 32 + (b >> 3);
    if (!seen[key]) { seen[key] = 1; colors++; }
    var l = (r * LUMA[0] + g * LUMA[1] + b * LUMA[2]) / 255; lumaSum += l; lumaSq += l * l; if (l < 0.04) dark++;
    var xx = j % w; if (xx < minX) minX = xx; if (xx > maxX) maxX = xx;
  }
  var mean = lumaSum / opaqueCount, std = Math.sqrt(Math.max(0, lumaSq / opaqueCount - mean * mean));
  add('INFO', 'liczba kolorow (5 bit/kanal): ' + colors);
  if (colors < TH.colors) add('WARN', 'malo kolorow - tekstury zbyt plaskie wzgledem referencji (setki kolorow); dodaj teksture, ziarno (grain) lub zroznicowanie tonow');
  add('INFO', 'srednia jasnosc ' + mean.toFixed(2) + ', odchylenie ' + std.toFixed(2));
  if (mean < TH.dark) add('WARN', 'sprite bardzo ciemny - zwieksz exposure lub jasnosc tekstur');
  if (mean > 0.70) add('WARN', 'sprite przepalony - zmniejsz exposure');
  if (std < TH.std) add('WARN', 'niski kontrast - brak czytelnej bryly (sprawdz swiatlo, ao i fazowanie krawedzi (rim))');
  if (dark / opaqueCount > TH.black) add('WARN', 'duzo prawie czarnych pikseli - zbyt ciemny material lub zbyt mocne ao');
  var softRatio = soft / Math.max(1, visible);
  if (softRatio < 0.004) add('WARN', 'krawedzie bez antyaliasingu (supersample < 2?) albo ostre alfa-testy');
  if (softRatio > TH.soft) add('WARN', 'bardzo duzo polprzezroczystych pikseli - rozmyty obiekt lub zbyt gesty szum');
  var teamCount = 0, outside = 0;
  for (var t = 0; t < n; t++) if (result.team.data[t] > 40) { teamCount++; if (!(alpha[t] > 0.1)) outside++; }
  if (expectTeam && !teamCount) add('WARN', 'maska koloru druzyny pusta - brak elementow z material({ team: true })');
  if (teamCount) {
    if (outside > 0.05 * teamCount) add('ERR', 'maska druzyny wychodzi poza sprite');
    add('INFO', 'pokrycie maski druzyny: ' + (teamCount / opaqueCount * 100).toFixed(1) + '% sprite\'a');
    if (teamCount > TH.team * opaqueCount) add('WARN', 'maska druzyny > ' + Math.round(TH.team * 100) + '% sprite\'a - zbyt duzo koloru gracza');
  }
  var shSum = 0, shX = 0, spSum = 0, spX = 0, shBig = 0;
  for (var q = 0; q < n; q++) {
    var sa = result.shadow.data[q * 4 + 3] / 255, cx = q % w; shSum += sa; shX += sa * cx; spSum += alpha[q]; spX += alpha[q] * cx; if (sa > 0.03) shBig++;
  }
  if (shSum < 20) { if (kind !== 'prop') add('WARN', 'brak warstwy cienia'); }
  else {
    var shCx = shX / shSum, spCx = spX / spSum;
    if (shadowSide === 'left' && shCx > spCx + 1) add('ERR', 'cien pada w prawo - w tym stylu swiatlo jest z prawej gornej, cien w lewo-dol (inny uklad swiatla: shadowSide)');
    if (shadowSide === 'right' && shCx < spCx - 1) add('ERR', 'cien pada w lewo, a oczekiwano prawej strony (shadowSide: right)');
    add('INFO', 'cien: ' + shSum.toFixed(0) + ' px-masy, srodek ' + (shCx - spCx >= 0 ? '+' : '') + (shCx - spCx).toFixed(1) + 'px wzgledem sprite\'a');
  }
  var ax = result.anchor[0], ay = result.anchor[1];
  if (!(ax >= 0 && ax < w && ay >= 0 && ay < h)) add('ERR', 'kotwica poza kadrem');
  add('INFO', 'rozmiar ' + w + 'x' + h + 'px, szerokosc obiektu ' + ((maxX - minX + 1) / result.tilePx).toFixed(2) + ' kafla, kotwica (' + ax.toFixed(0) + ',' + ay.toFixed(0) + ')');
  return findings;
}
function validateSheet(frames, options) {
  options = options || {};
  var findings = [];
  if (!frames || !frames.length) return [['ERR', 'pusta lista klatek']];
  var sizes = {};
  frames.forEach(function (f) { sizes[f.sprite.width + 'x' + f.sprite.height] = 1; });
  if (Object.keys(sizes).length > 1) return [['ERR', 'klatki arkusza maja rozne rozmiary - renderuj z trim:false i skladaj packSheet()']];
  var base = frames[0].anchor, masses = [], teamFlags = [];
  frames.forEach(function (f, index) {
    var n = f.sprite.width * f.sprite.height, mass = 0, opaque = 0, team = false;
    for (var i = 0; i < n; i++) { var a = f.sprite.data[i * 4 + 3]; mass += a / 255; if (a > 229) opaque++; if (f.team.data[i] > 40) team = true; }
    masses.push(mass);
    if (!opaque) { findings.push(['ERR', 'klatka ' + index + ': pusty sprite']); return; }
    if (Math.abs(f.anchor[0] - base[0]) > 0.5 || Math.abs(f.anchor[1] - base[1]) > 0.5) findings.push(['ERR', 'klatka ' + index + ': kotwica rozni sie od klatki 0']);
    teamFlags.push(team);
    validateSprite(f, { expectTeam: false, shadowSide: options.shadowSide }).forEach(function (x) { if (x[0] === 'ERR') findings.push(['ERR', 'klatka ' + index + ': ' + x[1]]); });
  });
  var positive = masses.filter(function (m) { return m > 0; }).sort(function (a, b) { return a - b; });
  if (positive.length) {
    var median = positive[Math.floor(positive.length / 2)];
    masses.forEach(function (m, index) { if (m < 0.4 * median || m > 2.5 * median) findings.push(['WARN', 'klatka ' + index + ': powierzchnia obiektu ' + Math.round(m) + ' px wobec mediany ' + Math.round(median) + ' px - ucieta, pusta albo inna skala?']); });
  }
  if (teamFlags.some(Boolean) && !teamFlags.every(Boolean)) findings.push(['WARN', 'maska druzyny jest tylko w czesci klatek - element druzyny niewidoczny z niektorych kierunkow lub blad modelu']);
  findings.push(['INFO', frames.length + ' klatek ' + frames[0].sprite.width + 'x' + frames[0].sprite.height + ' px']);
  return findings;
}
function report(findings) {
  var ok = true;
  findings.forEach(function (f) { if (f[0] === 'ERR') ok = false; if (typeof console !== 'undefined' && console.log) console.log('[' + f[0] + '] ' + f[1]); });
  return ok;
}

// reviewStrip(result, { scales: [0.5, 1, 2], gap: 12, background: [70, 70, 70] }) -> Image RGB: podglad w kilku skalach obok siebie (1x = rozmiar w grze).
// Duzy podglad ukrywa problemy widoczne dopiero po zmniejszeniu; oceniaj sylwetke, kontrast i kolor druzyny na najmniejszej skali.
function reviewStrip(result, options) {
  options = options || {};
  var scales = options.scales || [0.5, 1, 2], gap = options.gap === undefined ? 12 : options.gap, bg = options.background || [70, 70, 70], src = result.preview, tiles = [];
  scales.forEach(function (scale) {
    var w = Math.max(1, Math.round(src.width * scale)), h = Math.max(1, Math.round(src.height * scale)), tile = makeImage(w, h, 3);
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) for (var c = 0; c < 3; c++) {
      var value;
      if (scale < 1) {   // usrednianie obszaru zrodlowego (jak INTER_AREA)
        var x0 = Math.floor(x / scale), x1 = Math.max(x0 + 1, Math.min(src.width, Math.floor((x + 1) / scale))), y0 = Math.floor(y / scale), y1 = Math.max(y0 + 1, Math.min(src.height, Math.floor((y + 1) / scale))), sum = 0, count = 0;
        for (var yy = y0; yy < y1; yy++) for (var xx = x0; xx < x1; xx++) { sum += src.data[(yy * src.width + xx) * 3 + c]; count++; }
        value = sum / count;
      } else value = src.data[(Math.min(src.height - 1, Math.floor(y / scale)) * src.width + Math.min(src.width - 1, Math.floor(x / scale))) * 3 + c];
      tile.data[(y * w + x) * 3 + c] = Math.round(value);
    }
    tiles.push(tile);
  });
  var height = Math.max.apply(null, tiles.map(function (t) { return t.height; })), width = gap, i;
  tiles.forEach(function (t) { width += t.width + gap; });
  var out = makeImage(width, height + 2 * gap, 3);
  for (i = 0; i < out.width * out.height; i++) { out.data[i * 3] = bg[0]; out.data[i * 3 + 1] = bg[1]; out.data[i * 3 + 2] = bg[2]; }
  var left = gap;
  tiles.forEach(function (t) {
    for (var y = 0; y < t.height; y++) for (var x = 0; x < t.width; x++) for (var c = 0; c < 3; c++) out.data[((gap + y) * out.width + left + x) * 3 + c] = t.data[(y * t.width + x) * 3 + c];
    left += t.width + gap;
  });
  return out;
}

// ===== 09_figures.js =====
// ---------------------------------------------------------------- postacie i konie: szkielet 3D z kapsul i elipsoid, obrot wokol z daje 8/16 kierunkow
// Figura zwrocona jest w lokalnym +x; yaw (stopnie) obraca ja w swiecie. Ekranowo: yaw 0 = SE (w prawo-dol), 45 = E, 90 = NE, 135 = N (tylem), 180 = NW, 225 = W, 270 = SW, 315 = S (twarza do kamery).
function directions(n) {
  n = n || 8;
  var names8 = ['SE', 'E', 'NE', 'N', 'NW', 'W', 'SW', 'S'], out = [];
  for (var i = 0; i < n; i++) out.push({ index: i, yaw: i * 360 / n, name: n === 8 ? names8[i] : 'dir' + i });
  return out;
}

function limbSeg(P, a, b, r0, r1, mat) { P.frustum(a, b, r0, r1, mat, { caps: false }); P.ellipsoid(b, [r1, r1, r1], mat, {}); }
function polar(len, ang) { return [Math.sin(ang) * len, 0, -Math.cos(ang) * len]; }
function addv(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }

// humanoid(P, { pos, yaw, phase (0..1, krok), moving, scale, shirt, pants, boots, skin, hat: 'cowboy'|'sombrero'|'cap'|'none', hatColor, weapon: 'none'|'rifle'|'sword'|'axe'|'pickaxe'|'bow',
//   team: 'torso'|'sleeves'|'hat'|'none', ride (siedzi na koniu), poncho: [r,g,b] })
function humanoid(P, o) {
  o = copyOpts(o, { pos: [0, 0, 0], yaw: 0, phase: 0, moving: true, shirt: [0.72, 0.68, 0.58], pants: [0.28, 0.24, 0.20], boots: [0.20, 0.12, 0.07], skin: PALETTE.skin, hat: 'cowboy', hatColor: [0.45, 0.33, 0.20], weapon: 'none', team: 'torso', ride: false, scale: 0.72 });   // scale 0.72 = jednostka ok. 0.77 kafla (~45 px) jak w grach z 2000 r.; 1.0 = ok. 1.07 kafla
  var S = o.scale, g = { grain: 0.035 }, mShirt = solid(o.shirt, g), mPants = solid(o.pants, g), mBoot = solid(o.boots, { grain: 0.05, spec: 0.1 }), mSkin = solid(o.skin, { grain: 0.02 }), mHat = solid(o.hatColor, { grain: 0.05 });
  var mTeam = material({ color: [0.62, 0.22, 0.20], team: true, grain: 0.04 }), mTorso = o.team === 'torso' ? mTeam : mShirt, mSleeve = o.team === 'sleeves' ? mTeam : mShirt, mBand = o.team === 'hat' ? mTeam : solid([0.12, 0.09, 0.06], g);
  var mLeather = solid(PALETTE.leather, { grain: 0.05 }), mIron = solid(PALETTE.iron, { grain: 0.03, spec: 0.5, shin: 30 }), mWood = solid(PALETTE.wood, { grain: 0.05 });
  function v(x, y, z) { return [x * S, y * S, z * S]; }
  var t = o.phase * 2 * Math.PI, moving = o.moving && !o.ride;
  P.at(o.pos, o.yaw, function () {
    var bob = moving ? 0.014 * Math.abs(Math.sin(t * 2)) : 0, hipZ = 0.50 + bob, ride = o.ride, hipY = ride ? 0.075 : 0.05;
    // nogi
    [1, -1].forEach(function (side) {
      var theta = t + (side > 0 ? 0 : Math.PI), phi = moving ? 0.55 * Math.sin(theta) : 0, kappa = moving ? 0.85 * Math.max(0, Math.cos(theta)) : 0;
      var hip = v(0, side * hipY, hipZ), knee, ankle;
      if (ride) { knee = v(0.15, side * 0.15, hipZ - 0.10); ankle = v(0.10, side * 0.17, hipZ - 0.30); }
      else { knee = addv(hip, polar(0.235 * S, phi)); ankle = addv(knee, polar(0.235 * S, phi - kappa)); }
      limbSeg(P, hip, knee, 0.056 * S, 0.044 * S, mPants);
      P.frustum(knee, ankle, 0.044 * S, 0.034 * S, mPants, { caps: false });
      var footDir = ride ? [0.06, 0, -0.01] : [0.075, 0, 0];
      P.frustum(addv(ankle, [0, 0, 0.08 * S]), addv(ankle, [0, 0, -0.005]), 0.036 * S, 0.034 * S, mBoot, { caps: false });
      P.ellipsoid(addv(ankle, [footDir[0] * S, 0, 0.012 * S]), [0.075 * S, 0.034 * S, 0.026 * S], mBoot, {});
    });
    // tulow
    var chestZ = 0.66 + bob;
    P.ellipsoid(v(0, 0, hipZ + 0.02), [0.075 * S, 0.105 * S, 0.075 * S], mPants, {});
    P.ellipsoid(v(0, 0, chestZ), [0.088 * S, 0.128 * S, 0.178 * S], mTorso, {});
    P.ellipsoid(v(0, 0, 0.545 + bob), [0.083 * S, 0.116 * S, 0.016 * S], mLeather, { shadow: false });
    if (o.poncho) {
      var pm = solid(o.poncho, { grain: 0.05 });
      P.frustum(v(0, 0, chestZ - 0.17 + bob), v(0, 0, chestZ + 0.20 + bob), 0.19 * S, 0.10 * S, pm, { caps: false });
    }
    // glowa
    var headZ = 0.935 + bob;
    P.frustum(v(0, 0, 0.80 + bob), v(0.01, 0, headZ - 0.03), 0.032 * S, 0.030 * S, mSkin, { caps: false, shadow: false });
    P.ellipsoid(v(0.012, 0, headZ), [0.080 * S, 0.074 * S, 0.086 * S], mSkin, {});
    P.ellipsoid(v(-0.012, 0, headZ + 0.012), [0.076 * S, 0.074 * S, 0.074 * S], solid([0.15, 0.10, 0.07], g), { shadow: false });   // wlosy z tylu
    // kapelusz
    if (o.hat === 'cowboy' || o.hat === 'sombrero') {
      var br = o.hat === 'sombrero' ? 0.21 : 0.155, hh = o.hat === 'sombrero' ? 0.07 : 0.085, hz = headZ + 0.045;
      P.ellipsoid(v(0.005, 0, hz), [br * S, br * S, 0.017 * S], mHat, {});
      P.frustum(v(0.005, 0, hz), v(0.005, 0, hz + hh), 0.083 * S, o.hat === 'sombrero' ? 0.045 * S : 0.068 * S, mHat, { caps: true });
      P.frustum(v(0.005, 0, hz + 0.012), v(0.005, 0, hz + 0.034), 0.085 * S, 0.083 * S, mBand, { caps: false, shadow: false });
    } else if (o.hat === 'cap') {
      P.ellipsoid(v(0.01, 0, headZ + 0.035), [0.078 * S, 0.074 * S, 0.05 * S], mHat, {});
      P.ellipsoid(v(0.075, 0, headZ + 0.03), [0.05 * S, 0.06 * S, 0.01 * S], mHat, { shadow: false });
    }
    // rece
    var shoulderZ = 0.775 + bob, hands = {};
    [1, -1].forEach(function (side) {
      var theta = t + (side > 0 ? Math.PI : 0), phiA = moving ? 0.5 * Math.sin(theta) : 0.05, flex = moving ? 0.35 + 0.35 * Math.max(0, Math.cos(theta)) : 0.25;
      var sh = v(0, side * 0.125, shoulderZ), elbow = addv(sh, polar(0.15 * S, phiA)), hand = addv(elbow, polar(0.15 * S, phiA + flex));
      var armed = o.weapon === 'rifle' || o.weapon === 'bow' || ride;
      if (armed) {
        if (side < 0) { elbow = v(0.08, -0.16, 0.66 + bob); hand = v(0.20, -0.10, 0.70 + bob); } else { elbow = v(0.12, 0.14, 0.70 + bob); hand = v(0.30, 0.02, 0.76 + bob); }
        if (ride && o.weapon === 'none') { elbow = v(0.10, side * 0.16, 0.70); hand = v(0.22, side * 0.08, 0.72); }
      }
      limbSeg(P, sh, elbow, 0.040 * S, 0.034 * S, mSleeve);
      P.frustum(elbow, hand, 0.034 * S, 0.026 * S, mSleeve, { caps: false });
      P.ellipsoid(hand, [0.03 * S, 0.028 * S, 0.03 * S], mSkin, {});
      hands[side] = hand;
    });
    // bron
    var h1 = hands[-1], h2 = hands[1];
    if (o.weapon === 'rifle') { P.rod(addv(h1, v(-0.18, 0.02, -0.04)), addv(h2, v(0.26, 0.0, 0.08)), 0.014 * S, mIron, { shadow: false }); P.rod(addv(h1, v(-0.20, 0.02, -0.05)), addv(h1, v(0.02, 0.0, 0.0)), 0.022 * S, mWood, { shadow: false }); }
    else if (o.weapon === 'sword') { P.rod(h1, addv(h1, v(0.08, 0.04, 0.36)), 0.012 * S, mIron, { shadow: false }); P.rod(addv(h1, v(0.0, -0.05, 0.03)), addv(h1, v(0.0, 0.05, 0.03)), 0.01 * S, mIron, { shadow: false }); }
    else if (o.weapon === 'axe') { P.rod(addv(h1, v(-0.02, 0, -0.18)), addv(h1, v(0.04, 0, 0.24)), 0.014 * S, mWood, { shadow: false }); P.box(addv(h1, v(0.07, 0, 0.22)), [0.02 * S, 0.1 * S, 0.075 * S], mIron, { shadow: false }); }
    else if (o.weapon === 'pickaxe') { P.rod(addv(h1, v(-0.02, 0, -0.18)), addv(h1, v(0.04, 0, 0.24)), 0.014 * S, mWood, { shadow: false }); P.rod(addv(h1, v(0.04, -0.13, 0.22)), addv(h1, v(0.04, 0.13, 0.22)), 0.012 * S, mIron, { shadow: false }); }
    else if (o.weapon === 'bow') { P.rod(addv(h1, v(0.02, 0, -0.30)), addv(h1, v(0.02, 0, 0.30)), 0.011 * S, mWood, { shadow: false }); }
  });
}

// futro konia: jasnosc z wysokoscia (brzuch ciemniejszy), delikatne plamy
function coatMaterial(color, seed) {
  return material({ name: 'coat', shader: function (ctx, out) {
    var n = fbm3(ctx.px * 9, ctx.py * 9, ctx.pz * 9, seed || 2, 2), belly = 0.78 + 0.22 * smoothstep(0.28, 0.80, ctx.lz), k = (0.92 + 0.16 * n) * belly;
    ctx.P.lit(ctx, [color[0] * k, color[1] * k, color[2] * k], out, null); out[3] = 1;
  } });
}
// horse(P, { pos, yaw, phase, moving, coat: [r,g,b], mane, rider: { ...opcje humanoid } | null, saddle: true, team: true })
function horse(P, o) {
  o = copyOpts(o, { pos: [0, 0, 0], yaw: 0, phase: 0, moving: true, coat: [0.60, 0.34, 0.16], mane: [0.10, 0.07, 0.05], saddle: true, team: true, scale: 0.8 });
  var coat = coatMaterial(o.coat, 3), mane = solid(o.mane, { grain: 0.05 }), hoof = solid([0.10, 0.08, 0.07], { grain: 0.02 }), team = material({ color: [0.62, 0.22, 0.20], team: true, grain: 0.04 }), leather = solid(PALETTE.leather, { grain: 0.05 });
  var t = o.phase * 2 * Math.PI, S = o.scale, moving = o.moving;
  function v(x, y, z) { return [x * S, y * S, z * S]; }
  P.at(o.pos, o.yaw, function () {
    var bob = moving ? 0.012 * Math.sin(t * 2) : 0;
    // nogi: diagonalne pary
    [[0.27, 0.085, 0], [0.27, -0.085, 0.5], [-0.28, 0.085, 0.5], [-0.28, -0.085, 0]].forEach(function (leg, idx) {
      var front = idx < 2, theta = t + leg[2] * 2 * Math.PI, phi = moving ? 0.5 * Math.sin(theta) : 0, kappa = moving ? 0.9 * Math.max(0, Math.cos(theta)) * (front ? 1.0 : 0.7) : 0;
      var top = v(leg[0], leg[1], 0.58 + bob), knee = addv(top, polar(0.25 * S, front ? phi : -phi * 0.8)), fet = addv(knee, polar(0.25 * S, (front ? phi : -phi * 0.8) - (front ? kappa : -kappa * 0.5)));
      limbSeg(P, top, knee, 0.058 * S, 0.036 * S, coat);
      P.frustum(knee, fet, 0.036 * S, 0.026 * S, coat, { caps: false });
      P.frustum(fet, addv(fet, [0.01 * S, 0, -0.05 * S]), 0.030 * S, 0.034 * S, hoof, { caps: true });
    });
    // tulow, zad, klatka
    P.ellipsoid(v(0.0, 0, 0.64 + bob), [0.40 * S, 0.135 * S, 0.165 * S], coat, {});
    P.ellipsoid(v(0.24, 0, 0.66 + bob), [0.19 * S, 0.135 * S, 0.19 * S], coat, {});
    P.ellipsoid(v(-0.27, 0, 0.66 + bob), [0.19 * S, 0.145 * S, 0.185 * S], coat, {});
    // szyja i glowa
    P.frustum(v(0.30, 0, 0.72 + bob), v(0.50, 0, 1.0 + bob), 0.095 * S, 0.055 * S, coat, { caps: false });
    P.ellipsoid(v(0.57, 0, 1.03 + bob), [0.12 * S, 0.052 * S, 0.062 * S], coat, { pitch: -32 });
    P.ellipsoid(v(0.66, 0, 0.97 + bob), [0.05 * S, 0.042 * S, 0.045 * S], coat, {});
    [-1, 1].forEach(function (s) { P.frustum(v(0.50, s * 0.03, 1.07 + bob), v(0.49, s * 0.035, 1.14 + bob), 0.016 * S, 0.004 * S, coat, { caps: false, shadow: false }); });
    P.ellipsoid(v(0.64, 0.0, 1.0 + bob), [0.012 * S, 0.056 * S, 0.012 * S], hoof, { shadow: false });
    // grzywa i ogon
    for (var i = 0; i < 6; i++) { var f = i / 5; P.ellipsoid(v(0.31 + 0.20 * f - 0.035, 0, 0.78 + 0.26 * f + bob), [0.04 * S, 0.026 * S, 0.05 * S], mane, { shadow: false }); }
    P.frustum(v(-0.43, 0, 0.74 + bob), v(-0.50 - (moving ? 0.04 * Math.sin(t) : 0), 0, 0.34), 0.04 * S, 0.02 * S, mane, { caps: false });
    // siodlo, derka i jezdziec
    if (o.saddle) {
      P.ellipsoid(v(-0.02, 0, 0.80 + bob), [0.19 * S, 0.158 * S, 0.035 * S], o.team ? team : solid([0.6, 0.2, 0.2]), { shadow: false });
      P.ellipsoid(v(-0.02, 0, 0.83 + bob), [0.12 * S, 0.10 * S, 0.035 * S], leather, { shadow: false });
    }
    if (o.rider) {
      var r = copyOpts(o.rider, {}); r.scale = r.scale || 0.72; r.pos = [-0.02 * S, 0, 0.86 * S - 0.5 * r.scale + 0.02]; r.yaw = 0; r.ride = true; r.moving = false;
      humanoid(P, r);
    }
  });
}

return { TILE_PX: typeof TILE_PX !== 'undefined' ? TILE_PX : undefined, SUN_DIR: typeof SUN_DIR !== 'undefined' ? SUN_DIR : undefined, TO_CAMERA: typeof TO_CAMERA !== 'undefined' ? TO_CAMERA : undefined, Painter: typeof Painter !== 'undefined' ? Painter : undefined, sprite: typeof sprite !== 'undefined' ? sprite : undefined, material: typeof material !== 'undefined' ? material : undefined, makeRng: typeof makeRng !== 'undefined' ? makeRng : undefined, sampleTex: typeof sampleTex !== 'undefined' ? sampleTex : undefined, ramp: typeof ramp !== 'undefined' ? ramp : undefined, noise3: typeof noise3 !== 'undefined' ? noise3 : undefined, fbm3: typeof fbm3 !== 'undefined' ? fbm3 : undefined, cellular3: typeof cellular3 !== 'undefined' ? cellular3 : undefined, smoothstep: typeof smoothstep !== 'undefined' ? smoothstep : undefined, mix: typeof mix !== 'undefined' ? mix : undefined, mix3: typeof mix3 !== 'undefined' ? mix3 : undefined, clamp: typeof clamp !== 'undefined' ? clamp : undefined, fbm: typeof fbm !== 'undefined' ? fbm : undefined, newTexture: typeof newTexture !== 'undefined' ? newTexture : undefined, adjustTexture: typeof adjustTexture !== 'undefined' ? adjustTexture : undefined, standardTextures: typeof standardTextures !== 'undefined' ? standardTextures : undefined, textureToImage: typeof textureToImage !== 'undefined' ? textureToImage : undefined, TEXTURE_FUNCTIONS: typeof TEXTURE_FUNCTIONS !== 'undefined' ? TEXTURE_FUNCTIONS : undefined, texShingle: typeof texShingle !== 'undefined' ? texShingle : undefined, texPlaster: typeof texPlaster !== 'undefined' ? texPlaster : undefined, texTimber: typeof texTimber !== 'undefined' ? texTimber : undefined, texPlanks: typeof texPlanks !== 'undefined' ? texPlanks : undefined, texStone: typeof texStone !== 'undefined' ? texStone : undefined, texGrass: typeof texGrass !== 'undefined' ? texGrass : undefined, texLeaf: typeof texLeaf !== 'undefined' ? texLeaf : undefined, texNeedle: typeof texNeedle !== 'undefined' ? texNeedle : undefined, texCloth: typeof texCloth !== 'undefined' ? texCloth : undefined, texThatch: typeof texThatch !== 'undefined' ? texThatch : undefined, texBark: typeof texBark !== 'undefined' ? texBark : undefined, texDirt: typeof texDirt !== 'undefined' ? texDirt : undefined, texMetal: typeof texMetal !== 'undefined' ? texMetal : undefined, texSoil: typeof texSoil !== 'undefined' ? texSoil : undefined, texAutumnGrass: typeof texAutumnGrass !== 'undefined' ? texAutumnGrass : undefined, texAdobe: typeof texAdobe !== 'undefined' ? texAdobe : undefined, texClapboard: typeof texClapboard !== 'undefined' ? texClapboard : undefined, solid: typeof solid !== 'undefined' ? solid : undefined, foliageMaterial: typeof foliageMaterial !== 'undefined' ? foliageMaterial : undefined, needleMaterial: typeof needleMaterial !== 'undefined' ? needleMaterial : undefined, windowGlass: typeof windowGlass !== 'undefined' ? windowGlass : undefined, windowOn: typeof windowOn !== 'undefined' ? windowOn : undefined, doorOn: typeof doorOn !== 'undefined' ? doorOn : undefined, FOLIAGE: typeof FOLIAGE !== 'undefined' ? FOLIAGE : undefined, tree: typeof tree !== 'undefined' ? tree : undefined, conifer: typeof conifer !== 'undefined' ? conifer : undefined, bush: typeof bush !== 'undefined' ? bush : undefined, rock: typeof rock !== 'undefined' ? rock : undefined, tuft: typeof tuft !== 'undefined' ? tuft : undefined, field: typeof field !== 'undefined' ? field : undefined, deadTree: typeof deadTree !== 'undefined' ? deadTree : undefined, cactus: typeof cactus !== 'undefined' ? cactus : undefined, stump: typeof stump !== 'undefined' ? stump : undefined, house: typeof house !== 'undefined' ? house : undefined, tower: typeof tower !== 'undefined' ? tower : undefined, barrel: typeof barrel !== 'undefined' ? barrel : undefined, crate: typeof crate !== 'undefined' ? crate : undefined, fence: typeof fence !== 'undefined' ? fence : undefined, wagonWheel: typeof wagonWheel !== 'undefined' ? wagonWheel : undefined, tent: typeof tent !== 'undefined' ? tent : undefined, haystack: typeof haystack !== 'undefined' ? haystack : undefined, well: typeof well !== 'undefined' ? well : undefined, sign: typeof sign !== 'undefined' ? sign : undefined, campfire: typeof campfire !== 'undefined' ? campfire : undefined, humanoid: typeof humanoid !== 'undefined' ? humanoid : undefined, horse: typeof horse !== 'undefined' ? horse : undefined, PALETTE: typeof PALETTE !== 'undefined' ? PALETTE : undefined, groundLayer: typeof groundLayer !== 'undefined' ? groundLayer : undefined, groundMix: typeof groundMix !== 'undefined' ? groundMix : undefined, groundTile: typeof groundTile !== 'undefined' ? groundTile : undefined, composeScene: typeof composeScene !== 'undefined' ? composeScene : undefined, encodePng: typeof encodePng !== 'undefined' ? encodePng : undefined, toBase64: typeof toBase64 !== 'undefined' ? toBase64 : undefined, makeImage: typeof makeImage !== 'undefined' ? makeImage : undefined, saveSprite: typeof saveSprite !== 'undefined' ? saveSprite : undefined, packSheet: typeof packSheet !== 'undefined' ? packSheet : undefined, saveSheet: typeof saveSheet !== 'undefined' ? saveSheet : undefined, swapTeamColor: typeof swapTeamColor !== 'undefined' ? swapTeamColor : undefined, validateSprite: typeof validateSprite !== 'undefined' ? validateSprite : undefined, validateSheet: typeof validateSheet !== 'undefined' ? validateSheet : undefined, report: typeof report !== 'undefined' ? report : undefined, reviewStrip: typeof reviewStrip !== 'undefined' ? reviewStrip : undefined, directions: typeof directions !== 'undefined' ? directions : undefined, renderFrames: typeof renderFrames !== 'undefined' ? renderFrames : undefined };
});
