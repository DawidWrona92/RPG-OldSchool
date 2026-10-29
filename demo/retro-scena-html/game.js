'use strict';

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;

const VIEW_W = canvas.width;
const VIEW_H = canvas.height;
const WORLD_W = 960;

const WALK_MIN_Y = 98;
const WALK_MAX_Y = 150;

const COL = {
  sky0: '#0a0f1e', sky1: '#18233d',
  star: '#c9d6ff', moon: '#e8ecff',
  forestFar: '#0c151f', forestNear: '#122019',
  trunk: '#241a12', trunkL: '#3a2a1a',
  grass: '#1b2917', grassD: '#12200f',
  dirt: '#3a2e22', dirtL: '#4d3d2c', dirtD: '#281f16',
  road: '#4a3a28', roadD: '#342818',
  water: '#14304a', waterL: '#2a5578', waterD: '#0b1a2a',
  wood: '#4a3624', woodL: '#6b4f33', woodD: '#2e2116',
  stake: '#5c4530',
  roof: '#4a3520', roofL: '#6b4f2c',
  straw: '#7a6a3a', strawD: '#5a4c28',
  outline: '#0c0d12',
  skin: '#c8996f', skinD: '#9a6f4a',
  guardArmor: '#5a6270', guardArmorD: '#3c4350', guardArmorL: '#7f8798',
  guardCloak: '#5c1f24',
  villagerTunic: '#6a4c2a', villagerTunicD: '#4d361e',
  heroCloak: '#6a2a30', heroCloakD: '#4a1c22',
  heroTunic: '#3d4c5c', heroTunicD: '#2a3644',
  pants: '#2c2418', boot: '#1c1812',
  lanternOn: '#ffd27a', lanternGlow: 'rgba(255,190,90,0.10)',
  window: '#ffb35c',
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

function drawSky(camX) {
  const grad = ctx.createLinearGradient(0, 0, 0, 96);
  grad.addColorStop(0, COL.sky0);
  grad.addColorStop(1, COL.sky1);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, VIEW_W, 96);

  const stars = [];
  let s = 1;
  for (let i = 0; i < 70; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const x = (s % WORLD_W);
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const y = (s % 72);
    stars.push([x, y]);
  }
  for (const [x, y] of stars) {
    const sx = x - camX * 0.3;
    const wrapped = ((sx % WORLD_W) + WORLD_W) % WORLD_W;
    if (wrapped < VIEW_W) px(wrapped, y, 1, 1, COL.star);
  }
  const mx = 420 - camX * 0.2;
  px(mx, 14, 14, 14, COL.moon);
  px(mx - 2, 16, 18, 10, COL.moon);
  px(mx + 3, 11, 8, 18, COL.moon);
  px(mx - 2, 16, 18, 10, COL.moon);
}

function drawForestBand(y, h, colBase, colTrunk, camX, par, density, seedOff) {
  px(0, y, VIEW_W, h, colBase);
  let s = seedOff;
  for (let i = 0; i < density; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const wx = (s % WORLD_W);
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const ty = y + (s % Math.max(1, h - 10));
    const sx = wx - camX * par;
    const wrapped = ((sx % WORLD_W) + WORLD_W) % WORLD_W;
    const x = wrapped > WORLD_W - 20 ? wrapped - WORLD_W : wrapped;
    px(x, ty, 2, h - (ty - y), colTrunk);
    px(x - 2, ty, 6, 3, colBase);
    px(x - 1, ty + 3, 4, 2, colBase);
  }
}

function drawBackground(camX) {
  drawForestBand(56, 18, COL.forestFar, '#101c26', camX, 0.45, 26, 7);
  drawForestBand(70, 26, COL.forestNear, COL.trunk, camX, 0.7, 20, 91);
}

