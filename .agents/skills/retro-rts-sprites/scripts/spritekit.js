'use strict';
// spritekit.js: siatka ASCII (znak = 1 piksel) -> SVG / PNG, prymitywy rysowania, walidator, scena izometryczna.
// Bez zależności. PNG wymaga node (zlib). Ten sam kod jest wklejony w renderer.md.

// ---------- Palety (musi zgadzać się z palettes.md; sprawdza to scripts/check.js) ----------
// Kolejność tonów w rampie: [cień, baza, światło]
const PALETTES = {
  PRERENDER: {
    grass: ['#3e5c2a', '#5a7d36', '#79924a'],
    dryGrass: ['#7a6b3e', '#8a7f4a', '#a3955a'],
    dirt: ['#6b5236', '#8b6f47', '#a58a5f'],
    stone: ['#63615a', '#8f8a7f', '#b5b0a4'],
    wood: ['#57402a', '#7a5b39', '#9c7a4c'],
    roofRed: ['#6f3220', '#96402e', '#b8683f'],
    roofStraw: ['#8a7434', '#ab9449', '#c9b264'],
    water: ['#3b6a8a', '#4d84a5', '#6ba3bf'],
    skin: ['#96703f', '#c8a06a', '#e0bd8d'],
    metal: ['#5d646d', '#9aa2ab', '#cfd4da'],
    gold: ['#8a6a1e', '#c9a24b', '#e6cd7a'],
    foliage: ['#24401f', '#355c2b', '#55823a'],
    teamBlue: ['#2b4d8f', '#3f66b5', '#6f92d8'],
    teamRed: ['#8f2b2b', '#b53f3f', '#d86f6f'],
  },
  PIXELART: {
    grass: ['#4e9e2a', '#6abe30', '#8cd94f'],
    dirt: ['#96682f', '#b3822f', '#d1a44a'],
    stone: ['#75726a', '#9d998e', '#c6c2b4'],
    wood: ['#6d4a26', '#8f6230', '#b3834a'],
    roofRed: ['#a33627', '#c94a33', '#e07a4f'],
    roofStraw: ['#c39a35', '#dcb44e', '#f0cf70'],
    water: ['#2e86c9', '#4aa3e0', '#7cc4ee'],
    skin: ['#a5793d', '#d1a05c', '#ecc088'],
    metal: ['#6f7780', '#a8b0b9', '#dde2e8'],
    gold: ['#b3852a', '#e3b23c', '#f7d96a'],
    foliage: ['#3d7a20', '#5aa832', '#8cd94f'],
    teamBlue: ['#3050c8', '#4a6ee8', '#8aa8f5'],
    teamRed: ['#c83030', '#e04a4a', '#f58a8a'],
  },
  // Kontury (tylko PIXELART), jeden kolor na grupę materiałów, stały w całym zestawie
  CONTOUR: {
    green: '#22361a', wood: '#2e2013', cool: '#26333d',
    roofRed: '#5a2016', roofStraw: '#6d5a1e', teamBlue: '#1e2a5c', teamRed: '#5a1c1c',
  },
  CONTOUR_OF: {
    grass: 'green', foliage: 'green', dirt: 'wood', wood: 'wood', skin: 'wood', gold: 'wood',
    stone: 'cool', metal: 'cool', water: 'cool', roofRed: 'roofRed', roofStraw: 'roofStraw',
    teamBlue: 'teamBlue', teamRed: 'teamRed',
  },
  SHADOW: 'rgba(0,0,0,0.30)',
};

// Limit kolorów zależy od rozmiaru płótna: pole <= 1280 px (np. 24x32, 32x40, 16x16) = 12 kolorów, większe (budynek 64x64, tile) = 24
function colorLimit(width, height) { return width * height <= 1280 ? 12 : 24; }

function tone(mode, material, index) { return PALETTES[mode][material][index]; } // 0 cień, 1 baza, 2 światło
function contourOf(material) { return PALETTES.CONTOUR[PALETTES.CONTOUR_OF[material]]; }
function allowedColors(mode) {
  const list = [];
  for (const ramp of Object.values(PALETTES[mode])) list.push(...ramp);
  if (mode === 'PIXELART') list.push(...Object.values(PALETTES.CONTOUR));
  return list;
}

