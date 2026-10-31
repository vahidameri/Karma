// every staff user opens every page their menu offers (offline mode); reports JS errors and «no access» pages
const {chromium}=require('playwright');const path=require('path');
(async()=>{const app=path.resolve(process.argv[2]);const b=await chromium.launch();const p=await b.newPage({viewport:{width:1366,height:900}});const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('dialog',d=>d.dismiss());
await p.goto('file://'+app+'#/');await p.waitForFunction(()=>window.__KS_OK);let bad=0,n=0;
for(const u of await p.evaluate(()=>S.users.filter(u=>u.kind==='staff').map(u=>u.user))){
  await p.evaluate(u=>{ME=S.users.find(x=>x.user===u);permBump();go('#/admin/home')},u);await p.waitForTimeout(300);
  const links=await p.evaluate(()=>{const L=[...document.querySelectorAll('.side a[href^="#/admin"]')].map(a=>a.getAttribute('href'));if(canPage('work'))L.push('#/admin/work?v=board','#/admin/work?f=all');if(canPage('acc'))L.push('#/admin/acc/reports?r=tb','#/admin/acc/new/pi');return [...new Set(L)]});
  for(const h of links){errs.length=0;await p.evaluate(h=>{location.hash=h},h);await p.waitForTimeout(350);n++;
    const g=await p.evaluate(()=>(document.querySelector('.gate h1')||{}).innerText||'');if(errs.length||g.includes('دسترسی ندارید')){bad++;console.log('FAIL',u,h,errs.slice(0,2).join(' | '),g)}}
  console.log('ok',u,links.length,'pages')}
console.log(bad?'SMOKE FAIL '+bad:'SMOKE PASS '+n+' pages');process.exitCode=bad?1:0;await b.close()})();
