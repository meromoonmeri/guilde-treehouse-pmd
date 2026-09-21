// Simulated DOM: navigation, port links, layer toggles, weather, pause. Not a real browser test.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const dir=path.join(__dirname,'../../renders/winter_forest_native_v2');
const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const network=JSON.parse(fs.readFileSync(path.join(dir,'network.json'),'utf8'));
class El{constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.style={};this.dataset={};this.hidden=false;this.checked=false;this.value='';this._src='';this.textContent='';}
 set src(v){this._src=v;assert(fs.existsSync(path.join(dir,v.split('?')[0])),'missing asset '+v);}get src(){return this._src}
 set innerHTML(v){this.children=[];const m=v.match(/src="([^"]+)"/);if(m)assert(fs.existsSync(path.join(dir,m[1])),'missing thumb '+m[1]);}
 set href(v){this._href=v;if(!v.startsWith('..'))assert(fs.existsSync(path.join(dir,v)),'missing link '+v);}get href(){return this._href}
 append(...c){this.children.push(...c)}replaceChildren(){this.children=[]}setAttribute(k,v){this.attributes[k]=v}}
const els={};const ids=['network','snow','forest','powder','flakes','ports','sky','weather','zoom','pause','scene-title','dimensions','status','stage','sky-panel','sky-image','terrain','snow-image','forest-image','powder-image','flakes-image','port-buttons','terrain-link','ora-link','animation-link'];
ids.forEach(i=>els[i]=new El('x'));['snow','forest','ports'].forEach(i=>els[i].checked=true);els.weather.value='cloudy';els.zoom.value='1';
const document={getElementById:id=>{assert(els[id],'unknown id '+id);return els[id]},createElement:t=>new El(t),querySelectorAll:()=>els.network.children};
let resolveLoad;const loaded=new Promise(r=>resolveLoad=r);
const ctx={document,fetch:async()=>({ok:true,json:async()=>{setTimeout(resolveLoad,0);return network}}),Error,console};
vm.createContext(ctx);vm.runInContext(script,ctx);
(async()=>{await loaded;await new Promise(r=>setTimeout(r,5));
 assert.equal(els.network.children.length,6);assert.match(els['scene-title'].textContent,/01 — La lisière/);
 assert.equal(els['port-buttons'].children.length,3);
 // Follow the whole cycle through port buttons: 01.E→02, 02.N→04, 04.N→06, 06.W→05, 05.S→03, 03.S→01.
 const go=dir=>{const b=els['port-buttons'].children.find(b=>b.textContent.startsWith(dir+' '));assert(b,'no port '+dir);b.onclick()};
 go('E');assert.match(els['scene-title'].textContent,/^02/);go('N');assert.match(els['scene-title'].textContent,/^04/);go('N');assert.match(els['scene-title'].textContent,/^06/);
 assert.equal(els.weather.value,'boreal');go('N');assert.match(els.status.textContent,/arène V5/);go('W');assert.match(els['scene-title'].textContent,/^05/);go('S');assert.match(els['scene-title'].textContent,/^03/);go('S');assert.match(els['scene-title'].textContent,/^01/);go('S');assert.match(els.status.textContent,/extérieure/);
 els.forest.checked=false;els.forest.onchange();assert(els['forest-image'].hidden);
 els.powder.checked=true;els.powder.onchange();assert(!els['powder-image'].hidden&&/Powder_Animated/.test(els['powder-image'].src));
 els.pause.onclick();assert(/Powder_000/.test(els['powder-image'].src));els.pause.onclick();
 els.sky.checked=true;els.weather.value='boreal';els.sky.onchange();assert(!els['sky-panel'].hidden&&/boreal_Animated/.test(els['sky-image'].src));
 els.zoom.value='2';els.zoom.onchange();assert.equal(els.stage.style.zoom,'2');
 console.log('PASS simulated DOM: 6 nodes, full cycle by ports, arena/exterior messages, layers, effects, pause, sky, zoom');
})().catch(e=>{console.error(e);process.exit(1)});
