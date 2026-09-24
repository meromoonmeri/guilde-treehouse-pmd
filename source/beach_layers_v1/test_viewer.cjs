// DOM simulation only. Pixel/codec correctness is checked independently by verify.py.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'apercu_beach_calques_v1.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let downloads=[];
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.style={};this.value='';this.checked=false;this.disabled=false;this.clientWidth=750;this.ops=[];}
 append(...xs){this.children.push(...xs)}
 getContext(){return {clearRect:()=>{this.ops=[]},drawImage:(im)=>this.ops.push(im.src),imageSmoothingEnabled:false}}
 querySelectorAll(tag){return this.children.flatMap(c=>c instanceof Element?[(c.tag===tag?c:null),...c.querySelectorAll(tag)].filter(Boolean):[])}
 toDataURL(){return 'data:image/png;base64,TEST'}
 click(){downloads.push({name:this.download,src:this.href})}
}
const ids={};for(const m of html.matchAll(/id="([^"]+)"/g))ids[m[1]]=new Element(m[1]==='scene'?'canvas':'div');
ids.zoom.value='fit';ids.scene.width=702;ids.scene.height=466;
class MockImage{set src(v){this._src=v;queueMicrotask(()=>this.onload())}get src(){return this._src}}
const sandbox={console,Math,Number,String,JSON,Promise,Image:MockImage,document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag)},window:{addEventListener(){}},requestAnimationFrame(){}};
vm.createContext(sandbox);vm.runInContext(script,sandbox);
function run(code){return vm.runInContext(code,sandbox)}
(async()=>{
 await new Promise(r=>setImmediate(r));
 assert.equal(run('ready'),true);assert.equal(ids.play.disabled,false);assert.equal(ids.layers.querySelectorAll('input').length,9);
 assert.equal(run('DATA.surface.length'),64);assert.equal(run('DATA.foam.length'),64);assert.equal(ids.scene.ops.length,9);
 ids.play.onclick();assert.equal(run('playing'),false);
 ids.next.onclick();assert.equal(run('phase'),1);assert.equal(ids.scrub.value,1);
 ids.scrub.oninput({target:{value:'63'}});assert.equal(run('phase'),63);ids.next.onclick();assert.equal(run('phase'),0);
 ids.waterOnly.onclick();assert.equal(ids.scene.ops.length,2);assert.equal(ids.layers.querySelectorAll('input').filter(c=>c.checked).length,2);
 ids.original.onclick();assert.equal(run('referenceMode'),true);assert.equal(ids.scene.ops.length,1);
 ids.all.onclick();assert.equal(run('referenceMode'),false);assert.equal(ids.scene.ops.length,9);
 const c=ids.layers.querySelectorAll('input')[0];c.checked=false;c.onchange();assert.equal(ids.scene.ops.length,8);
 ids.export.onclick();assert.ok(downloads.at(-1).name.endsWith('.png'));
 ids.layers.children[2].children[2].onclick({preventDefault(){}});assert.ok(downloads.at(-1).name.includes('03_mer'));
 ids.zoom.value='2';ids.zoom.onchange();assert.equal(ids.scene.style.width,'1404px');assert.equal(ids.scene.style.height,'932px');
 ids.play.onclick();run('tick(100);tick(250)');assert.equal(run('phase'),3);
 const report={pass:true,scope:'DOM simulation only: preload, play/pause, advance, wrap, scrub, layer toggles, reference, water-only, downloads, zoom, clock',browser:'NOT TESTED: Chromium download failed (TLS ECONNRESET)',runtime_PMDO:'NOT TESTED'};
 fs.writeFileSync(path.join(root,'renders/beach_layers_v1/verification_viewer.json'),JSON.stringify(report,null,2)+'\n');
 console.log('PASS: viewer interactions (simulated DOM; not a browser).');
})().catch(e=>{console.error(e);process.exitCode=1});