// ---------- Kolor ----------
function parseColor(spec) {
  let match = /^#([0-9a-f]{6})$/i.exec(spec);
  if (match) return { hex: '#' + match[1].toLowerCase(), alpha: 1 };
  match = /^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)$/i.exec(spec);
  if (match) {
    const hex = '#' + [match[1], match[2], match[3]].map(v => Number(v).toString(16).padStart(2, '0')).join('');
    return { hex, alpha: Number(match[4]) };
  }
  throw new Error(`Nieznany format koloru: ${spec}`);
}
function hexToRgb(hex) { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function channelLinear(c) { const v = c / 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }
function luminance(hex) { const [r, g, b] = hexToRgb(hex); return 0.2126 * channelLinear(r) + 0.7152 * channelLinear(g) + 0.0722 * channelLinear(b); }
function contrast(hexA, hexB) { const [hi, lo] = [luminance(hexA), luminance(hexB)].sort((a, b) => b - a); return (hi + 0.05) / (lo + 0.05); }

// ---------- Siatka ----------
function makeGrid(width, height) { return { w: width, h: height, cells: Array.from({ length: height }, () => Array(width).fill('.')) }; }
function getCell(grid, x, y) { return (x < 0 || y < 0 || x >= grid.w || y >= grid.h) ? '.' : grid.cells[y][x]; }
function setCell(grid, x, y, ch) { if (x >= 0 && y >= 0 && x < grid.w && y < grid.h) grid.cells[y][x] = ch; }
function gridToRows(grid) { return grid.cells.map(row => row.join('')); }
function rowsToGrid(rows) {
  const grid = makeGrid(Math.max(...rows.map(r => r.length)), rows.length);
  rows.forEach((row, y) => [...row].forEach((ch, x) => { grid.cells[y][x] = ch; }));
  return grid;
}

// Deterministyczny szum 0..1 z pozycji piksela (zamiast Math.random)
function noise(x, y, seed = 0) {
  let n = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(seed, 1442695041)) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}

function fillRect(grid, x, y, w, h, ch) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) setCell(grid, x + i, y + j, ch); }

function fillPolygon(grid, points, ch) {
  const ys = points.map(p => p[1]);
  for (let y = Math.floor(Math.min(...ys)); y <= Math.ceil(Math.max(...ys)); y++) {
    const yc = y + 0.5, crossings = [];
    for (let i = 0; i < points.length; i++) {
      const [x1, y1] = points[i], [x2, y2] = points[(i + 1) % points.length];
      if ((y1 <= yc && y2 > yc) || (y2 <= yc && y1 > yc)) crossings.push(x1 + (yc - y1) * (x2 - x1) / (y2 - y1));
    }
    crossings.sort((a, b) => a - b);
    for (let i = 0; i + 1 < crossings.length; i += 2)
      for (let x = Math.ceil(crossings[i] - 0.5); x < Math.ceil(crossings[i + 1] - 0.5); x++) setCell(grid, x, y, ch);
  }
}

function drawLine(grid, x0, y0, x1, y1, ch) {
  const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), stepX = x0 < x1 ? 1 : -1, stepY = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  for (;;) {
    setCell(grid, x0, y0, ch);
    if (x0 === x1 && y0 === y1) break;
    const doubled = 2 * err;
    if (doubled >= dy) { err += dy; x0 += stepX; }
    if (doubled <= dx) { err += dx; y0 += stepY; }
  }
}

// Romb 2:1 o polu ograniczającym width x (width/2), szerokość wiersza = 4*min(r, h-1-r)+2, kafle układają się bez szczelin i nakładek
function fillDiamond(grid, x0, y0, width, ch) {
  const height = width / 2;
  for (let r = 0; r < height; r++) {
    const rowWidth = 4 * Math.min(r, height - 1 - r) + 2;
    const start = x0 + width / 2 - rowWidth / 2;
    for (let i = 0; i < rowWidth; i++) setCell(grid, start + i, y0 + r, ch);
  }
}

function fillEllipse(grid, cx, cy, rx, ry, ch) { shadeEllipse(grid, cx, cy, rx, ry, { light: ch, base: ch, shadow: ch }); }