function drawGround(camX) {
  px(0, 96, VIEW_W, VIEW_H - 96, COL.grass);
  let s = 13;
  for (let i = 0; i < 120; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const x = (s % WORLD_W) - camX;
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const y = 98 + (s % (VIEW_H - 100));
    px(x, y, 2, 1, COL.grassD);
  }
  // stream (foreground band)
  const wy = 152;
  px(0, wy, VIEW_W, 12, COL.waterD);
  px(0, wy + 1, VIEW_W, 7, COL.water);
  for (let i = 0; i < 30; i++) {
    const x = ((i * 41 + Math.floor(performance.now() / 300)) % (WORLD_W + 40)) - camX;
    px(((x % (WORLD_W + 40)) + WORLD_W + 40) % (WORLD_W + 40) - 20, wy + 2 + (i % 5), 6, 1, COL.waterL);
  }
  px(0, wy + 11, VIEW_W, 1, '#0a141f');
}

function drawRoad(camX) {
  // main dirt road along the walking band
  px(0, 112, VIEW_W, 30, COL.road);
  px(0, 112, VIEW_W, 1, COL.roadD);
  px(0, 141, VIEW_W, 1, COL.roadD);
  let s = 55;
  for (let i = 0; i < 90; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const x = (s % WORLD_W) - camX;
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const y = 114 + (s % 26);
    px(x, y, 3, 1, COL.roadD);
  }
}

// ---------- buildings ----------

function drawPalisadeSection(wx, wy) {
  const x = wx, y = wy;
  px(x, y, 3, 22, COL.wood);
  px(x, y, 1, 22, COL.woodL);
  px(x, y - 2, 3, 2, COL.stake);
}

function drawPalisade(wx, wy, count, camX) {
  for (let i = 0; i < count; i++) {
    const sx = wx + i * 5 - camX;
    if (sx > -6 && sx < VIEW_W + 6) drawPalisadeSection(sx, wy);
  }
}

function drawGateTower(wx, camX, t) {
  const x = Math.round(wx - camX);
  if (x < -60 || x > VIEW_W + 60) return;
  const y = 66;
  // tower body
  px(x, y, 24, 34, COL.wood);
  px(x, y, 3, 34, COL.woodL);
  px(x + 21, y, 3, 34, COL.woodD);
  // roof
  px(x - 2, y - 6, 28, 3, COL.roofL);
  px(x, y - 3, 24, 3, COL.roof);
  // window with warm light flicker
  const flick = 0.75 + 0.25 * Math.sin(t / 260);
  px(x + 10, y + 6, 5, 7, COL.window);
  ctx.globalAlpha = 0.25 * flick;
  px(x + 8, y + 4, 9, 11, COL.lanternOn);
  ctx.globalAlpha = 1;
  // gate posts
  px(x - 4, y + 34, 6, 14, COL.wood);
  px(x + 22, y + 34, 6, 14, COL.wood);
  // gate doors (slightly open)
  px(x + 2, y + 34, 8, 16, COL.woodD);
  px(x + 14, y + 34, 8, 16, COL.woodD);
  px(x + 2, y + 34, 8, 1, COL.wood);
  px(x + 14, y + 34, 8, 1, COL.wood);
  // lantern on the left post
  px(x - 3, y + 30, 4, 6, COL.woodD);
  px(x - 2, y + 31, 2, 4, COL.lanternOn);
  ctx.globalAlpha = 0.35 * flick;
  px(x - 5, y + 29, 8, 8, COL.lanternOn);
  ctx.globalAlpha = 1;
}

function drawHut(wx, camX, t, variant) {
  const x = Math.round(wx - camX);
  if (x < -60 || x > VIEW_W + 60) return;
  const y = 74;
  const w = variant ? 30 : 24;
  // wall
  px(x, y, w, 22, variant ? COL.wood : COL.woodD);
  px(x, y, w, 2, variant ? COL.woodL : COL.wood);
  // thatched roof
  px(x - 3, y - 7, w + 6, 5, COL.straw);
  px(x - 2, y - 2, w + 4, 3, COL.strawD);
  // window glow
  const flick = 0.7 + 0.3 * Math.sin(t / 200 + wx);
  px(x + 5, y + 8, 5, 5, COL.window);
  ctx.globalAlpha = 0.25 * flick;
  px(x + 3, y + 6, 9, 9, COL.lanternOn);
  ctx.globalAlpha = 1;
  // chimney + smoke
  px(x + w - 8, y - 10, 3, 5, COL.woodD);
  const puff = Math.floor((t / 420 + wx) % 4);
  ctx.globalAlpha = 0.28;
  px(x + w - 8 + puff, y - 14 - puff * 2, 2, 2, '#8a93a8');
  px(x + w - 9 + puff * 2, y - 18 - puff * 2, 3, 2, '#6a7488');
  ctx.globalAlpha = 1;
}

