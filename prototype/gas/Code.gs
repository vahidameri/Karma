/**
 * کارما — Google Sheets backend (Apps Script web app)
 *
 * The site (app.html) and its images live in a Drive folder; installAssets() unpacks
 * karma-assets.zip into it. All data lives in this spreadsheet:
 *   _store      one row per part of the app (sales, accounting, …) as JSON, with a version
 *   کاربران     users; passwords are stored only as salted hashes
 *   readable tabs (درخواست‌ها، پیش‌فاکتورها، سفارش‌ها، اسناد حسابداری، کالاها، …) are refreshed on
 *   every save, for viewing and reports; edits are made in the app.
 *
 * Security: every call carries a session token; the server works out the user's permissions from
 * their roles (defined in the app, Users › Roles, stored in the "iam" part) plus per-user allow /
 * deny, and decides which parts they may read and write (ROOTS). Members only ever receive their
 * own requests and quotes. The audit trail and the search log are append-only.
 */
var KARMA_VERSION = '1.5.1';

var T = {
  STORE: '_store', SESS: '_sessions', ASSETS: '_assets', USERS: 'کاربران', CFG: 'تنظیمات', LOG: 'گزارش فعالیت',
  REQ: 'درخواست‌ها', QUO: 'پیش‌فاکتورها', ORD: 'سفارش‌ها', INV: 'فاکتورها', CUST: 'مشتریان', VCH: 'اسناد حسابداری', AUD: 'گزارش ممیزی', WORK: 'میزکار', SKU: 'کالاها', STD: 'استانداردها', NEWSKU: 'کالاهای ساخته‌شده'
};
var USER_COLS = ['id', 'kind', 'name', 'user', 'mobile', 'email', 'role', 'active', 'last', 'joined', 'company', 'ptype', 'natid', 'eco', 'addr', 'data', 'hash', 'salt', 'roles', 'acl'];
/* roles shipped with the app; the live list is the "iam" part, edited in the app (Users › Roles) */
var DEFAULT_IAM = {"roles": [{"id": "admin", "name": "مدیر سیستم", "d": "دسترسی کامل؛ این نقش محدود یا حذف نمی‌شود.", "all": true, "sys": true, "bu": [], "own": false}, {"id": "sales", "name": "مدیر / کارشناس فروش", "d": "درخواست، پیش‌فاکتور، فاکتور، برگهٔ تأمین، مشتریان و کالاها", "sys": true, "bu": [], "own": false, "perms": ["sales.request.view", "sales.request.edit", "sales.quote.view", "sales.quote.create", "sales.quote.edit", "sales.quote.send", "sales.quote.approve", "sales.quote.revise", "sales.quote.print", "sales.supply.view", "sales.supply.edit", "sales.supply.assign", "sales.supply.print", "sales.invoice.view", "sales.invoice.create", "sales.invoice.issue", "sales.invoice.void", "sales.invoice.return", "sales.invoice.print", "sales.invoice.backdate", "sales.customer.view", "sales.customer.edit", "sales.customer.delete", "sales.customer.view_balance", "catalog.product.view", "catalog.product.create", "catalog.product.edit", "catalog.price.view", "catalog.price.edit", "catalog.search.view", "admin.settings.view", "admin.settings.edit"]}, {"id": "product", "name": "کارشناس محصول", "d": "استانداردها، کالاها، کاتالوگ، جستجو، دبیرخانه و رزومه", "sys": true, "bu": [], "own": false, "perms": ["catalog.product.view", "catalog.product.create", "catalog.product.edit", "catalog.price.view", "catalog.price.edit", "catalog.price.view_cost", "catalog.export.view", "catalog.search.view", "catalog.search.edit", "sales.request.view", "sales.quote.view", "sales.quote.print", "dabir.letter.view", "dabir.letter.create", "company.resume.view", "company.resume.edit"]}, {"id": "accounting", "name": "حسابدار", "d": "حسابداری کامل، حقوق، مالیات و دیدن فاکتورها و مشتریان", "sys": true, "bu": [], "own": false, "perms": ["acc.dash.view", "acc.voucher.view", "acc.voucher.create", "acc.voucher.post", "acc.voucher.reverse", "acc.sales.view", "acc.purchase.view", "acc.purchase.create", "acc.treasury.view", "acc.treasury.create", "acc.cheque.view", "acc.cheque.ops", "acc.party.view", "acc.party.edit", "acc.report.view", "acc.report.export", "acc.setup.view", "acc.setup.edit", "acc.close.run", "payroll.run.view", "payroll.run.run", "tax.tax.view", "tax.tax.run", "sales.invoice.view", "sales.invoice.print", "sales.customer.view", "sales.customer.view_balance", "catalog.price.view", "catalog.price.edit", "catalog.price.view_cost"]}, {"id": "viewer", "name": "فقط مشاهده", "d": "دیدن فروش، محصولات و دبیرخانه بدون امکان تغییر", "sys": true, "bu": [], "own": false, "perms": ["sales.request.view", "sales.quote.view", "sales.supply.view", "sales.invoice.view", "sales.customer.view", "catalog.product.view", "catalog.price.view", "catalog.export.view", "dabir.letter.view", "company.resume.view"]}, {"id": "warehouse", "name": "کارشناس تأمین", "d": "فقط برگه‌های تأمین سفارش", "sys": true, "bu": [], "own": false, "perms": ["sales.supply.view", "sales.supply.edit", "sales.supply.print"]}, {"id": "r_karma", "name": "کارشناس فروش کارما (نمونه)", "d": "نمونهٔ نقش سفارشی: فقط اسناد واحد کارما و فقط اسنادی که خودش ساخته؛ بدون ابطال و تاریخ گذشته", "sys": false, "bu": ["unofficial"], "own": true, "perms": ["sales.request.view", "sales.request.edit", "sales.quote.view", "sales.quote.create", "sales.quote.edit", "sales.quote.send", "sales.quote.approve", "sales.quote.revise", "sales.quote.print", "sales.supply.view", "sales.supply.print", "sales.invoice.view", "sales.invoice.create", "sales.invoice.issue", "sales.invoice.print", "sales.customer.view", "sales.customer.edit", "catalog.product.view", "catalog.price.view"]}], "modules": {"sales": true, "catalog": true, "acc": true, "payroll": true, "tax": true, "dabir": true, "company": true}};
/* who may read (r) and write (w) each part: a test on the user's permissions P (see permsOf_).
   add: append-only parts; the screen sends only its new entries and the server adds them. */
var EVERYONE = function () { return true; };
var ROOTS = {
  sales: { r: function (P) { return any_(P, /^sales\./); }, w: function (P) { return any_(P, /^sales\./, true) || has_(P, 'acc.voucher.create'); } },
  acc: { r: function (P) { return any_(P, /^(acc|payroll|tax)\./); }, w: function (P) { return any_(P, /^(acc|payroll|tax)\./, true); } },
  dabir: { r: function (P) { return any_(P, /^dabir\./); }, w: function (P) { return any_(P, /^dabir\./, true); } },
  cv: { r: EVERYONE, w: function (P) { return has_(P, 'company.resume.edit'); } },
  cat: { r: function (P) { return any_(P, /^catalog\.export\./); }, w: function (P) { return any_(P, /^catalog\.export\./); } },
  prod: { r: EVERYONE, w: function (P) { return has_(P, 'catalog.product.create') || has_(P, 'catalog.product.edit'); } },
  dict: { r: EVERYONE, w: function (P) { return has_(P, 'catalog.product.create') || has_(P, 'catalog.product.edit') || has_(P, 'catalog.search.edit'); } },
  iam: { r: function (P) { return P.kind === 'staff'; }, w: function (P) { return has_(P, 'admin.role.edit') || has_(P, 'admin.module.edit'); } },
  audit: { r: function (P) { return has_(P, 'admin.audit.view'); }, w: function (P) { return P.kind === 'staff'; }, add: 'list' },
  slog: { r: function (P) { return has_(P, 'catalog.search.view'); }, w: EVERYONE, add: 'count' },
  work: { r: function (P) { return any_(P, /^work\./); }, w: function (P) { return any_(P, /^work\./); } }
};
var NEWPERMS = ['sales.quote.archive', 'sales.invoice.archive', 'work.task.view', 'work.task.create', 'work.task.assign', 'work.task.view_all'];
var NOWRITE = /\.(view|print|view_balance|view_cost|export)$/;
/* first staff accounts (same as the prototype); setup() stores them hashed. Change them after the first sign-in. */
var SEED_USERS = [
  { id: 1, kind: 'staff', name: 'مدیر سیستم', user: 'admin', pw: '68lmPyeqe6uY', mobile: '09120000001', email: '', role: 'admin' },
  { id: 2, kind: 'staff', name: 'مدیر فروش', user: 'sales', pw: 'X3ybyXIAIrw1', mobile: '09120000002', email: '', role: 'sales' },
  { id: 3, kind: 'staff', name: 'کارشناس محصول', user: 'product', pw: 'LTOW9dUj2yrj', mobile: '09120000003', email: '', role: 'product' },
  { id: 4, kind: 'staff', name: 'حسابدار', user: 'accountant', pw: 'zdm143A3miGO', mobile: '09120000004', email: '', role: 'accounting' },
  { id: 5, kind: 'staff', name: 'کارشناس تأمین ۱', user: 'warehouse', pw: 'AAiWBv1Hhfdn', mobile: '09120000005', email: '', role: 'warehouse' },
  { id: 11, kind: 'member', name: 'نمونه عضو ۱', mobile: '09350000000', company: 'شرکت نمونه', ptype: 'legal', data: '{"favs":{"$set":["std:DIN912"]},"lists":[]}' },
  { id: 12, kind: 'member', name: 'نمونه عضو ۲', mobile: '09190000000', ptype: 'real' }
];
var CHUNK = 45000;          // characters per cell (Sheets allows 50,000)
var SESSION_DAYS = 30;

