// Simulated DOM/canvas calls, NOT a browser/GPU test.
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert');
const out=path.resolve(__dirname,'../../renders/ice_arena_northern_sky_v4');
const html=fs.readFileSync(path.join(out,'index.html'),'utf8'),script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements=[],checks=[];let clock=0,raf;
class Element{constructor(){this.children=[];this.events={};this.style={};this.disabled=true;this.value='0';this.calls=[];this.context={clearRect:()=>{this.calls=[]},drawImage:(...a)=>this.calls.push(a),imageSmoothingEnabled:true};elements.push(this)}append(...a){this.children.push(...a)}addEventListener(n,f){this.events[n]=f}getContext(){return this.context}emit(n){this.events[n]({target:this})}}
const ids=Object.fromEntries(['scene','skyview','layers','loading','play','reset','zoom','phase','readout','restore'].map(i=>[i,new Element()]));
const document={getElementById:id=>ids[id],createElement:()=>new Element(),createTextNode:s=>({textContent:s}),querySelectorAll:()=>elements.filter(e=>e.type==='checkbox')};
class Im{set src(v){this.srcValue=v;queueMicrotask(()=>this.onload())}}
function check(name,ok){assert(ok,name);checks.push({check:name,status:'PASS'})}
async function main(){
 vm.runInNewContext(script,{document,Image:Im,performance:{now:()=>clock},requestAnimationFrame:f=>raf=f,Promise,Error,Math,Number,Object,console});
 await new Promise(resolve=>setImmediate(resolve));
 check('Images load before controls are enabled',ids.loading.hidden&&!ids.play.disabled&&!ids.phase.disabled);
 check('Five layer toggles available',ids.layers.children.length===5);
 check('Background and terrain separated in render order',ids.skyview.calls.length===4&&ids.scene.calls.length===5);
 check('Pixel smoothing disabled',!ids.scene.context.imageSmoothingEnabled&&!ids.skyview.context.imageSmoothingEnabled);
 check('No canvas scaling of effect or terrain textures',ids.scene.calls.every(c=>c.length===3));
 clock=3200;raf(clock);check('Second key pose at 3.2 seconds',Number(ids.phase.value)===32);
 clock=6400;raf(clock);check('Aurora loops at 6.4 seconds',Number(ids.phase.value)===0);
 check('Clouds do not reset with the aurora loop',ids.scene.calls[3][1]===-12);
 ids.play.emit('click');clock=7400;raf(clock);check('Pause stops playback time',Number(ids.phase.value)===0&&ids.play.textContent==='Lecture');
 ids.phase.value='17';ids.phase.emit('input');check('Scrubbing displays chosen phase and pauses',Number(ids.phase.value)===17&&ids.play.textContent==='Lecture');
 const toggle=ids.layers.children[2].children[0];toggle.checked=false;toggle.emit('change');check('Aurora can be hidden independently',ids.skyview.calls.length===3&&ids.scene.calls.length===4);
 ids.restore.emit('click');check('All five layers can be restored',document.querySelectorAll().every(c=>c.checked)&&ids.scene.calls.length===5);
 ids.zoom.value='2';ids.zoom.emit('change');check('Inspection zoom changes CSS only',ids.scene.style.width==='1024px'&&ids.scene.style.height==='1440px');
 ids.reset.emit('click');check('Reset returns to initial paused state',Number(ids.phase.value)===0&&ids.scene.calls[3][1]===0&&ids.play.textContent==='Lecture');
 check('Generated art and runtime limits remain visible',html.includes('Extension générée, pas frames officielles')&&html.includes('Aucun rendu GPU PMDO'));
 fs.writeFileSync(path.join(out,'viewer_checks.json'),JSON.stringify({status:'PASS',count:checks.length,method:'simulated DOM / canvas-call recording',real_browser:false,GPU_tested:false,checks},null,2)+'\n');
 console.log(`${checks.length} simulated-DOM checks PASS; no browser/GPU validation.`);
}
main().catch(e=>{console.error(e);process.exitCode=1});
