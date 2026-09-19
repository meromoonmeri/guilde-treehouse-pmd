// DOM/canvas-call simulation only; not a browser, screenshot or GPU rendering test.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const out=path.resolve(__dirname,'../../exports/ice_arena_aurora_native_v2');
const html=fs.readFileSync(path.join(out,'review/index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const checks=[],all=[];let raf=null,clock=0;
class Element{
 constructor(tag,id=''){this.tagName=tag;this.id=id;this.children=[];this.style={};this.events={};this.value='0';this.disabled=true;this.calls=[];this.context={clearRect:(...a)=>{this.calls=[]},drawImage:(...a)=>this.calls.push(a),imageSmoothingEnabled:true};all.push(this)}
 append(...items){this.children.push(...items)}
 addEventListener(type,fn){this.events[type]=fn}
 getContext(){return this.context}
 emit(type){this.events[type]({target:this})}
}
const ids=Object.fromEntries(['scene','bg','play','time','readout','parts','terrain','reset','zoom','restore','loading'].map(id=>[id,new Element('element',id)]));
const document={getElementById:id=>ids[id],createElement:tag=>new Element(tag),createTextNode:text=>({textContent:text}),querySelectorAll:()=>all.filter(e=>e.type==='checkbox')};
class ImageMock{set src(v){this.source=v;queueMicrotask(()=>this.onload())}}
function check(name,condition){assert(condition,name);checks.push({check:name,status:'PASS'})}
async function main(){
 vm.runInNewContext(script,{document,Image:ImageMock,performance:{now:()=>clock},requestAnimationFrame:fn=>{raf=fn},console,Promise,Error,Object,Math,Number});
 await new Promise(resolve=>setImmediate(resolve));
 check('All embedded PNG references reached load callbacks',ids.loading.hidden===true);
 check('Playback controls enabled after loading',!ids.play.disabled&&!ids.time.disabled&&!ids.reset.disabled);
 check('Native pixel smoothing disabled on both canvases',!ids.scene.context.imageSmoothingEnabled&&!ids.bg.context.imageSmoothingEnabled);
 check('Five independent background components exposed',ids.parts.children.length===5&&ids.bg.calls.length===5);
 check('V1 sky and five foreground terrain layers exposed',ids.terrain.children.length===6&&ids.scene.calls.length===7);
 check('BG is positioned at (120,0), without a scaled draw call',ids.scene.calls[1][0]===ids.bg&&ids.scene.calls[1][1]===120&&ids.scene.calls[1][2]===0&&ids.scene.calls.every(c=>c.length===3));
 clock=2000;raf(clock);check('Nominal 60 Hz reaches the lower native endpoint at 2 seconds',ids.readout.textContent.includes('Tick 120 / 239')&&ids.readout.textContent.includes('EVA 0/16 · EVB 16/16'));
 clock=4000;raf(clock);check('240-tick playback wraps to phase zero at 4 seconds',Number(ids.time.value)===0);
 ids.play.emit('click');clock=5000;raf(clock);check('Pause stops time advancement',Number(ids.time.value)===0&&ids.play.textContent==='Lecture');
 ids.time.value='73';ids.time.emit('input');check('Scrubbing pauses and displays selected tick',ids.readout.textContent.includes('Tick 73 / 239')&&ids.play.textContent==='Lecture');
 const ribbons=ids.parts.children[1].children[0];ribbons.checked=false;ribbons.emit('change');check('Aurora checkbox removes just one background component',ids.bg.calls.length===4);
 ids.restore.emit('click');check('Restore re-enables all eleven displayed layers',document.querySelectorAll().every(c=>c.checked)&&ids.bg.calls.length===5);
 ids.zoom.value='2';ids.zoom.emit('change');check('2x inspection changes CSS only',ids.scene.style.width==='1024px'&&ids.scene.style.height==='1440px');
 ids.reset.emit('click');check('Initial-phase button resets and pauses playback',Number(ids.time.value)===0&&ids.play.textContent==='Lecture');
 check('Color-port and runtime limitations remain visible',html.includes('pas une capture bit-à-bit')&&html.includes('Aucun rendu GPU PMDO'));
 const report={status:'PASS',count:checks.length,method:'Node VM with simulated DOM, image load callbacks and canvas call recording',real_browser:false,GPU_rendered:false,checks};
 fs.writeFileSync(path.join(out,'viewer_checks.json'),JSON.stringify(report,null,2)+'\n');console.log(`${checks.length} simulated-DOM checks PASS; not a browser/GPU test.`);
}
main().catch(e=>{console.error(e);process.exitCode=1});
