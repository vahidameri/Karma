// End-to-end: the built app page + dist/Code.gs on the mocked Apps Script runtime (tools/mock.js).
// node e2e_gas.js   (after python3 build.py)
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');const {runtime}=require('./mock');
const D=path.resolve(__dirname,'../dist');const G=runtime(D+'/Code.gs');
const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)process.exitCode=1};
const w=ms=>new Promise(r=>setTimeout(r,ms));const root=k=>JSON.parse(G.readRoot_(k).d);
G.setup();G.__upload(D+'/karma-assets.zip');let m='';for(let i=0;i<5;i++){m=G.installAssets();if(/کامل شد/.test(m))break}
ok(/کامل شد/.test(m),'install complete: '+m);
const html=G.doGet().getContent();ok(html.includes('window.__KS={assets:')&&!html.includes('گروه صنعتی کارما')&&!html.includes('در حال اتصال'),'loading page: logo only, no text');
ok(G.SS_().getSheetByName('کالاها').getLastRow()===23199,'product tab imported (23,198 codes)');
fs.writeFileSync(D+'/t.html',html);
const idToPath={};Object.values(G.__files).forEach(f=>{if(f.blob&&f.blob.path)idToPath[f.id]=f.blob.path});
(async()=>{const b=await chromium.launch();
const page=async name=>{const ctx=await b.newContext({viewport:{width:1366,height:900}});await ctx.route('https://lh3.googleusercontent.com/**',r=>{const id=r.request().url().split('/d/')[1];idToPath[id]?r.fulfill({path:idToPath[id]}):r.abort()});
  const p=await ctx.newPage();p.errs=[];p.on('pageerror',e=>p.errs.push(name+': '+e.message));p.on('dialog',d=>d.accept());
  await p.exposeFunction('__gas',async(fn,args)=>{await w(20);try{return JSON.stringify(G[fn](...JSON.parse(args)))}catch(e){console.log('SERVER ERROR',fn,e.stack);throw e}});
  await p.addInitScript(()=>{const mk=(s,f)=>new Proxy({},{get(_,n){if(n==='withSuccessHandler')return h=>mk(h,f);if(n==='withFailureHandler')return h=>mk(s,h);return(...a)=>{window.__gas(n,JSON.stringify(a)).then(r=>s&&s(JSON.parse(r)),e=>f&&f(e))}}});window.google={script:{run:mk(null,null)}}});
  await p.goto('file://'+D+'/t.html#/');await p.waitForFunction(()=>window.__KS_OK,{timeout:90000});await w(300);return p};
const login=async(p,id,pw)=>{await p.evaluate(()=>auth('login'));await p.fill('#aform [name=mobile]',id);await p.fill('#aform [name=pw]',pw);await p.click('#ago');await w(900)};
const settle=async p=>{await w(1200);await p.evaluate(()=>KS.sync());await w(500)};
// visitor
const v=await page('visitor');ok(await v.evaluate(()=>!ME&&S.requests.length===0&&S.work.tasks.length===0),'visitor: no staff data, no tasks');
ok(!G.apiBoot('').roots.work,'server sends no tasks to visitors');
// admin
const a=await page('admin');await login(a,'admin','68lmPyeqe6uY');
ok(await a.evaluate(()=>ME&&isAdmin()&&KS.can('work')&&S.work.tasks.length>=4),'admin: tasks loaded from the server');
await a.goto('file://'+D+'/t.html#/admin/work');await w(500);await a.selectOption('#wqas',{label:'کارشناس تأمین ۱'});await a.fill('#wqadd','آزمون تسک سرور');await a.press('#wqadd','Enter');await settle(a);
const wr=root('work');const tk=wr.tasks.find(t=>t.title==='آزمون تسک سرور');ok(tk&&tk.as.join()==='5','task saved on the server ('+(tk&&tk.id)+')');
ok(G.SS_().getSheetByName('میزکار').getLastRow()===wr.tasks.length+1,'«میزکار» tab mirrored');
// quote numbers: a deleted draft uses no number
const q0=root('sales').qseq;
await a.evaluate(()=>newQuote());await w(400);await settle(a);ok(root('sales').qseq===q0&&Object.keys(root('sales').quotes).some(k=>/^DRF-/.test(k)),'draft quote saved without taking a number');
await a.click('#qdel');await w(300);await settle(a);ok(root('sales').qseq===q0&&!Object.keys(root('sales').quotes).some(k=>/^DRF-/.test(k)),'draft deleted on the server, numbering untouched');
// supply user: sees and completes the task
const s=await page('warehouse');await login(s,'warehouse','AAiWBv1Hhfdn');
ok(await s.evaluate(()=>KS.can('work')&&!KS.can('acc')),'supply user may write tasks, not accounting');
await s.goto('file://'+D+'/t.html#/admin/work');await w(500);await s.click(`[data-done="${tk.id}"]`);await w(300);await s.fill('#wask','انجام شد — آزمون');await s.click('#wok');await settle(s);
const t2=root('work').tasks.find(t=>t.id===tk.id);ok(t2.status==='done'&&t2.cm.some(c=>c.kind==='done'),'completion by the assignee saved on the server');
await a.evaluate(()=>KS.sync());await w(200);await a.evaluate(()=>new Promise(r=>setTimeout(r,100)));
// contact details: edited by the admin, saved in the resume part, seen by visitors
await a.goto('file://'+D+'/t.html#/admin/resume');await w(600);await a.fill('#cted .ct-row[data-ct="0"] [data-cf2=v]','نشانی آزمون سرور');await settle(a);
ok(root('cv').contact&&root('cv').contact[0].v==='نشانی آزمون سرور','contact details saved on the server');
ok(JSON.parse(G.apiBoot('').roots.cv.d).contact[0].v==='نشانی آزمون سرور','visitors receive the new address');
// member: no tasks
const r=G.apiRegister({name:'عضو آزمون',mobile:'09121110000',pw:'123456'});ok(r.token&&!G.apiBoot(r.token).roots.work&&!G.apiBoot(r.token).w.includes('work'),'members get no workspace');
// upgrade from 1.4: stored roles without the new permissions still work on the server
const iam=root('iam');iam.roles.forEach(x=>{if(x.perms)x.perms=x.perms.filter(p=>!/^work\.|archive$/.test(p))});G.writeRoot_('iam',JSON.stringify(iam),{name:'1.4'});G._IAM=null;
const stok=await s.evaluate(()=>localStorage.getItem('karma.tok'));ok(G.apiBoot(stok).w.includes('work'),'roles saved by 1.4 receive the workspace permissions on the server');
const sales=G.apiLogin('sales','X3ybyXIAIrw1');ok(sales.token&&G.permsOf_(G.sessionUser_(sales.token)).p['sales.quote.archive'],'… and the archive permission');
for(const p of [v,a,s])p.errs.length&&console.log('PAGE ERRORS',p.errs.slice(0,5));ok(![v,a,s].some(p=>p.errs.length),'no JS errors in the pages');
fs.unlinkSync(D+'/t.html');await b.close()})();
