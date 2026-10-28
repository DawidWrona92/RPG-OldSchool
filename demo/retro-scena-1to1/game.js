'use strict';

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;

const VIEW_W = canvas.width;
const VIEW_H = canvas.height;

function loadImage(src) {
  const im = new Image();
  im.src = src;
  return im;
}

const IMG = {
  s1: loadImage('assets/scena1_czyste.jpg'),
  s2: loadImage('assets/scena2_czyste.jpg'),
  hero: loadImage('assets/bohater.png'),
  guard: loadImage('assets/straznik.png')
};

// geometria scen wyliczona z detekcji w oryginałach:
// scena1: 1536x1024 — bohater stał w (626..686, 570..694), strażnik (1047..1103, 418..534+)
// brama na środku góry. scena2: 1672x941 — bohater stał w (655..719, 590..712)
const S1 = { w: 1536, h: 1024 };
const S2 = { w: 1672, h: 941 };

const scenes = {
  brama: {
    img: IMG.s1, ref: S1, name: 'Niemir — brama osady',
    walk: { x0: 0.06, x1: 0.94, y0: 0.55, y1: 0.95 },
    corridor: { x0: 0.40, x1: 0.60, yTop: 0.35 },
    exitUp: { x0: 0.42, x1: 0.58, y: 0.375 },
    spawnFromOsada: { x: 0.5, y: 0.60 }
  },
  osada: {
    img: IMG.s2, ref: S2, name: 'Niemir — wnętrze osady',
    walk: { x0: 0.06, x1: 0.94, y0: 0.50, y1: 0.92 },
    corridor: null,
    exitDown: { y: 0.915 },
    spawnFromBrama: { x: 0.5, y: 0.58 }
  }
};

let currentScene = 'brama';

const keys = {};
addEventListener('keydown', e => {
  keys[e.key.toLowerCase()] = true;
  if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(e.key.toLowerCase())) e.preventDefault();
});
addEventListener('keyup', e => { keys[e.key.toLowerCase()] = false; });

const HERO_SPRITE_SCALE = 1.0;   // sprite ma ~60x124 px sceny — rysujemy 1:1 w przeliczeniu na canvas
const GUARD_SPRITE_SCALE = 1.0;

const hero = {
  x: 0.5, y: 0.90,           // pozycja ułamkowa w danej scenie
  facing: 'right',
  moving: false,
  walkT: 0,
  breathPhase: 0.3,
  speed: 0.004, runSpeed: 0.008   // ułamek szerokości sceny na klatkę 16 ms
};

// strażnik: spaceruje przed bramą między punktami, z przystankami
const guard = {
  waypoints: [
    { x: 0.62, y: 0.475 },
    { x: 0.50, y: 0.46 },
    { x: 0.62, y: 0.475 },
    { x: 0.72, y: 0.50 }
  ],
  wpIndex: 0,
  x: 0.62, y: 0.475,
  facing: 'right',
  speed: 0.0012,
  state: 'walk',           // 'walk' | 'wait'
  waitT: 0,
  waitDur: 2600,           // ms postoju
  breathPhase: 0.1,
  walkT: 0
};

let fade = 0, fadeDir = 0;
let pendingSwitch = null;

function startTransition(to, spawn) {
  if (fadeDir !== 0) return;
  fadeDir = 1; fade = 0;
  pendingSwitch = () => {
    currentScene = to;
    hero.x = spawn.x; hero.y = spawn.y;
  };
}

function sceneOf() { return scenes[currentScene]; }

function walkable(fx, fy) {
  const s = sceneOf();
  const w = s.walk;
  if (fx < w.x0 || fx > w.x1) return false;
  if (fy > w.y1) return false;
  if (fy < w.y0) {
    if (s.corridor && fx > s.corridor.x0 && fx < s.corridor.x1 && fy > s.corridor.yTop) {
      // korytarz ścieżki do bramy — dozwolony
    } else {
      return false;
    }
  }
  return true;
}

function tryTransition() {
  const s = sceneOf();
  const fx = hero.x, fy = hero.y;
  if (s.exitUp && fy <= s.exitUp.y && fx > s.exitUp.x0 && fx < s.exitUp.x1) {
    startTransition('osada', scenes.osada.spawnFromBrama);
  } else if (s.exitDown && fy >= s.exitDown.y) {
    startTransition('brama', scenes.brama.spawnFromOsada);
  }
}

function updateHero(dt) {
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
    hero.walkT += dt * (run ? 1.7 : 1);
    if (dx < 0) hero.facing = 'left';
    if (dx > 0) hero.facing = 'right';
    const nx = hero.x + dx * sp;
    const ny = hero.y + dy * sp * 0.9;
    if (walkable(nx, hero.y)) hero.x = nx;
    if (walkable(hero.x, ny)) hero.y = ny;
    tryTransition();
  }
}

function updateGuard(dt) {
  if (guard.state === 'wait') {
    guard.waitT += dt;
    if (guard.waitT >= guard.waitDur) {
      guard.waitT = 0;
      guard.state = 'walk';
      guard.wpIndex = (guard.wpIndex + 1) % guard.waypoints.length;
    }
    return;
  }
  const wp = guard.waypoints[guard.wpIndex];
  const dx = wp.x - guard.x, dy = wp.y - guard.y;
  const dist = Math.hypot(dx, dy);
  if (dist < 0.004) {
    guard.state = 'wait';
    return;
  }
  const step = Math.min(dist, guard.speed * dt / 16);
  guard.x += dx / dist * step;
  guard.y += dy / dist * step;
  if (dx > 0.0005) guard.facing = 'right';
  if (dx < -0.0005) guard.facing = 'left';
  guard.walkT += dt;
}

