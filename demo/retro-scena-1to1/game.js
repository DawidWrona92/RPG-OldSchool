'use strict';

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;

const VIEW_W = canvas.width;
const VIEW_H = canvas.height;

const IMG1 = new Image();
const IMG2 = new Image();
IMG1.src = 'assets/scena1.jpg';
IMG2.src = 'assets/scena2.jpg';

const scenes = {
  brama: {
    img: IMG1,
    name: 'Niemir — brama osady',
    walkMinY: 0.50,
    walkMaxY: 0.93,
    corridor: { x0: 0.42, x1: 0.58, minY: 0.36 },
    exit: { type: 'up', x0: 0.44, x1: 0.56, y: 0.37, to: 'osada' }
  },
  osada: {
    img: IMG2,
    name: 'Niemir — wnętrze osady',
    walkMinY: 0.44,
    walkMaxY: 0.92,
    exit: { type: 'down', y: 0.91, to: 'brama' }
  }
};

let currentScene = 'brama';

const COL = {
  outline: '#0c0d12',
  skin: '#c8996f', skinD: '#9a6f4a',
  heroTunic: '#7a5a2e', heroTunicD: '#57401f', heroTunicL: '#97713c',
  pants: '#3a2f1e', boot: '#221c12',
  shield: '#6d5a34', shieldD: '#4a3c20', shieldEdge: '#8a7444',
  blade: '#b9c2cf', bladeD: '#7f8798', hilt: '#5c4322',
  guardArmor: '#5a6270', guardArmorD: '#3c4350', guardArmorL: '#7f8798',
  guardCloak: '#5c1f24', plume: '#a83232',
  dress: '#d8d5c8', dressD: '#a8a696', apron: '#8c2f2f',
  villagerTunic: '#6a4c2a', villagerTunicD: '#4d361e', hat: '#4a3a24',
  smithTunic: '#59422e', smithD: '#3d2c1c',
  horseBody: '#5a4028', horseD: '#3d2b18', horseMane: '#241a10',
  chicken: '#e8e4d8', chickenD: '#b8b4a8', comb: '#c23a2a',
  breath: 'rgba(220,235,255,'
};

const keys = {};
addEventListener('keydown', e => {
  keys[e.key.toLowerCase()] = true;
  if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(e.key.toLowerCase())) e.preventDefault();
});
addEventListener('keyup', e => { keys[e.key.toLowerCase()] = false; });

function px(x, y, w, h, c) {
  ctx.fillStyle = c;
  ctx.fillRect(Math.round(x), Math.round(y), w, h);
}

function drawCover(img) {
  const s = Math.max(VIEW_W / img.width, VIEW_H / img.height);
  const w = img.width * s, h = img.height * s;
  ctx.drawImage(img, (VIEW_W - w) / 2, (VIEW_H - h) / 2, w, h);
}

function breathOffset(t, phase) {
  const p = (Math.sin((t / 1000) * Math.PI * 2 * 0.7 + phase) + 1) / 2;
  return Math.round(p);
}

function drawBreath(x, y, t, phase, facing) {
  const cycle = ((t / 1000) * 0.55 + phase) % 1;
  if (cycle > 0.45) return;
  const k = cycle / 0.45;
  const drift = k * 9;
  const rise = Math.sin(k * Math.PI) * 4;
  const size = 1 + Math.round(k * 2);
  const a = (1 - k) * 0.45;
  const dx = facing === 'left' ? -3 - drift : 3 + drift;
  ctx.globalAlpha = a;
  px(x + dx, y - rise, size, Math.max(1, size - 1), COL.breath + '1)');
  ctx.globalAlpha = a * 0.6;
  px(x + dx + (facing === 'left' ? -1 : 1), y - rise - 1, size, 1, COL.breath + '1)');
  ctx.globalAlpha = 1;
}

function drawShadow(x, y, w) {
  ctx.globalAlpha = 0.3;
  px(x - w / 2 + 1, y, w, 2, '#000');
  ctx.globalAlpha = 1;
}

function drawLegs(x, y, walkT, moving) {
  const step = moving ? Math.sin(walkT / 80) : 0;
  const l1 = Math.round(step * 2), l2 = -l1;
  px(x - 4, y - 8, 4, 8 + l1, COL.pants);
  px(x + 1, y - 8, 4, 8 + l2, COL.pants);
  px(x - 4, y - 2 + l1, 4, 2, COL.boot);
  px(x + 1, y - 2 + l2, 4, 2, COL.boot);
}

