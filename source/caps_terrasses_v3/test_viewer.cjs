// Control/clock tests with a simulated DOM. Not a browser or engine render test.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element {
 constructor(){this.value='0';this.checked=true;this.children=[];this.listeners={};this.width=820;this.height=328;this.ctx={imageSmoothingEnabled:false,drawImage(){},clearRect(){},putImageData(){},getImageData:()=>({data:new Uint8ClampedArray(820*328*4)}),createImageData:()=>({data:new Uint8ClampedArray(820*328*4)})}}
 add(o){this.children.push(o)}addEventListener(name,fn){this.listeners[name]=fn}getContext(){return this.ctx}
 set src(s){this._src=s;if(this.onload)this.onload()}get src(){return this._src}
}
(async()=>{
 const elements={},$=id=>elements[id]??=new Element();$('cycle').value='smooth';$('night').checked=false;
 let next;const context={document:{getElementById:$,createElement:()=>new Element()},Image:Element,Option:class{constructor(text,value){this.text=text;this.value=value}},requestAnimationFrame:fn=>{next=fn},Uint8Array,Uint8ClampedArray,console};vm.createContext(context);
 const html=fs.readFileSync('apercu_caps_terrasses_v3.html','utf8'),script=html.match(/<script>([\s\S]*)<\/script>/)[1];vm.runInContext(script,context);await new Promise(setImmediate);assert(next);next(100);next(150);assert.equal(vm.runInContext('lastPhase',context),1);
 assert.equal($('zone').children.length,6);
 for(let i=0;i<6;i++)for(const night of [false,true]){$('zone').value=String(i);$('night').checked=night;$('zone').listeners.change();next(150);assert($('png').href.endsWith(night?'_terrain_nuit.png':'_terrain.png'))}
 const before=vm.runInContext('elapsed',context);$('play').onclick();next(500);assert.equal(vm.runInContext('elapsed',context),before);$('play').onclick();next(550);assert.equal(vm.runInContext('elapsed',context),before+50);
 for(const id of ['terrain','sea','sky','cloud']){$(id).checked=false;$(id).listeners.change();next(550);$(id).checked=true}
 for(let i=0;i<64;i++)assert.equal(vm.runInContext(`phaseAt(${i*50},false)`,context),i);
 assert.equal(vm.runInContext('phaseAt(3200,false)',context),0);
 for(let i=0;i<8;i++)assert.equal(vm.runInContext(`phaseAt(${i*160},true)`,context),i*8);
 assert.equal(vm.runInContext('phaseAt(1280,true)',context),0);
 console.log('PASS: 12 terrain/ambience choices, four visibility controls, pause/resume, 64-phase and legacy clocks; simulated DOM only.');
})().catch(e=>{console.error(e);process.exit(1)});