/* ================= web app ================= */
/* doGet sends a small loader page; the app (≈2.4 MB) is then fetched with apiApp() in pieces and
   started in place. This keeps HtmlService away from the big file (size limits, "Malformed HTML"). */
function doGet() {
  if (!cfg_('app_file')) return HtmlService.createHtmlOutput('<div dir="rtl" style="font:16px Tahoma;padding:40px;line-height:2">فایل‌های اپ هنوز نصب نشده‌اند.<br>در شیت، از منوی «کارما» گزینهٔ «۲. نصب / به‌روزرسانی فایل‌های اپ» را اجرا کنید تا پیغام «نصب کامل شد» بیاید.</div>');
  var boot = 'window.__KS={assets:' + JSON.stringify(assetMap_()) + ',ver:"' + KARMA_VERSION + '"};';
  var loader = LOADER_HTML;
  if (cfg_('loader_file')) try { loader = fileHtml_('loader_file'); } catch (e) {}
  return HtmlService.createHtmlOutput(loader.split('/*BOOT*/').join(boot)).setTitle(cfg_('title') || 'کارما | پیچ و مهره و اتصالات صنعتی')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
var APP_PART = 400000;
function apiApp(i) {
  var html = appHtml_(), n = Math.ceil(html.length / APP_PART);
  return { n: n, s: html.substr(i * APP_PART, APP_PART) };
}
var LOADER_HTML = '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style id="ldcss">' +
  'body{margin:0;font:15px/1.9 Tahoma,sans-serif;background:#f6f7fb;color:#333}#ld{min-height:100vh;display:grid;place-items:center;text-align:center;padding:24px}' +
  '#ld b{display:block;font-size:22px;color:#1f3a68;margin-bottom:6px}#ldbar{width:220px;height:6px;border-radius:9px;background:#dde3ef;margin:14px auto 0;overflow:hidden}' +
  '#ldbar i{display:block;height:100%;width:3%;background:#1f3a68;transition:width .3s}#lderr{color:#a11;font-size:13px;max-width:560px;direction:ltr;text-align:left;white-space:pre-wrap;margin-top:12px}</style></head>' +
  '<body><div id="ld"><div><b>کارما</b><span id="ldm"></span><div id="ldbar"><i id="ldb"></i></div><div id="lderr"></div></div></div><script>/*BOOT*/' +
  '(function(){var parts=[],n=0,got=0;' +
  'function fail(m){var e=document.getElementById("lderr");if(!e){e=document.createElement("div");e.id="lderr";e.style.cssText="position:fixed;bottom:0;left:0;right:0;background:#fde7e7;color:#a11;padding:10px;font:12px monospace;z-index:999;direction:ltr";document.body.appendChild(e)}' +
  'var t=document.getElementById("ldm");if(t)t.textContent="سایت بارگذاری نشد. یک بار صفحه را دوباره باز کنید؛ اگر باز هم نشد، از همین پیغام عکس بگیرید.";e.textContent+=String(m)+"\\n"}' +
  'window.__KSFAIL=fail;window.addEventListener("error",function(ev){if(!window.__KS_OK)fail((ev.message||"error")+" @"+(ev.lineno||""))});' +
  'function get(i,tries){google.script.run.withSuccessHandler(function(r){n=r.n;parts[i]=r.s;got++;document.getElementById("ldb").style.width=Math.round(got/n*100)+"%";' +
  'if(i===0)for(var k=1;k<n;k++)get(k,0);if(got===n)start(parts.join(""))}).withFailureHandler(function(e){if(tries<5)setTimeout(function(){get(i,tries+1)},1500*Math.pow(2,tries));else fail("apiApp: "+(e&&e.message||e))}).apiApp(i)}' +
  'function start(html){try{var lc=document.getElementById("ldcss");if(lc)lc.parentNode.removeChild(lc);var d=new DOMParser().parseFromString(html,"text/html"),sc=[].slice.call(d.querySelectorAll("script"));' +
  'sc.forEach(function(s){s.parentNode.removeChild(s)});' +
  '[].slice.call(d.head.children).forEach(function(el){if(el.tagName!=="TITLE"&&!(el.tagName==="META"&&el.name==="viewport"))document.head.appendChild(document.importNode(el,true))});' +
  'document.body.innerHTML=d.body.innerHTML;' +
  'sc.forEach(function(s){var e=document.createElement("script");e.text=s.textContent;document.body.appendChild(e)})}catch(e){fail("start: "+e.message)}}' +
  'get(0,0)})();<\/script></body></html>';

/* the page itself is cached in pieces (CacheService keeps up to 100 KB per entry) */
function appHtml_() { return fileHtml_('app_file'); }
function fileHtml_(cfgKey) {
  var id = cfg_(cfgKey); if (!id) throw new Error(cfgKey + ' not installed');
  var c = CacheService.getScriptCache(), key = 'app:' + id + ':' + cfg_('app_stamp');
  var n = +(c.get(key + ':n') || 0);
  if (n) {
    var keys = []; for (var i = 0; i < n; i++) keys.push(key + ':' + i);
    var got = c.getAll(keys), parts = [];
    for (var j = 0; j < n; j++) { if (got[keys[j]] == null) { parts = null; break; } parts.push(got[keys[j]]); }
    if (parts) return parts.join('');
  }
  var html = DriveApp.getFileById(id).getBlob().getDataAsString('UTF-8');
  try {
    var put = {}, k = 0; for (var p = 0; p < html.length; p += 30000) put[key + ':' + (k++)] = html.substr(p, 30000);
    put[key + ':n'] = String(k); c.putAll(put, 21600);
  } catch (e) {}
  return html;
}

function assetMap_() {
  var c = CacheService.getScriptCache(), hit = c.get('assets:' + cfg_('app_stamp'));
  if (hit) return JSON.parse(hit);
  var m = {}, sh = SS_().getSheetByName(T.ASSETS);
  if (sh && sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 2).getValues().forEach(function (r) { if (r[0]) m[r[0]] = r[1]; });
  try { c.put('assets:' + cfg_('app_stamp'), JSON.stringify(m), 21600); } catch (e) {}
  return m;
}

/* ================= API (google.script.run) ================= */
function apiBoot(token) {
  var me = sessionUser_(token);
  return boot_(me);
}

function apiLogin(id, pw) {
  id = String(id || '').trim().toLowerCase(); pw = String(pw || '');
  var c = CacheService.getScriptCache(), fk = 'fail:' + id, fails = +(c.get(fk) || 0);
  if (fails >= 8) return { err: 'تعداد تلاش‌های ناموفق زیاد بود. ۱۵ دقیقهٔ دیگر دوباره امتحان کنید.' };
  var users = readUsers_(), mob = id.replace(/\D/g, '').replace(/^98/, '0');
  var u = users.filter(function (x) { return (x.user && String(x.user).toLowerCase() === id) || (/^09\d{9}$/.test(mob) && x.mobile === mob); })[0];
  if (!u) { c.put(fk, String(fails + 1), 900); return { err: 'حسابی با این مشخصات پیدا نشد.' }; }
  if (!u.active) return { err: 'این حساب غیرفعال شده است' };
  if (!u.hash) return { err: 'برای این حساب هنوز رمز تعیین نشده است؛ با مدیر سایت تماس بگیرید.', field: 'pw' };
  if (hash_(pw, u.salt) !== u.hash) { c.put(fk, String(fails + 1), 900); return { err: 'رمز عبور درست نیست.', field: 'pw' }; }
  c.remove(fk);
  setUserCell_(u.id, 'last', nowFa_());
  log_(u, 'ورود', '', '');
  return { token: newSession_(u.id), boot: boot_(sessionUserById_(u.id)) };
}

function apiRegister(o) {
  o = o || {};
  var name = String(o.name || '').trim(), mobile = String(o.mobile || '').replace(/\D/g, '').replace(/^98/, '0'), pw = String(o.pw || '');
  if (!name) return { err: 'نام را وارد کنید', field: 'name' };
  if (!/^09\d{9}$/.test(mobile)) return { err: 'شمارهٔ موبایل معتبر نیست. مثال: 09121234567' };
  if (pw.length < 6) return { err: 'رمز عبور باید دست‌کم ۶ کاراکتر باشد.', field: 'pw' };
  if (cfg_('registration') === 'off') return { err: 'عضویت در سایت فعلاً بسته است.' };
  var lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    var users = readUsers_();
    if (users.some(function (x) { return x.mobile === mobile; })) return { err: 'این شماره قبلاً ثبت شده است. گزینهٔ «ورود» را بزنید.' };
    var id = Date.now(), salt = Utilities.getUuid();
    var u = { id: id, kind: 'member', name: name, user: '', mobile: mobile, email: '', role: '', active: true, last: nowFa_(), joined: todayFa_(),
      company: String(o.company || '').trim(), ptype: String(o.company || '').trim() ? 'legal' : 'real', natid: '', eco: '', addr: '',
      data: '{"favs":{"$set":[]},"lists":[]}', hash: hash_(pw, salt), salt: salt };
    writeUsers_(users.concat([u]));
    bump_('users');
    log_(u, 'عضویت', T.USERS, id);
    return { token: newSession_(id), boot: boot_(sessionUserById_(id)) };
  } finally { lock.releaseLock(); }
}

