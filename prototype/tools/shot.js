// screenshots of the app (offline mode) at several widths: node shot.js <app.html> <outdir> [hash...]
const {chromium}=require('playwright');const path=require('path');
(async()=>{const [app,out,...hs]=process.argv.slice(2);const b=await chromium.launch();
const W=[[1920,1000,'xl'],[1366,768,'lap'],[1024,768,'tab'],[390,844,'ph']];
for(const [w,h,n] of W){const p=await b.newPage({viewport:{width:w,height:h}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
 for(const hs1 of (hs.length?hs:['#/'])){await p.goto('file://'+path.resolve(app)+hs1);await p.waitForFunction(()=>window.__KS_OK,{timeout:30000}).catch(()=>{});await p.waitForTimeout(900);
  await p.screenshot({path:`${out}/${n}_${hs1.replace(/[#\/?=&]/g,'_')}.png`});}
 if(errs.length)console.log(n,errs.slice(0,3));await p.close()}
await b.close()})();
