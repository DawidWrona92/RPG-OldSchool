'use strict';
const assert=require('node:assert/strict');
const M=require('../rts-prerender-3d/scripts/meshkit');
const D=require('../painted-rts-sprites/scripts/direction-check');
const S=require('../painted-rts-sprites/scripts/silhouette-check');
let tests=0;function test(name,fn){fn();console.log('PASS',name);tests++;}
function parseOBJ(obj){let vs=[],faces=[],g='';for(let l of obj.split(/\r?\n/)){let p=l.split(/\s+/);if(p[0]==='v')vs.push(p.slice(1).map(Number));if(p[0]==='g')g=p[1];if(p[0]==='f')faces.push({g,v:p.slice(1).map(s=>vs[Number(s)-1])});}return {vs,faces};}
function normalZ(face){let [a,b,c]=face.v;return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
test('square prism caps outward, sides nonzero',()=>{let o=parseOBJ(M.polyPrismObj([[0,0],[1,0],[1,1],[0,1]],.5));assert.equal(o.vs.length,8);assert.equal(o.faces.length,12);assert(o.faces.filter(f=>f.g==='front').every(f=>normalZ(f)>0));assert(o.faces.filter(f=>f.g==='back').every(f=>normalZ(f)<0));for(let f of o.faces)assert(f.v.every(v=>v.every(Number.isFinite)));});
test('concave polygon triangulated outward',()=>{let p=[[0,0],[3,0],[3,1],[1,1],[1,3],[0,3]],o=parseOBJ(M.polyPrismObj(p,.4));assert.equal(o.faces.filter(f=>f.g==='front').length,p.length-2);assert(o.faces.filter(f=>f.g==='front').every(f=>normalZ(f)>0));assert(o.faces.filter(f=>f.g==='back').every(f=>normalZ(f)<0));});
test('taper prism correct caps',()=>{let a=[[0,0],[3,0],[3,3],[0,3]],b=[[1,1],[2,1],[2,2],[1,2]],o=parseOBJ(M.taperPrismObj(a,b,0,2));assert.equal(o.vs.length,8);assert(o.faces.filter(f=>f.g==='back').every(f=>normalZ(f)<0));assert(o.faces.filter(f=>f.g==='front').every(f=>normalZ(f)>0));});
test('reject invalid outlines',()=>{assert.throws(()=>M.polyPrismObj([[0,0],[1,1],[0,1],[1,0]],.2));assert.throws(()=>M.polyPrismObj([[0,0],[1,0],[1,1],[0,1]],0));assert.throws(()=>M.polyPrismObj([[0,0],[1,0],[2,0],[0,1]],.2));});
function frame(a,b){let d=new Uint8ClampedArray(4*4*4);d[(a+b*4)*4+3]=255;return {sprite:{width:4,height:4,data:d}};}
test('direction checker catches duplicates beyond direction 0',()=>{let res=D.checkDirections([frame(0,0),frame(1,0),frame(1,0)],{});assert(res.some(x=>x[0]==='ERR'&&x[1].includes('1 and 2')));});
test('direction checker rejects invalid RGBA',()=>{let res=D.checkDirections([frame(0,0),{sprite:{width:4,height:4,data:new Uint8ClampedArray(12)}}]);assert.equal(res[0][0],'ERR');});
test('direction checker allows distinct orientations',()=>{let res=D.checkDirections([frame(0,0),frame(1,0),frame(2,0)],{});assert.equal(res[0][0],'INFO');});
test('silhouette metrics: solid and hollow',()=>{let d=new Uint8ClampedArray(6*6*4);for(let y=1;y<5;y++)for(let x=1;x<5;x++)d[(y*6+x)*4+3]=255;let solid=S.silhouetteMetrics({width:6,height:6,data:d});assert.equal(solid.components,1);assert.equal(solid.holes,0);assert.equal(solid.area,16);d[(2*6+2)*4+3]=0;let ring=S.silhouetteMetrics({width:6,height:6,data:d});assert.equal(ring.holes,1);});
test('silhouette metrics reject invalid',()=>assert.throws(()=>S.silhouetteMetrics({width:2,height:3,data:new Uint8Array(2)})));
console.log(`OK ${tests} tests passed`);