function apiLogout(token) {
  if (!token) return true;
  CacheService.getScriptCache().remove('sess:' + token);
  var sh = SS_().getSheetByName(T.SESS), v = sh.getDataRange().getValues();
  for (var i = v.length - 1; i >= 1; i--) if (v[i][0] === tokenKey_(token)) sh.deleteRow(i + 1);
  return true;
}

/* ch = {root: {v: base version, d: json}, users: {v, d}, me: {d}} */
function apiSave(token, ch) {
  var me = token ? sessionUser_(token) : null;
  if (token && !me) return { auth: true };
  var P = permsOf_(me), res = { ok: {}, conflict: {} };
  var lock = LockService.getScriptLock(); lock.waitLock(30000);
  try {
    var idx = storeIndex_();
    Object.keys(ch || {}).forEach(function (k) {
      var x = ch[k];
      if (k === 'me') { if (me) { saveMe_(me, x.d); res.me = true; } return; }
      if (k === 'users') {
        if (!has_(P, 'admin.user.edit')) return;
        var cur = (idx.users || {}).v || 0;
        if (+x.v !== cur) { res.conflict.users = usersPayload_(me); return; }
        var e = saveUsers_(JSON.parse(x.d), me, P);
        if (e) { res.err = e; res.users = usersPayload_(me); return; }
        res.users = usersPayload_(me);
        return;
      }
      var def = ROOTS[k];
      if (!def || !def.w(P)) return;
      var d = JSON.parse(x.d); // must be valid JSON
      if (def.add) { var nd = appendRoot_(k, def.add, d, me); res.ok[k] = writeRoot_(k, JSON.stringify(nd), me || { name: 'سایت' }); try { mirror_(k, nd); } catch (err) {} return; }
      var v0 = (idx[k] || {}).v || 0;
      if (+x.v !== v0) { res.conflict[k] = readRoot_(k); return; }
      if (k === 'iam') { d = iamGuard_(d, P); x.d = JSON.stringify(d); }
      res.ok[k] = writeRoot_(k, x.d, me);
      if (k === 'iam') _IAM = null;
      try { mirror_(k, d); } catch (err) { console.error('mirror ' + k + ': ' + err); }
    });
  } finally { lock.releaseLock(); }
  return res;
}
/* audit: newest first, the server stamps who did it; search log: counts per query */
function appendRoot_(k, kind, inc, me) {
  var cur = readRoot_(k), base = cur.d ? JSON.parse(cur.d) : null;
  if (kind === 'list') {
    base = Array.isArray(base) ? base : [];
    var add = (Array.isArray(inc) ? inc : []).slice(-500).filter(function (e) { return e && typeof e === 'object'; }).map(function (e) {
      return { t: clip_(e.t, 40), ts: +e.ts || Date.now(), who: me ? me.name : '', uid: me ? me.id : 0, act: clip_(e.act, 120), obj: clip_(e.obj, 200), det: clip_(e.det, 600) };
    });
    return add.reverse().concat(base).slice(0, 3000);
  }
  base = base && typeof base === 'object' && !Array.isArray(base) ? base : {};
  (Array.isArray(inc) ? inc : []).slice(-(me ? 300 : 60)).forEach(function (e) {
    var q = clip_(e && e.q, 80); if (q.length < 2) return;
    var o = base[q] || (base[q] = { n: 0, z: 0, last: '' }); o.n++; if (e.z) o.z++; o.last = nowFa_();
  });
  var ks = Object.keys(base);
  if (ks.length > 5000) { ks.sort(function (a, b) { return base[b].n - base[a].n; }); var o2 = {}; ks.slice(0, 5000).forEach(function (q) { o2[q] = base[q]; }); base = o2; }
  return base;
}
/* only a full administrator can hand out full access; role editors and module editors change only their own part */
function iamGuard_(d, P) {
  var old = iam_(), oldById = {}; (old.roles || []).forEach(function (r) { oldById[r.id] = r; });
  var out = { roles: old.roles, modules: old.modules || {} };
  if (has_(P, 'admin.role.edit') && d && Array.isArray(d.roles)) {
    var seen = {};
    out.roles = d.roles.filter(function (r) { return r && r.id && !seen[r.id] && (seen[r.id] = 1); }).map(function (r) {
      var o = oldById[r.id];
      if (o && o.all) return o;                         // full-access roles stay as they are
      return { id: clip_(r.id, 40), name: clip_(r.name, 80), d: clip_(r.d, 300), sys: !!(o && o.sys), own: !!r.own,
        bu: (r.bu || []).filter(function (b) { return b === 'unofficial' || b === 'official'; }),
        perms: (r.perms || []).filter(function (x) { return /^[a-z_]+\.[a-z_]+\.[a-z_]+$/.test(x); }).slice(0, 400) };
    });
    (old.roles || []).forEach(function (r) { if (r.all && !seen[r.id]) out.roles.unshift(r); }); // never deleted
  }
  if (has_(P, 'admin.module.edit') && d && d.modules && typeof d.modules === 'object') {
    out.modules = {}; Object.keys(d.modules).forEach(function (m) { if (/^[a-z]+$/.test(m)) out.modules[m] = d.modules[m] !== false; });
  }
  return out;
}

/* vers = {root: version the screen has}; returns only the parts that changed */
function apiPull(token, vers) {
  var me = token ? sessionUser_(token) : null;
  if (token && !me) return { auth: true };
  var P = permsOf_(me), idx = storeIndex_(), out = {};
  vers = vers || {};
  Object.keys(ROOTS).forEach(function (k) {
    var v = (idx[k] || {}).v || 0;
    if (!v || v === +vers[k]) return;
    if (ROOTS[k].r(P)) out[k] = readRoot_(k);
    else if (k === 'sales' && P.kind === 'member') out[k] = memberSales_(me);
  });
  var uv = (idx.users || {}).v || 0;
  if (uv && uv !== +vers.users && me) out.users = usersPayload_(me);
  return { roots: out };
}