// ---------- Światło i tony ----------
// s = pozycja względem źródła światła (lewy górny róg): dodatnia po stronie światła, ujemna po stronie cienia
function toneForLight(s, chars, opts, x, y) {
  const { lightAt = 0.25, shadowAt = -0.2, jitter = 0.25, seed = 0, dither = false, band = 0.06 } = opts;
  const v = s + (noise(x, y, seed) - 0.5) * jitter;
  if (dither) {
    const odd = (x + y) & 1;
    if (Math.abs(v - lightAt) < band) return odd ? chars.base : chars.light;
    if (Math.abs(v - shadowAt) < band) return odd ? chars.shadow : chars.base;
  }
  return v > lightAt ? chars.light : v < shadowAt ? chars.shadow : chars.base;
}

// Elipsa (opcjonalnie poszarpana: wobble) cieniowana względem własnego środka. chars = { light, base, shadow }
function shadeEllipse(grid, cx, cy, rx, ry, chars, opts = {}) {
  const { wobble = 0, seed = 0 } = opts, reach = 1 + Math.abs(wobble);
  for (let y = Math.floor(cy - ry * reach) - 1; y <= Math.ceil(cy + ry * reach) + 1; y++) {
    for (let x = Math.floor(cx - rx * reach) - 1; x <= Math.ceil(cx + rx * reach) + 1; x++) {
      const dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry;
      const angle = Math.atan2(dy, dx);
      const radius = 1 + wobble * (Math.sin(3 * angle + seed) * 0.6 + Math.sin(5 * angle + 2 * seed) * 0.4);
      if (dx * dx + dy * dy > radius * radius) continue;
      setCell(grid, x, y, toneForLight(-(dx + dy) / (2 * radius), chars, opts, x, y));
    }
  }
}

// Zamienia płaski obszar znaku matchChar na 3 tony wg pozycji w jego polu ograniczającym
function shadeRegion(grid, matchChar, chars, opts = {}) {
  let minX = Infinity, minY = Infinity, maxX = -1, maxY = -1;
  for (let y = 0; y < grid.h; y++) for (let x = 0; x < grid.w; x++) if (grid.cells[y][x] === matchChar) {
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
  }
  if (maxX < 0) return;
  const cx = (minX + maxX + 1) / 2, cy = (minY + maxY + 1) / 2, rx = (maxX - minX + 1) / 2, ry = (maxY - minY + 1) / 2;
  for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) if (grid.cells[y][x] === matchChar)
    grid.cells[y][x] = toneForLight(-((x + 0.5 - cx) / rx + (y + 0.5 - cy) / ry) / 2, chars, opts, x, y);
}

// Zamienia piksele z listy znaków na replaceChar z zadaną gęstością (deterministycznie)
function scatter(grid, matchChars, replaceChar, density, seed = 0) {
  for (let y = 0; y < grid.h; y++) for (let x = 0; x < grid.w; x++)
    if (matchChars.includes(grid.cells[y][x]) && noise(x, y, seed) < density) grid.cells[y][x] = replaceChar;
}

// PRERENDER: brzeg bryły schodzi o jeden ton w dół własnej rampy (bez osobnego koloru konturu), gwarantuje czytelną sylwetkę na trawie
// ramps = [[światło, baza, cień], ...] jako znaki; outside = znaki traktowane jako tło
function rimDarken(grid, ramps, opts = {}) {
  const outside = opts.outside || ['.', 's'], darker = {};
  for (const [light, base, shadow] of ramps) { darker[light] = base; darker[base] = shadow; }
  const changes = [];
  for (let y = 0; y < grid.h; y++) for (let x = 0; x < grid.w; x++) {
    const ch = grid.cells[y][x];
    if (!(ch in darker)) continue;
    if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => outside.includes(getCell(grid, x + dx, y + dy)))) changes.push([x, y, darker[ch]]);
  }
  for (const [x, y, ch] of changes) grid.cells[y][x] = ch;
}

