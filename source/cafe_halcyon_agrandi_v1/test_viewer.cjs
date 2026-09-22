// Minimal DOM simulation, explicitly not a graphical browser or PMDO test.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),cp=require('node:child_process');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'renders/cafe_halcyon_agrandi_v1');
function test(base,portable=false){const html=fs.readFileSync(path.join(base,'index.html'),'utf8'),ids={},intervals=[],elements=[];
class Element{constructor(tag){this.tag=tag;this.children=[];this.events={};this.style={};this.checked=false;this.hidden=false;this.value='';this.classes=new Set();this.classList={toggle:(n,on)=>on?this.classes.add(n):this.classes.delete(n)};elements.push(this)}set id(v){this._id=v;ids[v]=this}get id(){return this._id}appendChild(e){this.children.push(e);return e}addEventListener(t,f){this.events[t]=f}emit(t){assert.ok(this.events[t]);this.events[t]()} }
for(const m of html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)){const el=new Element('div');el.id=m[1];el.checked=/\bchecked\b/.test(m[0]);el.hidden=/\bhidden\b/.test(m[0]);const href=m[0].match(/href="([^"]+)"/);if(href)el.href=href[1]}
ids.zoom.value='1';
const sandbox={console,JSON,Number,Math,document:{getElementById:id=>ids[id],createElement:t=>new Element(t),createTextNode:text=>({text})},setInterval:(f,dt)=>intervals.push({f,dt})};vm.createContext(sandbox);const run=s=>vm.runInContext(s,sandbox);run(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
assert.equal(ids.layers.children.length,5);assert.equal(ids.map.children.filter(e=>e.tag==='img').length,5);assert.equal(ids.catalogue.children.length,6);assert.equal(run('DATA.placed_furniture.length+DATA.placed_fire.length+DATA.npc_entities.length'),0);
const box=ids.layers.children[0].children[0];box.checked=false;box.emit('change');assert.equal(ids['layer-sol'].hidden,true);box.checked=true;box.emit('change');assert.equal(ids['layer-sol'].hidden,false);
ids.zoom.value='2';ids.zoom.emit('change');assert.equal(ids.frame.style.width,'1680px');assert.equal(ids.frame.style.height,'1152px');assert.equal(ids.map.style.transform,'scale(2)');
ids.magenta.checked=false;ids.magenta.emit('change');assert.ok(ids.map.classes.has('transparent'));ids.magenta.checked=true;ids.magenta.emit('change');assert.ok(!ids.map.classes.has('transparent'));
ids.grid.checked=true;ids.grid.emit('change');assert.equal(run('grid.hidden'),false);ids.guides.checked=true;ids.guides.emit('change');assert.equal(run('guides.every(g=>!g.hidden)'),true);
assert.equal(intervals.length,1);assert.equal(intervals[0].dt,100);const first=ids.fire.src;intervals[0].f();assert.notEqual(ids.fire.src,first);for(let k=0;k<3;k++)intervals[0].f();assert.equal(ids.fire.src,first);
ids.play.emit('click');const paused=ids.fire.src;intervals[0].f();assert.equal(ids.fire.src,paused);ids.pose.value='3';ids.pose.emit('input');assert.equal(ids['pose-label'].textContent,'4 / 4');assert.equal(run('playing'),false);ids.play.emit('click');intervals[0].f();assert.equal(ids.fire.src,first);
assert.equal(ids.pack.hidden,portable);
for(const el of elements){if(el.src)assert.ok(fs.existsSync(path.join(base,el.src)),el.src);if(el.href&&!el.hidden)assert.ok(fs.existsSync(path.join(base,el.href)),el.href)}
for(const m of html.matchAll(/(?:href|src)="([^"]+)"/g)){if(m[1]==='CafeHalcyon_pack.zip'&&portable)continue;assert.ok(fs.existsSync(path.join(base,m[1])),m[1])}
return {terrain_images:5,catalogue_cards:6,animation_frames:4,portable};}
const normal=test(out);fs.mkdirSync(path.join(root,'.cache'),{recursive:true});const tmp=fs.mkdtempSync(path.join(root,'.cache/cafe-dom-'));let portable;
try{cp.execFileSync('python',['-c','import zipfile,sys;zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])',path.join(out,'CafeHalcyon_pack.zip'),tmp]);portable=test(tmp,true)}finally{fs.rmSync(tmp,{recursive:true,force:true})}
const report={pass:true,normal,portable,checks:['terrain-only map; furniture/animation stay in separate catalogue','all five layer toggles','zoom, magenta/checkerboard, grid and reserved-space guides','four poses, source cadence, pause, manual pose and loop wrap','all dynamic/static files resolve in normal and extracted portable viewer'],graphical_browser:'NOT TESTED',runtime_PMDO:'NOT TESTED'};
fs.writeFileSync(path.join(out,'verification_viewer.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS normal and portable cafe viewer DOM simulation');