/* a visitor or member sends the cart as a request; the number is issued here */
function apiSubmitRequest(token, o) {
  var me = token ? sessionUser_(token) : null;
  o = o || {};
  var mobile = String(o.mobile || '').replace(/\D/g, '').replace(/^98/, '0');
  if (!/^09\d{9}$/.test(mobile)) return { err: 'شمارهٔ موبایل معتبر نیست.' };
  var items = (o.items || []).slice(0, 300).map(function (i) { return { p: String(i.p || ''), q: Math.max(1, +i.q || 1), u: String(i.u || 'عدد'), gr: i.gr == null ? undefined : String(i.gr) }; }).filter(function (i) { return i.p; });
  if (!items.length) return { err: 'سبد خالی است.' };
  var cache = CacheService.getScriptCache(), rk = 'rq:' + mobile, n = +(cache.get(rk) || 0);
  if (n >= 10) return { err: 'تعداد درخواست‌های این شماره امروز زیاد بوده است؛ لطفاً تماس بگیرید.' };
  var lock = LockService.getScriptLock(); lock.waitLock(30000);
  try {
    var S = salesRoot_();
    S.rseq = (+S.rseq || 0) + 1;
    var no = 'RQ-' + jalali_(new Date())[0] + '-0' + S.rseq;
    S.requests = S.requests || [];
    S.requests.unshift({ no: no, date: nowFa_(), name: clip_(o.name, 80) || '—', mobile: mobile, items: items, status: 'new', owner: '—', note: clip_(o.note, 1000), company: clip_(o.company, 120) });
    var v = writeRoot_('sales', JSON.stringify(S), me || { name: 'سایت' });
    mirror_('sales', S);
    cache.put(rk, String(n + 1), 86400);
    var P = permsOf_(me), res = { no: no };
    if (ROOTS.sales.r(P)) res.sales = { v: v, d: JSON.stringify(S) };
    else if (P.kind === 'member') res.sales = memberSales_(me);
    return res;
  } finally { lock.releaseLock(); }
}

/* a member approves their own quote (same steps as approveQuote() in the app) */
function apiApproveQuote(token, qid) {
  var me = sessionUser_(token);
  if (!me) return { auth: true };
  var lock = LockService.getScriptLock(); lock.waitLock(30000);
  try {
    var S = salesRoot_(), Q = (S.quotes || {})[qid];
    if (!Q || Q.customer.mobile !== me.mobile) return { err: 'این پیش‌فاکتور پیدا نشد.' };
    var po = null, q0 = Q;
    while (q0 && q0.prev) { q0 = S.quotes[q0.prev]; if (q0 && q0.order && S.orders[q0.order]) { po = S.orders[q0.order]; break; } }
    if (Q.status === 'sent' && po && po.status !== 'invoiced' && !po.inv) {
      // an amended quote: the existing checklist keeps what was already supplied
      var now0 = nowFa_();
      po.lines = Q.lines.map(function (l) {
        var ol = po.lines.filter(function (x) { return x.p === l.p && (l.p || x.desc === l.desc); })[0];
        if (ol) { var c = JSON.parse(JSON.stringify(ol)); c.q = l.q; c.u = l.u; c.desc = l.desc; c.done = ol.done && ol.got >= l.q; return c; }
        return { p: l.p, desc: l.desc, q: l.q, u: l.u, gr: l.gr, got: 0, done: false, src: '', note: '', pk: {} };
      });
      po.quote = Q.id; po.status = 'open'; po.log = (po.log || []).concat([[now0, 'با اصلاحیهٔ ' + Q.id + ' به‌روز شد']]);
      Q.status = 'approved'; Q.order = po.id; Q.log = (Q.log || []).concat([[now0, 'مشتری اصلاحیه را تأیید کرد'], [now0, 'چک‌لیست تأمین ' + po.id + ' به‌روز شد']]);
      (S.requests || []).forEach(function (r) { if (r.no === Q.req) r.status = 'approved'; });
      writeRoot_('sales', JSON.stringify(S), me); mirror_('sales', S); log_(me, 'تأیید اصلاحیهٔ پیش‌فاکتور', T.QUO, Q.id);
    } else if (Q.status === 'sent') {
      S.oseq = (+S.oseq || 0) + 1;
      var id = 'SO-' + jalali_(new Date())[0] + '-00' + S.oseq, now = nowFa_();
      S.orders = S.orders || {};
      var dn = Q.dn || String(Q.base || Q.id).replace(/^[A-Za-z]+-/, ''), sp = ((S.doc || {}).pref || {}).so;
      S.orders[id] = { id: id, dn: dn, no: (sp === '' ? '' : (sp || 'SUP') + '-') + dn, quote: Q.id, req: Q.req, customer: { name: Q.customer.name, mobile: Q.customer.mobile }, created: now, assignee: null, status: 'open',
        pf: (S.pack || []).filter(function (f) { return f.on && f.def; }).map(function (f) { return f.k; }),
        lines: Q.lines.map(function (l) { return { p: l.p, desc: l.desc, q: l.q, u: l.u, gr: l.gr, got: 0, done: false, src: '', note: '', pk: {} }; }), log: [[now, 'از پیش‌فاکتور ' + Q.id + ' ساخته شد']] };
      Q.status = 'approved'; Q.order = id;
      Q.log = (Q.log || []).concat([[now, 'مشتری پیش‌فاکتور را تأیید کرد'], [now, 'چک‌لیست تأمین ' + id + ' ساخته شد']]);
      (S.requests || []).forEach(function (r) { if (r.no === Q.req) r.status = 'approved'; });
      writeRoot_('sales', JSON.stringify(S), me);
      mirror_('sales', S);
      log_(me, 'تأیید پیش‌فاکتور', T.QUO, Q.id);
    }
    return { sales: memberSales_(me) };
  } finally { lock.releaseLock(); }
}

/* ================= boot payload & access ================= */
function boot_(me) {
  var P = permsOf_(me), idx = storeIndex_(), roots = {}, w = [];
  Object.keys(ROOTS).forEach(function (k) {
    if (ROOTS[k].r(P)) roots[k] = idx[k] ? readRoot_(k) : { v: 0 };
    else if (k === 'sales' && P.kind === 'member') roots[k] = memberSales_(me);
    if (ROOTS[k].w(P)) w.push(k);
  });
  if (has_(P, 'admin.user.edit')) w.push('users');
  return { me: me ? publicUser_(me) : null, roots: roots, w: w, users: usersPayload_(me), cfg: { requireLogin: cfg_('require_login') === 'yes' }, ver: KARMA_VERSION };
}

/* ================= permissions ================= */
/* P = {kind: anon | member | staff, all: full access, p: {permission: 1}} — the same rules as permSet() in the app */
var _IAM = null;
function iam_() {
  if (_IAM) return _IAM;
  var x = readRoot_('iam'), d = null; try { d = x.d ? JSON.parse(x.d) : null; } catch (e) {}
  if (!d || !Array.isArray(d.roles) || !d.roles.length) d = DEFAULT_IAM || { roles: [{ id: 'admin', name: 'مدیر سیستم', all: true, sys: true }], modules: {} };
  // permissions added in later versions reach the built-in roles saved before them (same as permUpgrade() in the app)
  if (DEFAULT_IAM) d.roles.forEach(function (r) {
    var def = DEFAULT_IAM.roles.filter(function (x) { return x.id === r.id; })[0];
    if (!def || r.all || !r.sys || !def.perms) return; r.perms = r.perms || [];
    NEWPERMS.forEach(function (p) { if (def.perms.indexOf(p) >= 0 && r.perms.indexOf(p) < 0) r.perms.push(p); });
  });
  return (_IAM = d);
}
function rolesOf_(u) { return u.roles && u.roles.length ? u.roles : u.role ? [u.role] : []; }
function modOn_(M, m) { return m === 'admin' || (M[m] !== false && (['payroll', 'tax'].indexOf(m) < 0 || M.acc !== false)); }
function permsOf_(u) {
  if (!u) return { kind: 'anon', all: false, p: {} };
  if (u.kind !== 'staff') return { kind: 'member', all: false, p: {} };
  var I = iam_(), byId = {}; I.roles.forEach(function (r) { byId[r.id] = r; });
  var R = rolesOf_(u).map(function (id) { return byId[id]; }).filter(Boolean), P = { kind: 'staff', all: R.some(function (r) { return r.all; }), p: {} };
  if (P.all) return P;
  R.forEach(function (r) { (r.perms || []).forEach(function (x) { P.p[x] = 1; }); });
  (u.allow || []).forEach(function (x) { P.p[x] = 1; }); (u.deny || []).forEach(function (x) { delete P.p[x]; });
  var M = I.modules || {}; Object.keys(P.p).forEach(function (x) { if (!modOn_(M, x.split('.')[0])) delete P.p[x]; });
  return P;
}
function has_(P, p) { return P.kind === 'staff' && (P.all || !!P.p[p]); }
function any_(P, re, write) { return P.kind === 'staff' && (P.all || Object.keys(P.p).some(function (x) { return re.test(x) && (!write || !NOWRITE.test(x)); })); }
function isFull_(u) { var I = iam_(), all = {}; I.roles.forEach(function (r) { if (r.all) all[r.id] = 1; }); return u.kind === 'staff' && rolesOf_(u).some(function (id) { return all[id]; }); }