// PIXELART: kontur. contourMap = { znakWypełnienia: znakKonturu }. where: 'inner' (kontur na pikselach granicznych) lub 'outer' (wokół, wymaga marginesu 1 px)
// between: kontur także na styku materiałów o różnych konturach (np. korona i pień)
function outline(grid, contourMap, opts = {}) {
  const { where = 'inner', outside = ['.', 's'], between = false } = opts, changes = [];
  const near = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  for (let y = 0; y < grid.h; y++) for (let x = 0; x < grid.w; x++) {
    const ch = grid.cells[y][x];
    const isEdge = (neighbor) => outside.includes(neighbor) || (between && neighbor in contourMap && contourMap[neighbor] !== contourMap[ch]);
    if (where === 'inner' && ch in contourMap && near.some(([dx, dy]) => isEdge(getCell(grid, x + dx, y + dy)))) changes.push([x, y, contourMap[ch]]);
    if (where === 'outer' && outside.includes(ch)) {
      const filled = near.map(([dx, dy]) => getCell(grid, x + dx, y + dy)).find(n => n in contourMap);
      if (filled) changes.push([x, y, contourMap[filled]]);
    }
  }
  for (const [x, y, ch] of changes) grid.cells[y][x] = ch;
}

// ---------- Bryły izometryczne (rzut 2:1) ----------
// Współrzędne komórkowe (u wzdłuż gx, v wzdłuż gy) -> piksele; origin = róg tylny (gx=0, gy=0) na poziomie gruntu
function isoPoint(origin, u, v, lift = 0) { return [origin[0] + (u - v) * 32, origin[1] + (u + v) * 16 - lift]; }

// Prostopadłościan o podstawie w x d komórek i wysokości ścian wallHeight; ściana lewa (długość w) i prawa (długość d), góra
function isoBox(grid, origin, w, d, wallHeight, chars) {
  const P = (u, v, lift = 0) => isoPoint(origin, u, v, lift);
  fillPolygon(grid, [P(0, d), P(w, d), P(w, d, wallHeight), P(0, d, wallHeight)], chars.left);
  fillPolygon(grid, [P(w, d), P(w, 0), P(w, 0, wallHeight), P(w, d, wallHeight)], chars.right);
  if (chars.top) fillPolygon(grid, [P(0, 0, wallHeight), P(w, 0, wallHeight), P(w, d, wallHeight), P(0, d, wallHeight)], chars.top);
}

// Dach czterospadowy nad prostopadłościanem (piramida dla w = d), widoczne tylko dwie połacie przednie
function hipRoof(grid, origin, w, d, wallHeight, rise, chars, overhang = 0.12) {
  const o = overhang, W = w + 2 * o, D = d + 2 * o, P = (u, v, lift) => isoPoint(origin, u - o, v - o, lift);
  const eave = wallHeight, top = wallHeight + rise;
  const ridgeA = w >= d ? [D / 2, D / 2] : [W / 2, W / 2], ridgeB = w >= d ? [W - D / 2, D / 2] : [W / 2, D - W / 2];
  const A = [P(...ridgeA, top), P(...ridgeB, top)];
  const cornerD = P(0, D, eave), cornerC = P(W, D, eave), cornerB = P(W, 0, eave);
  if (w >= d) {
    fillPolygon(grid, [cornerD, cornerC, A[1], A[0]], chars.left);
    fillPolygon(grid, [cornerC, cornerB, A[1]], chars.right);
  } else {
    fillPolygon(grid, [cornerD, cornerC, A[1]], chars.left);
    fillPolygon(grid, [cornerC, cornerB, A[0], A[1]], chars.right);
  }
}

// ---------- Rzut izometryczny sceny ----------
function isoToScreen(gx, gy) { return { x: (gx - gy) * 32, y: (gx + gy) * 16 }; } // środek komórki, kafel 64x32

function makeSprite({ id, rows, palette, anchor }) {
  if (typeof id !== 'string' || !id) throw new Error('makeSprite: id musi być niepustym tekstem');
  if (!Array.isArray(rows) || !rows.length) throw new Error(`makeSprite(${id}): brak wierszy`);
  if (!anchor || !Number.isFinite(anchor.x) || !Number.isFinite(anchor.y)) throw new Error(`makeSprite(${id}): brak kotwicy {x, y}`);
  return { id, rows, palette, anchor, width: Math.max(...rows.map(r => r.length)), height: rows.length };
}

