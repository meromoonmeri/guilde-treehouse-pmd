// DOM simulé : logique et chemins locaux. Ce n'est pas un test Chromium.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'renders/cliffs_metano_v1');
const html=fs.readFileSync(path.join(out,'index.html'),'utf8');
const manifest=JSON.parse(html.match(/<script id="manifest-data"[^>]*>([\s\S]*?)<\/script>/)[1]);
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let draws=[],errors=[];const ids={};
function element(tag){return {tag,children:[],listeners:{},style:{},attrs:{},checked:false,disabled:false,value:'',clientWidth:960,width:1264,height:848,textContent:'',classList:{toggle(){}},append(...children){this.children.push(...children)},addEventListener(type,fn){this.listeners[type]=fn},setAttribute(k,v){this.attrs[k]=v}};}
for(const id of ['manifest-data','canvas','mode','back','zoom','grid','viewport','status','terrain','ciel','astres','nuages','ocean','animate','title','meta','review','png','ora','scene-png','raw','cards'])ids[id]=element('div');
ids['manifest-data'].textContent=JSON.stringify(manifest);ids.mode.value='jour';ids.back.value='alpha';ids.zoom.value='fit';
for(const id of ['terrain','ciel','astres','nuages','ocean'])ids[id].checked=true;
ids.canvas.getContext=()=>({clearRect(){draws=[]},drawImage(im){draws.push(im.path)},beginPath(){},moveTo(){},lineTo(){},stroke(){}});
class Image{set src(src){this.path=src;queueMicrotask(()=>{if(fs.existsSync(path.join(out,src)))this.onload();else {errors.push(src);this.onerror();}})}}
const context=vm.createContext({document:{hidden:false,getElementById:id=>ids[id],createElement:element,querySelectorAll:()=>ids.cards.children},Image,ResizeObserver:class{observe(){}},matchMedia:()=>({matches:true}),requestAnimationFrame(){},console,Map,Promise});
vm.runInContext(code,context);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await flush();assert.equal(ids.cards.children.length,4);assert.equal(draws.length,1);
 for(let i=0;i<4;i++){
  ids.cards.children[i].listeners.click();await flush();
  assert.equal(ids.title.textContent,manifest.zones[i].title);
  assert.equal(ids.cards.children[i].attrs['aria-pressed'],'true');
  for(const mode of ['jour','nuit']){ids.mode.value=mode;ids.mode.listeners.change();await flush();assert.equal(ids.png.href,manifest.zones[i].files['terrain_'+mode]);assert(fs.existsSync(path.join(out,ids.ora.href)));}
 }
 ids.back.value='scene';ids.back.listeners.change();await flush();assert.equal(draws.length,5);assert(!ids.ciel.disabled);
 ids.terrain.checked=false;ids.terrain.listeners.change();await flush();assert.equal(draws.length,4);
 ids.ocean.checked=false;ids.ocean.listeners.change();await flush();assert.equal(draws.length,3);assert(!ids.animate.disabled);
 ids.back.value='magenta';ids.back.listeners.change();await flush();assert.equal(draws.length,0);assert(ids.ciel.disabled);
 ids.zoom.value='2';ids.zoom.listeners.change();assert.equal(ids.canvas.style.width,'2528px');
 ids.zoom.value='fit';ids.zoom.listeners.change();assert.equal(ids.canvas.style.width,'960px');
 assert.equal(errors.length,0);assert(!ids.animate.checked,'prefers-reduced-motion respecté');
 console.log('PASS : 4 sélections, 8 liens jour/nuit, calques, transparence, magenta, zoom, préférence mouvement et chemins PNG — DOM simulé.');
})().catch(e=>{console.error(e);process.exit(1)});