function memberSales_(me) {
  var S = salesRoot_(), v = (storeIndex_().sales || {}).v || 0, m = me.mobile, reqs = {}, out = { requests: [], quotes: {}, orders: {} };
  (S.requests || []).forEach(function (r) { if (r.mobile === m) { out.requests.push(r); reqs[r.no] = 1; } });
  Object.keys(S.quotes || {}).forEach(function (k) { var q = S.quotes[k]; if (q.status !== 'draft' && ((q.customer && q.customer.mobile === m) || reqs[q.req])) out.quotes[k] = q; });
  Object.keys(S.orders || {}).forEach(function (k) { var o = S.orders[k]; if (out.quotes[o.quote]) out.orders[k] = o; });
  if (S.doc) out.doc = S.doc; // seller details and term labels for the printed quote
  return { v: v, d: JSON.stringify(out) };
}
function salesRoot_() { var x = readRoot_('sales'); return x.d ? JSON.parse(x.d) : { requests: [], quotes: {}, orders: {}, rseq: 0, qseq: 0, oseq: 0, fseq: 0, pack: [] }; }

/* ================= _store: one row per part, JSON split over cells ================= */
function storeIndex_() {
  var sh = SS_().getSheetByName(T.STORE), n = sh.getLastRow(), idx = {};
  if (n < 2) return idx;
  sh.getRange(2, 1, n - 1, 2).getValues().forEach(function (r, i) { if (r[0]) idx[r[0]] = { row: i + 2, v: +r[1] || 0 }; });
  return idx;
}
function readRoot_(k) {
  var it = storeIndex_()[k]; if (!it) return { v: 0 };
  var sh = SS_().getSheetByName(T.STORE), head = sh.getRange(it.row, 1, 1, 5).getValues()[0], n = +head[4] || 0;
  if (!n) return { v: it.v };
  var cells = sh.getRange(it.row, 6, 1, n).getValues()[0];
  return { v: it.v, d: cells.map(function (c) { return String(c).slice(1); }).join('') };
}
function writeRoot_(k, json, by) {
  var sh = SS_().getSheetByName(T.STORE), idx = storeIndex_(), it = idx[k];
  var row = it ? it.row : sh.getLastRow() + 1, v = (it ? it.v : 0) + 1, parts = [];
  for (var i = 0; i < json.length; i += CHUNK) parts.push('~' + json.substr(i, CHUNK)); // "~" keeps Sheets from reading a piece as a number or formula
  var need = 5 + parts.length;
  ensureSize_(sh, row, need);
  var last = sh.getLastColumn();
  if (it && last > 5) sh.getRange(row, 6, 1, last - 5).clearContent();
  sh.getRange(row, 1, 1, need).setValues([[k, v, new Date(), by ? by.name || '' : '', parts.length].concat(parts)]);
  return v;
}
function bump_(k) {
  var sh = SS_().getSheetByName(T.STORE), it = storeIndex_()[k];
  if (it) { sh.getRange(it.row, 2, 1, 2).setValues([[it.v + 1, new Date()]]); return it.v + 1; }
  sh.appendRow([k, 1, new Date(), '', 0]); return 1;
}

/* ================= users ================= */
function readUsers_() {
  var sh = SS_().getSheetByName(T.USERS), n = sh.getLastRow();
  if (n < 2) return [];
  ensureSize_(sh, n, USER_COLS.length);
  return sh.getRange(2, 1, n - 1, USER_COLS.length).getValues().filter(function (r) { return r[0] !== ''; }).map(function (r) {
    var u = {}; USER_COLS.forEach(function (c, i) { u[c] = r[i]; });
    u.id = +u.id; u.active = u.active === true || String(u.active).toLowerCase() === 'true' || u.active === 1 || u.active === 'بله';
    ['user', 'mobile', 'email', 'name', 'role', 'kind', 'hash', 'salt', 'data'].forEach(function (c) { u[c] = String(u[c] == null ? '' : u[c]); });
    if (u.mobile && /^9\d{9}$/.test(u.mobile)) u.mobile = '0' + u.mobile; // a mobile typed into the sheet as a number
    u.roles = String(u.roles || '').split(/[,،\s]+/).filter(String);
    if (!u.roles.length && u.kind === 'staff' && u.role) u.roles = [u.role];
    var acl = {}; try { acl = JSON.parse(u.acl || '{}') || {}; } catch (e) {}
    u.allow = acl.allow || []; u.deny = acl.deny || []; u.bu = acl.bu || [];
    return u;
  });
}
function writeUsers_(list) {
  var sh = SS_().getSheetByName(T.USERS);
  ensureSize_(sh, list.length + 1, USER_COLS.length);
  sh.getRange(1, 1, 1, USER_COLS.length).setValues([USER_COLS]);
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, USER_COLS.length).clearContent();
  if (!list.length) return;
  sh.getRange(2, 1, list.length, USER_COLS.length).setValues(list.map(function (u) {
    return USER_COLS.map(function (c) {
      if (c === 'roles') return u.kind === 'staff' ? rolesOf_(u).join(',') : '';
      if (c === 'acl') return u.kind === 'staff' && ((u.allow || []).length || (u.deny || []).length || (u.bu || []).length) ? JSON.stringify({ allow: u.allow || [], deny: u.deny || [], bu: u.bu || [] }) : '';
      return u[c] == null ? '' : u[c];
    });
  }));
}
function setUserCell_(id, col, val) {
  var sh = SS_().getSheetByName(T.USERS), ids = sh.getRange(2, 1, Math.max(1, sh.getLastRow() - 1), 1).getValues();
  for (var i = 0; i < ids.length; i++) if (+ids[i][0] === +id) { sh.getRange(i + 2, USER_COLS.indexOf(col) + 1).setValue(val); return; }
}
function publicUser_(u) {
  var d = {}; try { d = JSON.parse(u.data || '{}'); } catch (e) {}
  var o = {}; USER_COLS.forEach(function (c) { if (['hash', 'salt', 'data', 'acl'].indexOf(c) < 0) o[c] = u[c]; });
  if (!o.role) delete o.role;
  if (u.kind === 'staff') { o.roles = rolesOf_(u); o.allow = u.allow || []; o.deny = u.deny || []; o.bu = u.bu || []; } else delete o.roles;
  if (!o.user) delete o.user;
  o.favs = d.favs || { $set: [] }; o.lists = d.lists || [];
  return o;
}
function usersPayload_(me) {
  var all = readUsers_(), list;
  if (!me) list = [];
  else if (me.kind !== 'staff') list = all.filter(function (u) { return u.id === me.id; });
  else list = all;
  return { v: (storeIndex_().users || {}).v || 0, d: JSON.stringify(list.map(publicUser_)) };
}
function saveMe_(me, json) {
  var x = JSON.parse(json || 'null'); if (!x) return;
  var users = readUsers_(), u = users.filter(function (q) { return q.id === me.id; })[0]; if (!u) return;
  var d = {}; try { d = JSON.parse(u.data || '{}'); } catch (e) {}
  if (x.favs) d.favs = x.favs; if (x.lists) d.lists = x.lists;
  u.data = JSON.stringify(d);
  if (u.kind === 'member') ['name', 'email', 'company', 'ptype', 'natid', 'eco', 'addr'].forEach(function (c) { if (x[c] != null) u[c] = clip_(x[c], 300); });
  writeUsers_(users);
}
/* admin's users screen: roles, activation, new staff, usernames and passwords */
function saveUsers_(list, admin, P) {
  var old = readUsers_(), byId = {}; old.forEach(function (u) { byId[u.id] = u; });
  var I = iam_(), known = {}; I.roles.forEach(function (r) { known[r.id] = 1; });
  var PERM = /^[a-z_]+\.[a-z_]+\.[a-z_]+$/, seenU = {}, seenM = {}, out = [];
  for (var i = 0; i < list.length; i++) {
    var x = list[i], id = +x.id, o = byId[id], kind = x.kind === 'staff' ? 'staff' : 'member';
    var user = String(x.user || '').trim().toLowerCase(), mobile = String(x.mobile || '').replace(/\D/g, '');
    if (user && !/^[a-z][a-z0-9._-]{2,}$/.test(user)) return 'نام کاربری «' + user + '» معتبر نیست.';
    if (user && seenU[user]) return 'نام کاربری «' + user + '» تکراری است.';
    if (mobile && seenM[mobile]) return 'موبایل ' + mobile + ' برای دو کاربر ثبت شده است.';
    if (user) seenU[user] = 1; if (mobile) seenM[mobile] = 1;
    var roles = kind === 'staff' ? (Array.isArray(x.roles) && x.roles.length ? x.roles : [x.role]).map(String).filter(function (r) { return known[r]; }) : [];
    if (kind === 'staff' && !roles.length) roles = [known.viewer ? 'viewer' : I.roles[I.roles.length - 1].id];
    var u = o ? JSON.parse(JSON.stringify(o)) : { id: id, joined: todayFa_(), last: 'هنوز وارد نشده', company: x.company || '', ptype: x.ptype || '', natid: '', eco: '', addr: '', data: '{"favs":{"$set":[]},"lists":[]}', hash: '', salt: '' };
    u.kind = kind; u.roles = roles; u.role = roles[0] || ''; u.active = x.active !== false; u.user = user; u.name = clip_(x.name, 120) || u.name; u.email = clip_(x.email, 120); u.mobile = mobile || u.mobile;
    u.allow = kind === 'staff' ? (x.allow || []).filter(function (p) { return PERM.test(p); }).slice(0, 400) : [];
    u.deny = kind === 'staff' ? (x.deny || []).filter(function (p) { return PERM.test(p); }).slice(0, 400) : [];
    u.bu = kind === 'staff' ? (x.bu || []).filter(function (b) { return b === 'unofficial' || b === 'official'; }) : [];
    if (x.pw) { if (String(x.pw).length < 8) return 'رمز «' + u.name + '» باید دست‌کم ۸ کاراکتر باشد.'; u.salt = Utilities.getUuid(); u.hash = hash_(String(x.pw), u.salt); }
    var was = !!o && isFull_(o), now = isFull_(u);
    if (!P.all && (was !== now || (was && JSON.stringify(publicUser_(o)) !== JSON.stringify(publicUser_(u))))) return 'فقط مدیر سیستم می‌تواند دسترسی کامل بدهد یا حساب مدیر را تغییر دهد.';
    if (id === admin.id && (!u.active || (was && !now))) return 'نمی‌توانید نقش یا وضعیت حساب خودتان را تغییر دهید.';
    out.push(u);
  }
  if (!out.some(function (u) { return u.active && isFull_(u); })) return 'دست‌کم یک مدیر فعال لازم است.';
  writeUsers_(out);
  bump_('users');
  log_(admin, 'ویرایش کاربران', T.USERS, '');
  return '';
}