// scene = { cols, rows, tileAt(gx, gy) -> sprite, objects: [{ sprite, gx, gy, footprint: { w, d } }] }
// Kolejność malowania: rosnąco po (gx+gy) przedniej komórki; w obrębie sumy najpierw kafle, potem obiekty
function composeScene(scene) {
  const items = [];
  for (let gy = 0; gy < scene.rows; gy++) for (let gx = 0; gx < scene.cols; gx++) {
    const sprite = scene.tileAt(gx, gy), at = isoToScreen(gx, gy);
    items.push({ sprite, x: at.x - sprite.anchor.x, y: at.y - sprite.anchor.y, key: gx + gy, layer: 0, order: gx });
  }
  for (const object of scene.objects || []) {
    const { w = 1, d = 1 } = object.footprint || {}, at = isoToScreen(object.gx + (w - 1) / 2, object.gy + (d - 1) / 2);
    items.push({ sprite: object.sprite, x: at.x - object.sprite.anchor.x, y: at.y - object.sprite.anchor.y, key: object.gx + w - 1 + object.gy + d - 1, layer: 1, order: object.gx });
  }
  items.sort((a, b) => a.key - b.key || a.layer - b.layer || a.order - b.order);
  const minX = Math.min(...items.map(i => i.x)), minY = Math.min(...items.map(i => i.y));
  const maxX = Math.max(...items.map(i => i.x + i.sprite.width)), maxY = Math.max(...items.map(i => i.y + i.sprite.height));
  for (const item of items) { item.x -= minX; item.y -= minY; }
  return { items, width: maxX - minX, height: maxY - minY };
}

// ---------- SVG ----------
function rowsToRects(rows, palette, width, height) {
  let svg = '';
  for (let y = 0; y < height; y++) {
    let x = 0;
    while (x < width) {
      const ch = rows[y][x] ?? '.';
      if (ch === '.') { x++; continue; }
      if (palette[ch] === undefined) throw new Error(`Brak koloru dla znaku '${ch}' w wierszu ${y}, kolumna ${x}`);
      const { hex, alpha } = parseColor(palette[ch]);
      let len = 1;
      while (x + len < width && (rows[y][x + len] ?? '.') === ch) len++;
      svg += `  <rect x="${x}" y="${y}" width="${len}" height="1" fill="${hex}"${alpha < 1 ? ` fill-opacity="${alpha}"` : ''}/>\n`;
      x += len;
    }
  }
  return svg;
}

// opts: scale (rozmiar wyświetlania), width/height (docelowe płótno), strict (błąd przy niezgodnych wymiarach)
function asciiToSvg(rows, palette, opts = {}) {
  const { scale = 8, strict = false } = opts;
  const width = opts.width ?? Math.max(...rows.map(r => r.length)), height = opts.height ?? rows.length;
  if (strict) {
    if (rows.length !== height) throw new Error(`Liczba wierszy ${rows.length}, oczekiwano ${height}`);
    rows.forEach((row, y) => { if (row.length !== width) throw new Error(`Wiersz ${y} ma ${row.length} znaków, oczekiwano ${width}`); });
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width * scale}" height="${height * scale}" shape-rendering="crispEdges">\n`
    + rowsToRects(rows, palette, width, height) + '</svg>\n';
}

// Identyfikator bezpieczny w atrybucie SVG (litery, cyfry, _ . -; zaczyna się od litery lub _)
function safeSvgId(raw) {
  const id = String(raw ?? 'sprite').replace(/[^A-Za-z0-9_.-]/g, '_');
  return /^[A-Za-z_]/.test(id) ? id : 's_' + id;
}
const spriteSignature = sprite => JSON.stringify([sprite.width, sprite.height, sprite.rows, sprite.palette]);

// Przydziela definicjom unikalne id: ten sam sprite (ta sama treść) dostaje jedną definicję, różne sprite'y o tym samym id dostają sufiks -2, -3...
function assignSvgIds(items) {
  const bySignature = new Map(), used = new Set(), sprites = [];
  for (const { sprite } of items) {
    const signature = spriteSignature(sprite);
    if (bySignature.has(signature)) continue;
    const base = safeSvgId(sprite.id);
    let id = base, n = 2;
    while (used.has(id)) id = `${base}-${n++}`;
    used.add(id); bySignature.set(signature, id); sprites.push({ sprite, id });
  }
  return { bySignature, sprites };
}

