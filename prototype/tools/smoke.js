// quick check: open pages as admin in offline mode, report JS errors. node smoke.js <app.html> [hash...]
const {chromium}=require('playwright');const path=require('path');
(async()=>{const [app,...hs]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:1366,height:900}});const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('dialog',d=>d.accept());
await p.goto('file://'+path.resolve(app)+'#/');await p.waitForFunction(()=>window.__KS_OK,{timeout:30000});
await p.evaluate(()=>{ME=S.users.find(u=>u.user==='admin');rerender()});
for(const h of hs){errs.length=0;await p.goto('file://'+path.resolve(app)+h);await p.waitForTimeout(500);const t=await p.evaluate(()=>document.querySelector('#app').innerText.slice(0,80).replace(/\s+/g,' '));console.log(errs.length?'ERR':'ok ',h,errs.slice(0,2).join(' | '),'|',t)}
await b.close()})();
