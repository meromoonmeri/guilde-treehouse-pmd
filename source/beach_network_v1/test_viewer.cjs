// Simulated DOM, not a browser render or PMDO runtime test.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),html=fs.readFileSync(path.join(root,'apercu_reseau_plage_v1.html'),'utf8'),code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const downloads=[],resources=[];
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.style={};this.clientWidth=840;this.value='';this.checked=false;this.disabled=false;this.ops=[]}
 set innerHTML(v){this.children=[]}get innerHTML(){return ''}
 append(...nodes){this.children.push(...nodes)}
 querySelectorAll(tag){return this.children.flatMap(c=>[(c.tag===tag?c:null),...c.querySelectorAll(tag)].filter(Boolean))}
 getContext(){return {imageSmoothingEnabled:false,clearRect:()=>{this.ops=[]},fillRect(){},drawImage:(im,...args)=>this.ops.push([im.src,...args]),save(){},restore(){},beginPath(){},rect(){},clip(){}}}
 getBoundingClientRect(){return {left:0,top:0,width:this.width,height:this.height}}
 toDataURL(){return 'data:image/png;base64,TEST'}click(){downloads.push(this.download)}
}
const ids={};for(const m of html.matchAll(/id="([^"]+)"/g))ids[m[1]]=new Element(m[1]==='view'?'canvas':'div');ids.zoom.value='fit';ids.view.width=1536;ids.view.height=1136;
class MockImage{set src(v){this._src=v;resources.push(v);queueMicrotask(()=>fs.existsSync(path.join(root,v))?this.onload():this.onerror())}get src(){return this._src}}
const sandbox={console,Math,Number,String,JSON,Promise,Map,Image:MockImage,document:{getElementById:k=>ids[k],createElement:tag=>new Element(tag)},window:{addEventListener(){}},requestAnimationFrame(){}};
vm.createContext(sandbox);const run=s=>vm.runInContext(s,sandbox);run(code);const settle=()=>new Promise(r=>setImmediate(r));
(async()=>{
 await settle();assert.equal(run('ready'),true);assert.equal(run('chosen.length'),6);assert.equal(ids.layers.querySelectorAll('input').length,13);assert.equal(ids.play.disabled,false);
 ids.play.onclick();assert.equal(run('playing'),false);const zero=JSON.stringify(ids.view.ops);ids.wrap.onclick();assert.equal(run('elapsed'),64000);assert.equal(JSON.stringify(ids.view.ops),zero);ids.wrap.onclick();assert.equal(run('elapsed'),0);
 ids.scrub.oninput({target:{value:'1200'}});assert.equal(run('elapsed'),1200);assert.notEqual(JSON.stringify(ids.view.ops),zero);
 const ch=ids.layers.querySelectorAll('input')[1];ch.checked=false;ch.onchange();assert.equal(run('enabled.cloud'),false);assert.ok(!ids.view.ops.some(x=>x[0].includes('nuages')));ids.all.onclick();assert.equal(run('enabled.cloud'),true);
 ids.layers.children[1].children[2].onclick({preventDefault(){}});assert.ok(downloads.at(-1).includes('cloud'));ids.export.onclick();assert.ok(downloads.at(-1).endsWith('.png'));
 ids.view.onclick({clientX:768,clientY:880});await settle();assert.equal(run('selection'),'05_carrefour_croix');assert.equal(ids.view.width,512);assert.equal(ids.ports.children.length,4);assert.equal(ids.layers.querySelectorAll('input').length,11);
 ids.ports.children[0].onclick();await settle();assert.equal(run('selection'),'02_carrefour_t');
 ids.room.value='05_carrefour_croix';ids.room.onchange();await settle();ids.ports.children[2].onclick();assert.equal(run('selection'),'05_carrefour_croix');assert.ok(ids.status.textContent.includes('réservée'));
 ids.skyFix.onclick();await settle();assert.equal(run('selection'),'plage_reference');assert.equal(ids.view.width,702);assert.equal(ids.view.height,578);assert.equal(ids.layers.querySelectorAll('input').length,10);
 ids.day.onclick();await settle();assert.equal(run('mode'),'jour');assert.ok(ids.view.ops.some(x=>x[0].includes('ciel_jour')));
 ids.zoom.value='2';ids.zoom.onchange();assert.equal(ids.view.style.width,'1404px');
 ids.plan.onclick();await settle();assert.equal(run('selection'),'ensemble');assert.equal(run('schematic'),true);assert.equal(ids.view.ops.length,1);ids.plan.onclick();assert.equal(run('schematic'),false);
 run('playing=true;elapsed=63900;last=100;tick(250)');assert.equal(run('elapsed'),50);
 // Race protection: the latest scene/mode load must win.
 ids.night.onclick();ids.day.onclick();await settle();assert.equal(run('mode'),'jour');assert.equal(run('ready'),true);
 assert.ok(resources.every(p=>fs.existsSync(path.join(root,p))));
 for(const m of html.matchAll(/href="([^"]+)"/g))if(!m[1].includes('://'))assert.ok(fs.existsSync(path.join(root,m[1])),'missing link '+m[1]);
 const packaged=fs.readFileSync(path.join(root,'renders/beach_network_v1/index.html'),'utf8');assert.ok(packaged.includes('const ROOT="./"'));assert.ok(!packaged.includes('href="renders/beach_network_v1/'));
 const report={pass:true,scope:'Simulated DOM: loading all assets, day/night, play/pause, scrub, whole-loop clock, exact 0/64 draw calls, layers, exports, zoom, clickable ensemble, linked ports, reserved exit, reference scene, plan, load races, links and packaged paths.',browser:'NOT TESTED: no installed graphical browser',runtime_PMDO:'NOT TESTED'};
 fs.writeFileSync(path.join(root,'renders/beach_network_v1/verification_viewer.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS viewer interactions (simulated DOM only).');
})().catch(e=>{console.error(e);process.exitCode=1});
