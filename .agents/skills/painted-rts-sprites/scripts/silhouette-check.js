'use strict';
// Diagnostic for one untrimmed RGBA sprite; report descriptive metrics, do not claim semantic recognition.
function silhouetteMetrics(sprite,threshold=127){
 if(!sprite||!Number.isInteger(sprite.width)||!Number.isInteger(sprite.height)||sprite.width<1||sprite.height<1||!(sprite.data instanceof Uint8Array || sprite.data instanceof Uint8ClampedArray)||sprite.data.length!==sprite.width*sprite.height*4)throw new Error('expected valid RGBA sprite');
 const w=sprite.width,h=sprite.height,mask=new Uint8Array(w*h),queue=new Int32Array(w*h);let area=0,xmin=w,xmax=-1,ymin=h,ymax=-1;
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  let i=y*w+x;if(sprite.data[i*4+3]>threshold){mask[i]=1;area++;xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);}
 }
 if(!area)return {empty:true,area:0,components:0,holes:0,coverage:0,fill:0,bbox:null};
 function componentsOf(target){let seen=new Uint8Array(w*h),count=0;
  for(let start=0;start<w*h;start++)if(mask[start]===target&&!seen[start]){
   count++;let a=0,b=0;queue[b++]=start;seen[start]=1;
   while(a<b){let k=queue[a++],x=k%w,y=Math.floor(k/w);for(let n of [x>0?k-1:-1,x+1<w?k+1:-1,y>0?k-w:-1,y+1<h?k+w:-1]){
    if(n>=0&&!seen[n]&&mask[n]===target){seen[n]=1;queue[b++]=n;}
   }}
  }
  return count;
 }
 // Background components not touching canvas edges are holes.
 let bgSeen=new Uint8Array(w*h), holes=0;
 for(let start=0;start<w*h;start++)if(!mask[start]&&!bgSeen[start]){
  let a=0,b=0,touches=false;queue[b++]=start;bgSeen[start]=1;
  while(a<b){let k=queue[a++],x=k%w,y=Math.floor(k/w);if(x===0||y===0||x===w-1||y===h-1)touches=true;
   for(let n of [x>0?k-1:-1,x+1<w?k+1:-1,y>0?k-w:-1,y+1<h?k+w:-1])if(n>=0&&!bgSeen[n]&&!mask[n]){bgSeen[n]=1;queue[b++]=n;}
  }if(!touches)holes++;
 }
 const bw=xmax-xmin+1,bh=ymax-ymin+1;
 return {empty:false,area,components:componentsOf(1),holes,coverage:area/(w*h),fill:area/(bw*bh),bbox:[xmin,ymin,xmax,ymax]};
}
function silhouetteCheck(sprite,opts={}){
 const m=silhouetteMetrics(sprite,opts.alphaThreshold??127),p=opts.profile||{},fail=[];
 if(m.empty)fail.push('empty sprite');
 if(!m.empty){if(m.components>(p.maxComponents??3))fail.push('too many components');
  if(m.fill<(p.minFill??0.2))fail.push('low bounding-box fill');
  if(m.coverage<(p.minCoverage??0.015))fail.push('very low coverage');
  if(m.holes>(p.maxHoles??12))fail.push('too many holes');
  if(p.minArea!=null&&m.area<p.minArea)fail.push('area below calibrated threshold');
 }
 return {...m,pass:fail.length===0,findings:fail};
}
module.exports={silhouetteMetrics,silhouetteCheck};
