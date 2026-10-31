// smart-search test set (GOLDEN in the app): node gold.js <app.html>
const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();const p=await b.newPage();const e=[];p.on('pageerror',x=>e.push(x.message));
await p.goto('file://'+path.resolve(process.argv[2])+'#/');await p.waitForFunction(()=>window.__KS_OK);
const r=await p.evaluate(()=>{const R=goldenRun();return R});const bad=r.filter(x=>!x.ok);console.log("golden",r.length-bad.length+"/"+r.length);bad.forEach(x=>console.log("FAIL",x.q,JSON.stringify(x.e),JSON.stringify(x.got)));if(bad.length)process.exitCode=1;if(e.length)console.log(e);await b.close()})();