/* ================= sessions & passwords ================= */
function hash_(pw, salt) {
  var h = salt + '|' + pw;
  for (var i = 0; i < 300; i++) h = Utilities.base64Encode(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, h + salt, Utilities.Charset.UTF_8));
  return h;
}
function tokenKey_(t) { return Utilities.base64Encode(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(t))); }
function newSession_(uid) {
  var t = Utilities.getUuid() + Utilities.getUuid().replace(/-/g, ''), exp = Date.now() + SESSION_DAYS * 864e5;
  SS_().getSheetByName(T.SESS).appendRow([tokenKey_(t), uid, new Date(), exp]);
  CacheService.getScriptCache().put('sess:' + t, JSON.stringify({ uid: uid, exp: exp }), 21600);
  return t;
}
function sessionUser_(token) {
  if (!token) return null;
  var c = CacheService.getScriptCache(), hit = c.get('sess:' + token), s = hit ? JSON.parse(hit) : null;
  if (!s) {
    var key = tokenKey_(token), v = SS_().getSheetByName(T.SESS).getDataRange().getValues();
    for (var i = 1; i < v.length; i++) if (v[i][0] === key) { s = { uid: +v[i][1], exp: +v[i][3] }; break; }
    if (s) c.put('sess:' + token, JSON.stringify(s), 21600);
  }
  if (!s || s.exp < Date.now()) return null;
  return sessionUserById_(s.uid);
}
function sessionUserById_(uid) {
  var u = readUsers_().filter(function (x) { return x.id === +uid; })[0];
  return u && u.active ? u : null;
}

/* ================= readable tabs ================= */
function mirror_(k, d) {
  if (k === 'audit') { mirrorAudit_(d); return; }
  if (k === 'work') { mirrorWork_(d); return; }
  if (k === 'sales') {
    put_(T.REQ, ['شماره', 'تاریخ', 'نام', 'موبایل', 'شرکت', 'وضعیت', 'کارشناس', 'تعداد اقلام', 'اقلام', 'پیش‌فاکتور', 'توضیح'],
      (d.requests || []).map(function (r) { return [r.no, r.date, r.name, r.mobile, r.company || '', r.status, r.owner || '', (r.items || []).length, (r.items || []).map(function (i) { return i.p + ' × ' + i.q + ' ' + (i.u || ''); }).join('، '), r.quote || '', r.note || '']; }));
    put_(T.QUO, ['شماره', 'درخواست', 'وضعیت', 'مشتری', 'موبایل', 'تعداد اقلام', 'جمع کالا (ریال)', 'مالیات ٪', 'حمل', 'جمع کل (ریال)', 'سفارش'],
      Object.keys(d.quotes || {}).map(function (id) {
        var q = d.quotes[id], sub = (q.lines || []).reduce(function (a, l) { return a + (+l.q || 0) * (+l.price || 0) * (1 - (+l.disc || 0) / 100); }, 0);
        return [id, q.req || '', q.status, (q.customer || {}).name || '', (q.customer || {}).mobile || '', (q.lines || []).length, Math.round(sub), q.vat || 0, q.ship || 0, Math.round(sub * (1 + (+q.vat || 0) / 100) + (+q.ship || 0)), q.order || ''];
      }));
    put_(T.ORD, ['شماره', 'پیش‌فاکتور', 'مشتری', 'موبایل', 'ایجاد', 'وضعیت', 'مسئول', 'اقلام', 'تعیین‌تکلیف‌شده'],
      Object.keys(d.orders || {}).map(function (id) { var o = d.orders[id]; return [id, o.quote || '', (o.customer || {}).name || '', (o.customer || {}).mobile || '', o.created || '', o.status, o.assignee || '', (o.lines || []).length, (o.lines || []).filter(function (l) { return l.done; }).length]; }));
    var SL = (d.doc && d.doc.sellers) || {}, KF = { official: (SL.official || {}).short || 'آلیاژ پیچ کار ماد', unofficial: (SL.unofficial || {}).short || 'کارما' }, SF = { draft: 'پیش‌نویس', issued: 'صادرشده', 'void': 'باطل‌شده' };
    put_(T.INV, ['شماره', 'نوع', 'فروشنده', 'وضعیت', 'تاریخ', 'خریدار', 'موبایل', 'کد اقتصادی', 'تعداد اقلام', 'جمع کالا (ریال)', 'مالیات ٪', 'اضافات', 'جمع کل (ریال)', 'فاکتور مبنا', 'علت ابطال'],
      Object.keys(d.invoices || {}).map(function (id) {
        var I = d.invoices[id], c = I.customer || {}, sub = (I.lines || []).reduce(function (a, l) { return a + (+l.q || 0) * (+l.price || 0) * (1 - (+l.disc || 0) / 100); }, 0);
        var base = I.ref && d.invoices[I.ref];
        return [I.no || '(پیش‌نویس)', I.type === 'return' ? 'برگشت از فروش' : 'فروش', KF[I.seller] || '', SF[I.status] || I.status, I.date || '', c.name || '', c.mobile || '', c.eco || '', (I.lines || []).length, Math.round(sub), I.vat || 0, +I.ship || 0, Math.round(sub * (1 + (+I.vat || 0) / 100) + (+I.ship || 0)), base ? base.no : '', I.voidWhy || ''];
      }));
    var BF = (d.doc && d.doc.buyerF) || [{ k: 'name', l: 'نام' }, { k: 'mobile', l: 'موبایل' }];
    put_(T.CUST, BF.map(function (f) { return f.l; }).concat(['یادداشت', 'تاریخ ثبت']),
      (d.customers || []).map(function (c) { return BF.map(function (f) { return c[f.k] == null ? '' : String(c[f.k]); }).concat([c.note || '', c.created || '']); }));
  } else if (k === 'acc') {
    var A = d.A || {}, nm = {};
    ((A.coa || {}).m || []).forEach(function (m) { nm[m.c] = m.n; });
    var rows = [];
    (A.vouchers || []).forEach(function (v) { (v.lines || []).forEach(function (l) { rows.push([v.no, v.date, v.type || '', v.st === 'perm' ? 'دائم' : v.st === 'tmp' ? 'موقت' : (v.st || ''), v.desc || '', l.m, nm[l.m] || '', l.t || '', l.d || '', +l.dr || 0, +l.cr || 0]); }); });
    put_(T.VCH, ['شمارهٔ سند', 'تاریخ', 'نوع', 'وضعیت', 'شرح سند', 'کد معین', 'نام معین', 'تفصیلی', 'شرح ردیف', 'بدهکار', 'بستانکار'], rows);
  } else if (k === 'prod') {
    put_(T.NEWSKU, ['کد محصول', 'کد فنی', 'استاندارد', 'سایز', 'طول', 'گرید', 'پوشش', 'تاریخ'], (d.sku || []).map(function (r) { return [r.pcode, r.tech, r.sid, r.size, r.len || '', r.grade, r.fin, r.created || '']; }));
  }
}
function mirrorWork_(d) {
  var cfg = (d && d.cfg) || {}, st = {}, pr = {}, ls = {}, nm = {};
  (cfg.statuses || []).forEach(function (x) { st[x.k] = x.t; }); (cfg.prios || []).forEach(function (x) { pr[x.k] = x.t; }); (cfg.lists || []).forEach(function (x) { ls[x.id] = x.name; });
  readUsers_().forEach(function (u) { nm[u.id] = u.name; });
  put_(T.WORK, ['شناسه', 'عنوان', 'وضعیت', 'اولویت', 'فهرست', 'مسئول', 'سازنده', 'سررسید', 'ثبت', 'انجام', 'آخرین توضیح', 'خصوصی'],
    ((d && d.tasks) || []).map(function (t) {
      var c = (t.cm || [])[(t.cm || []).length - 1];
      return [t.id, t.title || '', st[t.status] || t.status || '', pr[t.prio] || '', ls[t.list] || '', (t.as || []).map(function (x) { return nm[x] || x; }).join('، '), nm[t.by] || '', t.due || '', t.created || '', t.doneAt || '', t.priv ? '' : (c ? c.text : ''), t.priv ? 'بله' : ''];
    }));
}
function mirrorAudit_(d) {
  put_(T.AUD, ['زمان', 'کاربر', 'کار', 'موضوع', 'جزئیات'], (d || []).map(function (e) { return [e.t || '', e.who || '', e.act || '', e.obj || '', e.det || '']; }));
}
function put_(name, head, rows) {
  var sh = ensureSheet_(name, head);
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, Math.max(head.length, sh.getLastColumn())).clearContent();
  if (rows.length) { ensureSize_(sh, rows.length + 1, head.length); sh.getRange(2, 1, rows.length, head.length).setValues(rows); }
}