// HERO — brązowe ubranie, miecz i tarcza (jak na screenie 1)
function drawHero(h, t) {
  const x = Math.round(h.x), y = Math.round(h.y);
  const b = breathOffset(t, h.breathPhase);
  const bob = h.moving ? (Math.sin(h.walkT / 80) > 0 ? 1 : 0) : b;
  drawShadow(x, y + 1, 13);
  drawLegs(x, y, h.walkT, h.moving);
  // torso
  px(x - 5, y - 22 + bob, 11, 14, COL.heroTunic);
  px(x - 5, y - 22 + bob, 4, 14, COL.heroTunicL);
  px(x + 4, y - 22 + bob, 2, 14, COL.heroTunicD);
  // head
  px(x - 3, y - 28 + bob, 7, 6, COL.skin);
  px(x - 3, y - 23 + bob, 7, 1, COL.skinD);
  px(x - 4, y - 30 + bob, 9, 3, '#4c3a22');
  const ex = h.facing === 'left' ? x - 2 : x + 2;
  px(ex, y - 26 + bob, 1, 1, COL.outline);
  // shield (lewa ręka)
  const shx = h.facing === 'left' ? x + 5 : x - 11;
  px(shx, y - 21 + bob, 7, 10, COL.shield);
  px(shx, y - 21 + bob, 7, 1, COL.shieldEdge);
  px(shx + 1, y - 18 + bob, 5, 4, COL.shieldD);
  // miecz (prawa ręka, ostrze w dół)
  const swx = h.facing === 'left' ? x - 9 : x + 7;
  px(swx, y - 20 + bob, 1, 3, COL.hilt);
  px(swx, y - 17 + bob, 2, 12, COL.blade);
  px(swx + 1, y - 17 + bob, 1, 12, COL.bladeD);
  drawBreath(x, y - 24 + bob, t, h.breathPhase + 0.35, h.facing);
}

// STRAŻNIK przy bramie — zbroja, hełm z pióropuszem, włócznia
function drawGuard(wx, wy, t, phase) {
  const x = Math.round(wx * VIEW_W), y = Math.round(wy * VIEW_H);
  const b = breathOffset(t, phase);
  drawShadow(x, y + 1, 13);
  drawLegs(x, y, t, false);
  px(x - 5, y - 22 + b, 11, 14, COL.guardArmor);
  px(x - 5, y - 22 + b, 4, 14, COL.guardArmorL);
  px(x + 4, y - 22 + b, 2, 14, COL.guardArmorD);
  px(x - 7, y - 21 + b, 2, 12, COL.guardCloak);
  px(x - 3, y - 28 + b, 7, 6, COL.skin);
  px(x - 4, y - 30 + b, 9, 4, COL.guardArmor);
  px(x - 4, y - 32 + b, 9, 2, COL.guardArmorL);
  px(x - 2, y - 34 + b, 5, 2, COL.plume);
  px(x + 2, y - 26 + b, 1, 1, COL.outline);
  // włócznia
  px(x + 8, y - 34 + b, 1, 34, '#3a2a1a');
  px(x + 7, y - 37 + b, 3, 3, '#9aa4b5');
  drawBreath(x, y - 24 + b, t, phase, 'right');
}

// KOŃ przy ogrodzeniu — macha ogonem
function drawHorse(wx, wy, t) {
  const x = Math.round(wx * VIEW_W), y = Math.round(wy * VIEW_H);
  ctx.globalAlpha = 0.3;
  px(x - 16, y, 32, 2, '#000');
  ctx.globalAlpha = 1;
  px(x - 14, y - 14, 26, 12, COL.horseBody);
  px(x - 14, y - 14, 26, 3, '#6d5030');
  px(x - 14, y - 4, 3, 4, COL.horseD);
  px(x + 8, y - 4, 3, 4, COL.horseD);
  px(x + 10, y - 26, 8, 12, COL.horseBody);
  px(x + 10, y - 26, 8, 4, COL.horseMane);
  px(x + 15, y - 22, 4, 3, COL.horseD);
  px(x + 12, y - 30, 3, 5, COL.horseMane);
  const tail = Math.sin(t / 500) > 0 ? 0 : 1;
  px(x - 16, y - 16 + tail, 3, 8, COL.horseMane);
}

// KOBIETA w białej sukni z czerwonym fartuchem
function drawWoman(wx, wy, t, phase) {
  const x = Math.round(wx * VIEW_W), y = Math.round(wy * VIEW_H);
  const b = breathOffset(t, phase);
  drawShadow(x, y + 1, 12);
  px(x - 5, y - 8, 11, 8, COL.dress);
  px(x - 5, y - 3, 11, 3, COL.dressD);
  px(x - 3, y - 8, 7, 7, COL.apron);
  px(x - 4, y - 20 + b, 9, 12, COL.dress);
  px(x - 4, y - 10 + b, 9, 3, COL.dressD);
  px(x - 2, y - 26 + b, 6, 6, COL.skin);
  px(x - 3, y - 28 + b, 8, 3, '#7a4a28');
  px(x - 2, y - 24 + b, 1, 1, COL.outline);
  px(x + 2, y - 24 + b, 1, 1, COL.outline);
  drawBreath(x, y - 22 + b, t, phase, 'right');
}

