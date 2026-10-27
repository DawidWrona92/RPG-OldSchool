"""Rzeczywista kontrola odtwarzacza w Chromium, bez stałego serwera lub usług."""
import contextlib,functools,hashlib,http.server,json,threading,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
handler=functools.partial(QuietHandler,directory=str(ROOT));server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage']);page=browser.new_page(viewport={'width':1640,'height':1000},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/previews/review.html');page.wait_for_function('Object.values(imgs).length===8 && Object.values(imgs).every(i=>i.complete&&i.naturalWidth>0)');page.click('#play');assert not page.evaluate('playing')
  canvases=page.locator('canvas').evaluate_all('(es)=>es.map(e=>({internal:[e.width,e.height],css:[e.getBoundingClientRect().width,e.getBoundingClientRect().height]}))');assert all(c['internal']==c['css']==[768,432] for c in canvases),canvases
  steps={}
  for anim,count in [('chod',12),('spoczynek',8)]:
   page.select_option('#anim',anim);assert page.locator('#frame').get_attribute('max')==str(count-1)
   first=page.locator('#after').evaluate('(e)=>e.toDataURL()');page.locator('#frame').evaluate("e=>{e.value='3';e.dispatchEvent(new Event('input',{bubbles:true}))}");assert page.evaluate('frame')==3;second=page.locator('#after').evaluate('(e)=>e.toDataURL()');assert first!=second
   steps[anim]={'manual_frame_0_vs_3_different':True,'frame_count':count}
  page.select_option('#anim','chod');page.click('#play');start=page.evaluate('({t:performance.now(),f:frame})');page.wait_for_timeout(1200);end=page.evaluate('({t:performance.now(),f:frame})');page.click('#play');assert start['f']!=end['f'],(start,end)
  page.screenshot(path=str(ROOT/'previews/odtwarzacz-kontrola.png'),full_page=True);assert not errors,errors
  report={'browser':'system Chromium / Playwright','source_blend_sha256':json.loads((ROOT/'source/art-source.json').read_text())['source_sha256'],'loaded_atlases':8,'canvas_native_dimensions':canvases,'manual_steps':steps,'playback_sample':{'start':start,'end':end,'expected_ms_per_walk_frame':80},'javascript_errors':errors,'scope':'interactive preview only; not target engine or artistic motion acceptance'}
  (ROOT/'previews/viewer-validation.json').write_text(json.dumps(report,indent=2)+'\n');browser.close();print('PASS browser viewer: 8 atlases, native canvases, pause, step, playback, no JS errors')
finally:server.shutdown();server.server_close();thread.join()