function drawCart(wx, camX) {
  const x = Math.round(wx - camX);
  if (x < -40 || x > VIEW_W + 40) return;
  const y = 124;
  px(x, y, 20, 6, COL.wood);
  px(x, y, 20, 1, COL.woodL);
  px(x + 1, y + 6, 2, 4, COL.woodD);
  px(x + 16, y + 6, 2, 4, COL.woodD);
  px(x + 1, y + 10, 5, 5, COL.woodD);
  px(x + 14, y + 10, 5, 5, COL.woodD);
  px(x + 2, y + 11, 3, 3, '#0e0f14');
  px(x + 15, y + 11, 3, 3, '#0e0f14');
  px(x + 3, y - 3, 14, 3, COL.strawD);
}

function drawBridge(camX) {
  const x = Math.round(300 - camX);
  px(x, 150, 60, 4, COL.wood);
  px(x, 150, 60, 1, COL.woodL);
  px(x, 154, 60, 2, COL.woodD);
  for (let i = 0; i < 5; i++) px(x + 4 + i * 12, 156, 3, 6, COL.woodD);
}

function drawLanternPost(wx, camX, t) {
  const x = Math.round(wx - camX);
  if (x < -20 || x > VIEW_W + 20) return;
  const y = 108;
  px(x, y, 2, 26, COL.woodD);
  px(x - 2, y - 4, 6, 6, COL.woodD);
  const flick = 0.7 + 0.3 * Math.sin(t / 180 + wx * 2);
  px(x - 1, y - 3, 4, 4, COL.lanternOn);
  ctx.globalAlpha = 0.4 * flick;
  px(x - 4, y - 6, 10, 10, COL.lanternOn);
  ctx.globalAlpha = 1;
  ctx.fillStyle = COL.lanternGlow;
  ctx.beginPath();
  ctx.arc(x + 1, y - 1, 26, 0, Math.PI * 2);
  ctx.fill();
}

// ---------- characters ----------

// breath phase p: 0..1, returns vertical offset in px
function breathOffset(t, phase) {
  const p = (Math.sin((t / 1000) * Math.PI * 2 * 0.7 + phase) + 1) / 2;
  return Math.round(p * 1);
}

function drawBreath(x, y, t, phase, facing) {
  const cycle = ((t / 1000) * 0.55 + phase) % 1;
  if (cycle > 0.45) return;
  const k = cycle / 0.45;
  const drift = k * 10;
  const rise = Math.sin(k * Math.PI) * 5;
  const size = 1 + Math.round(k * 2);
  const a = (1 - k) * 0.5;
  const dx = facing === 'left' ? -3 - drift : 3 + drift;
  ctx.globalAlpha = a;
  px(x + dx, y - rise, size, Math.max(1, size - 1), COL.breath + '1)');
  ctx.globalAlpha = a * 0.6;
  px(x + dx + (facing === 'left' ? -1 : 1), y - rise - 1, size, 1, COL.breath + '1)');
  ctx.globalAlpha = 1;
}

function drawShadow(x, y, w) {
  ctx.globalAlpha = 0.35;
  px(x - w / 2 + 1, y, w, 2, '#000');
  ctx.globalAlpha = 1;
}

function drawLegs(x, y, walkT, moving) {
  const step = moving ? Math.sin(walkT / 90) : 0;
  const l1 = Math.round(step * 2);
  const l2 = -l1;
  px(x - 3, y - 6, 3, 6 + l1, COL.pants);
  px(x + 1, y - 6, 3, 6 + l2, COL.pants);
  px(x - 3, y - 1 + l1, 3, 2, COL.boot);
  px(x + 1, y - 1 + l2, 3, 2, COL.boot);
}

