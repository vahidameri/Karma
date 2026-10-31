// install seed and product tables taken from the app in offline mode: node dump.js <app.html> <outdir>
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{const [app,out]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+path.resolve(app)+'#/');await p.waitForFunction(()=>window.__KS_OK,{timeout:60000});if(errs.length){console.log(errs);process.exit(1)}
const r=await p.evaluate(()=>{const enc=KS.enc;
  const seed={sales:{requests:S.requests,quotes:S.quotes,orders:S.orders,rseq:S.rseq,qseq:S.qseq,oseq:S.oseq,fseq:S.fseq,pack:S.pack,invoices:S.invoices,customers:S.customers,iseq:S.iseq,cseq:S.cseq,doc:S.doc},acc:{A,PY},dabir:S.dabir,cv:S.cv,prod:{std:[],sku:[]},
    iam:{roles:roleDefaults(),modules:S.modules},dict:{syn:S.syn,alias:S.alias,wt:S.wt},audit:[],slog:{},work:S.work};
  const q=v=>{v=v==null?'':String(v);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v};
  const csv=rows=>rows.map(r=>r.map(q).join(',')).join('\n');
  const skus=[['کد محصول','کد فنی','استاندارد','نام کالا','سایز','طول','گرید','پوشش','منشأ']].concat([...REG.values()].map(r=>{const s=byId(r.sid)||{};return [r.pcode,r.tech,(s.din||r.sid),s.fa||'',r.size,r.len||'',r.grade,r.fin,r.origin]}));
  const std=[['شناسه','استاندارد','نام فارسی','دسته','زیردسته','تعداد سایز','طول‌دار','گریدها','معادل‌ها']].concat(STD.map(s=>[s.id,s.din,s.fa,(CATS.find(c=>c.id===s.cat)||{}).fa||s.cat,s.sub||'',(s.sizes||[]).length,s.hasLength?'بله':'خیر',Object.keys(s.grades||{}).join(' / '),(s.equiv||[]).map(e=>Array.isArray(e)?e.join(' '):typeof e==='object'?Object.values(e).join(' '):e).join('، ')]));
  return {seed:enc(seed),skus:csv(skus),std:csv(std),n:REG.size}});
fs.writeFileSync(out+'/seed.json',r.seed);fs.writeFileSync(out+'/skus.csv',r.skus);fs.writeFileSync(out+'/standards.csv',r.std);
console.log('seed',r.seed.length,'skus',r.n,'errors',errs);await b.close()})();