// WIEŚNIAK z kapeluszem i kijem
function drawVillager(wx, wy, t, phase) {
  const x = Math.round(wx * VIEW_W), y = Math.round(wy * VIEW_H);
  const b = breathOffset(t, phase);
  drawShadow(x, y + 1, 12);
  drawLegs(x, y, t, false);
  px(x - 5, y - 20 + b, 11, 12, COL.villagerTunic);
  px(x - 5, y - 20 + b, 4, 12, '#7d5a32');
  px(x + 4, y - 20 + b, 2, 12, COL.villagerTunicD);
  px(x - 2, y - 26 + b, 6, 6, COL.skin);
  px(x - 3, y - 28 + b, 9, 2, COL.hat);
  px(x - 1, y - 24 + b, 1, 1, COL.outline);
  px(x + 2, y - 24 + b, 1, 1, COL.outline);
  px(x + 7, y - 24 + b, 1, 24, '#4a3820');
  drawBreath(x, y - 22 + b, t, phase, 'left');
}

// KOWAL przy kowadle
function drawSmith(wx, wy, t, phase) {
  const x = Math.round(wx * VIEW_W), y = Math.round(wy * VIEW_H);
  const b = breathOffset(t, phase);
  const hammer = Math.sin(t / 300 + phase);
  drawShadow(x, y + 1, 13);
  drawLegs(x, y, t, false);
  px(x - 5, y - 20 + b, 11, 12, COL.smithTunic);
  px(x - 5, y - 20 + b, 4, 12, '#6d5438');
  px(x + 4, y - 20 + b, 2, 12, COL.smithD);
  px(x - 2, y - 26 + b, 6, 6, COL.skin);
  px(x - 3, y - 28 + b, 9, 2, '#241a10');
  px(x - 1, y - 24 + b, 1, 1, COL.outline);
  px(x + 2, y - 24 + b, 1, 1, COL.outline);
  // młot nad kowadłem
  const hx = x + 8, hy = y - 20 + b - Math.round(hammer * 4);
  px(hx, hy, 6, 3, '#5c5c66');
  px(hx + 1, hy + 3, 1, 6, '#4a3820');
  // kowadło
  px(x + 6, y - 6, 10, 4, '#3c3c46');
  px(x + 6, y - 6, 10, 1, '#55555f');
  px(x + 9, y - 2, 3, 2, '#2a2a32');
  // iskry
  if (hammer > 0.9) {
    ctx.globalAlpha = 0.8;
    px(x + 12, y - 9, 1, 1, '#ffb347');
    px(x + 14, y - 11, 1, 1, '#ff8c47');
    ctx.globalAlpha = 1;
  }
  drawBreath(x, y - 22 + b, t, phase, 'right');
}

// KURA — dziobie ziemię
function drawChicken(wx, wy, t, phase) {
  const x = Math.round(wx * VIEW_W), y = Math.round(wy * VIEW_H);
  const peck = Math.sin(t / 260 + phase) > 0.6 ? 1 : 0;
  px(x, y - 4, 6, 4, COL.chicken);
  px(x, y - 4, 6, 1, COL.chickenD);
  px(x + 5, y - 5 + peck, 3, 3, COL.chicken);
  px(x + 7, y - 4 + peck, 2, 1, COL.comb);
  px(x + 5, y - 5 + peck, 1, 1, '#e8a030');
  px(x + 1, y, 1, 1, COL.comb);
  px(x + 4, y, 1, 1, COL.comb);
}

// ---------- stany ----------

const hero = {
  x: VIEW_W * 0.5, y: VIEW_H * 0.86,
  facing: 'right', moving: false, walkT: 0, breathPhase: 0.3,
  speed: 0.09, runSpeed: 0.16
};

const npcsBrama = [
  { kind: 'horse', x: 0.13, y: 0.66 },
  { kind: 'guard', x: 0.60, y: 0.52, phase: 0.1 }
];

const npcsOsada = [
  { kind: 'woman', x: 0.16, y: 0.56, phase: 0.55 },
  { kind: 'villager', x: 0.34, y: 0.60, phase: 0.2 },
  { kind: 'smith', x: 0.80, y: 0.52, phase: 0.8 },
  { kind: 'chicken', x: 0.42, y: 0.72, phase: 0.3 },
  { kind: 'chicken', x: 0.47, y: 0.76, phase: 0.9 }
];

let fade = 0; // 0..1 przejście
let fadeDir = 0;

