const fs=require('fs');const src=fs.readFileSync('/home/claude/landing/project/Main.dc.html','utf8');
const js=src.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/)[1];
global.DCLogic=class{constructor(p){this.props=p||{}}setState(){}};
const C=eval('('+js.trim().replace(/^class Component/,'class Component')+')');
const c=new C({});const v=c.renderVals();
for(const k of Object.keys(v)) if(typeof v[k]==='function') delete v[k];
fs.writeFileSync('/tmp/vals.json',JSON.stringify(v,null,1));console.log(Object.keys(v));