// Scena jako jeden SVG: sprite'y w <defs> (raz każdy), ustawione przez <use>
function sceneToSvg(composed, opts = {}) {
  const { scale = 2, background = null } = opts, { bySignature, sprites } = assignSvgIds(composed.items);
  const defs = sprites.map(({ sprite, id }) => `<g id="${id}">\n${rowsToRects(sprite.rows, sprite.palette, sprite.width, sprite.height)}</g>\n`).join('');
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 ${composed.width} ${composed.height}" `
    + `width="${composed.width * scale}" height="${composed.height * scale}" shape-rendering="crispEdges">\n<defs>\n${defs}</defs>\n`;
  if (background) svg += `<rect width="${composed.width}" height="${composed.height}" fill="${background}"/>\n`;
  for (const { sprite, x, y } of composed.items) svg += `<use xlink:href="#${bySignature.get(spriteSignature(sprite))}" x="${x}" y="${y}"/>\n`;
  return svg + '</svg>\n';
}

// Kontrola sceny: różne sprite'y o tym samym id (w SVG dostaną sufiksy), id z niedozwolonymi znakami, kotwica poza płótnem sprite'a
function validateScene(composed) {
  const errors = [], warnings = [], seen = new Map();
  for (const { sprite } of composed.items) {
    const signature = spriteSignature(sprite);
    if (!seen.has(sprite.id)) seen.set(sprite.id, new Set());
    seen.get(sprite.id).add(signature);
    if (safeSvgId(sprite.id) !== sprite.id) warnings.push(`id '${sprite.id}' zawiera niedozwolone znaki, w SVG zostanie zapisane jako '${safeSvgId(sprite.id)}'`);
    if (sprite.anchor.x < 0 || sprite.anchor.y < 0 || sprite.anchor.x > sprite.width || sprite.anchor.y > sprite.height)
      errors.push(`Sprite '${sprite.id}': kotwica (${sprite.anchor.x}, ${sprite.anchor.y}) poza płótnem ${sprite.width}x${sprite.height}`);
  }
  for (const [id, signatures] of seen) if (signatures.size > 1) warnings.push(`${signatures.size} różne sprite'y mają to samo id '${id}', w SVG dostaną sufiksy -2, -3 (nadaj im unikalne id)`);
  return { ok: errors.length === 0, errors: [...new Set(errors)], warnings, stats: { items: composed.items.length, distinctSprites: new Set(composed.items.map(i => spriteSignature(i.sprite))).size } };
}

