// Runs the app's JavaScript against a minimal fake DOM. Usage: node tests/dom_test.js [path/to/index.html]
const fs=require('fs');
const path=require('path');
const html=fs.readFileSync(process.argv[2]||path.join(__dirname,'..','index.html'),'utf8');
const reg={};
class El{constructor(tag){this.tag=tag;this.children=[];this.attrs={};this._id='';this.value='';this.checked=false;this.hidden=false;this.type='';this.style={};this.listeners={};this.className='';this._text='';this.step='';this.onclick=null;this.parent=null;}
 set id(v){this._id=v;reg[v]=this}get id(){return this._id}
 appendChild(c){c.parent=this;this.children.push(c);if(this.tag=='select'&&this.children.length==1)this.value=c._text;return c}
 get firstChild(){return this.children[0]}
 addEventListener(t,f){(this.listeners[t]=this.listeners[t]||[]).push(f)}
 setAttribute(k,v){this.attrs[k]=v}getAttribute(k){return this.attrs[k]}
 set textContent(v){this._text=v;if(this.tag!='script')this.children=[]}get textContent(){return this._text}
 set innerHTML(h){this.children=[];if(h.includes('<span>'))this.appendChild(new El('span'));const re=/<input([^>]*)>/g;let m;while((m=re.exec(h))){const e=new El('input');const a=m[1];e.type=(/type="(\w+)"/.exec(a)||[])[1]||'';const id=/ id="(\w+)"/.exec(a);if(id)e.id=id[1];const df=/data-f="(\w+)"/.exec(a);if(df)e.attrs['data-f']=df[1];e.checked=/ checked/.test(a);this.appendChild(e)}}
 get innerHTML(){return ''}
 select(){}remove(){}
 walk(f){f(this);this.children.forEach(c=>c.walk(f))}}
const allids=[...html.matchAll(/ id="(\w+)"/g)].map(m=>m[1]);
allids.forEach(i=>{const e=new El(i=='hlp'||i=='run'||i=='tt'?'script':'div');e.id=i});
for(const b of ['hlp','run','tt']){reg[b]._text=new RegExp('<script type="text/plain" id="'+b+'">\\n?([\\s\\S]*?)</script>').exec(html)[1]}
global.document={getElementById:i=>reg[i],createElement:t=>new El(t),createTextNode:s=>{const e=new El('#text');e._text=s;return e},querySelectorAll:sel=>{const out=[];reg['fcat'].walk(e=>{if(e.tag=='input'&&e.checked)out.push(e)});return out},body:new El('body'),execCommand(){}};
const store={};global.localStorage={getItem:k=>store[k]||null,setItem:(k,v)=>{store[k]=v}};
global.navigator={clipboard:{writeText:()=>Promise.resolve()}};
const js=/<script>\n([\s\S]*?)<\/script>/.exec(html.slice(html.lastIndexOf('<script>\n')))[1];
(0,eval)(js+`
global.T={buildFcat,ticked,prompt,v,fvis,P:()=>P,ITEMS,PRE,FSTYLES};`);
const T=global.T;
let fails=0;const ck=(l,c)=>{if(!c){fails++;console.log('FAIL',l)}};
function setPreset(p){$('preset').value=p;$('preset').listeners.input.forEach(f=>f())}
// 1 every preset: every listed id exists in ITEMS, and ticked() matches defaults
for(const p of Object.keys(T.PRE)){setPreset(p);const want=T.PRE[p].filter(x=>x[1]).map(x=>x[0]).sort().join();ck('defaults '+p,T.ticked().sort().join()==want);T.PRE[p].forEach(x=>ck('ITEMS has '+x[0],T.ITEMS[x[0]]))}
// 2 preset list in the dropdown includes the new rooms
const opts=[];$('preset').children.forEach(o=>opts.push(o.textContent));
['Bedroom','Cafe','Retail shop'].forEach(r=>ck('option '+r,opts.includes(r)));ck('all presets have a list',opts.every(o=>T.PRE[o]));
// 3 Bedroom prompt
setPreset('Bedroom');let pr=T.prompt();
ck('bedroom space',pr.includes('- Space: Bedroom'));ck('lists bed',/Furniture pieces to build[^\n]*Bed, Nightstand\(s\), Dresser/.test(pr));ck('no desk in bedroom',!/Furniture pieces to build[^\n]*Desk/.test(pr));ck('rule 29',pr.includes('29. FURNITURE LIST'));
ck('header has bed()',pr.includes('def bed(')&&pr.includes('def display_unit('));
// 4 style dropdown
$('fst').value='Mid-century';ck('style midcentury',T.prompt().includes("'midcentury' for every furniture call"));
$('fst').value='Match the photo';ck('style auto',T.prompt().includes('choose the style that suits'));
// 5 show all keeps ticks, adds the rest
const before=T.ticked().sort().join();$('fall').checked=true;$('fall').listeners.input.forEach(f=>f());
let n=0;$('fcat').walk(e=>{if(e.tag=='input')n++});ck('show all lists every item',n==Object.keys(T.ITEMS).length);ck('show all keeps ticks',T.ticked().sort().join()==before);
$('fall').checked=false;$('fall').listeners.input.forEach(f=>f());
// 6 clear floor hides the picker and the prompt lines
$('furn').value='None, clear floor';$('furn').listeners.input.forEach(f=>f());ck('fbox hidden',$('fbox').hidden===true);pr=T.prompt();ck('no pieces line',!pr.includes('Furniture pieces to build'));ck('no rule 29',!pr.includes('29. FURNITURE LIST'));
$('furn').value='Match to the photo';$('furn').listeners.input.forEach(f=>f());ck('fbox shown',$('fbox').hidden===false);
// 7 save / load round trip with a non-default tick
setPreset('Cafe');const box=[];$('fcat').walk(e=>{if(e.tag=='input')box.push(e)});box.find(e=>e.attrs['data-f']=='display_unit').checked=true;const want=T.ticked().sort().join();
$('name').value='T1';$('save').onclick();ck('saved fcat',store.backdrop_projects.includes('display_unit'));
setPreset('Living room');ck('switched',T.ticked().includes('sofa'));
// click Load (first saved row)
const sl=$('sl');let load;sl.children.forEach(r=>r.children.forEach(b=>{if(b.textContent=='Load')load=b}));load.onclick();
ck('restored preset',T.v('preset')=='Cafe');ck('restored ticks',T.ticked().sort().join()==want);
console.log(fails?('DOM FAILS: '+fails):'DOM TESTS PASSED');process.exit(fails?1:0);