function update(dt) {
  if (fadeDir !== 0) {
    fade += fadeDir * dt / 350;
    if (fade >= 1 && fadeDir === 1) {
      fade = 1; fadeDir = -1;
      if (pendingSwitch) { pendingSwitch(); pendingSwitch = null; }
    } else if (fade <= 0 && fadeDir === -1) {
      fade = 0; fadeDir = 0;
    }
    return;
  }
  updateHero(dt);
  updateGuard(dt);
}

// ---------- render ----------

function drawCover(img, ref) {
  const s = Math.max(VIEW_W / ref.w, VIEW_H / ref.h);
  const w = ref.w * s, h = ref.h * s;
  ctx.drawImage(img, (VIEW_W - w) / 2, (VIEW_H - h) / 2, w, h);
}

// wspólna skala: piksel sceny -> piksel canvas
function sceneScale(ref) {
  return Math.max(VIEW_W / ref.w, VIEW_H / ref.h);
}
function toCanvas(fx, fy, ref) {
  const s = sceneScale(ref);
  return [ (VIEW_W - ref.w * s) / 2 + fx * ref.w * s,
           (VIEW_H - ref.h * s) / 2 + fy * ref.h * s ];
}

function drawSpriteSprite(img, cxs, cys, facing, bob, scale) {
  const w = img.naturalWidth * scale, h = img.naturalHeight * scale;
  ctx.save();
  ctx.translate(Math.round(cxs), Math.round(cys) + bob);
  if (facing === 'left') ctx.scale(-1, 1);
  ctx.drawImage(img, -w / 2, -h, w, h);
  ctx.restore();
}

function drawBreath(cxs, cys, t, phase, facing, scale) {
  const cycle = ((t / 1000) * 0.55 + phase) % 1;
  if (cycle > 0.45) return;
  const k = cycle / 0.45;
  const drift = k * 9 * scale;
  const rise = Math.sin(k * Math.PI) * 4 * scale;
  const size = Math.max(1, Math.round((1 + k * 2) * scale));
  const a = (1 - k) * 0.45;
  const dir = facing === 'left' ? -1 : 1;
  ctx.globalAlpha = a;
  ctx.fillStyle = 'rgb(220,235,255)';
  ctx.fillRect(Math.round(cxs + dir * (6 * scale + drift)), Math.round(cys - rise), size, Math.max(1, size - 1));
  ctx.globalAlpha = a * 0.6;
  ctx.fillRect(Math.round(cxs + dir * (6 * scale + drift + 2)), Math.round(cys - rise - 1), size, 1);
  ctx.globalAlpha = 1;
}

function breathBob(t, phase) {
  const p = (Math.sin((t / 1000) * Math.PI * 2 * 0.7 + phase) + 1) / 2;
  return p < 0.5 ? 0 : 1;   // delikatny ruch torsu: 0/1 px
}

function render(t) {
  const s = sceneOf();
  ctx.fillStyle = '#0a0c12';
  ctx.fillRect(0, 0, VIEW_W, VIEW_H);
  if (s.img.complete && s.img.naturalWidth) drawCover(s.img, s.ref);

  const scale = sceneScale(s.ref);
  // bohater
  const [hx, hy] = toCanvas(hero.x, hero.y, s.ref);
  const heroBob = hero.moving ? (Math.sin(hero.walkT / 90) > 0 ? 1 : 0) : breathBob(t, hero.breathPhase);
  // strażnik (tylko scena bramy)
  let entities = [];
  if (currentScene === 'brama') {
    const [gx, gy] = toCanvas(guard.x, guard.y, s.ref);
    const gBob = guard.state === 'wait' ? breathBob(t, guard.breathPhase) : 0;
    entities.push({ y: gy, draw: () => {
      drawSpriteSprite(IMG.guard, gx, gy, guard.facing, gBob, GUARD_SPRITE_SCALE * scale);
      if (guard.state === 'wait') drawBreath(gx, gy - 34 * scale, t, guard.breathPhase, guard.facing, scale);
    }});
  }
  entities.push({ y: hy, draw: () => {
    drawSpriteSprite(IMG.hero, hx, hy, hero.facing, heroBob, HERO_SPRITE_SCALE * scale);
    drawBreath(hx, hy - 40 * scale, t, hero.breathPhase + 0.35, hero.facing, scale);
  }});
  entities.sort((a, b) => a.y - b.y);
  for (const e of entities) if (IMG.hero.complete) e.draw();

  // podpowiedzi
  ctx.font = 'bold 13px "Courier New", monospace';
  ctx.textAlign = 'center';
  ctx.fillStyle = 'rgba(255,214,140,0.85)';
  if (currentScene === 'brama') {
    const [, gateY] = toCanvas(0.5, 0.38, S1);
    ctx.fillText('W — wejście przez bramę', VIEW_W / 2, gateY - 6);
  } else {
    ctx.fillText('S — powrót do bramy', VIEW_W / 2, VIEW_H - 8);
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