function drawGuard(wx, camX, t, phase) {
  const x = Math.round(wx - camX);
  if (x < -20 || x > VIEW_W + 20) return;
  const y = 126;
  const b = breathOffset(t, phase);
  drawShadow(x, y + 1, 10);
  drawLegs(x, y, t, false);
  // torso with armor
  px(x - 4, y - 16 + b, 9, 10, COL.guardArmor);
  px(x - 4, y - 16 + b, 3, 10, COL.guardArmorL);
  px(x + 3, y - 16 + b, 2, 10, COL.guardArmorD);
  // cloak
  px(x - 5, y - 15 + b, 2, 9, COL.guardCloak);
  // head + helmet
  px(x - 2, y - 21 + b, 6, 5, COL.skin);
  px(x - 2, y - 21 + b, 6, 2, COL.guardArmorD);
  px(x - 3, y - 22 + b, 8, 2, COL.guardArmor);
  px(x - 3, y - 24 + b, 8, 2, COL.guardArmorL);
  // spear
  px(x + 7, y - 26 + b, 1, 26, COL.trunkL);
  px(x + 6, y - 28 + b, 3, 3, '#9aa4b5');
  // face
  px(x + 2, y - 19 + b, 1, 1, COL.outline);
  drawBreath(x, y - 16 + b, t, phase, 'right');
}

function drawVillager(wx, camX, t, phase) {
  const x = Math.round(wx - camX);
  if (x < -20 || x > VIEW_W + 20) return;
  const y = 132;
  const b = breathOffset(t, phase);
  drawShadow(x, y + 1, 10);
  drawLegs(x, y, t, false);
  px(x - 4, y - 15 + b, 9, 9, COL.villagerTunic);
  px(x - 4, y - 15 + b, 3, 9, COL.villagerTunicD);
  px(x - 2, y - 20 + b, 6, 5, COL.skin);
  px(x - 3, y - 22 + b, 8, 3, '#3d3020');
  px(x - 1, y - 18 + b, 1, 1, COL.outline);
  px(x + 2, y - 18 + b, 1, 1, COL.outline);
  px(x - 4, y - 24 + b, 9, 3, '#5c4a30');
  px(x - 4, y - 24 + b, 9, 1, '#75603e');
  drawBreath(x, y - 15 + b, t, phase, 'left');
}

function drawHero(hero, t) {
  const x = Math.round(hero.x);
  const y = Math.round(hero.y);
  const b = breathOffset(t, hero.breathPhase);
  const moving = hero.moving;
  drawShadow(x, y + 1, 11);
  drawLegs(x, y, hero.walkT, moving);
  const bob = moving ? (Math.sin(hero.walkT / 90) > 0 ? 1 : 0) : b;
  // torso
  px(x - 4, y - 16 + bob, 9, 10, COL.heroTunic);
  px(x - 4, y - 16 + bob, 3, 10, '#4d5f72');
  px(x + 3, y - 16 + bob, 2, 10, COL.heroTunicD);
  // cloak (gray-streaked dark red)
  px(x - 6, y - 15 + bob, 2, 10, COL.heroCloak);
  px(x - 6, y - 11 + bob, 2, 1, COL.heroCloakD);
  // belt
  px(x - 4, y - 8 + bob, 9, 2, COL.boot);
  // head: long gray-streaked hair, gray-green eyes, full jaw
  px(x - 2, y - 21 + bob, 6, 5, COL.skin);
  px(x - 2, y - 17 + bob, 6, 1, COL.skinD);
  px(x - 3, y - 22 + bob, 8, 2, '#4c4a48');
  px(x - 3, y - 20 + bob, 2, 6, '#4c4a48');
  px(x + 4, y - 20 + bob, 2, 6, '#4c4a48');
  px(x - 3, y - 20 + bob, 2, 1, '#8a8880');
  px(x + 4, y - 19 + bob, 2, 1, '#8a8880');
  const eye = COL.outline;
  if (hero.facing === 'left') {
    px(x - 1, y - 19 + bob, 1, 1, eye);
  } else {
    px(x + 2, y - 19 + bob, 1, 1, eye);
  }
  // sword on the back
  px(x - 7, y - 14 + bob, 1, 12, '#9aa4b5');
  px(x - 8, y - 13 + bob, 3, 1, COL.trunkL);
  drawBreath(x, y - 16 + bob, t, hero.breathPhase + 0.35, hero.facing);
}

