'use strict';
const $=s=>document.querySelector(s), canvas=$('#map'), ctx=canvas.getContext('2d');
const names={jour:'Jour',nuit:'Nuit',crepuscule:'Crépuscule',aube:'Aube',soir:'Soir',orageux:'Orageux'}, images={};
let scene=DATA.scenes.find(s=>s.id==='littoral')||DATA.scenes[0], M=scene.manifest, A=M.animation, mode='jour';
let width=M.dimensions[0],height=M.dimensions[1],vis=M.calques.map(()=>true);
canvas.width=width;canvas.height=height;
let frame=0,elapsed=0,speed=1,baseOnly=false,ready=false;
let running=!matchMedia('(prefers-reduced-motion: reduce)').matches,last=performance.now();
function fit(){
  if(!ready)return;
  const z=$('#zoom').value;
  const scale=z==='fit'?Math.min(($('#stage').clientWidth-28)/width,(innerWidth<680?390:530)/height,1.65):Number(z);
  canvas.style.width=(width*Math.max(.2,scale))+'px';canvas.style.height=(height*Math.max(.2,scale))+'px';
}
function clock(){
  const seconds=(frame*A.duree_image_ms/1000).toFixed(2).replace('.',',');
  $('#time').textContent=`Image ${frame+1} / ${A.frames} · ${seconds} s`;
  $('#frame').value=String(frame);
}
function draw(){
  if(!ready)return;
  ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,width,height);
  const variant=scene.variants[mode];
  variant.layers.forEach((key,i)=>{
    if(!vis[i]||(baseOnly&&i<M.base_start))return;
    const id=M.calques[i].id,op=variant.files.operations[id];
    if(op&&op.kind==='scroll'){
      const x=-(frame%op.period);ctx.drawImage(images[key],x,0);ctx.drawImage(images[key],x+width,0);
    }else if(op&&op.kind==='waves'){
      const [dx,dy,opacity]=op.phases[frame%op.period];ctx.save();ctx.globalAlpha=opacity/255;
      for(const xx of [-width,0,width])for(const yy of [-height,0,height])ctx.drawImage(images[key],dx+xx,dy+yy);
      ctx.restore();
    }else if(op){
      const animation=variant.motion[id],index=frame%animation.frames.length;
      ctx.drawImage(images[animation.frames[index]],...animation.offset);
    }else ctx.drawImage(images[key],0,0);
  });
  if($('#grid').checked){
    ctx.save();ctx.lineWidth=1;
    for(let x=0;x<width;x+=8){ctx.strokeStyle=x%64?'rgba(249,235,186,.17)':'rgba(249,235,186,.4)';ctx.beginPath();ctx.moveTo(x+.5,0);ctx.lineTo(x+.5,height);ctx.stroke()}
    for(let y=0;y<height;y+=8){ctx.strokeStyle=y%64?'rgba(249,235,186,.17)':'rgba(249,235,186,.4)';ctx.beginPath();ctx.moveTo(0,y+.5);ctx.lineTo(width,y+.5);ctx.stroke()}
    ctx.restore();
  }
  clock();
}
function update(){
  if(!ready)return;
  $('#title').textContent=scene.label+' · '+names[mode];$('#ambiance').value=mode;
  $('#stage').classList.toggle('magenta',baseOnly);$('#composite').classList.toggle('on',!baseOnly);$('#base').classList.toggle('on',baseOnly);
  $('#animation').textContent=running?'❚❚ Pause':'▶ Animer';$('#animation').setAttribute('aria-pressed',String(running));
  const active=M.note?'Calques animés':(scene.id==='sharpedo'?'Nuages et vagues animés':'Nuages en mouvement');
  $('#status').textContent=running?active+(mode==='nuit'?' · étoiles scintillantes':''):'Animation en pause';
  $('#layers').replaceChildren();
  M.calques.forEach((layer,i)=>{
    const empty=scene.variants[mode].empty[i],label=document.createElement('label'),check=document.createElement('input'),text=document.createElement('span');
    label.className='layer'+(empty?' empty':'');check.type='checkbox';check.dataset.layer=i;
    check.disabled=empty;check.checked=!empty&&vis[i]&&!(baseOnly&&i<M.base_start);check.setAttribute('aria-label',layer.nom);
    check.onchange=()=>{vis[i]=check.checked;if(i<M.base_start&&check.checked)baseOnly=false;update()};text.textContent=layer.nom;label.append(check,text);
    if(empty||scene.variants[mode].files.operations[layer.id]){const tag=document.createElement('small');tag.textContent=empty?'vide':'animé';label.append(tag)}
    $('#layers').append(label);
  });
  document.querySelectorAll('.variant').forEach(b=>b.classList.toggle('on',b.dataset.mode===mode));
  document.querySelectorAll('[data-sky]').forEach(b=>{const active=b.dataset.sky===mode;b.classList.toggle('on',active);b.setAttribute('aria-pressed',String(active))});
  document.querySelectorAll('[data-scene]').forEach(b=>{const active=b.dataset.scene===scene.id;b.classList.toggle('on',active);b.setAttribute('aria-pressed',String(active))});
  const f=scene.variants[mode].files;
  $('#png').href=scene.directory+'/'+f.composition;$('#ase').href=scene.directory+'/'+f.aseprite;$('#tiled').href=scene.directory+'/'+f.tiled;
  $('#tileset').hidden=!f.tileset_bordures;if(f.tileset_bordures)$('#tileset').href=scene.directory+'/'+f.tileset_bordures.png;
  fit();draw();
}
function menus(){
  $('#ambiance').replaceChildren();$('#variants').replaceChildren();
  $('#variants').classList.toggle('pair',M.ambiances.length===2);
  M.ambiances.forEach(value=>{
    const option=document.createElement('option');option.value=value;option.textContent=names[value];$('#ambiance').append(option);
    const button=document.createElement('button');button.type='button';button.className='variant';button.dataset.mode=value;
    const im=document.createElement('img');im.src=DATA.assets[scene.variants[value].thumb];im.alt=scene.label+' — '+names[value];
    const text=document.createElement('span');text.textContent=names[value];button.append(im,text);button.onclick=()=>setMode(value);$('#variants').append(button);
  });
  $('#dimensions').textContent=`${width} × ${height} px · grille 8 px`;
  $('#frame').max=String(A.frames-1);$('#end-time').textContent=(A.duree_boucle_ms/1000)+' s';
  $('#layer-title').textContent=M.calques.length+' calques indépendants';
  $('#documentation').href=scene.directory+'/README.md';$('#manifest').href=scene.directory+'/kit.json';
  $('#badge').textContent=M.badge||(scene.id==='sharpedo'?'Prairie · mer en contrebas':'Prairie · escalier sud');
  $('#scene-note').textContent=M.note||(scene.id==='sharpedo'
    ?'Falaise côtière : rives et angles redessinés d’après les bordures de PMD Sky, adaptés au contour du cap. Le chemin reste ouvert à droite, sans bordure artificielle. Le tileset de 20 motifs est fourni ; la mer animée et la prairie intérieure restent inchangées.'
    :'Falaise entière repassée au générateur avec la référence EoS : prairie, chemin, bordures et paroi harmonisés. L’escalier de référence reste inchangé. Aucun arbre, rocher ou mobilier ajouté sur le plateau.');
  $('#animation-note').textContent=M.animation_note||(scene.id==='sharpedo'
    ?'Les vagues avancent en 10 phases sur leur propre overlay : cycle de 2,5 secondes. Les nuages défilent et les étoiles scintillent la nuit. La lune, la prairie et la paroi restent fixes.'
    :'Six familles de nuages : cumulus, bancs étirés, cirrus et fragments. Les étoiles scintillent par groupes la nuit, sur un cycle doux de 6 secondes. La lune et le terrain restent fixes.');
}
function setScene(id){
  const selected=DATA.scenes.find(s=>s.id===id);if(!selected)throw new Error('Scène inconnue');
  scene=selected;M=scene.manifest;A=M.animation;[width,height]=M.dimensions;
  if(!M.ambiances.includes(mode))mode='jour';vis=M.calques.map(()=>true);baseOnly=false;frame=0;elapsed=0;last=performance.now();
  canvas.width=width;canvas.height=height;menus();update();
}
function setFrame(value){
  const n=Number(value);if(!Number.isFinite(n))return;
  running=false;frame=((Math.floor(n)%A.frames)+A.frames)%A.frames;elapsed=frame*A.duree_image_ms;last=performance.now();update();
}
function setMode(value){if(!M.ambiances.includes(value))throw new Error('Ambiance inconnue');mode=value;update()}
function tick(now){
  // Un callback RAF peut porter un timestamp antérieur à une reprise récente.
  const delta=Math.max(0,now-last);last=now;
  if(ready&&running){elapsed=(elapsed+delta*speed)%A.duree_boucle_ms;const next=Math.floor(elapsed/A.duree_image_ms);if(next!==frame){frame=next;draw()}}
  requestAnimationFrame(tick);
}
DATA.scenes.forEach(s=>{const b=document.createElement('button');b.type='button';b.dataset.scene=s.id;b.textContent=s.label;b.onclick=()=>setScene(s.id);$('#scenes').append(b)});
menus();
$('#ambiance').onchange=e=>setMode(e.target.value);
document.querySelectorAll('[data-sky]').forEach(b=>b.onclick=()=>setMode(b.dataset.sky));
$('#animation').onclick=()=>{running=!running;last=performance.now();update()};
$('#speed').onchange=e=>{speed=Number(e.target.value);last=performance.now()};
$('#frame').oninput=e=>setFrame(e.target.value);$('#grid').onchange=draw;$('#zoom').onchange=fit;
$('#base').onclick=()=>{baseOnly=true;update()};$('#composite').onclick=()=>{baseOnly=false;for(let i=0;i<M.base_start;i++)vis[i]=true;update()};
$('#reset').onclick=()=>{vis.fill(true);baseOnly=false;update()};window.addEventListener('resize',fit);document.addEventListener('visibilitychange',()=>{last=performance.now()});
$('#capture').onclick=()=>{const link=document.createElement('a');link.download=`${scene.id}_${mode}_${String(frame).padStart(3,'0')}.png`;link.href=canvas.toDataURL('image/png');link.click()};
window.FALAISE={setFrame,setMode,setScene,pause:()=>{running=false;update()},getState:()=>({scene:scene.id,mode,frame,running,baseOnly,visible:[...vis],speed}),draw};
Promise.all(Object.entries(DATA.assets).map(([key,url])=>new Promise((resolve,reject)=>{
  const im=new Image();im.onload=()=>{images[key]=im;resolve()};im.onerror=()=>reject(new Error('Image '+key));im.src=url;
}))).then(()=>{ready=true;last=performance.now();update();document.body.dataset.ready='true';requestAnimationFrame(tick)})
.catch(error=>{$('#status').textContent='Erreur de chargement : '+error.message;$('#status').classList.add('error')});
