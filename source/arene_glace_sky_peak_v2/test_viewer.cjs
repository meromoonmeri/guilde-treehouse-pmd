// DOM simulé : logique UI et présence des fichiers ; pas navigateur réel.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const R=path.resolve(__dirname,'../..'),O=path.join(R,'renders/arene_glace_sky_peak_v2'),html=fs.readFileSync(path.join(O,'index.html'),'utf8');
const data=JSON.parse(html.match(/<script id="data"[^>]*>([\s\S]*?)<\/script>/)[1]),code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let draws=[],missing=[];const ids={},checks=[];
function el(tag){return {tag,children:[],listeners:{},style:{},value:'',checked:false,textContent:'',clientWidth:800,append(...x){this.children.push(...x)},addEventListener(k,f){this.listeners[k]=f},click(){this.listeners.click?.()},toDataURL(){return 'data:image/png;base64,TEST'}};}
for(const id of ['data','canvas','viewport','toggles','zoom','status','clock','seek','play','step','all','before','alone','export'])ids[id]=el('div');
ids.data.textContent=JSON.stringify(data);ids.zoom.value='fit';ids.canvas.getContext=()=>({clearRect(){draws=[]},drawImage(im){draws.push(im.path)}});
class Image{set src(p){this.path=p;queueMicrotask(()=>{if(fs.existsSync(path.join(O,p)))this.onload();else{missing.push(p);this.onerror()}})}}
const sandbox=vm.createContext({document:{hidden:false,getElementById:id=>ids[id],createElement:el,createTextNode:text=>({textContent:text})},Image,ResizeObserver:class{observe(){}},matchMedia:()=>({matches:true}),requestAnimationFrame(){},console,Promise});
function check(name,test){assert(test,name);checks.push(name)}
(async()=>{
 vm.runInContext(code,sandbox);await new Promise(r=>setImmediate(r));
 check('10calques chargés, préférences mouvement respectées',draws.length===10&&ids.toggles.children.length===10&&ids.play.textContent==='Lecture');
 check('Ordre : onde derrière lune et montagnes',draws.indexOf(data.aurora.frames[0])<draws.indexOf(data.layers['03_lune_canonique'])&&draws.indexOf(data.layers['03_lune_canonique'])<draws.indexOf(data.layers['04_montagnes_lointaines']));
 ids.before.listeners.click();check('Avant :8plans V1 sans onde ni sapins',draws.length===8&&!draws.some(p=>p.includes('sapins')||p.includes('_onde_')));
 ids.all.listeners.click();check('Après :10plans',draws.length===10);
 ids.alone.listeners.click();check('Onde seule transparente',draws.length===1&&draws[0]===data.aurora.frames[0]);
 ids.step.listeners.click();check('Frame suivante sur pose1',draws[0]===data.aurora.frames[1]);
 ids.seek.value='31';ids.seek.listeners.input();check('Curseur sur pose31',draws[0]===data.aurora.frames[31]);
 ids.step.listeners.click();check('Raccord31→0',draws[0]===data.aurora.frames[0]);
 ids.all.listeners.click();ids.toggles.children[3].children[0].checked=false;ids.toggles.children[3].children[0].listeners.change();check('Lune indépendante désactivable',draws.length===9&&!draws.includes(data.layers['03_lune_canonique']));
 ids.zoom.value='2';ids.zoom.listeners.change();check('Zoom2x',ids.canvas.style.width==='1920px');ids.zoom.value='fit';ids.zoom.listeners.change();check('Ajustement',ids.canvas.style.width==='800px');
 ids.export.listeners.click();check('Export PNG sans exception',true);
 check('42images locales existantes',missing.length===0);
 fs.writeFileSync(path.join(__dirname,'viewer_checks.json'),JSON.stringify({status:'PASS',type:'DOM simulé, pas navigateur réel',checks_count:checks.length,checks},null,2)+'\n');console.log(checks.length+' contrôles UI PASS (DOM simulé).');
})().catch(e=>{console.error(e);process.exit(1)});