// ---------- entities ----------

const hero = {
  x: 120, y: 132,
  facing: 'right',
  moving: false,
  walkT: 0,
  breathPhase: 0.3,
  speed: 0.55,
  runSpeed: 0.95
};

const npcGuard = { x: 386, phase: 0.1 };
const npcVillager = { x: 160, phase: 0.6 };

// solid colliders: [x0, x1, y0, y1] in world coords
const solids = [
  [296, 356, 100, 114],  // gate tower footprint
  [640, 676, 100, 116],  // hut 1 footprint
  [800, 828, 100, 116],  // hut 2 footprint
  [540, 562, 116, 134],  // cart
  [690, 694, 104, 134],  // lantern post
  [500, 504, 104, 134]   // lantern post 2
];

function collides(nx, ny) {
  if (ny < WALK_MIN_Y || ny > WALK_MAX_Y) return true;
  const rx = nx, ry = ny - 2;
  for (const [x0, x1, y0, y1] of solids) {
    if (rx + 5 > x0 && rx - 5 < x1 && ry + 2 > y0 && ry - 24 < y1) return true;
  }
  return false;
}

function update(dt) {
  const left = keys['a'] || keys['arrowleft'];
  const right = keys['d'] || keys['arrowright'];
  const up = keys['w'] || keys['arrowup'];
  const down = keys['s'] || keys['arrowdown'];
  const run = keys['shift'];
  const sp = (run ? hero.runSpeed : hero.speed) * dt / 16;

  let dx = (right ? 1 : 0) - (left ? 1 : 0);
  let dy = (down ? 1 : 0) - (up ? 1 : 0);
  if (dx && dy) { dx *= 0.707; dy *= 0.707; }
  hero.moving = !!(dx || dy);
  if (hero.moving) {
    hero.walkT += dt * (run ? 1.6 : 1);
    if (dx < 0) hero.facing = 'left';
    if (dx > 0) hero.facing = 'right';
    const nx = Math.max(8, Math.min(WORLD_W - 8, hero.x + dx * sp * 2));
    const ny = hero.y + dy * sp * 1.4;
    if (!collides(nx, hero.y)) hero.x = nx;
    if (!collides(hero.x, ny)) hero.y = ny;
  }
}

function render(t) {
  const camX = Math.max(0, Math.min(WORLD_W - VIEW_W, hero.x - VIEW_W / 2));
  drawSky(camX);
  drawBackground(camX);
  drawGround(camX);
  drawRoad(camX);
  // back palisade behind the gate
  drawPalisade(300, 100, 6, camX);
  drawPalisade(360, 100, 8, camX);
  drawPalisade(180, 100, 24, camX);
  drawPalisade(520, 100, 22, camX);
  drawHut(640, camX, t, 1);
  drawHut(800, camX, t, 0);
  drawGateTower(318, camX, t);
  drawBridge(camX);
  drawCart(546, camX);
  drawLanternPost(500, camX, t);
  drawLanternPost(692, camX, t);

  const ySort = [
    { y: npcVillager.x === 160 ? 132 : 132, draw: () => drawVillager(npcVillager.x, camX, t, npcVillager.phase) },
    { y: 126, draw: () => drawGuard(npcGuard.x, camX, t, npcGuard.phase) },
    { y: hero.y, draw: () => drawHero(hero, t) }
  ];
  ySort.sort((a, b) => a.y - b.y);
  for (const e of ySort) e.draw();

  // vignette
  const vg = ctx.createRadialGradient(VIEW_W / 2, VIEW_H / 2, 60, VIEW_W / 2, VIEW_H / 2, 260);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, 'rgba(0,0,0,0.45)');
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, VIEW_W, VIEW_H);
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
