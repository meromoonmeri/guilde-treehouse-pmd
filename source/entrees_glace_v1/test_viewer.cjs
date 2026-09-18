// Logique de galerie, DOM simulé. Pas un vrai navigateur.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'renders/entrees_glace_v1');
const html=fs.readFileSync(path.join(out,'index.html'),'utf8'),data=JSON.parse(html.match(/<script id="data"[^>]*>([\s\S]*?)<\/script>/)[1]);
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];let draws=[],errors=[],raf;const ids={},passed=[];
function element(tag){return {tag,children:[],listeners:{},attrs:{},style:{},value:'',checked:false,clientWidth:700,width:768,height:640,textContent:'',append(...x){this.children.push(...x)},setAttribute(k,v){this.attrs[k]=v},addEventListener(k,v){this.listeners[k]=v}}}
for(const id of ['data','canvas','mode','effect','zoom','viewport','grid','route','seek','clock','status','layers','cards','title','description','ora','scene','webp','raw','play','step'])ids[id]=element('div');
ids.data.textContent=JSON.stringify(data);ids.mode.value='nuit';ids.effect.value='canonical';ids.zoom.value='fit';
ids.canvas.getContext=()=>({globalAlpha:1,clearRect(){draws=[]},drawImage(im,x,y){draws.push({file:im.path,x,y,alpha:this.globalAlpha})},beginPath(){},moveTo(){},lineTo(){},stroke(){}});
class Image{set src(src){this.path=src;queueMicrotask(()=>{if(fs.existsSync(path.join(out,src)))this.onload();else {errors.push(src);this.onerror()}})}}
const context=vm.createContext({document:{hidden:false,getElementById:id=>ids[id],createElement:element,querySelectorAll:()=>ids.cards.children},Image,ResizeObserver:class{observe(){}},matchMedia:()=>({matches:true}),performance:{now:()=>1000},requestAnimationFrame:fn=>{raf=fn},console,Map,Promise});
vm.runInContext(code,context);const flush=()=>new Promise(r=>setImmediate(r));function check(name,test){assert(test,name);passed.push(name)}
(async()=>{
 await flush();check('3 cartes, 9 calques, pause si mouvement réduit',ids.cards.children.length===3&&ids.layers.children.length===9&&ids.play.textContent==='Lecture');
 for(let i=0;i<3;i++){ids.cards.children[i].listeners.click();await flush();check('Sélection'+i,ids.title.textContent===data.zones[i].title&&ids.cards.children[i].attrs['aria-pressed']==='true');for(const mode of ['jour','nuit']){ids.mode.value=mode;ids.mode.listeners.change();await flush();check('Téléchargement'+i+mode,ids.ora.href===data.zones[i].files['ora_'+mode]&&fs.existsSync(path.join(out,ids.ora.href)));}}
 ids.effect.value='cycling';ids.effect.listeners.change();await flush();check('Alternative cycling',draws.some(d=>d.file.includes('palette_cycling')));
 ids.effect.value='none';ids.effect.listeners.change();await flush();check('Sans onde',!draws.some(d=>d.file.includes('palette_cycling')||d.file.includes('onde_canonique')));
 ids.effect.value='canonical';ids.effect.listeners.change();await flush();
 ids.seek.value=359999;ids.seek.listeners.input();await flush();let cloud=draws.filter(d=>d.file.includes('nuages_bande'));check('Wrap fin de boucle : copies jointives',cloud.length===2&&cloud[0].x===-1439&&cloud[1].x===1);
 ids.step.listeners.click();await flush();check('Retour zéro et frame suivante',ids.seek.value===0&&draws.some(d=>d.file.endsWith('onde_canonique_00.png')));
 const terrainrow=ids.layers.children[3];terrainrow.children[0].checked=false;terrainrow.children[0].listeners.change();await flush();check('Masquer sol',!draws.some(d=>d.file.includes('01_sol_avec_chemin')));
 terrainrow.children[0].checked=true;terrainrow.children[2].value=35;terrainrow.children[2].listeners.input();await flush();check('Opacité sol',draws.find(d=>d.file.includes('01_sol_avec_chemin')).alpha===.35);
 ids.zoom.value='2';ids.zoom.listeners.change();check('Zoom2x',ids.canvas.style.width==='1536px');ids.zoom.value='fit';ids.zoom.listeners.change();check('Zoomfit',ids.canvas.style.width==='700px');
 ids.route.checked=true;ids.route.listeners.change();ids.grid.checked=true;ids.grid.listeners.change();await flush();check('Parcours/grille et toutes images locales',errors.length===0);
 const report={status:'PASS',type:'DOM simulé + fichiers locaux, pas Chromium',checks_count:passed.length,checks:passed};fs.writeFileSync(path.join(__dirname,'viewer_checks.json'),JSON.stringify(report,null,2)+'\n');console.log(passed.length+' contrôles galerie PASS (DOM simulé).');
})().catch(e=>{console.error(e);process.exit(1)});
