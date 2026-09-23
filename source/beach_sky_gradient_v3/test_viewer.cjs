// DOM simulation only. No claim of graphical-browser or PMDO validation.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),cp=require('node:child_process');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'renders/beach_sky_gradient_v3');
class Element{constructor(tag){this.tag=tag;this.children=[];this.style={};this.clientWidth=840;this.value='';this.hidden=false;this.checked=false;this.ops=[];this.downloads=[]}set innerHTML(v){this.children=[]}append(...xs){this.children.push(...xs)}querySelectorAll(tag){return this.children.flatMap(c=>[(c.tag===tag?c:null),...c.querySelectorAll(tag)].filter(Boolean))}getContext(){return{clearRect:()=>{this.ops=[]},fillRect(){},drawImage:(im,...args)=>this.ops.push([im.src,...args]),save(){},restore(){},beginPath(){},rect(){},clip(){},moveTo(){},lineTo(){},stroke(){},fillText(){}}}getBoundingClientRect(){return{left:0,top:0,width:this.width,height:this.height}}toDataURL(){return'data:image/png;base64,TEST'}click(){this.downloads.push(this.download)}}
const settle=()=>new Promise(r=>setImmediate(r));
function create(html,base){const ids={},files=[],downloads=[];for(const m of html.matchAll(/id="([^"]+)"/g))ids[m[1]]=new Element(m[1]==='view'?'canvas':'div');ids.zoom.value='fit';ids.view.width=1024;ids.view.height=1024;const legend=new Element('div');class MockImage{set src(v){this._src=v;files.push(v);queueMicrotask(()=>fs.existsSync(path.join(base,v))?this.onload():this.onerror())}get src(){return this._src}}
const sandbox={console,Math,Number,String,JSON,Promise,Map,Image:MockImage,document:{getElementById:k=>ids[k],querySelector:()=>legend,createElement:tag=>{const e=new Element(tag);e.click=()=>downloads.push(e.download);return e}},window:{addEventListener(){}},requestAnimationFrame(){}};vm.createContext(sandbox);const run=s=>vm.runInContext(s,sandbox);run(html.match(/<script>([\s\S]*?)<\/script>/)[1]);return{ids,run,files,downloads,base,legend}}
(async()=>{
 const full=create(fs.readFileSync(path.join(out,'index.html'),'utf8'),out);await settle();const {ids,run}=full;
 assert(run('ready'));assert.equal(run('selection'),'plage_reference');assert.equal(ids.view.width,702);assert.equal(ids.view.height,578);
 const selections=[...run('DATA.rooms.map(r=>r.id)'),'plage_reference','reseau','extension'];let tested=0;
 for(const mode of ['jour','crepuscule','nuit']){
  await run(`mode=${JSON.stringify(mode)};load()`);
  for(const selection of selections){
   await run(`selection=${JSON.stringify(selection)};load()`);assert(run('ready'));tested++;
   assert(ids.view.ops.some(o=>o[0].includes('ciel_'+mode)));assert(ids.view.ops.some(o=>o[0].includes('etoiles_'+mode)));
   if(!['reseau','extension','plage_reference'].includes(selection)){assert.equal(ids.view.width,512);assert.equal(ids.view.height,624)}
   run('playing=false;elapsed=0;draw()');const zero=JSON.stringify(ids.view.ops);run('elapsed=64000;draw()');assert.equal(JSON.stringify(ids.view.ops),zero);
  }
 }
 ids.dusk.onclick();await settle();assert.equal(run('mode'),'crepuscule');assert.equal(ids.dusk.className,'active');
 ids.reference.onclick();await settle();assert.equal(ids.view.height,578);
 const clouds=ids.layers.querySelectorAll('input')[2];clouds.checked=false;clouds.onchange();assert(!ids.view.ops.some(o=>o[0].includes('nuages')));ids.all.onclick();assert(ids.view.ops.some(o=>o[0].includes('nuages')));
 ids.layers.children[0].children[2].onclick({preventDefault(){}});assert(full.downloads.at(-1).includes('sky'));ids.export.onclick();assert(full.downloads.at(-1).endsWith('.png'));
 ids.day.onclick();ids.night.onclick();await settle();assert(run('ready'));assert.equal(run('mode'),'nuit');
 for(const key of ['pack','still','readme','previous'])assert(fs.existsSync(path.join(out,ids[key].href)),key);
 assert(full.files.every(p=>fs.existsSync(path.join(out,p))));
 const report={pass:true,selections:tested,modes:3,checks:['all ten maps and reference beach','both group layouts','new header on individual maps','sky/stars/cloud layer toggles','64 s canvas-operation equality','PNG export controls','dusk mode button','asynchronous load races','all resource and download URLs'],method:'Node VM DOM/canvas mocks; graphical browser unavailable (Chromium download failed TLS); not PMDO'};
 fs.writeFileSync(path.join(out,'verification_viewer.json'),JSON.stringify(report,null,2)+'\n');console.log(report);
})().catch(e=>{console.error(e);process.exitCode=1});
