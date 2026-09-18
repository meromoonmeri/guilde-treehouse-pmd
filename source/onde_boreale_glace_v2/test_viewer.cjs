// Test logique du lecteur, DOM simulé, aucun navigateur réel revendiqué.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'renders/onde_boreale_glace_v2');
const page=fs.readFileSync(path.join(out,'index.html'),'utf8');const data=JSON.parse(page.match(/<script id="data"[^>]*>([\s\S]*?)<\/script>/)[1]);const code=page.match(/<script>([\s\S]*?)<\/script>/)[1];
const ids={},checks=[];let draws=[],errors=[];
function element(tag){return {tag,children:[],listeners:{},attrs:{},style:{},value:'',textContent:'',checked:false,width:768,height:640,clientWidth:720,append(...v){this.children.push(...v)},setAttribute(k,v){this.attrs[k]=v},addEventListener(k,f){this.listeners[k]=f},click(){this.listeners.click?.()},toDataURL(){return 'data:image/png;base64,TEST'}};}
for(const id of ['data','canvas','viewport','view','mode','zoom','png','webp','clip','ora','error','time','seek','title','cards','layers','play','step','export'])ids[id]=element('div');
ids.data.textContent=JSON.stringify(data);ids.mode.value='nuit';ids.view.value='scene';ids.zoom.value='fit';ids.canvas.getContext=()=>({clearRect(){draws=[]},drawImage(im,x,y){draws.push({src:im.path,x,y})}});
class Image{set src(p){this.path=p;queueMicrotask(()=>{if(fs.existsSync(path.join(out,p)))this.onload();else {errors.push(p);this.onerror();}})}}
const sandbox=vm.createContext({document:{hidden:false,getElementById:id=>ids[id],createElement:element,createTextNode:t=>({textContent:t}),querySelectorAll:()=>ids.cards.children},Image,ResizeObserver:class{observe(){}},matchMedia:()=>({matches:true}),requestAnimationFrame(){},console,Map,Promise});
const run=code=>vm.runInContext(code,sandbox),flush=()=>new Promise(r=>setImmediate(r));
function check(name,test){assert(test,name);checks.push(name)}
(async()=>{
 run(code);await flush();check('3 layouts,9 cases de calques',ids.cards.children.length===3&&ids.layers.children.length===9);
 check('Réduction des mouvements respectée',ids.play.textContent==='Lecture');
 for(let i=0;i<3;i++){ids.cards.children[i].listeners.click();await flush();check('Sélection layout'+i,ids.title.textContent===data.zones[i].title&&ids.cards.children[i].attrs['aria-pressed']==='true');check('Liens WebP/ORA'+i,ids.webp.href===data.zones[i].webp_loop&&ids.clip.href===data.zones[i].webp_cloud_excerpt&&fs.existsSync(path.join(out,ids.ora.href)));}
 ids.mode.value='jour';ids.mode.listeners.change();await flush();check('Jour sans onde mais avec sol/ciel corrects',!draws.some(d=>d.src.includes('/onde_'))&&draws.some(d=>d.src.includes('ciel_jour'))&&ids.png.href===data.zones[2].scene_jour);
 ids.mode.value='nuit';ids.mode.listeners.change();await flush();check('Nuit avec onde',draws.some(d=>d.src===data.aurora.frames[0]));
 ids.step.listeners.click();await flush();check('Frame suivante =1, lecture pausée',draws.some(d=>d.src===data.aurora.frames[1])&&ids.play.textContent==='Lecture');
 ids.seek.value='160';ids.seek.listeners.input();await flush();check('Seek2s =frame16',draws.some(d=>d.src===data.aurora.frames[16]));
 ids.view.value='effect';ids.view.listeners.change();await flush();check('Onde seule =1plan sur canevas768×224',draws.length===1&&ids.canvas.height===224);
 ids.view.value='sky';ids.view.listeners.change();await flush();check('Ciel seul + étoiles + onde, sans terrain/nuages',draws.length===3&&ids.canvas.height===640);
 ids.view.value='scene';ids.view.listeners.change();await flush();
 run('elapsed=359750;refresh()');await flush();check('Wrap : deux copies jointives au raccord',draws.filter(d=>d.src.includes('nuages_bande')).map(d=>d.x).join(',')==='-1439,1');
 run('elapsed=360000;refresh()');await flush();check('Après360s, position nuage0 et onde0',draws.filter(d=>d.src.includes('nuages_bande')).map(d=>d.x).join(',')==='0'&&draws.some(d=>d.src===data.aurora.frames[0]));
 run('visible.nuages.checked=false;refresh()');await flush();check('Nuages désactivables',!draws.some(d=>d.src.includes('nuages_bande')));
 run('visible.onde.checked=false;refresh()');await flush();check('Onde désactivable',!draws.some(d=>d.src.includes('GLACE_BOREALE_V2_onde_')));
 ids.zoom.value='2';ids.zoom.listeners.change();check('Zoom2x',ids.canvas.style.width==='1536px');ids.zoom.value='fit';ids.zoom.listeners.change();check('Zoom ajusté',ids.canvas.style.width==='720px');
 check('Tous les chemins demandés existent',errors.length===0);
 fs.writeFileSync(path.join(__dirname,'viewer_checks.json'),JSON.stringify({status:'PASS',type:'DOM simulé et fichiers locaux, pas Chromium',checks_count:checks.length,checks},null,2)+'\n');console.log(checks.length+' tests de galerie PASS (DOM simulé).');
})().catch(e=>{console.error(e);process.exit(1)});
