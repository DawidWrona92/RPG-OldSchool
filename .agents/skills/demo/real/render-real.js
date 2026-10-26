'use strict';
/** Real backends render laboratory. Run node demo/real/render-real.js from the package root. */
const fs=require('fs'), path=require('path');
const ROOT=path.resolve(__dirname,'../..'), OUT=path.join(__dirname,'output');fs.mkdirSync(OUT,{recursive:true});
const kit=require(path.join(ROOT,'retro-rts-sprites/scripts/spritekit.js'));
const pt=require(path.join(ROOT,'painted-rts-sprites/scripts/painter.js'));
const rt=require(path.join(ROOT,'rts-prerender-3d/scripts/rtcore.js'));
const manifest={version:'3.0', engines:{retro:'spritekit.js',painted:'painter.js',prerender3d:'rtcore.js'}, assets:[], testResults:[]};
function saveBytes(name,contents) {fs.writeFileSync(path.join(OUT,name),contents);}
function record(kind,name,result,findings) {
 const errors=findings.filter(f=>(Array.isArray(f)?f[0]==='ERR':false));
 const warnings=findings.filter(f=>(Array.isArray(f)?f[0]==='WARN':false));
 manifest.assets.push({kind,name,anchor:result.anchor,dimensions:[result.sprite.width,result.sprite.height],tilePx:result.tilePx,frameClipped:result.frameClipped,errors,warnings});
 console.log(`[${kind}] ${name} ${result.sprite.width}x${result.sprite.height} ERR:${errors.length} WARN:${warnings.length}`);
 for (const f of errors) console.error('  ERROR',f[1]);
}
function saveRetro(name, grid, palette, mode, ground, factor=4) {
 const rows=kit.gridToRows(grid); const check=kit.validate(rows,palette,{width:grid.w,height:grid.h,mode,ground,lightCheck:false});
 let image=kit.rasterize(rows,palette), big=kit.upscale(image,factor);
 saveBytes(name+'.png',kit.encodePng(big));saveBytes(name+'.svg',kit.asciiToSvg(rows,palette,{scale:factor,width:grid.w,height:grid.h,strict:true}));
 saveBytes(name+'.json',JSON.stringify({name,engine:'spritekit.js',width:grid.w,height:grid.h,scale:factor,checks:check},null,2));
 manifest.assets.push({kind:'retro',name,dimensions:[grid.w,grid.h],engine:'spritekit',validation:check.ok,errors:check.errors,warnings:check.warnings});
 console.log(`[retro] ${name} ${grid.w}x${grid.h} ERR:${check.errors.length} WARN:${check.warnings.length}`);
 if(!check.ok) console.error(check.errors);
}
// RETRO: two small pixel-art examples rendered by spritekit primitives.
{
 const g=kit.makeGrid(160,132), p={
 a:kit.tone('PIXELART','stone',0), b:kit.tone('PIXELART','stone',1), c:kit.tone('PIXELART','stone',2),
 d:kit.tone('PIXELART','wood',0), e:kit.tone('PIXELART','wood',1), f:kit.tone('PIXELART','wood',2),
 r:kit.tone('PIXELART','roofRed',0), s:kit.tone('PIXELART','roofRed',1), t:kit.tone('PIXELART','roofRed',2),
 x:kit.tone('PIXELART','teamBlue',1), y:kit.tone('PIXELART','gold',2),
 o:kit.PALETTES.CONTOUR.wood, z:kit.PALETTES.CONTOUR.roofRed, q:kit.PALETTES.SHADOW
 };
 kit.fillEllipse(g,78,117,46,10,'q');
 const O=[80,104];kit.isoBox(g,O,1,1,37,{left:'c',right:'a',top:'b'});
 kit.hipRoof(g,O,1,1,37,21,{left:'s',right:'r'},0.10);
 // posts and main door + reinforced braces
 kit.drawLine(g,48,94,48,121,'d');kit.drawLine(g,79,112,79,127,'d');kit.drawLine(g,110,94,110,119,'d');
 kit.fillRect(g,65,101,13,20,'d');kit.fillRect(g,68,104,7,17,'e');kit.setCell(g,73,113,'y');
 kit.fillRect(g,93,95,10,10,'o');kit.fillRect(g,95,97,6,6,'x');
 kit.drawLine(g,80,53,80,42,'e');kit.drawLine(g,80,42,94,45,'x');
 const boundaries={a:'o',b:'o',c:'o',d:'o',e:'o',f:'o',r:'z',s:'z',t:'z',x:'o',y:'o'};kit.outline(g,boundaries,{where:'inner',outside:['.','q']});
 saveRetro('retro_fortified_cottage',g,p,'PIXELART',null,4);
}
{
 const g=kit.makeGrid(48,64), p={
 a:kit.tone('PIXELART','metal',0),b:kit.tone('PIXELART','metal',1),c:kit.tone('PIXELART','metal',2),
 d:kit.tone('PIXELART','skin',1),e:kit.tone('PIXELART','teamBlue',0), f:kit.tone('PIXELART','teamBlue',1), g:kit.tone('PIXELART','teamBlue',2),
 h:kit.tone('PIXELART','wood',0), i:kit.tone('PIXELART','wood',1), j:kit.tone('PIXELART','gold',2),
 o:kit.PALETTES.CONTOUR.cool, p:kit.PALETTES.CONTOUR.teamBlue, q:kit.PALETTES.SHADOW};
 kit.fillEllipse(g,23,56,13,4,'q');
 kit.fillRect(g,16,39,6,15,'h');kit.fillRect(g,26,39,6,15,'h');
 kit.fillRect(g,15,50,9,5,'o');kit.fillRect(g,25,50,9,5,'o');
 kit.shadeEllipse(g,24,34,10,14,{shadow:'e',base:'f',light:'g'}, {seed:7,jitter:0.12});
 kit.fillEllipse(g,24,17,9,9,'b');kit.fillEllipse(g,24,20,7,6,'d');
 kit.fillRect(g,17,13,14,5,'c');kit.fillRect(g,16,17,5,6,'a');kit.fillRect(g,27,17,5,6,'a');
 kit.fillRect(g,15,30,6,15,'b');kit.fillRect(g,30,30,5,15,'b');
 // shield and protruding sword make it clearly directional
 kit.shadeEllipse(g,37,34,8,13,{light:'g',base:'f',shadow:'e'},{seed:1,jitter:0.1});
 kit.drawLine(g,7,39,7,12,'c');kit.drawLine(g,4,23,10,23,'j');kit.drawLine(g,7,12,10,7,'c');
 const boundaries={a:'o',b:'o',c:'o',d:'o',e:'p',f:'p',g:'p',h:'o',i:'o',j:'o'};kit.outline(g,boundaries,{where:'inner',outside:['.','q']});
 saveRetro('retro_blue_swordsman',g,p,'PIXELART',null,5);
}
function saveResult(engine,name,result,kind,options) {
 const findings=engine.validateSprite(result,Object.assign({kind},options||{}));
 const saved=engine.saveSprite(result,name); for(const [fn,data] of Object.entries(saved.files)) saveBytes(fn,data);
 record(engine===rt?'prerender3d':'painted',name,result,findings);
}
// PAINTED: original backend, no mockups.
{
 const P=pt.sprite({width:470,height:390,anchor:[235,307],supersample:2});
 pt.house(P,{style:'stone',roofTone:'tile',w:2.45,d:1.75,floors:1,h:1.10,porch:true,shutters:true,team:true,seed:7});
 pt.barrel(P,[-1.4,-0.15],{scale:0.85});pt.crate(P,[1.35,-0.50],{scale:0.78});
 const r=P.render();saveResult(pt,'painted_market_house',r,'building',{expectTeam:true});
}
{
 const P=pt.sprite({width:235,height:220,anchor:[120,175],supersample:2});
 pt.humanoid(P,{pos:[0,0,0],yaw:0,phase:0.18,scale:1.15,weapon:'sword',hat:'none',moving:false,shirt:[0.28,0.38,0.50],pants:[0.18,0.18,0.21],team:'torso'});
 const r=P.render();saveResult(pt,'painted_swordsman',r,'unit',{expectTeam:true});
}
// 3D PRERENDER: real mesh / texture / ray-occlusion renderer.
const textures=rt.standardTextures(['roof','plaster','timber','planks','stone','leaf','needle','bark','thatch','dirt','metal','cloth','grass']);
function base3d(){return rt.standardModel(textures)}
{
 const m=base3d();
 m.box('stone',[0,0,0.22],[2.8,2.15,0.44]);
 m.box('plaster',[0,0,1.06],[2.58,1.98,1.4]);
 rt.halfTimberWall(m,'+x',0.98,1.29,0.40,1.77,{columns:5});
 rt.halfTimberWall(m,'-y',1.29,0.99,0.40,1.77,{columns:5});
 rt.gableRoof(m,1.29,0.99,1.79,0.83,{material:'roof',gableMaterial:'plaster',ridgeMaterial:'timber'});
 m.box('timber',[0,-1.03,0.74],[0.60,0.07,1.12]);
 m.box('iron',[0,-1.09,0.75],[0.46,0.06,1.00]);
 m.box('metal',[0.15,-1.15,0.7],[0.055,0.055,0.055]);
 for(const x of [-0.83,0.83]) {m.box('timber',[x,-1.05,1.17],[0.40,0.10,0.44]);m.box('glass',[x,-1.11,1.17],[0.29,0.03,0.31]);}
 m.box('stone',[0.89,0.48,2.44],[0.31,0.33,0.85]);
 m.box('stone',[0.89,0.48,2.9],[0.38,0.40,0.10]);
 rt.barrel(m,-1.67,-0.7,{height:0.55});rt.crate(m,1.62,-0.65,{size:0.43});
 m.box('team',[0.98,-1.04,1.36],[0.20,0.045,0.34]);
 const cam=new rt.Camera({tilePx:96,halfExtent:3.9,target:[0,0,1.15],supersample:2});
 const r=rt.renderSprite(m,cam,{trim:true});saveResult(rt,'prerender_timber_house',r,'building',{expectTeam:true});
}
{
 const m=base3d();
 rt.roundTower(m,0,0,{radius:0.82,height:2.6,roof:true,roofMaterial:'roof'});
 m.box('stone',[0,-0.87,0.68],[0.52,0.12,1.11]);
 m.box('iron',[0,-0.94,0.68],[0.38,0.06,0.96]);
 m.box('glass',[0.47,-0.71,1.62],[0.23,0.12,0.36]);
 m.box('team',[0.3,-0.87,2.75],[0.31,0.05,0.31]);
 m.cylinder('timber',[0.3,-0.89,2.6],[0.3,-0.89,3.5],0.035,0.035,8);
 const cam=new rt.Camera({tilePx:96,halfExtent:4.8,target:[0,0,2.0],supersample:2});
 const r=rt.renderSprite(m,cam,{trim:true});saveResult(rt,'prerender_guard_tower',r,'building',{expectTeam:true});
}
// Painted: 8 real directions, one pose per direction, sample sheet.
{
 const frames=pt.renderFrames({frame:{width:170,height:155,anchor:[85,127],supersample:2},directions:8,phases:1,
  build:(P,dir,phase)=>pt.humanoid(P,{pos:[0,0,0],yaw:dir.yaw,scale:0.9,weapon:'sword',hat:'none',moving:false,team:'torso'}),render:{trim:false}});
 const val=pt.validateSheet(frames); const sheet=pt.packSheet(frames,{columns:8,padding:6});
 const saved=pt.saveSheet(sheet,'painted_eight_directions');for(const [name,data] of Object.entries(saved.files))saveBytes(name,data);
 const checkDirections=require(path.join(ROOT,'painted-rts-sprites/scripts/direction-check.js'));
 const chk=checkDirections.checkDirections?checkDirections.checkDirections(frames,{framesPerDirection:1,strict:true}):[];
 manifest.directions={n:frames.length,validation:val,distinctness:chk};
 console.log(`[atlas] frames:${frames.length} errors:${val.filter(x=>x[0]==='ERR').length} distinctness: ${chk.map(x=>x[0]).join(',')}`);
}
fs.writeFileSync(path.join(OUT,'manifest.json'),JSON.stringify(manifest,null,2));
console.log('DONE',path.join(OUT,'manifest.json'));
