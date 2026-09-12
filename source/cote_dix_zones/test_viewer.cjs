// DOM-mocked interaction smoke test, NOT a real browser/rendering test.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2]||'apercu_dix_zones_metano.html','utf8');
const ids=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]));
const all=[],nodes={},downloads=[];
class Element {
 constructor(id=''){this.id=id;this.children=[];this.style={};this.value='0';this.checked=false;this.width=1312;this.height=1024;this.clientWidth=1100;this.classList={toggle(){}};all.push(this)}
 append(...items){this.children.push(...items)}
 replaceChildren(){this.children=[]}
 getContext(){return {clearRect(){},drawImage(im){assert(im,'undefined image referenced')},beginPath(){},moveTo(){},lineTo(){},stroke(){},fillRect(){},fillText(){}}}
 toBlob(callback){downloads.push([this.width,this.height]);callback({})}
 click(){}
}
const document={getElementById(id){assert(ids.has(id),'Unknown HTML element '+id);return nodes[id]??=new Element(id)},querySelectorAll(){return all},createElement(){return new Element()},createTextNode(s){return s}};
class MockImage {set src(value){assert(value&&value.startsWith('data:image/webp;base64,'));this.width=1312;this.height=1024;queueMicrotask(()=>this.onload())}}
const sandbox={document,Image:MockImage,window:{innerHeight:1000,addEventListener(){}},requestAnimationFrame(){},console,URL:{createObjectURL(){return 'blob:test'},revokeObjectURL(){}},setTimeout(fn){fn()}};
vm.createContext(sandbox);
vm.runInContext("document.getElementById('zoom').value='fit'",sandbox);
vm.runInContext(html.split('<script>')[1].split('</script>')[0],sandbox);
const settle=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await settle();
 assert(vm.runInContext('ready',sandbox));
 const count=vm.runInContext('zones.length',sandbox);
 for(let i=0;i<count;i++){
  nodes.zone.value=String(i);nodes.zone.onchange();await settle();
  for(const mode of ['day','night']){
   nodes[mode].onclick();await settle();
   assert(vm.runInContext('ready',sandbox));
   assert(vm.runInContext('Object.keys(images).length<=17',sandbox),'Decoded images are not evicted');
   nodes.grid.checked=true;nodes.grid.onchange();nodes.grid.checked=false;
   nodes.reset.onclick();nodes.export.onclick();nodes.dry.onclick();
   nodes.which.value='0';nodes.exportLayer.onclick();
   nodes.zoom.value='1';nodes.zoom.onchange();
  }
 }
 await nodes.board.onclick();
 assert(vm.runInContext('Object.keys(images).length<=17',sandbox));
 assert.equal(downloads.length,count*6+1);
 assert.deepEqual(downloads.at(-1),[1312,2720]);
 console.log(`PASS: ${count*2} selections, layer/scene/dry exports, board, lazy image eviction (DOM mocks only).`);
})().catch(error=>{console.error(error);process.exitCode=1});
