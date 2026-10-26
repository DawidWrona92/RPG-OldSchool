'use strict';
// Standalone polygon prisms in OBJ, no external deps. Front is zMax with outward +z.
const EPS = 1e-9;
function area2(p) {let s=0;for(let i=0;i<p.length;i++){let a=p[i],b=p[(i+1)%p.length];s+=a[0]*b[1]-b[0]*a[1];}return s;}
function cross(a,b,c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
function between(a,b,c){return c>=Math.min(a,b)-EPS&&c<=Math.max(a,b)+EPS;}
function onSeg(a,b,c){return Math.abs(cross(a,b,c))<EPS&&between(a[0],b[0],c[0])&&between(a[1],b[1],c[1]);}
function intersect(a,b,c,d){let ab1=cross(a,b,c),ab2=cross(a,b,d),cd1=cross(c,d,a),cd2=cross(c,d,b);
 if((ab1>EPS&&ab2< -EPS||ab1< -EPS&&ab2>EPS)&&(cd1>EPS&&cd2< -EPS||cd1< -EPS&&cd2>EPS))return true;
 return onSeg(a,b,c)||onSeg(a,b,d)||onSeg(c,d,a)||onSeg(c,d,b);
}
function validate(pts){if(!Array.isArray(pts)||pts.length<3)throw new Error('outline: >=3 points required');
 const p=pts.map(a=>{if(!Array.isArray(a)||a.length!==2||a.some(x=>!Number.isFinite(x)))throw new Error('outline: 2D finite coordinates required');return a.slice();});
 for(let i=0;i<p.length;i++)if(Math.hypot(p[i][0]-p[(i+1)%p.length][0],p[i][1]-p[(i+1)%p.length][1])<EPS)throw new Error('outline: repeated/zero edge');
 if(Math.abs(area2(p))<EPS)throw new Error('outline: degenerate polygon');
 for(let i=0;i<p.length;i++)for(let j=i+1;j<p.length;j++){
  if(i===j||(i+1)%p.length===j||i===(j+1)%p.length)continue;
  if(intersect(p[i],p[(i+1)%p.length],p[j],p[(j+1)%p.length]))throw new Error('outline: self intersecting');
 }
 // remove redundant collinear vertices? Reject to preserve taper correspondence.
 for(let i=0;i<p.length;i++)if(Math.abs(cross(p[(i+p.length-1)%p.length],p[i],p[(i+1)%p.length]))<EPS)throw new Error('outline: collinear points');
 return p;
}
function insideTri(p,a,b,c){return cross(a,b,p)>=-EPS&&cross(b,c,p)>=-EPS&&cross(c,a,p)>=-EPS;}
function triangulate(p){const idx=p.map((_,i)=>i),out=[];let loops=0;
 while(idx.length>3){if(++loops>p.length*p.length)throw new Error('cannot triangulate');let found=false;
  for(let t=0;t<idx.length;t++){
   let ia=idx[(t-1+idx.length)%idx.length],ib=idx[t],ic=idx[(t+1)%idx.length];
   if(cross(p[ia],p[ib],p[ic])<=EPS)continue;
   let hidden=idx.some(k=>k!==ia&&k!==ib&&k!==ic&&insideTri(p[k],p[ia],p[ib],p[ic]));if(hidden)continue;
   out.push([ia,ib,ic]);idx.splice(t,1);found=true;break;
  }
  if(!found)throw new Error('cannot triangulate; check polygon');
 }
 out.push(idx);return out;
}
function fmt(v){return Number(v).toFixed(6);}
function taperPrismObj(bottom,top,zMin,zMax,materials={}){
 let b=validate(bottom),t=validate(top);if(b.length!==t.length)throw new Error('bottom/top vertex counts differ');
 if(!Number.isFinite(zMin)||!Number.isFinite(zMax)||zMax-zMin<EPS)throw new Error('zMax must exceed zMin');
 // index correspondence preserved by reversing both polygons together
 if(Math.sign(area2(b))!==Math.sign(area2(t)))throw new Error('opposite windings; inconsistent index correspondence');
 if(area2(b)<0){b.reverse();t.reverse();}
 // Triangulate planar endcaps independently; both can be concave and shapes differ.
 let bb=triangulate(b),tt=triangulate(t),n=b.length;
 let o=['# RTS Meshkit v2; zMax front (+z), zMin back (-z)','o prism'];
 for(let x of b)o.push(`v ${fmt(x[0])} ${fmt(x[1])} ${fmt(zMin)}`);
 for(let x of t)o.push(`v ${fmt(x[0])} ${fmt(x[1])} ${fmt(zMax)}`);
 const emit=(g,mat,faces)=>{o.push('g '+g);if(mat)o.push('usemtl '+String(mat).replace(/[^A-Za-z0-9_.-]/g,'_'));for(let face of faces)o.push('f '+face.map(i=>i+1).join(' '));};
 emit('back',materials.back||'back',bb.map(tr=>tr.slice().reverse()));
 emit('front',materials.front||'front',tt.map(tr=>tr.map(i=>i+n)));
 let sides=[];for(let i=0;i<n;i++){let j=(i+1)%n;sides.push([i,j,j+n],[i,j+n,i+n]);}
 emit('sides',materials.sides||'sides',sides);
 return o.join('\n')+'\n';
}
function polyPrismObj(outline,thickness,materials={}){if(!Number.isFinite(thickness)||thickness<=EPS)throw new Error('thickness must be positive');return taperPrismObj(outline,outline,-thickness/2,thickness/2,materials);}
function heaterOutline(s=1){if(!Number.isFinite(s)||s<=0)throw new Error('scale must be positive');return [[-.43,.43],[.43,.43],[.42,0],[.29,-.30],[0,-.61],[-.29,-.30],[-.42,0]].map(p=>p.map(x=>x*s));}
// rtcore.Model.addObj(material, obj) ignores `usemtl`. Split OBJ face groups to render separate materials.
function splitObjByGroup(obj){
 if(typeof obj!=='string')throw new TypeError('OBJ must be text');
 const header=[], groups={}, metadata={}, lines=obj.split(/\r?\n/);let current='default';
 const ensure=(name)=>{if(!groups[name]){groups[name]=[];metadata[name]=null;}};ensure(current);
 for(const line of lines){const src=line.trim();if(!src||src.startsWith('#'))continue;
  if(/^(v|vn|vt)\s/.test(src))header.push(src);
  else if(src.startsWith('g ')){current=src.slice(2).trim().split(/\s+/)[0];ensure(current);}
  else if(src.startsWith('usemtl ')){ensure(current);metadata[current]=src.slice(7).trim();}
  else if(src.startsWith('f ')){ensure(current);groups[current].push(src);}
 }
 const out={};for(const [name,faces] of Object.entries(groups))if(faces.length)out[name]={obj:header.concat(faces).join('\n')+'\n',materialHint:metadata[name],faces:faces.length};
 return out;
}
module.exports={area2,validate,triangulate,polyPrismObj,taperPrismObj,heaterOutline,splitObjByGroup};
