'use strict';
// frames: array of {sprite:{width,height,data:Uint8Array/Uint8ClampedArray}}; ordered direction-major.
function checkDirections(frames, opts={}){
 const fpd=opts.framesPerDirection??1,strict=opts.strict!==false, results=[];
 if(!Number.isInteger(fpd)||fpd<1) return [['ERR','Invalid framesPerDirection']];
 if(!Array.isArray(frames)||frames.length<2*fpd||frames.length%fpd!==0)return [['ERR','Expected 2+ directions, whole frames per direction']];
 const canonical=frames[0]&&frames[0].sprite;
 if(!canonical||!Number.isInteger(canonical.width)||!Number.isInteger(canonical.height)||canonical.width<1||canonical.height<1) return [['ERR','Invalid first sprite size']];
 const len=canonical.width*canonical.height*4;
 for(let i=0;i<frames.length;i++){
  const f=frames[i]&&frames[i].sprite;
  if(!f||f.width!==canonical.width||f.height!==canonical.height||!(f.data instanceof Uint8Array || f.data instanceof Uint8ClampedArray)||f.data.length!==len)
   return [['ERR',`Frame ${i}: mismatched size/data`]];
 }
 const nd=frames.length/fpd;
 for(let a=0;a<nd;a++)for(let b=a+1;b<nd;b++){
  let fullEqual=true,alphaEqual=true;
  for(let q=0;q<fpd;q++){
   const A=frames[a*fpd+q].sprite.data,B=frames[b*fpd+q].sprite.data;
   for(let k=0;k<len;k+=4){
    if(Math.abs(A[k+3]-B[k+3])>8)alphaEqual=false;
    if(A[k]!==B[k]||A[k+1]!==B[k+1]||A[k+2]!==B[k+2]||A[k+3]!==B[k+3])fullEqual=false;
   }
  }
  if(fullEqual)results.push([strict?'ERR':'WARN',`directions ${a} and ${b} same RGBA in all ${fpd} phases (or symmetric)`]);
  else if(alphaEqual)results.push(['WARN',`directions ${a} and ${b} share alpha in all ${fpd} phases; inspect asymmetry`]);
 }
 if(!results.length)results.push(['INFO',`No duplicate directions among ${nd} directions × ${fpd} phases (not proof of semantic orientation)`]);
 return results;
}
module.exports={checkDirections};
