const {chromium}=require('playwright');const path=require('path');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+path.resolve(process.argv[2])+'#/');await p.waitForFunction(()=>window.__KS_OK);
console.log(await p.evaluate(()=>{const A=STD.filter(s=>/^ASTM/.test(s.id));return A.length+'\n'+A.map(s=>[s.id,s.din,s.fa,s.cat,s.sub||'',JSON.stringify(s.grades).slice(0,220),(s.sizes||[]).length,[...REG.values()].filter(r=>r.sid===s.id).length].join(' | ')).join('\n')+'\nKEYS '+JSON.stringify(Object.keys(A[0]))}));
console.log(await p.evaluate(()=>JSON.stringify(CATS.filter(c=>/^a-/.test(c.id)))));
await b.close()})();
