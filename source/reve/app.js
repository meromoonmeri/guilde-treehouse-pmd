import * as THREE from 'three';

const DATA=DREAM_DATA, $=s=>document.querySelector(s), clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const TAU=Math.PI*2, period=DATA.manifest.atlas.cycle_seconds;
const descriptions={hardy:'Tu avances avec constance, même quand le chemin devient incertain.',brave:'Quand quelqu’un a besoin de toi, tu trouves le courage de faire le premier pas.',hasty:'Ton énergie ouvre des chemins. Prends aussi le temps de regarder autour de toi.',jolly:'Tu apportes de la lumière et de l’élan à ceux qui voyagent à tes côtés.',docile:'Tu sais écouter, aider et construire une confiance qui dure.',relaxed:'Tu gardes ton propre rythme et trouves du calme au milieu du mouvement.',calm:'Ton regard posé aide à distinguer l’essentiel, même dans l’inconnu.',timid:'Ta sensibilité remarque ce que les autres ne voient pas toujours.',lonely:'Tu connais la valeur des moments tranquilles et des liens choisis.',sassy:'Tu gardes un esprit libre et tu oses regarder les choses autrement.',impish:'Ton imagination transforme souvent les détours en aventures.',naive:'Tu accueilles le monde avec curiosité et avec un cœur ouvert.',quirky:'Ton chemin ne ressemble à aucun autre, et c’est aussi sa force.'};
function random(seed){let s=seed>>>0;return()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}
class Quiz{
  constructor(seed){
    this.seed=seed;const rng=random(seed),indices=DATA.questions.questions.map((_,i)=>i);
    for(let i=indices.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[indices[i],indices[j]]=[indices[j],indices[i]]}
    this.items=indices.slice(0,DATA.questions.tirage).sort((a,b)=>a-b).map(i=>DATA.questions.questions[i]);
    this.history=[];this.index=0;this.weights=Object.fromEntries(DATA.natures.map(n=>[n.id,0]));
  }
  get done(){return this.index===this.items.length}
  get question(){return this.items[this.index]||null}
  answer(choice){if(this.done||!Number.isInteger(choice)||!this.question.reponses[choice])return false;for(const [id,w]of Object.entries(this.question.reponses[choice].poids))this.weights[id]+=w;this.history.push(choice);this.index++;return true}
  back(){if(!this.index)return false;this.index--;const c=this.history.pop();for(const[id,w]of Object.entries(this.question.reponses[c].poids))this.weights[id]-=w;return true}
  result(){if(!this.done)return null;let best=DATA.natures[0];for(const n of DATA.natures)if(this.weights[n.id]>this.weights[best.id])best=n;return{id:best.id,fr:best.fr,rgb:[...best.rgb],accent:[...best.accent]}}
}
const query=new URLSearchParams(location.search), requestedSeed=query.get('seed');
const seed=requestedSeed!==null?Number(requestedSeed)>>>0:(globalThis.crypto?.getRandomValues(new Uint32Array(1))[0]??Date.now())>>>0;
let quiz=new Quiz(seed),selection=-1,clock=0,last=performance.now(),manual=false,ready=false,paused=matchMedia('(prefers-reduced-motion: reduce)').matches;
let travelling=false,moveStart=0,moveDuration=0,pose={travel:0,angle:-.52,stage:0},from={...pose},target={...pose};
const host=$('#world'),scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(53,1,.1,180);
let renderer,backgroundScene,backgroundCamera,backgroundMaterial,orb,halo,heroRing,stars,ringMeshes=[],width=1,height=1;
let graphicsError=null;
const moods=[[.37,.85,1],[.91,.49,.81],[.36,.94,.76],[1,.73,.43],[.59,.57,1],[.38,.79,.98],[.92,.55,.57],[.60,.91,.58],[.72,.67,1]];
const pathX=t=>Math.sin(t*.058)*1.2;
const pathY=t=>Math.sin(t*.043)*.35;
const vertex=`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`;
const hueGLSL=`vec3 hueRotate(vec3 c,float a){vec3 k=normalize(vec3(1.0));return max(vec3(0.0),c*cos(a)+cross(k,c)*sin(a)+k*dot(k,c)*(1.0-cos(a)));}`;
function glowTexture(){
  const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d'),g=x.createRadialGradient(64,64,1,64,64,64);
  g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.12,'rgba(215,250,255,.85)');g.addColorStop(.36,'rgba(113,218,255,.25)');g.addColorStop(1,'rgba(70,136,255,0)');x.fillStyle=g;x.fillRect(0,0,128,128);
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
}
async function makeWorld(){
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;renderer.autoClear=false;
  renderer.domElement.setAttribute('aria-label','Sphère lumineuse voyageant dans un rêve circulaire en trois dimensions');host.append(renderer.domElement);
  const loader=new THREE.TextureLoader();const[nebula,atlas]=await Promise.all([loader.loadAsync(DATA.assets.nebuleuse),loader.loadAsync(DATA.assets.anneaux)]);
  for(const t of[nebula,atlas]){t.colorSpace=THREE.SRGBColorSpace;t.minFilter=THREE.LinearFilter;t.magFilter=THREE.LinearFilter;t.generateMipmaps=false}
  backgroundScene=new THREE.Scene();backgroundCamera=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
  backgroundMaterial=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms:{map:{value:nebula},uTime:{value:0},uAspect:{value:1},uLook:{value:new THREE.Vector2()},uStage:{value:0},uTint:{value:new THREE.Color(...moods[0])}},
    vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.0,1.0);}',
    fragmentShader:`uniform sampler2D map;uniform float uTime,uAspect,uStage;uniform vec2 uLook;uniform vec3 uTint;varying vec2 vUv;${hueGLSL}
    void main(){vec2 fit=vec2(min(uAspect/1.7777778,1.0),min(1.7777778/uAspect,1.0));vec2 uv=(vUv-.5)*fit*.84+.5;
      vec2 drift=vec2(sin(uTime*.027),cos(uTime*.021))*.013;
      vec3 a=texture2D(map,clamp(uv+uLook*.005+drift,vec2(.01),vec2(.99))).rgb;
      vec3 b=texture2D(map,clamp((uv-.5)*1.08+.5-uLook*.010-drift*.5,vec2(.01),vec2(.99))).rgb;
      vec3 c=texture2D(map,clamp((uv-.5)*.90+.5+uLook*.020+drift*1.3,vec2(.01),vec2(.99))).rgb;
      vec3 color=hueRotate(a*.58+b*.27+c*.15,uStage*.25+sin(uTime*.08)*.12);
      color*=vec3(.86)+uTint*.38; color=max(color,vec3(.017,.024,.05)+uTint*.012);
      gl_FragColor=vec4(color,1.0);
      #include <colorspace_fragment>
    }`});
  backgroundScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),backgroundMaterial));
  const plane=new THREE.PlaneGeometry(15,15);
  for(let i=0;i<9;i++){
    const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,depthTest:true,side:THREE.DoubleSide,blending:THREE.AdditiveBlending,toneMapped:false,
      uniforms:{map:{value:atlas},uFrame:{value:0},uGain:{value:.4},uTint:{value:new THREE.Color(1,1,1)}},vertexShader:vertex,
      fragmentShader:`uniform sampler2D map;uniform float uFrame,uGain;uniform vec3 uTint;varying vec2 vUv;
      vec4 sampleFrame(float n){n=mod(n,36.0);vec2 cell=vec2(mod(n,6.0),5.0-floor(n/6.0));vec2 uv=(cell*260.0+vec2(2.5)+vUv*255.0)/1560.0;return texture2D(map,uv);}
      void main(){float n=floor(uFrame);vec4 a=sampleFrame(n),b=sampleFrame(n+1.0);vec4 c=mix(a,b,fract(uFrame));gl_FragColor=vec4(c.rgb*uTint,c.a*uGain);
        #include <colorspace_fragment>
      }`});
    const mesh=new THREE.Mesh(plane,material);scene.add(mesh);ringMeshes.push(mesh);
  }
  heroRing=new THREE.Mesh(new THREE.PlaneGeometry(6.5,6.5),ringMeshes[0].material.clone());
  heroRing.material.uniforms.uGain.value=.23;scene.add(heroRing);
  orb=new THREE.Group();
  const sphere=new THREE.Mesh(new THREE.SphereGeometry(.51,48,32),new THREE.MeshPhysicalMaterial({color:0xe4faff,roughness:.20,metalness:.04,clearcoat:.8,clearcoatRoughness:.15,iridescence:.65,iridescenceIOR:1.25,emissive:0x73bed5,emissiveIntensity:.52}));
  orb.add(sphere);halo=new THREE.Sprite(new THREE.SpriteMaterial({map:glowTexture(),color:0xa4e8ff,transparent:true,opacity:.58,blending:THREE.AdditiveBlending,depthWrite:false}));halo.scale.set(2.8,2.8,1);orb.add(halo);scene.add(orb);
  scene.add(new THREE.HemisphereLight(0xbbeeff,0x523b77,2.5));const sun=new THREE.DirectionalLight(0xfff1d5,3.2);sun.position.set(-4,6,8);scene.add(sun);
  const fill=new THREE.DirectionalLight(0xa189ff,1.6);fill.position.set(6,-2,-4);scene.add(fill);
  const rng=random(331);const points=new Float32Array(320*3),colors=new Float32Array(320*3);
  for(let i=0;i<320;i++){const ang=rng()*TAU,rad=1.6+rng()*8;points[i*3]=Math.cos(ang)*rad;points[i*3+1]=Math.sin(ang)*rad;points[i*3+2]=-rng()*100;colors.set([.7+rng()*.3,.8+rng()*.2,1],i*3)}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(points,3));geo.setAttribute('color',new THREE.BufferAttribute(colors,3));
  stars=new THREE.Points(geo,new THREE.PointsMaterial({map:glowTexture(),size:.10,vertexColors:true,transparent:true,opacity:.8,blending:THREE.AdditiveBlending,depthWrite:false,sizeAttenuation:true}));scene.add(stars);
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();paused=true;$('#notice').textContent='Le rendu 3D a été interrompu. Recharge la page pour le reprendre.'});
  resize();new ResizeObserver(resize).observe(host);
}
function resize(){width=Math.max(1,host.clientWidth);height=Math.max(1,host.clientHeight);if(!renderer)return;renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();if(backgroundMaterial)backgroundMaterial.uniforms.uAspect.value=width/height}
function updatePose(){
  const u=moveDuration?clamp((clock-moveStart)/moveDuration,0,1):1, e=u*u*(3-2*u);
  for(const key of['travel','angle','stage'])pose[key]=from[key]+(target[key]-from[key])*e;
  const was=travelling;travelling=u<1;if(was&&!travelling)syncControls();
}
function render(){
  if(!ready||!renderer)return;updatePose();
  const travel=pose.travel, idle=paused?0:Math.sin(clock*.8)*.055;
  orb.position.set(pathX(travel),pathY(travel)+idle,-travel);
  orb.children[0].rotation.y=clock*.12;orb.children[0].rotation.z=Math.sin(clock*.25)*.05;
  const angle=pose.angle+(paused?0:Math.sin(clock*.17)*.035);
  camera.position.set(orb.position.x+Math.sin(angle)*8.8,orb.position.y+.75+Math.sin(angle*2)*.22,orb.position.z+Math.cos(angle)*8.8);
  camera.lookAt(orb.position.x,orb.position.y-.75,orb.position.z-1.5);
  const stage=clamp(pose.stage,0,moods.length-1),lo=Math.floor(stage),hi=Math.min(moods.length-1,lo+1),mix=stage-lo;
  const result=quiz.result(),tint=new THREE.Color(...moods[lo]).lerp(new THREE.Color(...moods[hi]),mix);
  if(result&&stage>=quiz.items.length-.1)tint.setRGB(...result.rgb);
  backgroundMaterial.uniforms.uTime.value=clock;backgroundMaterial.uniforms.uStage.value=stage;backgroundMaterial.uniforms.uLook.value.set(camera.position.x,camera.position.y);backgroundMaterial.uniforms.uTint.value.copy(tint);
  const first=Math.floor(travel/10)-1;
  ringMeshes.forEach((ring,i)=>{
    const absolute=first+i,z=-absolute*10,depth=camera.position.z-z;
    ring.position.set(pathX(absolute*10),pathY(absolute*10),z);
    ring.rotation.set(Math.sin(absolute*.31)*.035,Math.sin(absolute*.27)*.04,absolute*.16+clock*.018);
    const near=clamp((depth-1.5)/4,0,1),far=clamp((100-depth)/20,0,1);
    ring.visible=depth>1&&depth<105;
    ring.material.uniforms.uFrame.value=((clock/period+absolute*.137)%1+1)%1*36;
    ring.material.uniforms.uGain.value=near*far*.13/(1+Math.max(0,depth-10)*.012);
    ring.material.uniforms.uTint.value.setRGB(.91+tint.r*.13,.91+tint.g*.13,.91+tint.b*.13);
  });
  heroRing.position.copy(orb.position);heroRing.position.z-=1;
  heroRing.quaternion.copy(camera.quaternion);
  heroRing.material.uniforms.uFrame.value=(clock/period%1)*36;
  heroRing.material.uniforms.uGain.value=.23;
  heroRing.material.uniforms.uTint.value.setRGB(.96+tint.r*.08,.96+tint.g*.08,.96+tint.b*.08);
  stars.position.z=-Math.floor(travel/100)*100;stars.rotation.z=clock*.007;
  halo.material.opacity=.55+(paused?0:.06*Math.sin(clock*1.3));
  renderer.clear();renderer.render(backgroundScene,backgroundCamera);renderer.clearDepth();renderer.render(scene,camera);
}
function syncControls(){
  $('#previous').disabled=travelling||quiz.index===0;$('#validate').disabled=travelling||selection<0||quiz.done;
  document.querySelectorAll('.answer').forEach((b,i)=>{b.disabled=travelling;b.classList.toggle('selected',i===selection);b.setAttribute('aria-pressed',String(i===selection))});
  $('#travel-state').textContent=travelling?'Le voyage continue…':'Prends ton temps.';
  $('#motion').textContent=paused?'Animer':'Pause';$('#motion').setAttribute('aria-pressed',String(paused));
}
function drawQuestion(){
  $('#chapter').textContent=quiz.done?'LE RÊVE TE RECONNAÎT':`QUESTION ${quiz.index+1} / ${quiz.items.length}`;
  $('#dialogue').hidden=quiz.done;$('#result').hidden=!quiz.done;
  if(quiz.done){const r=quiz.result();$('#result-title').textContent=r.fr;$('#result-description').textContent=descriptions[r.id];}
  else{$('#question').textContent=quiz.question.texte;$('#choices').replaceChildren();quiz.question.reponses.forEach((answer,i)=>{const b=document.createElement('button');b.type='button';b.className='answer';b.dataset.answer=i;const mark=document.createElement('span');mark.className='diamond';mark.textContent='◆';mark.setAttribute('aria-hidden','true');const text=document.createElement('span');text.textContent=answer.label;b.append(mark,text);b.onclick=()=>select(i);$('#choices').append(b)});}
  syncControls();
}
function travelToStage(){
  updatePose();from={...pose};target={travel:quiz.index*14,angle:quiz.index%2?.52:-.52,stage:quiz.index};moveStart=clock;
  moveDuration=paused?0:1.7;travelling=moveDuration>0;selection=-1;drawQuestion();render();
  window.dispatchEvent(new CustomEvent('dream-question-changed',{detail:{question:quiz.index,total:quiz.items.length}}));
  if(quiz.done)window.dispatchEvent(new CustomEvent('personality-result',{detail:quiz.result()}));
}
function select(i){if(travelling||quiz.done||!quiz.question.reponses[i])return false;selection=i;syncControls();return true}
function validate(){if(travelling||!quiz.answer(selection))return false;travelToStage();return true}
function back(){if(travelling||!quiz.back())return false;travelToStage();return true}
function reset(newSeed=seed){quiz=new Quiz(Number(newSeed)>>>0);selection=-1;pose={travel:0,angle:-.52,stage:0};from={...pose};target={...pose};moveDuration=0;travelling=false;drawQuestion();render();return true}
function setPaused(value){paused=!!value;last=performance.now();if(paused&&travelling){pose={...target};from={...target};moveDuration=0;travelling=false}syncControls();render()}
$('#validate').onclick=validate;$('#previous').onclick=back;$('#restart').onclick=()=>reset((Date.now()^seed)>>>0);$('#motion').onclick=()=>setPaused(!paused);
$('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('#dream').requestFullscreen();$('#notice').textContent=''}catch{$('#notice').textContent='Le plein écran est bloqué dans ce cadre. Ouvre le fichier dans un onglet du navigateur.'}};
document.addEventListener('keydown',e=>{if(!ready||quiz.done||travelling||e.altKey||e.ctrlKey||e.metaKey)return;if(['ArrowDown','ArrowRight','ArrowUp','ArrowLeft'].includes(e.key)){e.preventDefault();const delta=['ArrowDown','ArrowRight'].includes(e.key)?1:-1;select((selection+delta+quiz.question.reponses.length)%quiz.question.reponses.length)}else if(e.key==='Enter'&&e.target.tagName!=='BUTTON'){e.preventDefault();validate()}});
document.addEventListener('visibilitychange',()=>{last=performance.now()});
window.REVE={select,validate,back,reset,setPaused,getState:()=>({question:quiz.index,total:quiz.items.length,questionId:quiz.question?.id||null,selection,finished:quiz.done,result:quiz.result(),travelling,paused,render3d:!!renderer,clock,viewport:[width,height],logicalReference:[320,240],camera:camera.position.toArray(),sphere:orb?.position.toArray()||null,travel:pose.travel,azimuth:pose.angle,atlasFrame:(clock/period*36)%36}),
  capture:{begin:(s=42)=>{manual=true;clock=0;paused=false;document.documentElement.classList.add('capture');reset(s)},time:t=>{if(!manual)throw new Error('Mode capture non actif');clock=Math.max(0,Number(t)||0);render()},end:()=>{manual=false;last=performance.now();document.documentElement.classList.remove('capture')}}};
function tick(now){const delta=clamp((now-last)/1000,0,.1);last=now;if(ready&&!manual){if(!paused)clock+=delta;render()}requestAnimationFrame(tick)}
drawQuestion();
makeWorld().then(()=>{ready=true;$('#loading').hidden=true;document.body.dataset.ready='true';render();requestAnimationFrame(tick)})
.catch(error=>{graphicsError=String(error);$('#loading').textContent='Le rendu 3D n’est pas disponible dans ce navigateur.';$('#notice').textContent='Active WebGL ou utilise un navigateur récent.';document.body.dataset.graphicsError=graphicsError;console.error(error)});