function walkable(nx, ny) {
  const s = scenes[currentScene];
  const fx = nx / VIEW_W, fy = ny / VIEW_H;
  if (fy > s.walkMaxY) return false;
  if (fy < s.walkMinY) {
    if (s.corridor && fx > s.corridor.x0 && fx < s.corridor.x1 && fy > s.corridor.minY) {
      // korytarz ścieżki do bramy — dozwolony
    } else {
      return false;
    }
  }
  return true;
}

function tryTransition() {
  const s = scenes[currentScene];
  const e = s.exit;
  const fx = hero.x / VIEW_W, fy = hero.y / VIEW_H;
  if (e.type === 'up' && fy <= e.y && fx > e.x0 && fx < e.x1) {
    startTransition(e.to, VIEW_W * 0.5, VIEW_H * 0.88);
  } else if (e.type === 'down' && fy >= e.y) {
    startTransition(e.to, VIEW_W * 0.5, VIEW_H * 0.46);
  }
}

function startTransition(to, nx, ny) {
  if (fadeDir !== 0) return;
  fadeDir = 1;
  fade = 0;
  const doSwitch = () => {
    currentScene = to;
    hero.x = nx; hero.y = ny;
  };
  window.__pendingSwitch = doSwitch;
}

function update(dt) {
  const left = keys['a'] || keys['arrowleft'];
  const right = keys['d'] || keys['arrowright'];
  const up = keys['w'] || keys['arrowup'];
  const down = keys['s'] || keys['arrowdown'];
  const run = keys['shift'];
  const sp = (run ? hero.runSpeed : hero.speed) * dt / 16;

  if (fadeDir !== 0) {
    fade += fadeDir * dt / 350;
    if (fade >= 1 && fadeDir === 1) {
      fade = 1; fadeDir = -1;
      if (window.__pendingSwitch) { window.__pendingSwitch(); window.__pendingSwitch = null; }
    } else if (fade <= 0 && fadeDir === -1) {
      fade = 0; fadeDir = 0;
    }
    return;
  }

  let dx = (right ? 1 : 0) - (left ? 1 : 0);
  let dy = (down ? 1 : 0) - (up ? 1 : 0);
  if (dx && dy) { dx *= 0.707; dy *= 0.707; }
  hero.moving = !!(dx || dy);
  if (hero.moving) {
    hero.walkT += dt * (run ? 1.7 : 1);
    if (dx < 0) hero.facing = 'left';
    if (dx > 0) hero.facing = 'right';
    const nx = Math.max(10, Math.min(VIEW_W - 10, hero.x + dx * sp * 2.2));
    const ny = hero.y + dy * sp * 1.6;
    if (walkable(nx, hero.y)) hero.x = nx;
    if (walkable(hero.x, ny)) hero.y = ny;
    tryTransition();
  }
}

function drawNpc(n, t) {
  switch (n.kind) {
    case 'horse': drawHorse(n.x, n.y, t); break;
    case 'guard': drawGuard(n.x, n.y, t, n.phase); break;
    case 'woman': drawWoman(n.x, n.y, t, n.phase); break;
    case 'villager': drawVillager(n.x, n.y, t, n.phase); break;
    case 'smith': drawSmith(n.x, n.y, t, n.phase); break;
    case 'chicken': drawChicken(n.x, n.y, t, n.phase); break;
  }
}

function render(t) {
  const s = scenes[currentScene];
  ctx.fillStyle = '#0a0c12';
  ctx.fillRect(0, 0, VIEW_W, VIEW_H);
  if (s.img.complete && s.img.naturalWidth) drawCover(s.img);

  const npcs = currentScene === 'brama' ? npcsBrama : npcsOsada;
  const all = [...npcs.map(n => ({ y: n.y * VIEW_H, draw: () => drawNpc(n, t) }))];
  all.push({ y: hero.y, draw: () => drawHero(hero, t) });
  all.sort((a, b) => a.y - b.y);
  for (const e of all) e.draw();

  // podpowiedź przy przejściu
  ctx.font = 'bold 13px "Courier New", monospace';
  ctx.textAlign = 'center';
  if (currentScene === 'brama') {
    ctx.fillStyle = 'rgba(255,214,140,0.9)';
    ctx.fillText('W — wejście przez bramę', VIEW_W * 0.5, VIEW_H * 0.40);
  } else {
    ctx.fillStyle = 'rgba(255,214,140,0.75)';
    ctx.fillText('S — powrót do bramy', VIEW_W * 0.5, VIEW_H * 0.97);
  }
  ctx.textAlign = 'left';
  ctx.fillStyle = 'rgba(255,255,255,0.85)';
  ctx.fillText(s.name, 10, 18);

  if (fade > 0) {
    ctx.fillStyle = `rgba(0,0,0,${fade})`;
    ctx.fillRect(0, 0, VIEW_W, VIEW_H);
  }
}

let last = performance.now();
function loop(t) {
  const dt = Math.min(50, t - last);
  last = t;
  update(dt);
  render(t);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