// ---------- Walidator ----------
// opts: width, height, maxColors (domyślnie colorLimit(width, height): 12 lub 24), translucent (dozwolone kolory rgba, domyślnie tylko PALETTES.SHADOW), lightCheck (false dla kafli z szumem), mode ('PRERENDER' | 'PIXELART'), ground (hex tła do kontrastu), shadowChars (['s']), edgeTouchAllowed
function validate(rows, palette, opts = {}) {
  const { mode = null, ground = null, shadowChars = ['s'], edgeTouchAllowed = false, lightCheck = true, translucent = [PALETTES.SHADOW] } = opts;
  const errors = [], warnings = [], width = opts.width ?? Math.max(...rows.map(r => r.length)), height = opts.height ?? rows.length;
  const maxColors = opts.maxColors ?? colorLimit(width, height);
  const allowedTranslucent = new Set(translucent.map(spec => { const { hex, alpha } = parseColor(spec); return hex + '@' + alpha; }));
  if (rows.length !== height) errors.push(`Liczba wierszy ${rows.length}, oczekiwano ${height}`);
  rows.forEach((row, y) => { if (row.length !== width) errors.push(`Wiersz ${y} ma ${row.length} znaków, oczekiwano ${width}`); });
  const used = new Set();
  rows.forEach(row => [...row].forEach(ch => { if (ch !== '.') used.add(ch); }));
  for (const ch of used) if (palette[ch] === undefined) errors.push(`Znak '${ch}' nie ma wpisu w palecie`);
  const fills = new Set(), solidHexes = new Set();
  for (const ch of used) if (palette[ch] !== undefined) {
    const { hex, alpha } = parseColor(palette[ch]);
    if (alpha === 1) { solidHexes.add(hex); fills.add(hex); }
    else {
      fills.add(hex + '@' + alpha);
      if (!(alpha > 0 && alpha < 1)) errors.push(`Nieprawidłowa przezroczystość ${alpha} w znaku '${ch}'`);
      else if (!allowedTranslucent.has(hex + '@' + alpha)) errors.push(`Półprzezroczysty kolor ${palette[ch]} w znaku '${ch}' spoza dozwolonych (${[...allowedTranslucent].join(', ')})`);
    }
    if (hex === '#000000' && alpha === 1) errors.push(`Czysta czerń (#000000) w znaku '${ch}'`);
  }
  if (fills.size > maxColors) errors.push(`Kolorów ${fills.size}, limit ${maxColors}`);
  if (mode) {
    const allowed = new Set(allowedColors(mode));
    for (const hex of solidHexes) if (!allowed.has(hex)) errors.push(`Kolor ${hex} spoza palety ${mode}`);
  }
  const grid = rowsToGrid(rows.map(r => r.padEnd(width, '.')));
  const isOpaque = ch => ch !== '.' && palette[ch] !== undefined && !shadowChars.includes(ch) && parseColor(palette[ch]).alpha === 1;
  const hexAt = (x, y) => parseColor(palette[getCell(grid, x, y)]).hex;
  const boundary = [], opaque = [];
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    if (!isOpaque(getCell(grid, x, y))) continue;
    opaque.push([x, y]);
    if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => !isOpaque(getCell(grid, x + dx, y + dy)))) boundary.push([x, y]);
  }
  const stats = { width, height, colors: fills.size, maxColors, opaquePixels: opaque.length };
  if (!edgeTouchAllowed && opaque.some(([x, y]) => x === 0 || y === 0 || x === width - 1)) warnings.push('Piksele sprite\'a dotykają górnej, lewej lub prawej krawędzi płótna (przycięty?)');
  if (mode === 'PIXELART' && boundary.length) {
    const contours = new Set(Object.values(PALETTES.CONTOUR));
    const share = boundary.filter(([x, y]) => contours.has(hexAt(x, y))).length / boundary.length;
    stats.contourShare = Number(share.toFixed(2));
    if (share < 0.9) warnings.push(`Kontur na ${Math.round(share * 100)}% pikseli brzegowych, oczekiwano co najmniej 90%`);
  }
  if (mode === 'PRERENDER' && boundary.length) {
    const contours = new Set(Object.values(PALETTES.CONTOUR));
    if (boundary.some(([x, y]) => contours.has(hexAt(x, y)))) warnings.push('PRERENDER nie używa konturu, a na brzegu są kolory konturu PIXELART');
  }
  if (ground && boundary.length) {
    const ratios = boundary.map(([x, y]) => contrast(hexAt(x, y), ground));
    const low = ratios.filter(r => r < 1.3).length / ratios.length;
    stats.edgeContrast = { min: Number(Math.min(...ratios).toFixed(2)), mean: Number((ratios.reduce((a, b) => a + b, 0) / ratios.length).toFixed(2)), lowShare: Number(low.toFixed(2)) };
    if (low > 0.25) warnings.push(`${Math.round(low * 100)}% pikseli brzegowych ma kontrast < 1.3 względem tła, sylwetka może zlewać się z podłożem`);
  }
  if (lightCheck && opaque.length > 8) {
    const sums = opaque.map(([x, y]) => x + y).sort((a, b) => a - b), median = sums[Math.floor(sums.length / 2)];
    const mean = list => list.reduce((acc, [x, y]) => acc + luminance(hexAt(x, y)), 0) / Math.max(1, list.length);
    const lit = mean(opaque.filter(([x, y]) => x + y < median)), dark = mean(opaque.filter(([x, y]) => x + y >= median));
    stats.lightDirection = { topLeftMean: Number(lit.toFixed(3)), bottomRightMean: Number(dark.toFixed(3)) };
    if (lit < dark) warnings.push('Lewa górna połowa jest ciemniejsza niż prawa dolna, sprawdź kierunek światła (heurystyka)');
  }
  return { ok: errors.length === 0, errors, warnings, stats };
}