/* ================= install: app files and images from karma-assets.zip ================= */
function installAssets() {
  var t0 = Date.now(), ui = safeUi_();
  var zip = null, it = DriveApp.searchFiles('title contains "karma-assets" and trashed = false');
  while (it.hasNext()) { var f = it.next(); if (/\.zip$/i.test(f.getName()) && (!zip || f.getLastUpdated() > zip.getLastUpdated())) zip = f; }
  if (!zip) return say_(ui, 'فایل karma-assets.zip در درایو پیدا نشد. ابتدا آن را در Google Drive آپلود کنید.');
  var blobs = Utilities.unzip(zip.getBlob());
  var folder = assetFolder_();
  try { folder.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW); } catch (e) {}
  var have = assetMap_(), sh = SS_().getSheetByName(T.ASSETS), fresh = [], left = 0, manifest = null;
  CacheService.getScriptCache().remove('assets:' + cfg_('app_stamp'));
  have = {}; if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 2).getValues().forEach(function (r) { if (r[0]) have[r[0]] = r[1]; });
  blobs.forEach(function (b) { if (b.getName().split('/').pop() === 'manifest.json') manifest = JSON.parse(b.getDataAsString('UTF-8')); });
  for (var i = 0; i < blobs.length; i++) {
    var b = blobs[i], name = b.getName().split('/').pop(), dir = b.getName().indexOf('img/') >= 0;
    if (!name) continue;
    if (dir) {
      if (have[name]) continue;
      if (Date.now() - t0 > 270000) { left++; continue; }
      var file = folder.createFile(b.setName(name));
      fresh.push([name, file.getId()]); have[name] = file.getId();
    }
  }
  if (fresh.length) { ensureSize_(sh, sh.getLastRow() + fresh.length, 2); sh.getRange(sh.getLastRow() + 1, 1, fresh.length, 2).setValues(fresh); }
  if (left) { stamp_(); return say_(ui, fresh.length + ' تصویر نصب شد؛ ' + left + ' تصویر مانده است. همین گزینه را یک بار دیگر اجرا کنید.'); }
  if (Date.now() - t0 > 150000) { stamp_(); return say_(ui, 'همهٔ تصاویر نصب شد. برای تکمیل نصب، همین گزینه را یک بار دیگر اجرا کنید.'); }
  // the page itself, seed data and the product list
  blobs.forEach(function (b) {
    var name = b.getName().split('/').pop();
    if (name === 'app.html' || name === 'loader.html') {
      var key = name === 'app.html' ? 'app_file' : 'loader_file', old = cfg_(key);
      if (old) try { DriveApp.getFileById(old).setTrashed(true); } catch (e) {}
      var f = folder.createFile(b.setName(name).setContentType('text/html'));
      setCfg_(key, f.getId());
    } else if (name === 'seed.json') {
      var seed = JSON.parse(b.getDataAsString('UTF-8')), idx = storeIndex_();
      Object.keys(seed).forEach(function (k) { if (!idx[k]) { writeRoot_(k, JSON.stringify(seed[k]), { name: 'نصب' }); try { mirror_(k, seed[k]); } catch (e) {} } });
    } else if (name === 'skus.csv' || name === 'standards.csv') {
      var tab = name === 'skus.csv' ? T.SKU : T.STD, rows = Utilities.parseCsv(b.getDataAsString('UTF-8'));
      var s2 = ensureSheet_(tab, rows[0]);
      s2.clearContents();
      ensureSize_(s2, rows.length, rows[0].length);
      s2.getRange(1, 1, rows.length, rows[0].length).setNumberFormat('@').setValues(rows);
      s2.getRange(1, 1, 1, rows[0].length).setFontWeight('bold').setNumberFormat('General'); s2.setFrozenRows(1);
    }
  });
  if (manifest) setCfg_('app_version', manifest.version || '');
  stamp_();
  return say_(ui, 'نصب کامل شد (' + Object.keys(have).length + ' تصویر). اگر اپ را منتشر کرده‌اید، کافی است صفحهٔ آن را دوباره باز کنید.');
}
function stamp_() { setCfg_('app_stamp', String(Date.now())); }
function assetFolder_() {
  var id = cfg_('assets_folder');
  if (id) try { var f = DriveApp.getFolderById(id); if (!f.isTrashed()) return f; } catch (e) {}
  var parent = DriveApp.getFileById(SS_().getId()).getParents(), p = parent.hasNext() ? parent.next() : DriveApp.getRootFolder();
  var folder = p.createFolder('Karma Assets (تصاویر و فایل‌های اپ)');
  setCfg_('assets_folder', folder.getId());
  return folder;
}

