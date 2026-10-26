'use strict';
const assert=require('node:assert/strict');
const rt=require('../rts-prerender-3d/scripts/rtcore.js');
const pt=require('../painted-rts-sprites/scripts/painter.js');
const kit=require('../retro-rts-sprites/scripts/spritekit.js');
const mesh=require('../rts-prerender-3d/scripts/meshkit.js');
const dirs=require('../painted-rts-sprites/scripts/direction-check.js');
let count=0;function test(label,fn){fn();count++;console.log('[PASS]',label);}
test('three engines load',()=>{assert.equal(typeof rt.renderSprite,'function');assert.equal(typeof pt.renderFrames,'function');assert.equal(typeof kit.makeGrid,'function');});
test('genuine meshkit material split for importer',()=>{const groups=mesh.splitObjByGroup(mesh.polyPrismObj(mesh.heaterOutline(),.08,{front:'team',back:'iron',sides:'metal'}));assert.equal(groups.front.materialHint,'team');assert.equal(groups.back.materialHint,'iron');assert.equal(groups.sides.materialHint,'metal');assert.equal(groups.front.faces,5);const m=rt.standardModel(rt.standardTextures(['metal']));for(const g of Object.values(groups))m.addObj(g.materialHint,g.obj);assert(m.meshes.team.faces.length>0);assert(m.meshes.iron.faces.length>0);});
test('retro PNG pixels encoded',()=>{const g=kit.makeGrid(20,20);kit.fillEllipse(g,10,10,5,6,'a');const p={a:kit.tone('PIXELART','foliage',1)};const rows=kit.gridToRows(g);assert(kit.validate(rows,p,{mode:'PIXELART',width:20,height:20}).ok);const png=kit.encodePng(kit.rasterize(rows,p));assert(Buffer.isBuffer(png));assert(png.subarray(1,4).equals(Buffer.from('PNG')));});
test('painted raw image + separate masks',()=>{const P=pt.sprite({width:140,height:130,anchor:[70,100],supersample:2});pt.humanoid(P,{scale:.8,team:'torso',moving:false,hat:'none'});const r=P.render();assert(r.sprite.data.some((v,i)=>i%4===3&&v>0));assert(r.team.data.some(v=>v>0));assert.equal(pt.validateSprite(r,{kind:'unit',expectTeam:true}).filter(x=>x[0]==='ERR').length,0);});
test('checker detects arbitrary duplicate direction pairs',()=>{function frame(a){return {sprite:{width:1,height:1,data:Uint8Array.from([a,a,a,255])}};}let r=dirs.checkDirections([frame(1),frame(2),frame(2)],{framesPerDirection:1});assert(r.some(x=>x[0]==='ERR'&&x[1].includes('1 and 2')));});
console.log(`Passed ${count} integration checks`);