// ---------- Raster (podgląd 1:1 i skalowany, PNG) ----------
function rasterize(rows, palette, opts = {}) {
  const { background = null } = opts, width = opts.width ?? Math.max(...rows.map(r => r.length)), height = opts.height ?? rows.length;
  const data = new Uint8Array(width * height * 4);
  if (background) fillRgba({ width, height, data }, background);
  const target = { width, height, data };
  const source = { width, height, data: new Uint8Array(width * height * 4) };
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const ch = rows[y][x] ?? '.';
    if (ch === '.') continue;
    const { hex, alpha } = parseColor(palette[ch]), [r, g, b] = hexToRgb(hex), i = (y * width + x) * 4;
    source.data.set([r, g, b, Math.round(alpha * 255)], i);
  }
  blit(target, source, 0, 0);
  return target;
}
function fillRgba(image, hex) { const [r, g, b] = hexToRgb(hex); for (let i = 0; i < image.data.length; i += 4) image.data.set([r, g, b, 255], i); }
function blit(target, source, dx, dy) {
  for (let y = 0; y < source.height; y++) for (let x = 0; x < source.width; x++) {
    const tx = x + dx, ty = y + dy;
    if (tx < 0 || ty < 0 || tx >= target.width || ty >= target.height) continue;
    const s = (y * source.width + x) * 4, t = (ty * target.width + tx) * 4, sa = source.data[s + 3] / 255;
    if (sa === 0) continue;
    const ta = target.data[t + 3] / 255, oa = sa + ta * (1 - sa);
    for (let c = 0; c < 3; c++) target.data[t + c] = Math.round((source.data[s + c] * sa + target.data[t + c] * ta * (1 - sa)) / oa);
    target.data[t + 3] = Math.round(oa * 255);
  }
}
function upscale(image, factor) {
  const out = { width: image.width * factor, height: image.height * factor, data: new Uint8Array(image.width * image.height * factor * factor * 4) };
  for (let y = 0; y < out.height; y++) for (let x = 0; x < out.width; x++)
    out.data.set(image.data.subarray(((Math.floor(y / factor)) * image.width + Math.floor(x / factor)) * 4, ((Math.floor(y / factor)) * image.width + Math.floor(x / factor)) * 4 + 4), (y * out.width + x) * 4);
  return out;
}
function sceneToRgba(composed, background = null) {
  const image = { width: composed.width, height: composed.height, data: new Uint8Array(composed.width * composed.height * 4) };
  if (background) fillRgba(image, background);
  for (const { sprite, x, y } of composed.items) blit(image, rasterize(sprite.rows, sprite.palette, { width: sprite.width, height: sprite.height }), x, y);
  return image;
}
function encodePng(image) { // tylko node
  const zlib = require('zlib'), table = [];
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; table[n] = c >>> 0; }
  const crc = buf => { let c = 0xFFFFFFFF; for (const byte of buf) c = table[(c ^ byte) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
  const chunk = (type, body) => {
    const head = Buffer.alloc(8); head.writeUInt32BE(body.length, 0); head.write(type, 4, 'ascii');
    const tail = Buffer.alloc(4); tail.writeUInt32BE(crc(Buffer.concat([head.subarray(4), body])), 0);
    return Buffer.concat([head, body, tail]);
  };
  const header = Buffer.alloc(13); header.writeUInt32BE(image.width, 0); header.writeUInt32BE(image.height, 4); header.set([8, 6, 0, 0, 0], 8);
  const raw = Buffer.alloc((image.width * 4 + 1) * image.height);
  for (let y = 0; y < image.height; y++) { raw[y * (image.width * 4 + 1)] = 0; Buffer.from(image.data.buffer, image.data.byteOffset + y * image.width * 4, image.width * 4).copy(raw, y * (image.width * 4 + 1) + 1); }
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', header), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

const api = {
  PALETTES, tone, contourOf, allowedColors, parseColor, luminance, contrast,
  makeGrid, getCell, setCell, gridToRows, rowsToGrid, noise,
  fillRect, fillPolygon, drawLine, fillDiamond, fillEllipse, shadeEllipse, shadeRegion, scatter, rimDarken, outline,
  isoPoint, isoBox, hipRoof, isoToScreen, makeSprite, composeScene,
  asciiToSvg, sceneToSvg, validateScene, colorLimit, safeSvgId, validate, rasterize, blit, upscale, sceneToRgba, encodePng,
};
if (typeof module !== 'undefined') module.exports = api;
