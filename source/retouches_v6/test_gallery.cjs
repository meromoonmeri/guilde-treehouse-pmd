// Script behavior test with a minimal DOM, not a browser/GPU certification.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{
 constructor(){this.children=[];this.style={};this.value='0';this.checked=false;this.hidden=false;this.classList={toggle(){}};this.width=768;this.height=512}
 set innerHTML(v){this.children=[]}get innerHTML(){return ''}
 append(...v){this.children.push(...v)}add(v){this.children.push(v)}
 set src(v){this._src=v;if(this.onload)this.onload()}get src(){return this._src}
}
const els={};const document={getElementById:id=>els[id]??=new Element(),createElement:()=>new Element(),createTextNode:s=>s};
const html=fs.readFileSync('apercu_retouches_et_calques_v6.html','utf8'),script=html.match(/<script>([\s\S]*)<\/script>/)[1];
const context={document,Image:Element,Option:class{constructor(t,v){this.text=t;this.value=v}}};vm.createContext(context);vm.runInContext(script,context);
assert.equal(els.zone.children.length,10);assert.equal(els.kit.children.length,2);assert.equal(els.stack.children.length,4);
for(let z=0;z<10;z++)for(const night of [false,true]){els.zone.value=String(z);els['zone-night'].checked=night;els.zone.onchange();assert(els.before.src.startsWith('data:image/webp'));assert(els.after.src.startsWith('data:image/webp'));assert(els['zone-download'].href.endsWith('.png'))}
for(let k=0;k<2;k++)for(const night of [false,true]){els.kit.value=String(k);els['kit-night'].checked=night;els.kit.onchange();assert.equal(els.stack.children.length,4);els['no-path'].onclick();assert.equal(els.stack.children[1].style.display,'none');els.all.onclick();assert(els.stack.children.every(x=>x.style.display==='block'))}
els['tab-zones'].onclick();assert(els.layers.hidden&&!els.zones.hidden);els['tab-layers'].onclick();assert(els.zones.hidden&&!els.layers.hidden);
console.log('PASS: 20 zone/ambience selections, 4 kit/ambience selections, layer visibility, no-path, reset and tabs; simulated DOM only.');