/* ================= setup & menu ================= */
function setup() {
  var ss = SS_();
  ensureSheet_(T.STORE, ['key', 'ver', 'updated', 'by', 'chunks', 'json…']);
  ensureSheet_(T.SESS, ['token', 'uid', 'created', 'expires']);
  ensureSheet_(T.ASSETS, ['name', 'drive_id']);
  ensureSheet_(T.LOG, ['زمان', 'کاربر', 'کار', 'بخش', 'شناسه']);
  var cfg = ensureSheet_(T.CFG, ['key', 'value', 'توضیح']);
  if (cfg.getLastRow() < 2) cfg.getRange(2, 1, 4, 3).setValues([
    ['title', 'کارما | پیچ و مهره و اتصالات صنعتی', 'عنوان زبانهٔ مرورگر'],
    ['require_login', 'no', 'yes = کل سایت فقط پس از ورود دیده شود'],
    ['registration', 'on', 'off = عضویت مشتریان در سایت بسته شود'],
    ['app_stamp', String(Date.now()), 'خودکار']]);
  var us = ensureSheet_(T.USERS, USER_COLS);
  us.getRange(1, 1, us.getMaxRows(), USER_COLS.length).setNumberFormat('@');
  us.getRange(2, USER_COLS.indexOf('active') + 1, us.getMaxRows() - 1, 1).setNumberFormat('General');
  if (!readUsers_().length) {
    writeUsers_(SEED_USERS.map(function (s) {
      var salt = s.pw ? Utilities.getUuid() : '';
      return { id: s.id, kind: s.kind, name: s.name, user: s.user || '', mobile: s.mobile, email: s.email || '', role: s.role || '', roles: s.kind === 'staff' ? [s.role] : [], active: true, last: 'هنوز وارد نشده', joined: todayFa_(),
        company: s.company || '', ptype: s.ptype || '', natid: '', eco: '', addr: '', data: s.data || '{"favs":{"$set":[]},"lists":[]}', hash: s.pw ? hash_(s.pw, salt) : '', salt: salt };
    }));
    us.getRange(2, USER_COLS.indexOf('active') + 1, SEED_USERS.length, 1).insertCheckboxes();
  }
  if (!storeIndex_().users) bump_('users');
  [T.STORE, T.SESS, T.ASSETS].forEach(function (n) { var s = ss.getSheetByName(n); s.setFrozenRows(1); s.hideSheet(); });
  var first = ss.getSheetByName('Sheet1') || ss.getSheetByName('برگه۱');
  if (first && first.getLastRow() === 0 && ss.getSheets().length > 1) ss.deleteSheet(first);
  say_(safeUi_(), 'راه‌اندازی انجام شد. حالا فایل karma-assets.zip را در درایو آپلود کنید و از منوی «کارما» گزینهٔ «نصب / به‌روزرسانی فایل‌های اپ» را بزنید.');
}

function onOpen() {
  SpreadsheetApp.getUi().createMenu('کارما')
    .addItem('۱. راه‌اندازی اولیه', 'setup')
    .addItem('۲. نصب / به‌روزرسانی فایل‌های اپ', 'installAssets')
    .addSeparator()
    .addItem('تعیین رمز کاربر', 'promptSetPassword')
    .addItem('پاک‌کردن درخواست‌ها، پیش‌فاکتورها و سفارش‌های نمونه', 'clearSampleSales')
    .addItem('بررسی وضعیت نصب', 'diagnose')
    .addToUi();
}

function promptSetPassword() {
  var ui = SpreadsheetApp.getUi();
  var a = ui.prompt('تعیین رمز', 'نام کاربری یا موبایل کاربر:', ui.ButtonSet.OK_CANCEL); if (a.getSelectedButton() !== ui.Button.OK) return;
  var id = a.getResponseText().trim().toLowerCase(), users = readUsers_();
  var u = users.filter(function (x) { return String(x.user).toLowerCase() === id || x.mobile === id; })[0];
  if (!u) return ui.alert('کاربری با این مشخصات نیست.');
  var b = ui.prompt('رمز تازه برای «' + u.name + '»', 'حداقل ۸ کاراکتر:', ui.ButtonSet.OK_CANCEL); if (b.getSelectedButton() !== ui.Button.OK) return;
  var pw = b.getResponseText(); if (pw.length < 8) return ui.alert('رمز کوتاه است.');
  u.salt = Utilities.getUuid(); u.hash = hash_(pw, u.salt); u.active = true;
  writeUsers_(users);
  ui.alert('رمز «' + u.name + '» ذخیره شد.');
}

function clearSampleSales() {
  var ui = SpreadsheetApp.getUi();
  if (ui.alert('همهٔ درخواست‌ها، پیش‌فاکتورها و سفارش‌ها پاک شوند؟ (شماره‌گذاری ادامه پیدا می‌کند)', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  var lock = LockService.getScriptLock(); lock.waitLock(30000);
  try { var S = salesRoot_(); S.requests = []; S.quotes = {}; S.orders = {}; writeRoot_('sales', JSON.stringify(S), { name: 'مدیر' }); mirror_('sales', S); } finally { lock.releaseLock(); }
  ui.alert('پاک شد.');
}

function diagnose() {
  var idx = storeIndex_(), a = assetMap_(), lines = ['نسخهٔ سرور: ' + KARMA_VERSION, 'نسخهٔ اپ نصب‌شده: ' + (cfg_('app_version') || '—'),
    'فایل app.html: ' + (cfg_('app_file') ? 'نصب شده' : 'نصب نشده'), 'تعداد تصاویر: ' + Object.keys(a).length,
    'بخش‌های داده: ' + Object.keys(idx).map(function (k) { return k + ' (v' + idx[k].v + ')'; }).join('، '), 'کاربران: ' + readUsers_().length];
  say_(safeUi_(), lines.join('\n'));
}

/* ================= helpers ================= */
function SS_() { return SpreadsheetApp.getActive(); }
function ensureSheet_(name, head) {
  var ss = SS_(), sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); sh.setRightToLeft(true); }
  if (head && sh.getLastRow() === 0) { sh.getRange(1, 1, 1, head.length).setValues([head]).setFontWeight('bold'); sh.setFrozenRows(1); }
  else if (head && name !== T.STORE) sh.getRange(1, 1, 1, head.length).setValues([head]);
  return sh;
}
function ensureSize_(sh, rows, cols) {
  if (sh.getMaxRows() < rows) sh.insertRowsAfter(sh.getMaxRows(), rows - sh.getMaxRows() + 50);
  if (sh.getMaxColumns() < cols) sh.insertColumnsAfter(sh.getMaxColumns(), cols - sh.getMaxColumns());
}
function cfg_(k) {
  var c = CacheService.getScriptCache(), hit = c.get('cfg');
  var m = hit ? JSON.parse(hit) : null;
  if (!m) {
    m = {}; var sh = SS_().getSheetByName(T.CFG);
    if (sh && sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 2).getValues().forEach(function (r) { if (r[0]) m[r[0]] = String(r[1]); });
    c.put('cfg', JSON.stringify(m), 600);
  }
  return m[k] || '';
}
function setCfg_(k, v) {
  var sh = SS_().getSheetByName(T.CFG), n = sh.getLastRow(), keys = n > 1 ? sh.getRange(2, 1, n - 1, 1).getValues() : [];
  for (var i = 0; i < keys.length; i++) if (keys[i][0] === k) { sh.getRange(i + 2, 2).setValue(v); CacheService.getScriptCache().remove('cfg'); return; }
  sh.appendRow([k, v, 'خودکار']); CacheService.getScriptCache().remove('cfg');
}
function log_(u, what, sheet, id) { try { SS_().getSheetByName(T.LOG).appendRow([new Date(), u ? u.name : '', what, sheet, String(id)]); } catch (e) {} }
function clip_(s, n) { return String(s == null ? '' : s).trim().slice(0, n); }
function safeUi_() { try { return SpreadsheetApp.getUi(); } catch (e) { return null; } }
function say_(ui, msg) { if (ui) ui.alert(msg); else console.log(msg); return msg; }

/* Jalali date, Persian digits: «۸ مهر ۰۹:۴۰» like the app */
var FA_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
function faDigits_(s) { return String(s).replace(/\d/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; }); }
function jalali_(d) {
  var p = Utilities.formatDate(d, 'Asia/Tehran', 'yyyy-M-d').split('-'), gy = +p[0], gm = +p[1], gd = +p[2];
  var gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334], gy2 = gm > 2 ? gy + 1 : gy;
  var days = 355666 + 365 * gy + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) + Math.floor((gy2 + 399) / 400) + gd + gdm[gm - 1];
  var jy = -1595 + 33 * Math.floor(days / 12053); days %= 12053; jy += 4 * Math.floor(days / 1461); days %= 1461;
  if (days > 365) { jy += Math.floor((days - 1) / 365); days = (days - 1) % 365; }
  var jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30), jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
  return [jy, jm, jd];
}
function nowFa_() { var d = new Date(), j = jalali_(d); return faDigits_(j[2]) + ' ' + FA_MONTHS[j[1] - 1] + ' ' + faDigits_(Utilities.formatDate(d, 'Asia/Tehran', 'HH:mm')); }
function todayFa_() { var j = jalali_(new Date()); return faDigits_(j[2]) + ' ' + FA_MONTHS[j[1] - 1] + ' ' + faDigits_(j[0]); }
