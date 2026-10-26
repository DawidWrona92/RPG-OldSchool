/* rtcore.js - przenosny rdzen pre-renderu 3D (czysty JavaScript, ZERO zaleznosci: bez fs, Buffer, process, DOM, sieci).
 * WYGENEROWANY z src/*.js przez build.js - nie edytuj recznie. Typy: rtcore.d.ts.
 * Dziala w Node, Bun, Deno, przegladarce i w piaskownicach, ktore wykonuja zwykly JS/TS. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  root.rtcore = api;
})(typeof globalThis !== 'undefined' ? globalThis : typeof self !== 'undefined' ? self : this, function () {
'use strict';
// ===== 01_math.js =====
// ---------------------------------------------------------------- matematyka i losowanie
var TILE_PX = 96;                                  // szerokosc kafla (rombu) w pikselach; wysokosc = polowa
var SUN_DIR = [-0.45, -1.35, -1.5];                // kierunek PROMIENI; cien pada w lewo-dol ekranu (jak AoE2)
var SUN_COLOR = [3.4, 3.1, 2.6];                   // irradiancja prostopadla do promieni
var SKY_COLOR = [0.55, 0.66, 0.85];                // stala luminancja nieboskłonu
var LUMA = [0.2126, 0.7152, 0.0722];

function v3(x, y, z) { return [x, y, z]; }
function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function mul(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function length(a) { return Math.sqrt(dot(a, a)); }
function normalize(a) { var l = length(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }
function clamp(x, lo, hi) { return x < lo ? lo : x > hi ? hi : x; }

// macierze 3x3 w postaci [[...],[...],[...]] (jak w Pythonie)
function identity() { return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]; }
function matVec(m, v) { return [m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2], m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2], m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]]; }
function matMul(a, b) {
  var out = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) for (var k = 0; k < 3; k++) out[i][j] += a[i][k] * b[k][j];
  return out;
}
function rotX(angle) { var c = Math.cos(angle), s = Math.sin(angle); return [[1, 0, 0], [0, c, -s], [0, s, c]]; }
function rotY(angle) { var c = Math.cos(angle), s = Math.sin(angle); return [[c, 0, s], [0, 1, 0], [-s, 0, c]]; }
function rotZ(angle) { var c = Math.cos(angle), s = Math.sin(angle); return [[c, -s, 0], [s, c, 0], [0, 0, 1]]; }
// obrot przeprowadzajacy os z na zadany kierunek
function rotationTo(axis) {
  var a = normalize(axis), z = [0, 0, 1], v = cross(z, a), c = dot(z, a);
  if (length(v) < 1e-9) return c > 0 ? identity() : rotX(Math.PI);
  var vx = [[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]], vx2 = matMul(vx, vx), k = 1 / (1 + c), out = identity();
  for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) out[i][j] += vx[i][j] + vx2[i][j] * k;
  return out;
}

// deterministyczny generator (mulberry32) i funkcje pochodne
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
  return next;
}
function hashString(text) { var h = 2166136261; for (var i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }

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

var TEXTURE_FUNCTIONS = {
  roof: function () { return texShingle(512, 1); }, plaster: function () { return texPlaster(512, 2); }, timber: function () { return texTimber(512, 3); },
  planks: function () { return texPlanks(512, 4); }, stone: function () { return texStone(512, 5); }, grass: function () { return texGrass(512, 6); },
  leaf: function () { return texLeaf(256, 7); }, needle: function () { return texNeedle(256, 13); }, thatch: function () { return texThatch(512, 8); }, bark: function () { return texBark(512, 9); },
  dirt: function () { return texDirt(512, 10); }, metal: function () { return texMetal(256, 11); }, cloth: function () { return texCloth(256, 12); },
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

// ===== 03_geometry.js =====
// ---------------------------------------------------------------- siatki proceduralne
// Os z = gora, ziemia z = 0, jednostka swiata = 1 kafel. Model grupuje siatki wg materialu.

var BOX_FACES = [  // normalna, narozniki (CCW z zewnatrz), osie UV
  [[1, 0, 0], [[1, -1, -1], [1, 1, -1], [1, 1, 1], [1, -1, 1]], [1, 2]],
  [[-1, 0, 0], [[-1, 1, -1], [-1, -1, -1], [-1, -1, 1], [-1, 1, 1]], [1, 2]],
  [[0, 1, 0], [[1, 1, -1], [-1, 1, -1], [-1, 1, 1], [1, 1, 1]], [0, 2]],
  [[0, -1, 0], [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1]], [0, 2]],
  [[0, 0, 1], [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], [0, 1]],
  [[0, 0, -1], [[-1, 1, -1], [1, 1, -1], [1, -1, -1], [-1, -1, -1]], [0, 1]],
];

function Mesh() { this.positions = []; this.normals = []; this.uvs = []; this.faces = []; }
Mesh.prototype.addPolygon = function (points, normals, uvs) {
  var start = this.positions.length;
  for (var j = 0; j < points.length; j++) {   // NaN/undefined (np. punkt 2D tam, gdzie trzeba 3D) inaczej po cichu zniknalby z obrazu
    var q = points[j], n = normals[j];
    if (!q || !isFinite(q[0]) || !isFinite(q[1]) || !isFinite(q[2]) || !n || !isFinite(n[0]) || !isFinite(n[1]) || !isFinite(n[2])) throw new Error('niepoprawny wierzcholek lub normalna (NaN/undefined): sprawdz, czy punkty maja 3 wspolrzedne [x, y, z]');
  }
  for (var i = 0; i < points.length; i++) { this.positions.push(points[i]); this.normals.push(normals[i]); this.uvs.push(uvs[i]); }
  for (var k = 1; k < points.length - 1; k++) this.faces.push([start, start + k, start + k + 1]);
};

function Model() { this.meshes = {}; this.materials = {}; }
// material(nazwa, { texture, color, worldSize = 2, team = false }): texture to obiekt z standardTextures(), color to [r, g, b] w przestrzeni liniowej
Model.prototype.material = function (name, options) {
  options = options || {};
  this.materials[name] = { texture: options.texture || null, color: options.color || null, worldSize: options.worldSize || 2.0, team: !!options.team };
  if (!this.meshes[name]) this.meshes[name] = new Mesh();
  return this;
};
Model.prototype._uvOffset = function (center) {
  var h = hashString(center.map(function (v) { return v.toFixed(3); }).join(','));
  return [(h & 255) / 255, ((h >>> 8) & 255) / 255];
};
// box(material, center, size, { rotation, swapUv, uvOffset })
Model.prototype.box = function (material, center, size, options) {
  options = options || {};
  var rotation = options.rotation || identity(), half = [size[0] / 2, size[1] / 2, size[2] / 2], scale = 1 / this.materials[material].worldSize;
  var offset = options.uvOffset || this._uvOffset(center), mesh = this.meshes[material];
  for (var f = 0; f < BOX_FACES.length; f++) {
    var normal = BOX_FACES[f][0], corners = BOX_FACES[f][1], ua = BOX_FACES[f][2][0], va = BOX_FACES[f][2][1];
    var local = corners.map(function (c) { return [c[0] * half[0], c[1] * half[1], c[2] * half[2]]; });
    var uvs = local.map(function (p) { var u = p[ua] * scale + offset[0], v = p[va] * scale + offset[1]; return options.swapUv ? [v, u] : [u, v]; });
    var world = local.map(function (p) { return add(matVec(rotation, p), center); }), n = matVec(rotation, normal);
    mesh.addPolygon(world, [n, n, n, n], uvs);
  }
};
// beam(material, p0, p1, width, depth, normal): belka od p0 do p1; przekroj width (w plaszczyznie sciany) x depth (wzdluz normalnej)
Model.prototype.beam = function (material, p0, p1, width, depth, normal) {
  normal = normal || [0, 0, 1];
  var axisFull = sub(p1, p0), len = length(axisFull), axis = mul(axisFull, 1 / len);
  var n = normalize(sub(normal, mul(axis, dot(normal, axis)))), third = cross(axis, n);
  var rotation = [[axis[0], n[0], third[0]], [axis[1], n[1], third[1]], [axis[2], n[2], third[2]]];
  this.box(material, mul(add(p0, p1), 0.5), [len, depth, width], { rotation: rotation });
};
// lathe(material, center, profile, segments = 28, { rotation, caps = true }): bryla obrotowa wokol z z profilu [[promien, z], ...]
Model.prototype.lathe = function (material, center, profile, segments, options) {
  options = options || {}; segments = segments || 28;
  var rotation = options.rotation || identity(), caps = options.caps !== false, scale = 1 / this.materials[material].worldSize, mesh = this.meshes[material];
  for (var i = 0; i < profile.length - 1; i++) {
    var r0 = profile[i][0], z0 = profile[i][1], r1 = profile[i + 1][0], z1 = profile[i + 1][1];
    var tx = r1 - r0, tz = z1 - z0, nl = Math.sqrt(tx * tx + tz * tz) + 1e-9, nr = tz / nl, nz = -tx / nl;
    for (var k = 0; k < segments; k++) {
      var a0 = 2 * Math.PI * k / segments, a1 = 2 * Math.PI * (k + 1) / segments, quad = [], norms = [], uvs = [];
      var corners = [[a0, r0, z0, a0], [a1, r0, z0, a1], [a1, r1, z1, a1], [a0, r1, z1, a0]];
      for (var c = 0; c < 4; c++) {
        var ang = corners[c][0], rad = corners[c][1], z = corners[c][2], uu = corners[c][3];
        quad.push(add(matVec(rotation, [rad * Math.cos(ang), rad * Math.sin(ang), z]), center));
        norms.push(matVec(rotation, [nr * Math.cos(ang), nr * Math.sin(ang), nz]));
        uvs.push([uu * Math.max(r0, r1, 0.05) * scale, z * scale]);
      }
      mesh.addPolygon(quad, norms, uvs);
    }
  }
  if (!caps) return;
  var ends = [[profile[0][1], profile[0][0], -1], [profile[profile.length - 1][1], profile[profile.length - 1][0], 1]];
  for (var e = 0; e < 2; e++) {
    var zc = ends[e][0], radius = ends[e][1], sign = ends[e][2];
    if (radius <= 1e-6) continue;
    var ring = [];
    for (var s = 0; s < segments; s++) ring.push([radius * Math.cos(2 * Math.PI * s / segments), radius * Math.sin(2 * Math.PI * s / segments), zc]);
    if (sign < 0) ring.reverse();
    var nn = matVec(rotation, [0, 0, sign]);
    mesh.addPolygon(ring.map(function (p) { return add(matVec(rotation, p), center); }), ring.map(function () { return nn; }), ring.map(function (p) { return [p[0] * scale + 0.5, p[1] * scale + 0.5]; }));
  }
};
// cylinder(material, p0, p1, radius0, radius1, segments = 18): walec lub stozek sciety od p0 do p1
Model.prototype.cylinder = function (material, p0, p1, radius0, radius1, segments) {
  var len = length(sub(p1, p0));
  this.lathe(material, p0, [[radius0, 0], [radius1 === undefined || radius1 === null ? radius0 : radius1, len]], segments || 18, { rotation: rotationTo(sub(p1, p0)) });
};
function icosphere(subdivisions) {
  var t = (1 + Math.sqrt(5)) / 2, verts = [[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]].map(normalize);
  var faces = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]];
  for (var s = 0; s < subdivisions; s++) {
    var cache = {}, next = [];
    var mid = function (a, b) {
      var key = a < b ? a + '_' + b : b + '_' + a;
      if (cache[key] === undefined) { verts.push(normalize(mul(add(verts[a], verts[b]), 0.5))); cache[key] = verts.length - 1; }
      return cache[key];
    };
    faces.forEach(function (f) { var ab = mid(f[0], f[1]), bc = mid(f[1], f[2]), ca = mid(f[2], f[0]); next.push([f[0], ab, ca], [f[1], bc, ab], [f[2], ca, bc], [ab, bc, ca]); });
    faces = next;
  }
  return { verts: verts, faces: faces };
}
// blob(material, center, radii, { seed = 0, roughness = 0.18, subdivisions = 3 }): zaburzona elipsoida (krzak, korona)
Model.prototype.blob = function (material, center, radii, options) {
  options = options || {};
  var seed = options.seed || 0, roughness = options.roughness === undefined ? 0.18 : options.roughness, sphere = icosphere(options.subdivisions === undefined ? 3 : options.subdivisions);
  var rng = makeRng(seed + 101), freqs = [], phases = [], i;
  for (i = 0; i < 4; i++) { freqs.push([rng.uniform(2, 6), rng.uniform(2, 6), rng.uniform(2, 6)]); phases.push(rng.uniform(0, 2 * Math.PI)); }
  var verts = sphere.verts.map(function (v) {
    var d = 0; for (var j = 0; j < 4; j++) d += Math.sin(dot(v, freqs[j]) + phases[j]);
    var k = 1 + roughness * d / 4;
    return [v[0] * k * radii[0] + center[0], v[1] * k * radii[1] + center[1], v[2] * k * radii[2] + center[2]];
  });
  var normals = verts.map(function () { return [0, 0, 0]; });
  sphere.faces.forEach(function (f) {
    var n = cross(sub(verts[f[1]], verts[f[0]]), sub(verts[f[2]], verts[f[0]]));
    for (var j = 0; j < 3; j++) normals[f[j]] = add(normals[f[j]], n);
  });
  normals = normals.map(normalize);
  var scale = 1 / this.materials[material].worldSize, mesh = this.meshes[material];
  sphere.faces.forEach(function (f) {
    var fn = [0, 1, 2].reduce(function (acc, j) { return add(acc, normals[f[j]]); }, [0, 0, 0]).map(Math.abs);
    var axes = fn[2] >= Math.max(fn[0], fn[1], fn[2]) ? [0, 1] : (fn[0] >= fn[1] ? [1, 2] : [0, 2]);
    mesh.addPolygon([verts[f[0]], verts[f[1]], verts[f[2]]], [normals[f[0]], normals[f[1]], normals[f[2]]],
      [0, 1, 2].map(function (j) { return [verts[f[j]][axes[0]] * scale, verts[f[j]][axes[1]] * scale]; }));
  });
};
// addObj(material, tekstObj, { scale, offset, rotation }): wczytuje zewnetrzny model w formacie OBJ (tekst), os z do gory
Model.prototype.addObj = function (material, text, options) {
  options = options || {};
  var scale = options.scale || 1, offset = options.offset || [0, 0, 0], rotation = options.rotation || identity();
  var verts = [], uvs = [], norms = [], mesh = this.meshes[material], worldScale = 1 / this.materials[material].worldSize;
  var place = function (v) { return add(matVec(rotation, mul(v, scale)), offset); };
  text.split('\n').forEach(function (line) {
    var parts = line.trim().split(/\s+/);
    if (parts[0] === 'v') verts.push(place([+parts[1], +parts[2], +parts[3]]));
    else if (parts[0] === 'vt') uvs.push([+parts[1], +parts[2]]);
    else if (parts[0] === 'vn') norms.push(matVec(rotation, [+parts[1], +parts[2], +parts[3]]));
    else if (parts[0] === 'f') {
      var corners = parts.slice(1).map(function (token) {
        var ids = token.split('/'), pick = function (list, id) { if (id === '' || id === undefined) return null; var n = parseInt(id, 10); return list[n < 0 ? list.length + n : n - 1]; };
        return { p: pick(verts, ids[0]), t: pick(uvs, ids[1]), n: pick(norms, ids[2]) };
      });
      var fn = normalize(cross(sub(corners[1].p, corners[0].p), sub(corners[2].p, corners[0].p)));
      mesh.addPolygon(corners.map(function (c) { return c.p; }), corners.map(function (c) { return c.n || fn; }),
        corners.map(function (c) {   // brak UV: rzut wzdluz dominujacej osi normalnej sciany (bez smug)
          if (c.t) return c.t;
          var ax = Math.abs(fn[0]), ay = Math.abs(fn[1]), az = Math.abs(fn[2]);
          return az >= ax && az >= ay ? [c.p[0] * worldScale, c.p[1] * worldScale] : ax >= ay ? [c.p[1] * worldScale, c.p[2] * worldScale] : [c.p[0] * worldScale, c.p[2] * worldScale];
        }));
    }
  });
};

// ===== 04_parts.js =====
// ---------------------------------------------------------------- gotowe elementy (lustro parts.py); opcje w obiekcie na koncu
var STANDARD_MATERIALS = {
  roof: ['roof', 1.7], plaster: ['plaster', 2.4], timber: ['timber', 1.2], planks: ['planks', 1.2], stone: ['stone', 2.0], leaf: ['leaf', 1.0], needle: ['needle', 1.0],
  bark: ['bark', 1.4], thatch: ['thatch', 1.6], dirt: ['dirt', 3.0], metal: ['metal', 1.0], cloth: ['cloth', 0.8],
};
var SOLID_MATERIALS = { glass: [0.05, 0.07, 0.09], iron: [0.12, 0.12, 0.13], rope: [0.55, 0.45, 0.28], foliage_core: [0.035, 0.085, 0.03] };
var TEAM_COLOR = [0.06, 0.16, 0.55];                // stonowany niebieski (maska druzyny nie zalezy od koloru); tylko materialy team*

// Nowy Model ze standardowymi materialami; textures = wynik standardTextures(); teamColor = kolor bazowy druzyny ([r, g, b] liniowo).
// Materialy druzynowe: 'team', 'team_dark' (ciemniejszy), 'team_light' (jasniejszy) - wszystkie trafiaja do maski.
function standardModel(textures, teamColor) {
  var model = new Model(), base = teamColor || TEAM_COLOR;
  Object.keys(STANDARD_MATERIALS).forEach(function (name) { model.material(name, { texture: textures[STANDARD_MATERIALS[name][0]], worldSize: STANDARD_MATERIALS[name][1] }); });
  Object.keys(SOLID_MATERIALS).forEach(function (name) { model.material(name, { color: SOLID_MATERIALS[name] }); });
  model.material('team', { color: base, team: true });
  model.material('team_dark', { color: base.map(function (c) { return 0.55 * c; }), team: true });
  model.material('team_light', { color: base.map(function (c) { return Math.min(1, 1.35 * c); }), team: true });
  return model;
}
function opt(options, key, fallback) { return options && options[key] !== undefined ? options[key] : fallback; }

// halfTimberWall(model, face '+x' | '-y', halfAlong, wallHalfOther, zBottom, zTop, { columns, offset, beamWidth, beamDepth, material })
function halfTimberWall(model, face, halfAlong, wallHalfOther, zBottom, zTop, options) {
  var columns = opt(options, 'columns', 5), offset = opt(options, 'offset', 0.02), beamWidth = opt(options, 'beamWidth', 0.13), beamDepth = opt(options, 'beamDepth', 0.07), material = opt(options, 'material', 'timber');
  var point, normal;
  if (face === '+x') { point = function (along, z) { return [wallHalfOther + offset, along, z]; }; normal = [1, 0, 0]; }
  else { point = function (along, z) { return [along, -wallHalfOther - offset, z]; }; normal = [0, -1, 0]; }
  var middle = (zBottom + zTop) / 2, i;
  for (i = 0; i < columns; i++) { var along = -halfAlong + 2 * halfAlong * i / (columns - 1); model.beam(material, point(along, zBottom), point(along, zTop), beamWidth, beamDepth, normal); }
  [zBottom + 0.04, middle, zTop - 0.06].forEach(function (z) { model.beam(material, point(-halfAlong, z), point(halfAlong, z), beamWidth, beamDepth, normal); });
  model.beam(material, point(-halfAlong, zBottom), point(-halfAlong / 3, middle), 0.1, beamDepth, normal);
  model.beam(material, point(halfAlong, zBottom), point(halfAlong / 3, middle), 0.1, beamDepth, normal);
}
// gableRoof(model, halfX, halfY, zEave, rise, { overhangX, overhangY, material, ridgeMaterial, gableMaterial, gableFrame }) -> z kalenicy
function gableRoof(model, halfX, halfY, zEave, rise, options) {
  var overhangX = opt(options, 'overhangX', 0.25), overhangY = opt(options, 'overhangY', 0.28), material = opt(options, 'material', 'roof');
  var ridge = opt(options, 'ridgeMaterial', 'timber'), gableMaterial = opt(options, 'gableMaterial', 'plaster'), gableFrame = opt(options, 'gableFrame', true);
  var ex = halfX + overhangX, ey = halfY + overhangY, zTop = zEave + rise * (ey / halfY), scale = 1 / model.materials[material].worldSize, slope = Math.hypot(ey, zTop - zEave);
  var roof = model.meshes[material], sign;
  [-1, 1].forEach(function (sg) {
    var n = normalize([0, sg * (zTop - zEave), ey]);
    var points = [[-ex, sg * ey, zEave], [ex, sg * ey, zEave], [ex, 0, zTop], [-ex, 0, zTop]];
    var uvs = [[-ex * scale, 0], [ex * scale, 0], [ex * scale, slope * scale], [-ex * scale, slope * scale]];
    if (sg > 0) { points.reverse(); uvs.reverse(); }
    roof.addPolygon(points, [n, n, n, n], uvs);
  });
  model.box(ridge, [0, 0, zTop + 0.02], [2 * ex + 0.08, 0.20, 0.10]);
  [-1, 1].forEach(function (sg) { model.box(ridge, [0, sg * ey, zEave - 0.02], [2 * ex, 0.08, 0.10]); });
  [-1, 1].forEach(function (sx) {
    var tri = [[sx * halfX, -halfY, zEave + 0.05], [sx * halfX, halfY, zEave + 0.05], [sx * halfX, 0, zEave + 0.05 + rise]], n = [sx, 0, 0];
    var uvs = tri.map(function (p) { return [p[1] / 2.4, p[2] / 2.4]; });
    if (sx < 0) { tri.reverse(); uvs.reverse(); }
    model.meshes[gableMaterial].addPolygon(tri, [n, n, n], uvs);
    if (gableFrame) {
      var z0 = zEave + 0.05, off = sx * (halfX + 0.02);
      [-halfY, halfY].forEach(function (end) { model.beam(ridge, [off, end, z0], [off, 0, z0 + rise], 0.10, 0.06, [sx, 0, 0]); });
      model.beam(ridge, [off, 0, z0], [off, 0, z0 + rise], 0.09, 0.06, [sx, 0, 0]);
      model.beam(ridge, [off, -halfY * 0.55, z0 + rise * 0.33], [off, halfY * 0.55, z0 + rise * 0.33], 0.09, 0.06, [sx, 0, 0]);
    }
  });
  return zTop;
}
// barrel(model, cx, cy, { height, radius, wood, hoop })
function barrel(model, cx, cy, options) {
  var height = opt(options, 'height', 0.6), radius = opt(options, 'radius', 0.28), wood = opt(options, 'wood', 'planks'), hoop = opt(options, 'hoop', 'iron'), s = height / 0.6;
  model.lathe(wood, [cx, cy, 0], [[0, 0], [0.20 * s, 0], [0.25 * s, 0.14 * s], [radius, 0.30 * s], [0.25 * s, 0.46 * s], [0.20 * s, height], [0, height]], 24);
  [[0.10 * s, 0.225 * s], [0.30 * s, radius * 1.007], [0.50 * s, 0.225 * s]].forEach(function (zr) {
    var z = zr[0], r = zr[1];
    model.lathe(hoop, [cx, cy, 0], [[r - 0.005, z - 0.015], [r + 0.012, z - 0.015], [r + 0.012, z + 0.015], [r - 0.005, z + 0.015]], 24);
  });
}
function crate(model, cx, cy, options) { var size = opt(options, 'size', 0.45); model.box(opt(options, 'material', 'planks'), [cx, cy, size / 2], [size, size, size], { rotation: rotZ(opt(options, 'angle', 0)) }); }
// ---- liscie jako geometria (lustro add_leaf / leaf_cluster / bush / tree_oak / tree_pine z parts.py; ten sam mulberry32, te same drzewa)
var SKY_BIAS = 0.35;   // przechylenie normalnych cieniowania ku gorze: spod korony nie robi sie czern
function crownNormal(point, center, flatten) { return normalize([point[0] - center[0], point[1] - center[1], (point[2] - center[2]) * flatten + SKY_BIAS]); }
function randomUnit(rng) { return normalize([rng.normal(), rng.normal(), rng.normal()]); }
var LEAF_OUTLINE = [[0.25, 0.85], [0.60, 1.0]];   // (polozenie wzdluz liscia, polowa szerokosci wzgledem width / 2)
// addLeaf(model, material, base, axis, length, width, shadeCenter, flatten, shadeWeight, rng): pojedynczy lisc (6 wierzcholkow, zgiety wzdluz zylki);
// normalne cieniowania mieszane z normalna "kuli" korony, wiec kepy cieniuja sie jak bryly
function addLeaf(model, material, base, axis, length, width, shadeCenter, flatten, shadeWeight, rng) {
  axis = normalize(axis);
  var side = cross(axis, randomUnit(rng));
  if (dot(side, side) < 1e-6) side = cross(axis, [1, 0, 0]);
  side = normalize(side);
  var facing = cross(side, axis), uvU = rng.uniform(0, 1), uvV = rng.uniform(0, 1), lift = mul(facing, 0.18 * width);
  var corners = [base], tilts = [0], i, o, point, back = [LEAF_OUTLINE[1], LEAF_OUTLINE[0]];
  for (i = 0; i < 2; i++) { o = LEAF_OUTLINE[i]; point = add(add(base, mul(axis, o[0] * length)), add(mul(side, 0.5 * width * o[1]), lift)); corners.push(point); tilts.push(0.35 * o[1]); }
  corners.push(add(base, mul(axis, length))); tilts.push(0);
  for (i = 0; i < 2; i++) { o = back[i]; point = add(add(base, mul(axis, o[0] * length)), add(mul(side, -0.5 * width * o[1]), lift)); corners.push(point); tilts.push(-0.35 * o[1]); }
  facing = dot(facing, crownNormal(base, shadeCenter, flatten)) >= 0 ? facing : mul(facing, -1);
  var normals = corners.map(function (corner, k) {
    var outward = crownNormal(corner, shadeCenter, flatten), leafNormal = normalize(add(facing, mul(side, tilts[k])));
    return normalize(add(mul(leafNormal, 1 - shadeWeight), mul(outward, shadeWeight)));
  });
  var uvs = [[uvU, uvV - 0.04]];
  for (i = 0; i < 2; i++) uvs.push([uvU + 0.025 * LEAF_OUTLINE[i][1], uvV - 0.04 + 0.08 * LEAF_OUTLINE[i][0]]);
  uvs.push([uvU, uvV + 0.04]);
  for (i = 0; i < 2; i++) uvs.push([uvU - 0.025 * back[i][1], uvV - 0.04 + 0.08 * back[i][0]]);
  model.meshes[material].addPolygon(corners, normals, uvs);
}
// leafCluster(model, material, center, radii, count, shadeCenter, flatten, lengthRange, rng, { outwardBias, minZ, shadeWeight })
function leafCluster(model, material, center, radii, count, shadeCenter, flatten, lengthRange, rng, options) {
  var outwardBias = opt(options, 'outwardBias', 0.9), minZ = opt(options, 'minZ', 0), shadeWeight = opt(options, 'shadeWeight', 0.75);
  for (var n = 0; n < count; n++) {
    var direction = randomUnit(rng), fraction = Math.pow(rng(), 1 / 3);
    var position = [center[0] + direction[0] * radii[0] * fraction, center[1] + direction[1] * radii[1] * fraction, Math.max(center[2] + direction[2] * radii[2] * fraction, minZ)];
    var outward = normalize([position[0] - shadeCenter[0], position[1] - shadeCenter[1], (position[2] - shadeCenter[2]) * flatten]);
    var axis = normalize(add(add(mul(outward, outwardBias), mul(randomUnit(rng), 0.9)), [0, 0, 0.25]));
    var length = rng.uniform(lengthRange[0], lengthRange[1]);
    addLeaf(model, material, position, axis, length, length * rng.uniform(0.55, 0.78), shadeCenter, flatten, shadeWeight, rng);
  }
}
// bush(model, cx, cy, { radius, seed, material }): ciemny rdzen + kepa pojedynczych lisci
function bush(model, cx, cy, options) {
  var r = opt(options, 'radius', 0.45), seed = opt(options, 'seed', 0), material = opt(options, 'material', 'leaf'), rng = makeRng(seed * 5 + 3), center = [cx, cy, r * 0.72];
  model.blob('foliage_core', [cx, cy, r * 0.7], [r * 0.72, r * 0.72, r * 0.58], { seed: seed, roughness: 0.15, subdivisions: 2 });
  leafCluster(model, material, center, [r * 0.92, r * 0.92, r * 0.72], Math.floor(60 + 260 * r), center, 1.0, [0.09 + 0.12 * r, 0.14 + 0.17 * r], rng, { minZ: 0.03 });
}
function pennant(model, x, y, zBase, options) {
  var height = opt(options, 'height', 0.95), material = opt(options, 'material', 'team'), pole = opt(options, 'pole', 'timber'), dir = opt(options, 'direction', 1);
  model.beam(pole, [x, y, zBase], [x, y, zBase + height], 0.05, 0.05, [1, 0, 0]);
  model.box(material, [x, y + 0.2 * dir, zBase + height - 0.17], [0.015, 0.5, 0.26]);
  model.box(material, [x, y + 0.54 * dir, zBase + height - 0.17], [0.015, 0.2, 0.17]);
}
// wheel(model, center, { radius, thickness, spokes, axis 'y' | 'x', wood, metal })
function wheel(model, center, options) {
  var radius = opt(options, 'radius', 0.4), thickness = opt(options, 'thickness', 0.12), spokes = opt(options, 'spokes', 6), axis = opt(options, 'axis', 'y'), wood = opt(options, 'wood', 'planks'), metal = opt(options, 'metal', 'iron');
  var rotation = axis === 'y' ? rotX(Math.PI / 2) : rotY(Math.PI / 2), t2 = thickness / 2;
  model.lathe(wood, center, [[radius - 0.06, -t2], [radius, -t2], [radius, t2], [radius - 0.06, t2], [radius - 0.06, -t2]], 28, { rotation: rotation, caps: false });
  model.lathe(wood, center, [[0, -thickness * 0.7], [0.09, -thickness * 0.7], [0.09, thickness * 0.7], [0, thickness * 0.7]], 16, { rotation: rotation });
  var normal = matVec(rotation, [0, 0, 1]);
  for (var k = 0; k < spokes; k++) {
    var angle = Math.PI * k / spokes, dir = matVec(rotation, [Math.cos(angle), Math.sin(angle), 0]);
    model.beam(wood, sub(center, mul(dir, radius - 0.05)), add(center, mul(dir, radius - 0.05)), 0.05, thickness * 0.6, normal);
  }
  model.lathe(metal, center, [[radius - 0.02, -t2 - 0.01], [radius + 0.015, -t2 - 0.01], [radius + 0.015, t2 + 0.01], [radius - 0.02, t2 + 0.01], [radius - 0.02, -t2 - 0.01]], 28, { rotation: rotation, caps: false });
}
// roundTower(model, cx, cy, { radius, height, battlementCount, roof, wall, roofMaterial }) -> z szczytu
function roundTower(model, cx, cy, options) {
  var radius = opt(options, 'radius', 0.9), height = opt(options, 'height', 3.4), count = opt(options, 'battlementCount', 12), roof = opt(options, 'roof', true), wall = opt(options, 'wall', 'stone'), roofMaterial = opt(options, 'roofMaterial', 'roof');
  model.lathe(wall, [cx, cy, 0], [[radius + 0.12, 0], [radius + 0.12, 0.35], [radius + 0.02, 0.45], [radius, height]], 36);
  model.lathe(wall, [cx, cy, 0], [[radius + 0.16, height], [radius + 0.16, height + 0.14], [radius, height + 0.14]], 36);
  var top = height + 0.14;
  if (roof) { model.lathe(roofMaterial, [cx, cy, top], [[radius + 0.28, 0], [radius + 0.28, 0.06], [radius * 0.12, 1.35], [0, 1.40]], 36); return top + 1.40; }
  for (var k = 0; k < count; k++) {
    var angle = 2 * Math.PI * k / count;
    model.box(wall, [cx + (radius + 0.08) * Math.cos(angle), cy + (radius + 0.08) * Math.sin(angle), top + 0.2], [0.28, 0.2, 0.4], { rotation: rotZ(angle + Math.PI / 2) });
  }
  return top + 0.4;
}
function log(model, p0, p1, options) { model.cylinder(opt(options, 'material', 'bark'), p0, p1, opt(options, 'radius', 0.09), null, 14); }
// palisade(model, p0, p1, { height, spacing, radius, material, seed })
function palisade(model, p0, p1, options) {
  var height = opt(options, 'height', 1.1), spacing = opt(options, 'spacing', 0.17), radius = opt(options, 'radius', 0.085), material = opt(options, 'material', 'bark'), rng = makeRng(opt(options, 'seed', 0) + 7);
  p0 = [p0[0], p0[1], 0]; p1 = [p1[0], p1[1], 0];   // punkty podajemy jako [x, y]
  var count = Math.max(2, Math.floor(length(sub(p1, p0)) / spacing));
  for (var k = 0; k <= count; k++) {
    var pos = add(p0, mul(sub(p1, p0), k / count)), h = height * rng.uniform(0.9, 1.1);
    model.lathe(material, [pos[0], pos[1], 0], [[0, 0], [radius, 0], [radius, h - 0.16], [0.012, h], [0, h]], 10);
  }
}
// treeOak(model, cx, cy, { height, crown, seed, trunk, leaf }): drzewo lisciaste - pochylony pien, 5 konarow z odgalezieniami i ~2500 pojedynczych lisci w kepach
function treeOak(model, cx, cy, options) {
  var height = opt(options, 'height', 2.4), crown = opt(options, 'crown', 1.0), seed = opt(options, 'seed', 0), trunk = opt(options, 'trunk', 'bark'), leaf = opt(options, 'leaf', 'leaf');
  var rng = makeRng(seed * 7 + 13), topZ = 0.42 * height, crownZ = 0.70 * height, crownRy = Math.max(0.35, (height - crownZ) * 0.95), flatten = crown / crownRy, crownCenter = [cx, cy, crownZ];
  var leanAngle = rng.uniform(0, 2 * Math.PI), lean = 0.05 * crown, trunkPoints = [], k, index;
  for (k = 0; k < 4; k++) trunkPoints.push([cx + Math.cos(leanAngle) * lean * Math.pow(k / 3, 2), cy + Math.sin(leanAngle) * lean * Math.pow(k / 3, 2), topZ * k / 3]);
  var trunkRadii = [0.13, 0.095, 0.078, 0.066];
  for (k = 0; k < 3; k++) model.cylinder(trunk, trunkPoints[k], trunkPoints[k + 1], trunkRadii[k], trunkRadii[k + 1], 10);
  var anchors = [], azimuthStart = rng.uniform(0, 2 * Math.PI);
  for (index = 0; index < 5; index++) {
    var azimuth = azimuthStart + index * (2 * Math.PI / 5) + rng.uniform(-0.35, 0.35), elevation = rng.uniform(0.55, 0.95), length = crown * rng.uniform(0.75, 1.0);
    var direction = [Math.cos(azimuth) * Math.cos(elevation), Math.sin(azimuth) * Math.cos(elevation), Math.sin(elevation)];
    var start = [trunkPoints[3][0], trunkPoints[3][1], topZ * rng.uniform(0.85, 1.0)];
    var middle = add(add(start, mul(direction, length * 0.5)), [0, 0, 0.06]), end = add(add(start, mul(direction, length)), [0, 0, 0.10]);
    model.cylinder(trunk, start, middle, 0.07, 0.05, 7);
    model.cylinder(trunk, middle, end, 0.05, 0.025, 7);
    anchors.push([end, 1.0, 130]);
    anchors.push([add(middle, [0, 0, 0.15]), 0.8, 80]);
    [-1, 1].forEach(function (sign) {
      var twigAzimuth = azimuth + sign * rng.uniform(0.5, 0.95), twigElevation = elevation + rng.uniform(-0.05, 0.45), twigLength = crown * rng.uniform(0.35, 0.5);
      var twigDirection = [Math.cos(twigAzimuth) * Math.cos(twigElevation), Math.sin(twigAzimuth) * Math.cos(twigElevation), Math.sin(twigElevation)];
      var twigEnd = add(middle, mul(twigDirection, twigLength));
      model.cylinder(trunk, middle, twigEnd, 0.035, 0.015, 6);
      anchors.push([twigEnd, 0.9, 120]);
    });
  }
  for (index = 0; index < 2; index++) anchors.push([[cx + rng.uniform(-0.2, 0.2) * crown, cy + rng.uniform(-0.2, 0.2) * crown, crownZ + crownRy * rng.uniform(0.55, 0.8)], 1.0, 130]);
  var shellCount = 18;
  for (index = 0; index < shellCount; index++) {
    var shellZ = 1 - (index + 0.5) * 2 / shellCount, shellRing = Math.sqrt(Math.max(0, 1 - shellZ * shellZ)), shellPhi = index * Math.PI * (3 - Math.sqrt(5)) + azimuthStart;
    anchors.push([[cx + Math.cos(shellPhi) * shellRing * crown * 0.74, cy + Math.sin(shellPhi) * shellRing * crown * 0.74, crownZ + shellZ * crownRy * 0.78], 0.85, 90]);
  }
  model.blob('foliage_core', [cx, cy, crownZ - 0.1], [crown * 0.42, crown * 0.42, crownRy * 0.4], { seed: seed, roughness: 0.12, subdivisions: 2 });
  var clusterRadius = crown * 0.36;
  anchors.forEach(function (a) {
    var scale = a[1];
    leafCluster(model, leaf, a[0], [clusterRadius * scale, clusterRadius * scale, clusterRadius * scale * 0.75], a[2], crownCenter, flatten, [0.11 * crown, 0.18 * crown], rng, { minZ: topZ * 0.8 });
  });
}
// treePine(model, cx, cy, { height, baseRadius, tiers, trunk, leaf, seed }): swierk - cienki pien, pietra opadajacych galezi z pekami igliwia i ciemny stozkowy rdzen
function treePine(model, cx, cy, options) {
  var height = opt(options, 'height', 3.2), base = opt(options, 'baseRadius', 0.85), tiers = opt(options, 'tiers', 5), trunk = opt(options, 'trunk', 'bark'), leaf = opt(options, 'leaf', 'needle'), seed = opt(options, 'seed', 0);
  var rng = makeRng(seed * 11 + 5);
  model.cylinder(trunk, [cx, cy, 0], [cx, cy, height * 0.9], 0.13, 0.035, 9);
  for (var tier = 0; tier < tiers; tier++) {
    var fraction = tier / tiers, tierZ = height * (0.20 + 0.70 * fraction), tierRadius = base * (1 - 0.80 * fraction), branchCount = Math.max(7, 12 - tier), azimuthOffset = rng.uniform(0, 2 * Math.PI);
    model.lathe('foliage_core', [cx, cy, tierZ], [[0.42 * tierRadius, -0.02 * height], [0.20 * tierRadius, 0.09 * height], [0.02 * tierRadius, 0.20 * height]], 12);
    var shadeCenter = [cx, cy, tierZ + 0.05 * height];
    for (var index = 0; index < branchCount; index++) {
      var azimuth = azimuthOffset + index * (2 * Math.PI / branchCount) + rng.uniform(-0.18, 0.18), droop = rng.uniform(0.25, 0.45) + 0.1 * (1 - fraction);
      var direction = normalize([Math.cos(azimuth), Math.sin(azimuth), -droop]), length = tierRadius * rng.uniform(0.85, 1.05), start = [cx, cy, tierZ];
      var tip = add(add(start, mul(direction, length)), [0, 0, 0.08 * length]);
      model.cylinder(trunk, start, tip, 0.025, 0.01, 5);
      for (var card = 0; card < 44; card++) {
        var along = rng.uniform(0.05, 1.0), cardBase = add(start, mul(sub(tip, start), along)), spread = rng.uniform(-0.75, 0.75), cardAzimuth = azimuth + spread;
        var cardAxis = [Math.cos(cardAzimuth) * Math.cos(0.25), Math.sin(cardAzimuth) * Math.cos(0.25), -Math.sin(0.25) + rng.uniform(-0.05, 0.4)];
        var cardLength = rng.uniform(0.22, 0.36) * (0.55 + 0.45 * tierRadius / base);
        addLeaf(model, leaf, cardBase, cardAxis, cardLength, cardLength * 0.32, shadeCenter, 1.6, 0.42, rng);
      }
    }
  }
  for (var n = 0; n < 8; n++) addLeaf(model, leaf, [cx, cy, height * 0.9], [rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 1.0], 0.22 * height / 3.2, 0.06, [cx, cy, height * 0.75], 1.0, 0.5, rng);
}

// ===== 05_camera_raster.js =====
// ---------------------------------------------------------------- kamera i rasteryzacja (z-bufor, shadow mapy)

// Camera({ tilePx = 96, halfExtent = 3.6, supersample = 2, target = [0,0,1], elevationDeg = 30, azimuthDeg = 45 })
// Rzut 2:1; ekran: prawo = (+x,+y); widoczne sciany +x (prawa, oswietlona) i -y (lewa, w cieniu); glebokosc: im wieksze x - y, tym blizej kamery.
function Camera(options) {
  options = options || {};
  this.tilePx = options.tilePx || TILE_PX; this.halfExtent = options.halfExtent || 3.6; this.supersample = options.supersample || 2;
  this.target = options.target || [0, 0, 1.0]; this.elevationDeg = options.elevationDeg === undefined ? 30 : options.elevationDeg; this.azimuthDeg = options.azimuthDeg === undefined ? 45 : options.azimuthDeg;
  this.ppu = this.tilePx / Math.SQRT2;
  var el = this.elevationDeg * Math.PI / 180, az = this.azimuthDeg * Math.PI / 180;
  var toCamera = [Math.cos(el) * Math.cos(az), -Math.cos(el) * Math.sin(az), Math.sin(el)];
  this.toCamera = toCamera; this.forward = mul(toCamera, -1);
  this.right = normalize(cross(this.forward, [0, 0, 1])); this.up = cross(this.right, this.forward);
  this.size = Math.round(this.ppu * 2 * this.halfExtent); this.film = this.size * this.supersample;
}
Camera.prototype.rotated = function (angleDeg) {
  return new Camera({ tilePx: this.tilePx, halfExtent: this.halfExtent, supersample: this.supersample, target: this.target, elevationDeg: this.elevationDeg, azimuthDeg: this.azimuthDeg + angleDeg });
};
// punkt swiata -> piksel obrazu wyjsciowego [x, y]
Camera.prototype.project = function (point) {
  var d = sub(point, this.target);
  return [this.size / 2 + dot(d, this.right) * this.ppu, this.size / 2 - dot(d, this.up) * this.ppu];
};

// ---- tekstury: mipmapy w przestrzeni liniowej
function textureMips(tex) {
  if (tex._mips) return tex._mips;
  var size = tex.size, level0 = new Float32Array(size * size * 3);
  for (var i = 0; i < level0.length; i++) level0[i] = srgbToLinear(tex.data[i]);
  var mips = [{ size: size, data: level0 }];
  while (mips[mips.length - 1].size > 1) {
    var prev = mips[mips.length - 1], s = prev.size / 2, data = new Float32Array(s * s * 3);
    for (var y = 0; y < s; y++) for (var x = 0; x < s; x++) for (var c = 0; c < 3; c++)
      data[(y * s + x) * 3 + c] = (prev.data[((2 * y) * prev.size + 2 * x) * 3 + c] + prev.data[((2 * y) * prev.size + 2 * x + 1) * 3 + c] + prev.data[((2 * y + 1) * prev.size + 2 * x) * 3 + c] + prev.data[((2 * y + 1) * prev.size + 2 * x + 1) * 3 + c]) / 4;
    mips.push({ size: s, data: data });
  }
  tex._mips = mips;
  return mips;
}
function sampleTexture(mips, u, v, lod, out) {
  var level = clamp(Math.round(lod), 0, mips.length - 1), m = mips[level], s = m.size, d = m.data;
  var x = u * s - 0.5, y = v * s - 0.5, x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
  var xa = ((x0 % s) + s) % s, xb = (xa + 1) % s, ya = ((y0 % s) + s) % s, yb = (ya + 1) % s;
  var i00 = (ya * s + xa) * 3, i10 = (ya * s + xb) * 3, i01 = (yb * s + xa) * 3, i11 = (yb * s + xb) * 3;
  for (var c = 0; c < 3; c++) out[c] = (d[i00 + c] * (1 - fx) + d[i10 + c] * fx) * (1 - fy) + (d[i01 + c] * (1 - fx) + d[i11 + c] * fx) * fy;
}
function textureMeanLinear(tex) { var m = textureMips(tex), top = m[m.length - 1].data; return [top[0], top[1], top[2]]; }

// ---- zbieranie trojkatow modelu
function collectTriangles(model) {
  var names = Object.keys(model.meshes).filter(function (n) { return model.meshes[n].faces.length > 0; }), count = 0;
  names.forEach(function (n) { count += model.meshes[n].faces.length; });
  var tris = { count: count, pos: new Float32Array(count * 9), nrm: new Float32Array(count * 9), uv: new Float32Array(count * 6), mat: new Int16Array(count), materials: [] }, t = 0;
  names.forEach(function (name, mi) {
    var def = model.materials[name], mesh = mesh0(model, name);
    tris.materials.push({ name: name, mips: def.texture ? textureMips(def.texture) : null, color: def.color || [0.5, 0.5, 0.5], team: def.team });
    mesh.faces.forEach(function (f) {
      for (var k = 0; k < 3; k++) {
        var p = mesh.positions[f[k]], n = mesh.normals[f[k]], uv = mesh.uvs[f[k]];
        tris.pos.set(p, t * 9 + k * 3); tris.nrm.set(n, t * 9 + k * 3); tris.uv[t * 6 + k * 2] = uv[0]; tris.uv[t * 6 + k * 2 + 1] = uv[1];
      }
      tris.mat[t++] = mi;
    });
  });
  return tris;
}
function mesh0(model, name) { return model.meshes[name]; }
function boundingSphere(tris) {
  var lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (var i = 0; i < tris.count * 3; i++) for (var c = 0; c < 3; c++) { var v = tris.pos[i * 3 + c]; if (v < lo[c]) lo[c] = v; if (v > hi[c]) hi[c] = v; }
  var center = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
  return { center: center, radius: length(sub(hi, lo)) / 2 + 0.05 };
}

// ---- bufor geometrii z kamery (z-bufor, atrybuty na subpiksel)
function rasterizeGBuffer(tris, cam) {
  var W = cam.film, N = W * W, scale = cam.ppu * cam.supersample, half = W / 2;
  var g = { size: W, depth: new Float32Array(N).fill(Infinity), mat: new Int16Array(N).fill(-1), nrm: new Float32Array(N * 3), alb: new Float32Array(N * 3) };
  var r = cam.right, u = cam.up, f = cam.forward, tg = cam.target, tc = cam.toCamera, tmp = [0, 0, 0];
  var sx = [0, 0, 0], sy = [0, 0, 0], sz = [0, 0, 0];
  for (var t = 0; t < tris.count; t++) {
    var o = t * 9;
    for (var k = 0; k < 3; k++) {
      var dx = tris.pos[o + k * 3] - tg[0], dy = tris.pos[o + k * 3 + 1] - tg[1], dz = tris.pos[o + k * 3 + 2] - tg[2];
      sx[k] = half + (dx * r[0] + dy * r[1] + dz * r[2]) * scale; sy[k] = half - (dx * u[0] + dy * u[1] + dz * u[2]) * scale; sz[k] = dx * f[0] + dy * f[1] + dz * f[2];
    }
    var area2 = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0]);
    if (Math.abs(area2) < 1e-9) continue;
    var minX = Math.max(0, Math.floor(Math.min(sx[0], sx[1], sx[2]) - 0.5)), maxX = Math.min(W - 1, Math.ceil(Math.max(sx[0], sx[1], sx[2]) + 0.5));
    var minY = Math.max(0, Math.floor(Math.min(sy[0], sy[1], sy[2]) - 0.5)), maxY = Math.min(W - 1, Math.ceil(Math.max(sy[0], sy[1], sy[2]) + 0.5));
    var mdef = tris.materials[tris.mat[t]], lod = 0;
    var u0 = tris.uv[t * 6], v0 = tris.uv[t * 6 + 1], u1 = tris.uv[t * 6 + 2], v1 = tris.uv[t * 6 + 3], u2 = tris.uv[t * 6 + 4], v2 = tris.uv[t * 6 + 5];
    if (mdef.mips) {
      var uvArea = Math.abs((u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0)) / 2, texels = uvArea * mdef.mips[0].size * mdef.mips[0].size, pixels = Math.abs(area2) / 2;
      lod = texels > pixels ? 0.5 * Math.log(texels / pixels) / Math.LN2 : 0;
    }
    var inv = 1 / area2;
    for (var y = minY; y <= maxY; y++) for (var x = minX; x <= maxX; x++) {
      var px = x + 0.5, py = y + 0.5;
      var w0 = ((sx[2] - sx[1]) * (py - sy[1]) - (sy[2] - sy[1]) * (px - sx[1])) * inv, w1 = ((sx[0] - sx[2]) * (py - sy[2]) - (sy[0] - sy[2]) * (px - sx[2])) * inv, w2 = 1 - w0 - w1;
      if (w0 < 0 || w1 < 0 || w2 < 0) continue;
      var idx = y * W + x, z = w0 * sz[0] + w1 * sz[1] + w2 * sz[2];
      if (z >= g.depth[idx]) continue;
      g.depth[idx] = z; g.mat[idx] = tris.mat[t];
      var nx = w0 * tris.nrm[o] + w1 * tris.nrm[o + 3] + w2 * tris.nrm[o + 6], ny = w0 * tris.nrm[o + 1] + w1 * tris.nrm[o + 4] + w2 * tris.nrm[o + 7], nz = w0 * tris.nrm[o + 2] + w1 * tris.nrm[o + 5] + w2 * tris.nrm[o + 8];
      var nl = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1; nx /= nl; ny /= nl; nz /= nl;
      if (nx * tc[0] + ny * tc[1] + nz * tc[2] < 0) { nx = -nx; ny = -ny; nz = -nz; }   // material dwustronny: normalna zwrocona ku kamerze
      g.nrm[idx * 3] = nx; g.nrm[idx * 3 + 1] = ny; g.nrm[idx * 3 + 2] = nz;
      if (mdef.mips) { sampleTexture(mdef.mips, w0 * u0 + w1 * u1 + w2 * u2, w0 * v0 + w1 * v1 + w2 * v2, lod, tmp); g.alb[idx * 3] = tmp[0]; g.alb[idx * 3 + 1] = tmp[1]; g.alb[idx * 3 + 2] = tmp[2]; }
      else { g.alb[idx * 3] = mdef.color[0]; g.alb[idx * 3 + 1] = mdef.color[1]; g.alb[idx * 3 + 2] = mdef.color[2]; }
    }
  }
  return g;
}

// ---- mapa glebokosci z kierunku swiatla (dir = jednostkowy wektor ku zrodlu); przechowuje najwieksze w = dot(p - srodek, dir)
function buildDepthMap(tris, dir, sphere, res) {
  var helper = Math.abs(dir[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0], u = normalize(cross(dir, helper)), v = cross(dir, u);
  var map = { res: res, dir: dir, u: u, v: v, center: sphere.center, radius: sphere.radius, depth: new Float32Array(res * res).fill(-Infinity), texel: 2 * sphere.radius / res };
  var s = res / (2 * sphere.radius), c = sphere.center, sx = [0, 0, 0], sy = [0, 0, 0], sw = [0, 0, 0];
  for (var t = 0; t < tris.count; t++) {
    var o = t * 9;
    for (var k = 0; k < 3; k++) {
      var dx = tris.pos[o + k * 3] - c[0], dy = tris.pos[o + k * 3 + 1] - c[1], dz = tris.pos[o + k * 3 + 2] - c[2];
      sx[k] = res / 2 + (dx * u[0] + dy * u[1] + dz * u[2]) * s; sy[k] = res / 2 + (dx * v[0] + dy * v[1] + dz * v[2]) * s; sw[k] = dx * dir[0] + dy * dir[1] + dz * dir[2];
    }
    var area2 = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0]);
    if (Math.abs(area2) < 1e-9) continue;
    var inv = 1 / area2, minX = Math.max(0, Math.floor(Math.min(sx[0], sx[1], sx[2]) - 1)), maxX = Math.min(res - 1, Math.ceil(Math.max(sx[0], sx[1], sx[2]) + 1));
    var minY = Math.max(0, Math.floor(Math.min(sy[0], sy[1], sy[2]) - 1)), maxY = Math.min(res - 1, Math.ceil(Math.max(sy[0], sy[1], sy[2]) + 1));
    // tolerancja barycentryczna ~0.5 piksela mapy od krawedzi (cienkie trojkaty nie znikaja)
    var e0 = Math.hypot(sx[2] - sx[1], sy[2] - sy[1]), e1 = Math.hypot(sx[0] - sx[2], sy[0] - sy[2]), e2 = Math.hypot(sx[1] - sx[0], sy[1] - sy[0]), a = Math.abs(area2);
    var tol0 = -0.5 * e0 / a, tol1 = -0.5 * e1 / a, tol2 = -0.5 * e2 / a;
    for (var y = minY; y <= maxY; y++) for (var x = minX; x <= maxX; x++) {
      var px = x + 0.5, py = y + 0.5;
      var w0 = ((sx[2] - sx[1]) * (py - sy[1]) - (sy[2] - sy[1]) * (px - sx[1])) * inv, w1 = ((sx[0] - sx[2]) * (py - sy[2]) - (sy[0] - sy[2]) * (px - sx[2])) * inv, w2 = 1 - w0 - w1;
      if (w0 < tol0 || w1 < tol1 || w2 < tol2) continue;
      var idx = y * res + x, wi = w0 * sw[0] + w1 * sw[1] + w2 * sw[2];   // poza trojkatem (dylatacja o ~0.5 teksela) glebokosc jest ekstrapolowana liniowo
      if (wi > map.depth[idx]) map.depth[idx] = wi;
    }
  }
  return map;
}
// 1 gdy punkt p widzi zrodlo (nic blizej zrodla w mapie), 0 w cieniu; punkty poza mapa sa widoczne
function mapVisibility(map, p, bias) {
  var dx = p[0] - map.center[0], dy = p[1] - map.center[1], dz = p[2] - map.center[2], s = map.res / (2 * map.radius);
  var x = Math.floor(map.res / 2 + (dx * map.u[0] + dy * map.u[1] + dz * map.u[2]) * s), y = Math.floor(map.res / 2 + (dx * map.v[0] + dy * map.v[1] + dz * map.v[2]) * s);
  if (x < 0 || y < 0 || x >= map.res || y >= map.res) return 1;
  return (dx * map.dir[0] + dy * map.dir[1] + dz * map.dir[2]) >= map.depth[y * map.res + x] - bias ? 1 : 0;
}
function mapVisibilityPcf(map, p, bias) {
  var dx = p[0] - map.center[0], dy = p[1] - map.center[1], dz = p[2] - map.center[2], s = map.res / (2 * map.radius);
  var fx = map.res / 2 + (dx * map.u[0] + dy * map.u[1] + dz * map.u[2]) * s, fy = map.res / 2 + (dx * map.v[0] + dy * map.v[1] + dz * map.v[2]) * s;
  var w = dx * map.dir[0] + dy * map.dir[1] + dz * map.dir[2], sum = 0, count = 0, x0 = Math.floor(fx - 0.5), y0 = Math.floor(fy - 0.5), res = map.res;
  // 2x2 z wagami dwuliniowymi na pol-teksel: miekka krawedz bez ziarna
  var ax = fx - 0.5 - x0, ay = fy - 0.5 - y0;
  for (var j = 0; j < 2; j++) for (var i = 0; i < 2; i++) {
    var x = x0 + i, y = y0 + j, wt = (i ? ax : 1 - ax) * (j ? ay : 1 - ay);
    if (x < 0 || y < 0 || x >= res || y >= res) { sum += wt; count += wt; continue; }
    sum += wt * (w >= map.depth[y * res + x] - bias ? 1 : 0); count += wt;
  }
  return sum / (count || 1);
}

// ===== 06_render.js =====
// ---------------------------------------------------------------- oswietlenie, tonemapping, renderSprite

// Obraz: { width, height, channels, data: Uint8Array } (RGBA = 4, RGB = 3, maska = 1)
function makeImage(width, height, channels) { return { width: width, height: height, channels: channels, data: new Uint8Array(width * height * channels) }; }

function tonemapChannel(x, exposure, contrast, saturationLuma) {   // jak tonemap() w rtskit3d/render.py (bez saturacji; ta jest na trojce)
  x = Math.max(x * exposure, 0); x = x / (1 + 0.12 * x);
  x = Math.pow(Math.min(Math.max(x, 0), 1), 1 / 2.2);
  return Math.min(Math.max((x - 0.5) * contrast + 0.5, 0), 1);
}
function tonemapRgb(r, g, b, exposure, out, o) {
  var x = tonemapChannel(r, exposure, 1.10), y = tonemapChannel(g, exposure, 1.10), z = tonemapChannel(b, exposure, 1.10);
  var l = x * LUMA[0] + y * LUMA[1] + z * LUMA[2], sat = 1.12;
  out[o] = Math.min(Math.max(l + (x - l) * sat, 0), 1); out[o + 1] = Math.min(Math.max(l + (y - l) * sat, 0), 1); out[o + 2] = Math.min(Math.max(l + (z - l) * sat, 0), 1);
}

function gaussianKernel(sigma) {
  var radius = Math.max(1, Math.ceil(sigma * 3)), k = new Float32Array(2 * radius + 1), sum = 0;
  for (var i = -radius; i <= radius; i++) { k[i + radius] = Math.exp(-i * i / (2 * sigma * sigma)); sum += k[i + radius]; }
  for (var j = 0; j < k.length; j++) k[j] /= sum;
  return k;
}
function gaussianBlur(data, w, h, ch, sigma) {
  var k = gaussianKernel(sigma), r = (k.length - 1) / 2, tmp = new Float32Array(data.length), out = new Float32Array(data.length);
  for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) for (var c = 0; c < ch; c++) {
    var s = 0;
    for (var i = -r; i <= r; i++) { var xx = Math.min(Math.max(x + i, 0), w - 1); s += data[(y * w + xx) * ch + c] * k[i + r]; }
    tmp[(y * w + x) * ch + c] = s;
  }
  for (var y2 = 0; y2 < h; y2++) for (var x2 = 0; x2 < w; x2++) for (var c2 = 0; c2 < ch; c2++) {
    var s2 = 0;
    for (var j = -r; j <= r; j++) { var yy = Math.min(Math.max(y2 + j, 0), h - 1); s2 += tmp[(yy * w + x2) * ch + c2] * k[j + r]; }
    out[(y2 * w + x2) * ch + c2] = s2;
  }
  return out;
}
function boxDownsample(data, w, ch, factor, outSize) {   // usrednianie blokow factor x factor (w jest szerokoscia zrodla)
  var out = new Float32Array(outSize * outSize * ch), inv = 1 / (factor * factor);
  for (var y = 0; y < outSize; y++) for (var x = 0; x < outSize; x++) for (var c = 0; c < ch; c++) {
    var s = 0;
    for (var j = 0; j < factor; j++) for (var i = 0; i < factor; i++) s += data[((y * factor + j) * w + x * factor + i) * ch + c];
    out[(y * outSize + x) * ch + c] = s * inv;
  }
  return out;
}

// Rownomierny rozklad kierunkow na sferze (spirala Fibonacciego)
function sphereDirections(count) {
  var dirs = [], golden = Math.PI * (3 - Math.sqrt(5));
  for (var i = 0; i < count; i++) {
    var z = 1 - (i + 0.5) * 2 / count, r = Math.sqrt(Math.max(0, 1 - z * z)), phi = i * golden;
    dirs.push([r * Math.cos(phi), r * Math.sin(phi), z]);
  }
  return dirs;
}

// Parametry oswietlenia przyblizajace sciezkowy render (patrz references/backends.md)
var LIGHTING = { skyDirections: 96, skyMapRes: 320, sunMapRes: 2048, groundAlbedo: 0.16, bounce: 0.85, fill: 0.10, groundFill: 1.0, shadowSigma: 0.6 };

// Ground: tekstura planarna 3 jednostki na kafel (jak w wersji Mitsuba)
function groundAlbedoAt(groundTex, x, y, lod, out) {
  sampleTexture(groundTex.mips, (x + 40) / 3, (y + 40) / 3, lod, out);
}

// Zbiera swiatlo: przygotowuje mapy glebokosci slonca i nieba
function prepareLighting(tris, sunDir, params) {
  var sphere = boundingSphere(tris), toSun = normalize(mul(sunDir, -1));
  var sunMap = buildDepthMap(tris, toSun, sphere, params.sunMapRes);
  var all = sphereDirections(params.skyDirections), upper = [];
  all.forEach(function (d) { if (d[2] > 0.02) upper.push(d); });
  var skyMaps = upper.map(function (d) { return buildDepthMap(tris, d, sphere, params.skyMapRes); });
  return { sphere: sphere, toSun: toSun, sunMap: sunMap, allDirs: all, skyMaps: skyMaps, params: params };
}

// Luma sloneczna/niebieska irradiancja na poziomej powierzchni (do cienia na gruncie i odbicia od gruntu)
function groundIrradiance(toSun, sunColor, skyColor) {
  var cosS = Math.max(toSun[2], 0), sun = [sunColor[0] * cosS / Math.PI, sunColor[1] * cosS / Math.PI, sunColor[2] * cosS / Math.PI];
  return { sun: sun, sky: skyColor.slice(), total: [sun[0] + skyColor[0], sun[1] + skyColor[1], sun[2] + skyColor[2]] };
}

// Cieniowanie bufora geometrii (promieniowanie liniowe RGB na subpiksel)
function shadeGBuffer(g, tris, cam, light, sunColor, skyColor) {
  var W = g.size, N = W * W, params = light.params, out = new Float32Array(N * 3), team = new Uint8Array(N);
  var half = W / 2, scale = cam.ppu * cam.supersample, tg = cam.target, r = cam.right, u = cam.up, f = cam.forward;
  var toSun = light.toSun, sunMap = light.sunMap, skyMaps = light.skyMaps, nSky = skyMaps.length;
  var gi = groundIrradiance(toSun, sunColor, skyColor);
  var groundRad = [params.groundAlbedo * gi.total[0], params.groundAlbedo * gi.total[1], params.groundAlbedo * gi.total[2]];
  var sunScale = [sunColor[0] / Math.PI, sunColor[1] / Math.PI, sunColor[2] / Math.PI];
  var skyRes = skyMaps[0] ? skyMaps[0].res : 1, skyScale = skyMaps[0] ? skyRes / (2 * light.sphere.radius) : 1, skyTexel = skyMaps[0] ? skyMaps[0].texel : 0;
  var allDirs = light.allDirs, p = [0, 0, 0], q = [0, 0, 0];
  for (var y = 0; y < W; y++) for (var x = 0; x < W; x++) {
    var idx = y * W + x, m = g.mat[idx];
    if (m < 0) continue;
    if (tris.materials[m].team) team[idx] = 1;
    var dx = (x + 0.5 - half) / scale, dy = (half - (y + 0.5)) / scale, dz = g.depth[idx];
    p[0] = tg[0] + r[0] * dx + u[0] * dy + f[0] * dz; p[1] = tg[1] + r[1] * dx + u[1] * dy + f[1] * dz; p[2] = tg[2] + r[2] * dx + u[2] * dy + f[2] * dz;
    var nx = g.nrm[idx * 3], ny = g.nrm[idx * 3 + 1], nz = g.nrm[idx * 3 + 2];
    // slonce
    var ndl = nx * toSun[0] + ny * toSun[1] + nz * toSun[2], sunVis = 0;
    if (ndl > 0) {
      var off = sunMap.texel * 1.2;
      q[0] = p[0] + nx * off; q[1] = p[1] + ny * off; q[2] = p[2] + nz * off;
      sunVis = mapVisibilityPcf(sunMap, q, sunMap.texel * 1.6 + 0.01) * ndl;
    }
    // niebo: widocznosc wazona cosinusem; dolna polkula zastapiona odbiciem od gruntu
    var wUpper = 0, wVis = 0, wAll = 0, wLower = 0;
    for (var i = 0; i < allDirs.length; i++) { var dd = allDirs[i], w = nx * dd[0] + ny * dd[1] + nz * dd[2]; if (w > 0) { wAll += w; if (dd[2] <= 0.02) wLower += w; } }
    var off2 = skyTexel * 1.2;
    q[0] = p[0] + nx * off2; q[1] = p[1] + ny * off2; q[2] = p[2] + nz * off2;
    for (var k = 0; k < nSky; k++) {
      var map = skyMaps[k], d = map.dir, w2 = nx * d[0] + ny * d[1] + nz * d[2];
      if (w2 <= 0) continue;
      wUpper += w2;
      var ex = q[0] - map.center[0], ey = q[1] - map.center[1], ez = q[2] - map.center[2];
      var mx = Math.floor(skyRes / 2 + (ex * map.u[0] + ey * map.u[1] + ez * map.u[2]) * skyScale), my = Math.floor(skyRes / 2 + (ex * map.v[0] + ey * map.v[1] + ez * map.v[2]) * skyScale);
      var vis = 1;
      if (mx >= 0 && my >= 0 && mx < skyRes && my < skyRes) vis = (ex * d[0] + ey * d[1] + ez * d[2]) >= map.depth[my * skyRes + mx] - skyTexel * 2.2 - 0.012 ? 1 : 0;
      wVis += w2 * vis;
    }
    var skyAo = wAll > 0 ? wVis / wAll : 0, lowerFrac = wAll > 0 ? wLower / wAll : 0, upperFrac = wAll > 0 ? wUpper / wAll : 0;
    // odbicie od gruntu: tylko dolna polkula, tlumione tym, jak bardzo punkt jest "nad ziemia" (przy ziemi grunt jest zacieniony przez sam obiekt)
    var height = Math.max(p[2], 0), bounceAtt = Math.min(1, 0.55 + height * 0.5);
    var bounce = lowerFrac * params.bounce * bounceAtt;
    var skyTerm = skyAo, fillTerm = params.fill * Math.max(0, upperFrac - skyAo) / Math.max(upperFrac, 1e-3) * 0 + params.fill * (1 - skyAo) * upperFrac;
    var o3 = idx * 3;
    for (var c = 0; c < 3; c++) {
      var irr = sunScale[c] * sunVis + skyColor[c] * skyTerm + groundRad[c] * bounce + skyColor[c] * fillTerm;
      out[o3 + c] = g.alb[o3 + c] * irr;
    }
  }
  return { radiance: out, team: team };
}

// srednie promieniowanie pionowych/pochylonych powierzchni obiektu (to widzi grunt w miejscu, gdzie niebo jest zaslonieta)
function wallRadiance(g, radiance) {
  var sum = [0, 0, 0], n = 0, sumAll = [0, 0, 0], nAll = 0;
  for (var i = 0; i < g.mat.length; i++) {
    if (g.mat[i] < 0) continue;
    for (var c = 0; c < 3; c++) sumAll[c] += radiance[i * 3 + c]; nAll++;
    if (Math.abs(g.nrm[i * 3 + 2]) < 0.5) { for (var c2 = 0; c2 < 3; c2++) sum[c2] += radiance[i * 3 + c2]; n++; }
  }
  if (n < 50) { sum = sumAll; n = nAll; }
  return n ? [sum[0] / n, sum[1] / n, sum[2] / n] : [0, 0, 0];
}

// Warstwa gruntu: promieniowanie liniowe gruntu (z cieniami obiektu) dla pikseli niepokrytych; wartosc cienia = 1 - L/L_gruntu
function shadeGround(g, tris, cam, light, sunColor, skyColor, groundTex, wantColor, wall) {
  var W = g.size, N = W * W, params = light.params, half = W / 2, scale = cam.ppu * cam.supersample, tg = cam.target, r = cam.right, u = cam.up, f = cam.forward;
  var shadow = new Float32Array(N), color = wantColor ? new Float32Array(N * 3) : null;
  var toSun = light.toSun, sunMap = light.sunMap, skyMaps = light.skyMaps, nSky = skyMaps.length, gi = groundIrradiance(toSun, sunColor, skyColor);
  var sunL = gi.sun[0] * LUMA[0] + gi.sun[1] * LUMA[1] + gi.sun[2] * LUMA[2], skyL = skyColor[0] * LUMA[0] + skyColor[1] * LUMA[1] + skyColor[2] * LUMA[2];
  var reach = light.sphere.radius * 2.2, cx = light.sphere.center[0], cy = light.sphere.center[1];
  var skyRes = skyMaps[0] ? skyMaps[0].res : 1, skyScale = skyMaps[0] ? skyRes / (2 * light.sphere.radius) : 1, skyTexel = skyMaps[0] ? skyMaps[0].texel : 0;
  var wTotal = 0; for (var k0 = 0; k0 < nSky; k0++) wTotal += skyMaps[k0].dir[2];
  var allW = 0; light.allDirs.forEach(function (d) { if (d[2] > 0) allW += d[2]; });
  var albedo = [0, 0, 0], lod = Math.max(0, Math.log((groundTex ? groundTex.mips[0].size : 1) / (3 * scale)) / Math.LN2 + 0.5), q = [0, 0, 0];
  for (var y = 0; y < W; y++) for (var x = 0; x < W; x++) {
    var idx = y * W + x;
    var dx = (x + 0.5 - half) / scale, dy = (half - (y + 0.5)) / scale;
    var t = -(tg[2] + r[2] * dx + u[2] * dy) / f[2];
    var px = tg[0] + r[0] * dx + u[0] * dy + f[0] * t, py = tg[1] + r[1] * dx + u[1] * dy + f[1] * t;
    var sunVis = 1, skyAo = 1;
    if (g.mat[idx] < 0 && Math.hypot(px - cx, py - cy) < reach) {
      q[0] = px; q[1] = py; q[2] = 0.0;
      var mapOff = sunMap.texel; q[2] = mapOff * 0.8;
      sunVis = mapVisibilityPcf(sunMap, q, sunMap.texel * 1.6 + 0.01);
      var visSum = 0;
      q[2] = skyTexel * 0.8;
      for (var k = 0; k < nSky; k++) {
        var map = skyMaps[k], d = map.dir, ex = q[0] - map.center[0] + 0 + (px - q[0]), ey = q[1] - map.center[1] + (py - q[1]), ez = q[2] - map.center[2];
        ex = px - map.center[0]; ey = py - map.center[1];
        var mx = Math.floor(skyRes / 2 + (ex * map.u[0] + ey * map.u[1] + ez * map.u[2]) * skyScale), my = Math.floor(skyRes / 2 + (ex * map.v[0] + ey * map.v[1] + ez * map.v[2]) * skyScale), vis = 1;
        if (mx >= 0 && my >= 0 && mx < skyRes && my < skyRes) vis = (ex * d[0] + ey * d[1] + ez * d[2]) >= map.depth[my * skyRes + mx] - skyTexel * 2.2 - 0.012 ? 1 : 0;
        visSum += d[2] * vis;
      }
      skyAo = allW > 0 ? 1 - (wTotal - visSum) / allW : 1;
      skyAo = Math.min(1, Math.max(0, skyAo));
    }
    // wzgledny cien (luma): jak 1 - L_beauty / L_ground
    // zasloniete niebo zastepuje promieniowanie scian obiektu (odbicie posrednie), skalowane parametrem groundFill
    var occ = (1 - skyAo) * params.groundFill, lit = sunL * sunVis + skyL * skyAo + occ * (wall[0] * LUMA[0] + wall[1] * LUMA[1] + wall[2] * LUMA[2]), full = sunL + skyL;
    shadow[idx] = g.mat[idx] < 0 ? Math.min(1, Math.max(0, 1 - lit / full)) : 0;
    if (wantColor) {
      groundAlbedoAt(groundTex, px, py, lod, albedo);
      for (var c = 0; c < 3; c++) color[idx * 3 + c] = albedo[c] * gi.total[c];   // grunt bez obiektow; cien nakladany jest osobno (jak w wersji Mitsuba)
    }
  }
  return { shadow: shadow, color: color };
}

// renderSprite(model, camera, options) -> { sprite, shadow, team, preview, anchor, ppu, tilePx, viewAngleDeg, groundGain }
// options: { groundTexture, viewAngleDeg, sunDir, sunColor, skyColor, exposure, trim, margin, lighting }
function renderSprite(model, camera, options) {
  options = options || {};
  var angle = options.viewAngleDeg || 0, cam = angle ? camera.rotated(angle) : camera;
  var sunDir = options.sunDir || SUN_DIR, sunColor = options.sunColor || SUN_COLOR, skyColor = options.skyColor || SKY_COLOR;
  if (angle) sunDir = matVec(rotZ(-angle * Math.PI / 180), sunDir);
  var exposure = options.exposure === undefined ? 1.0 : options.exposure, trim = options.trim !== false, margin = options.margin === undefined ? 3 : options.margin;
  var params = {}; for (var key in LIGHTING) params[key] = options.lighting && options.lighting[key] !== undefined ? options.lighting[key] : LIGHTING[key];
  var groundTex = options.groundTexture ? { mips: textureMips(options.groundTexture) } : { mips: textureMips(standardTextures(['grass']).grass) };
  var tris = collectTriangles(model), g = rasterizeGBuffer(tris, cam), light = prepareLighting(tris, sunDir, params);
  var shaded = shadeGBuffer(g, tris, cam, light, sunColor, skyColor), ground = shadeGround(g, tris, cam, light, sunColor, skyColor, groundTex, true, wallRadiance(g, shaded.radiance));
  var W = g.size, N = W * W, ss = cam.supersample, size = cam.size;
  // premult. kolor obiektu po tonemappingu, alfa, maska druzyny, cien, grunt
  var premult = new Float32Array(N * 3), alpha = new Float32Array(N), teamF = new Float32Array(N), groundLd = new Float32Array(N * 3), tm = [0, 0, 0];
  for (var i = 0; i < N; i++) {
    if (g.mat[i] >= 0) {
      tonemapRgb(shaded.radiance[i * 3], shaded.radiance[i * 3 + 1], shaded.radiance[i * 3 + 2], exposure, tm, 0);
      premult[i * 3] = tm[0]; premult[i * 3 + 1] = tm[1]; premult[i * 3 + 2] = tm[2]; alpha[i] = 1; teamF[i] = shaded.team[i];
    }
    tonemapRgb(ground.color[i * 3], ground.color[i * 3 + 1], ground.color[i * 3 + 2], exposure, tm, 0);
    groundLd[i * 3] = tm[0]; groundLd[i * 3 + 1] = tm[1]; groundLd[i * 3 + 2] = tm[2];
  }
  var shadowBlur = gaussianBlur(ground.shadow, W, W, 1, params.shadowSigma * ss);
  for (var s = 0; s < N; s++) { var sv = (shadowBlur[s] - 0.05) / 0.95; shadowBlur[s] = sv < 0 ? 0 : sv > 1 ? 1 : sv; }
  var premultLow = boxDownsample(premult, W, 3, ss, size), alphaLow = boxDownsample(alpha, W, 1, ss, size), teamLow = boxDownsample(teamF, W, 1, ss, size);
  var shadowLow = boxDownsample(shadowBlur, W, 1, ss, size), groundLow = boxDownsample(groundLd, W, 3, ss, size);
  var colorLow = new Float32Array(size * size * 3);
  for (var j = 0; j < size * size; j++) { var a = alphaLow[j]; if (a > 0.01) for (var c = 0; c < 3; c++) colorLow[j * 3 + c] = premultLow[j * 3 + c] / Math.max(a, 1e-3); }
  var blurred = gaussianBlur(colorLow, size, size, 3, 0.9);
  for (var k = 0; k < colorLow.length; k++) { var v = colorLow[k] + 0.45 * (colorLow[k] - blurred[k]); colorLow[k] = v < 0 ? 0 : v > 1 ? 1 : v; }
  var frameClipped = false;   // obiekt lub cien dotyka krawedzi kadru kamery (przed przycieciem): model/cien uciety
  for (var e = 0; e < size && !frameClipped; e++) {
    var edges = [e, (size - 1) * size + e, e * size, e * size + size - 1];
    for (var q = 0; q < 4; q++) if (alphaLow[edges[q]] > 0.05 || shadowLow[edges[q]] > 0.25) frameClipped = true;
  }
  var anchor0 = cam.project([0, 0, 0]), x0 = 0, y0 = 0, x1 = size, y1 = size;
  if (trim) {
    var minX = size, maxX = -1, minY = size, maxY = -1;
    for (var yy = 0; yy < size; yy++) for (var xx = 0; xx < size; xx++) {
      var ii = yy * size + xx;
      if (alphaLow[ii] > 0.02 || shadowLow[ii] > 0.05) { if (xx < minX) minX = xx; if (xx > maxX) maxX = xx; if (yy < minY) minY = yy; if (yy > maxY) maxY = yy; }
    }
    if (maxX >= 0) { x0 = Math.max(minX - margin, 0); x1 = Math.min(maxX + margin + 1, size); y0 = Math.max(minY - margin, 0); y1 = Math.min(maxY + margin + 1, size); }
  }
  var w = x1 - x0, h = y1 - y0, sprite = makeImage(w, h, 4), shadow = makeImage(w, h, 4), teamImg = makeImage(w, h, 1), preview = makeImage(w, h, 3);
  var to8 = function (v) { return v <= 0 ? 0 : v >= 1 ? 255 : Math.floor(v * 255 + 0.5); };
  for (var py = 0; py < h; py++) for (var px = 0; px < w; px++) {
    var src = (py + y0) * size + px + x0, dst = py * w + px, al = alphaLow[src], sh = shadowLow[src];
    for (var ch = 0; ch < 3; ch++) {
      sprite.data[dst * 4 + ch] = to8(colorLow[src * 3 + ch]);
      preview.data[dst * 3 + ch] = to8(groundLow[src * 3 + ch] * (1 - sh) * (1 - al) + colorLow[src * 3 + ch] * al);
    }
    sprite.data[dst * 4 + 3] = to8(al); shadow.data[dst * 4 + 3] = to8(sh); teamImg.data[dst] = to8(teamLow[src]);
  }
  var gain = options.wantGroundGain ? groundGain(camera, { groundTexture: options.groundTexture, sunDir: options.sunDir, sunColor: sunColor, skyColor: skyColor, exposure: exposure, lighting: params }) : null;
  return { sprite: sprite, shadow: shadow, team: teamImg, preview: preview, anchor: [anchor0[0] - x0, anchor0[1] - y0], ppu: cam.ppu, tilePx: cam.tilePx, viewAngleDeg: angle, groundGain: gain, frameClipped: frameClipped };
}

// Mnoznik RGB: tekstura gruntu (surowa) -> wyglad w renderze (do tla scen); liczony analitycznie dla plaskiego gruntu
function groundGain(camera, options) {
  options = options || {};
  var params = {}; for (var key in LIGHTING) params[key] = options.lighting && options.lighting[key] !== undefined ? options.lighting[key] : LIGHTING[key];
  var sunDir = options.sunDir || SUN_DIR, sunColor = options.sunColor || SUN_COLOR, skyColor = options.skyColor || SKY_COLOR, exposure = options.exposure === undefined ? 1.0 : options.exposure;
  var tex = options.groundTexture || standardTextures(['grass']).grass, mean = textureMeanLinear(tex);
  var gi = groundIrradiance(normalize(mul(sunDir, -1)), sunColor, skyColor), out = [0, 0, 0], rad = [0, 0, 0], srgbMean = [0, 0, 0];
  for (var i = 0; i < tex.size * tex.size; i++) for (var c = 0; c < 3; c++) srgbMean[c] += tex.data[i * 3 + c] / (tex.size * tex.size);
  for (var c2 = 0; c2 < 3; c2++) rad[c2] = mean[c2] * gi.total[c2];
  tonemapRgb(rad[0], rad[1], rad[2], exposure, out, 0);
  return [out[0] / (srgbMean[0] + 1e-6), out[1] / (srgbMean[1] + 1e-6), out[2] / (srgbMean[2] + 1e-6)];
}

// Przebarwia maske druzyny zachowujac wzgledna jasnosc (team_dark / team_light zostaja ciemniejsze / jasniejsze); jasnosc normalizowana srednia maskowanych pikseli
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

// ===== 07_export.js =====
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
    light: 'shadow falls to the lower-left of the screen', team_color: 'see *_team.png mask' };
  for (var k in (extraMeta || {})) meta[k] = extraMeta[k];
  files[name + '.json'] = JSON.stringify(meta, null, 2);
  return { files: files, meta: meta };
}

function checkFrames(frames) {   // kontrola wejscia arkusza; rzuca Error z opisem
  if (!frames || !frames.length) throw new Error('packSheet: pusta lista klatek');
  var w = frames[0].sprite && frames[0].sprite.width, h = frames[0].sprite && frames[0].sprite.height, base = frames[0].anchor;
  frames.forEach(function (f, index) {
    if (!f.sprite || !f.shadow || !f.team || !f.anchor || !f.tilePx) throw new Error('packSheet: klatka ' + index + ' nie jest wynikiem renderSprite');
    if (f.sprite.width !== w || f.sprite.height !== h) throw new Error('packSheet: klatka ' + index + ' ma inny rozmiar (' + f.sprite.width + 'x' + f.sprite.height + ' zamiast ' + w + 'x' + h + '); renderuj z trim:false i tym samym Camera');
    if (f.shadow.width !== w || f.shadow.height !== h || f.team.width !== w || f.team.height !== h) throw new Error('packSheet: warstwy klatki ' + index + ' (sprite/shadow/team) maja rozne wymiary');
    var any = false;
    for (var i = 0; i < w * h && !any; i++) if (Math.max(f.sprite.data[i * 4 + 3], f.shadow.data[i * 4 + 3]) > 6) any = true;
    if (!any) throw new Error('packSheet: klatka ' + index + ' jest pusta (brak pikseli sprite\'a i cienia); sprawdz model i halfExtent kamery');
    if (Math.abs(f.anchor[0] - base[0]) > 0.5 || Math.abs(f.anchor[1] - base[1]) > 0.5) throw new Error('packSheet: klatka ' + index + ' ma inna kotwice niz klatka 0; uzyj jednej kamery i trim:false');
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

// ---- sceny
function worldToCanvas(camera) {
  var base = camera.project([0, 0, 0]), a = camera.project([1, 0, 0]), b = camera.project([0, 1, 0]);
  return { ux: [a[0] - base[0], a[1] - base[1]], uy: [b[0] - base[0], b[1] - base[1]] };
}
// groundLayer(camera, width, height, originPx, texture, { gain, tileWorld }) -> { width, height, data: Float32Array RGB 0..1 }
function groundLayer(camera, width, height, originPx, texture, options) {
  options = options || {};
  var gain = options.gain || [1, 1, 1], tile = options.tileWorld || 3.0, m = worldToCanvas(camera), det = m.ux[0] * m.uy[1] - m.uy[0] * m.ux[1];
  var data = new Float32Array(width * height * 3), size = texture.size, out = new Float32Array(3);
  var mips = { data: null }, tex = new Float32Array(size * size * 3);
  for (var i = 0; i < tex.length; i++) tex[i] = texture.data[i];
  var s = size;
  for (var y = 0; y < height; y++) for (var x = 0; x < width; x++) {
    var px = x - originPx[0], py = y - originPx[1];
    var wx = (px * m.uy[1] - py * m.uy[0]) / det, wy = (-px * m.ux[1] + py * m.ux[0]) / det;
    var u = ((wx / tile) % 1 + 1) % 1 * s - 0.5, v = ((wy / tile) % 1 + 1) % 1 * s - 0.5, x0 = Math.floor(u), y0 = Math.floor(v), fx = u - x0, fy = v - y0;
    var xa = ((x0 % s) + s) % s, xb = (xa + 1) % s, ya = ((y0 % s) + s) % s, yb = (ya + 1) % s;
    for (var c = 0; c < 3; c++) {
      var val = (tex[(ya * s + xa) * 3 + c] * (1 - fx) + tex[(ya * s + xb) * 3 + c] * fx) * (1 - fy) + (tex[(yb * s + xa) * 3 + c] * (1 - fx) + tex[(yb * s + xb) * 3 + c] * fx) * fy;
      data[(y * width + x) * 3 + c] = Math.min(1, Math.max(0, val * gain[c]));
    }
  }
  return { width: width, height: height, data: data };
}
// composeScene(items, camera, width, height, originPx, ground) -> Image RGB; items: [{ res, x, y }] (x, y w kaflach)
function composeScene(items, camera, width, height, originPx, ground) {
  var m = worldToCanvas(camera), canvas = new Float32Array(ground.data), placed = [];
  items.forEach(function (item) {
    var px = originPx[0] + m.ux[0] * item.x + m.uy[0] * item.y, py = originPx[1] + m.ux[1] * item.x + m.uy[1] * item.y;
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
  var expectTeam = options.expectTeam !== false, kind = options.kind || 'building', shadowSide = options.shadowSide || 'left', findings = [];   // shadowSide: 'left' | 'right' | 'any'
  function add(level, text) { findings.push([level, text]); }
  var sp = result.sprite, w = sp.width, h = sp.height, n = w * h, alpha = new Float32Array(n), opaqueCount = 0;
  for (var i = 0; i < n; i++) { alpha[i] = sp.data[i * 4 + 3] / 255; if (alpha[i] > 0.9) opaqueCount++; }
  if (!opaqueCount) { add('ERR', 'pusty sprite (brak pikseli o alfa > 0.9)'); return findings; }
  if (result.frameClipped) add('ERR', 'obiekt lub cien dotyka krawedzi kadru kamery - uciety, zwieksz halfExtent kamery (przy trim:true ta flaga zastepuje test krawedzi)');
  var borderMax = 0;
  for (var x = 0; x < w; x++) borderMax = Math.max(borderMax, alpha[x], alpha[(h - 1) * w + x]);
  for (var y = 0; y < h; y++) borderMax = Math.max(borderMax, alpha[y * w], alpha[y * w + w - 1]);
  if (borderMax > 0.05) add('ERR', 'sprite dotyka krawedzi kadru - model uciety, zwieksz halfExtent kamery');
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
  if (colors < (kind === 'foliage' ? 120 : 250)) add('WARN', 'malo kolorow - tekstury zbyt plaskie wzgledem referencji (setki kolorow)');
  add('INFO', 'srednia jasnosc ' + mean.toFixed(2) + ', odchylenie ' + std.toFixed(2));
  if (mean < (kind === 'foliage' ? 0.14 : 0.18)) add('WARN', 'sprite bardzo ciemny - zwieksz exposure lub jasnosc tekstur');
  if (mean > 0.70) add('WARN', 'sprite przepalony - zmniejsz exposure');
  if (std < (kind === 'foliage' ? 0.06 : 0.08)) add('WARN', 'niski kontrast - brak czytelnej bryly (sprawdz swiatlo i AO)');
  if (dark / opaqueCount > 0.08) add('WARN', 'duzo prawie czarnych pikseli - zbyt ostry cien wlasny lub zbyt ciemny material');
  var softRatio = soft / Math.max(1, visible);
  if (softRatio < 0.004) add('WARN', 'krawedzie bez antyaliasingu (supersample < 2?)');
  if (softRatio > 0.18) add('WARN', 'bardzo duzo polprzezroczystych pikseli - rozmyty obiekt lub zbyt gesty szum');
  var teamCount = 0, outside = 0;
  for (var t = 0; t < n; t++) if (result.team.data[t] > 40) { teamCount++; if (!(alpha[t] > 0.1)) outside++; }
  if (expectTeam && !teamCount) add('WARN', 'maska koloru druzyny pusta - brak elementow w materiale team');
  if (teamCount) {
    if (outside > 0.05 * teamCount) add('ERR', 'maska druzyny wychodzi poza sprite');
    add('INFO', 'pokrycie maski druzyny: ' + (teamCount / opaqueCount * 100).toFixed(1) + '% sprite\'a');
    if (teamCount > 0.25 * opaqueCount) add('WARN', 'maska druzyny > 25% sprite\'a - zbyt duzo koloru gracza');
  }
  var shSum = 0, shX = 0, spSum = 0, spX = 0, shBig = 0;
  for (var q = 0; q < n; q++) {
    var sa = result.shadow.data[q * 4 + 3] / 255, cx = q % w; shSum += sa; shX += sa * cx; spSum += alpha[q]; spX += alpha[q] * cx; if (sa > 0.03) shBig++;
  }
  if (shSum < 20) add('WARN', 'brak warstwy cienia');
  else {
    var shCx = shX / shSum, spCx = spX / spSum;
    if (shadowSide === 'left' && shCx > spCx + 1) add('ERR', 'cien pada w prawo - w tym stylu swiatlo jest z prawej gornej, cien w lewo-dol (inny uklad swiatla: shadowSide)');
    if (shadowSide === 'right' && shCx < spCx - 1) add('ERR', 'cien pada w lewo, a oczekiwano prawej strony (shadowSide: right)');
    add('INFO', 'cien: ' + shSum.toFixed(0) + ' px-masy, srodek ' + (shCx - spCx >= 0 ? '+' : '') + (shCx - spCx).toFixed(1) + 'px wzgledem sprite\'a');
    if (shBig / n > 0.35) add('WARN', 'cien zajmuje wiekszosc kadru - szum poza cieniem');
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

return { TILE_PX: TILE_PX, SUN_DIR: SUN_DIR, SUN_COLOR: SUN_COLOR, SKY_COLOR: SKY_COLOR, LIGHTING: LIGHTING, Camera: Camera, Model: Model, Mesh: Mesh, makeRng: makeRng, standardTextures: standardTextures, textureToImage: textureToImage, TEXTURE_FUNCTIONS: TEXTURE_FUNCTIONS, newTexture: newTexture, fbm: fbm, adjustTexture: adjustTexture, texShingle: texShingle, texPlaster: texPlaster, texTimber: texTimber, texPlanks: texPlanks, texStone: texStone, texGrass: texGrass, texLeaf: texLeaf, texNeedle: texNeedle, texCloth: texCloth, texThatch: texThatch, texBark: texBark, texDirt: texDirt, texMetal: texMetal, standardModel: standardModel, halfTimberWall: halfTimberWall, gableRoof: gableRoof, roundTower: roundTower, palisade: palisade, log: log, wheel: wheel, barrel: barrel, crate: crate, bush: bush, addLeaf: addLeaf, leafCluster: leafCluster, pennant: pennant, treeOak: treeOak, treePine: treePine, rotX: rotX, rotY: rotY, rotZ: rotZ, renderSprite: renderSprite, groundGain: groundGain, swapTeamColor: swapTeamColor, makeImage: makeImage, encodePng: encodePng, toBase64: toBase64, saveSprite: saveSprite, packSheet: packSheet, saveSheet: saveSheet, groundLayer: groundLayer, composeScene: composeScene, validateSprite: validateSprite, validateSheet: validateSheet, report: report, reviewStrip: reviewStrip };
});
