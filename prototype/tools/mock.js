// Minimal Apps Script runtime for testing Code.gs in Node: Sheets (with number coercion and the
// 50,000-character cell limit), Drive, Cache, Lock, Utilities, HtmlService. runtime(codePath) → globals.
const vm = require('vm'), fs = require('fs'), crypto = require('crypto'), path = require('path'), cp = require('child_process'), os = require('os');
function mkSheet(name) {
  const sh = { name, data: [], fmt: {}, maxRows: 1000, maxCols: 26 };
  const lastRow = () => { for (let r = sh.data.length; r > 0; r--) if ((sh.data[r - 1] || []).some(v => v !== '' && v != null)) return r; return 0; };
  const lastCol = () => { let m = 0; sh.data.forEach(row => { for (let c = row.length; c > m; c--) if (row[c - 1] !== '' && row[c - 1] != null) { m = c; break; } }); return m; };
  const get = (r, c) => ((sh.data[r - 1] || [])[c - 1] ?? '');
  const set = (r, c, v) => {
    if (typeof v === 'string') {
      if (v.length > 50000) throw new Error('Your input contains more than the maximum of 50000 characters in a single cell.');
      if (sh.fmt[c] !== '@') { if (/^[-+]?\d+(\.\d+)?$/.test(v.trim())) v = Number(v); else if (v[0] === '=') v = '#ERROR!'; }
    }
    while (sh.data.length < r) sh.data.push([]);
    sh.data[r - 1][c - 1] = v;
  };
  const range = (r, c, nr = 1, nc = 1) => {
    if (r < 1 || c < 1 || nr < 1 || nc < 1 || r + nr - 1 > sh.maxRows || c + nc - 1 > sh.maxCols) throw new Error(`Range out of bounds ${name} ${r},${c},${nr},${nc} (max ${sh.maxRows}x${sh.maxCols})`);
    const R = {
      getValues: () => Array.from({ length: nr }, (_, i) => Array.from({ length: nc }, (_, j) => get(r + i, c + j))),
      setValues: v => { if (v.length !== nr || v.some(x => x.length !== nc)) throw new Error('setValues dims ' + name); v.forEach((row, i) => row.forEach((x, j) => set(r + i, c + j, x))); return R; },
      setValue: v => { set(r, c, v); return R; },
      clearContent: () => { for (let i = 0; i < nr; i++) for (let j = 0; j < nc; j++) if (sh.data[r + i - 1]) sh.data[r + i - 1][c + j - 1] = ''; return R; },
      setFontWeight: () => R, insertCheckboxes: () => R,
      setNumberFormat: f => { for (let j = 0; j < nc; j++) sh.fmt[c + j] = f; return R; }
    };
    return R;
  };
  Object.assign(sh, {
    getName: () => name, getLastRow: lastRow, getLastColumn: lastCol, getMaxRows: () => sh.maxRows, getMaxColumns: () => sh.maxCols,
    getRange: range, getDataRange: () => range(1, 1, Math.max(1, lastRow()), Math.max(1, lastCol())),
    insertRowsAfter: (a, n) => { sh.maxRows += n; }, insertColumnsAfter: (a, n) => { sh.maxCols += n; },
    setFrozenRows: () => sh, hideSheet: () => sh, setRightToLeft: () => sh, clearContents: () => { sh.data = []; return sh; },
    appendRow: row => { const r = lastRow() + 1; if (r > sh.maxRows) sh.maxRows = r; row.forEach((v, j) => set(r, j + 1, v)); return sh; },
    deleteRow: r => { sh.data.splice(r - 1, 1); }
  });
  return sh;
}
function blob(name, bytes, type) {
  const b = { name, bytes, type: type || '' };
  return Object.assign(b, { getName: () => b.name, setName: n => { b.name = n; return b; }, setContentType: t => { b.type = t; return b; }, getBytes: () => b.bytes, getDataAsString: () => Buffer.from(b.bytes).toString('utf8') });
}
function runtime(code) {
  const sheets = [], files = {}, cache = new Map();
  let fid = 0;
  const mkFile = (bl, parent) => { const id = 'F' + (++fid); const f = { id, blob: bl, trashed: false, parent, updated: new Date(Date.now() + fid) };
    Object.assign(f, { getId: () => id, getName: () => bl.getName(), getBlob: () => bl, setTrashed: t => { f.trashed = t; }, isTrashed: () => f.trashed, getLastUpdated: () => f.updated,
      getParents: () => { let d = false; return { hasNext: () => !d, next: () => { d = true; return root; } }; }, setSharing: () => f });
    files[id] = f; return f; };
  const mkFolder = name => { const id = 'D' + (++fid); const fo = { id, name, trashed: false };
    Object.assign(fo, { getId: () => id, isTrashed: () => false, setSharing: () => fo, createFile: bl => mkFile(bl, fo), createFolder: n => mkFolder(n) }); files[id] = fo; return fo; };
  const root = mkFolder('root');
  files.SS1 = { getId: () => 'SS1', getParents: () => { let d = false; return { hasNext: () => !d, next: () => { d = true; return root; } }; } };
  const ss = { getSheetByName: n => sheets.find(s => s.name === n) || null, insertSheet: n => { const s = mkSheet(n); sheets.push(s); return s; },
    getSheets: () => sheets, deleteSheet: s => sheets.splice(sheets.indexOf(s), 1), getId: () => 'SS1' };
  sheets.push(mkSheet('Sheet1'));
  const bytesOf = (s) => Array.from(Buffer.from(String(s), 'utf8')).map(x => x > 127 ? x - 256 : x);
  const G = {
    console, Date, Math, JSON, String, Number, Object, Array, RegExp, Error, parseInt, parseFloat, isNaN, encodeURIComponent,
    SpreadsheetApp: { getActive: () => ss, getUi: () => { throw new Error('no ui'); } },
    CacheService: { getScriptCache: () => ({ get: k => cache.has(k) ? cache.get(k) : null, put: (k, v) => { cache.set(k, String(v)); }, remove: k => cache.delete(k),
      getAll: ks => Object.fromEntries(ks.filter(k => cache.has(k)).map(k => [k, cache.get(k)])), putAll: o => Object.entries(o).forEach(([k, v]) => cache.set(k, String(v))) }) },
    LockService: { getScriptLock: () => ({ waitLock: () => {}, releaseLock: () => {} }) },
    Utilities: { getUuid: () => crypto.randomUUID(), DigestAlgorithm: { SHA_256: 'sha256' }, Charset: { UTF_8: 'utf8' },
      computeDigest: (a, s) => Array.from(crypto.createHash(a).update(Array.isArray(s) ? Buffer.from(s.map(x => x & 255)) : Buffer.from(String(s), 'utf8')).digest()).map(x => x > 127 ? x - 256 : x),
      base64Encode: b => Buffer.from((Array.isArray(b) ? b : bytesOf(b)).map(x => x & 255)).toString('base64'),
      formatDate: (d, tz, f) => { const p = new Intl.DateTimeFormat('en-GB', { timeZone: tz, year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(d).reduce((o, x) => (o[x.type] = x.value, o), {});
        return f.replace('yyyy', p.year).replace('M', +p.month).replace('d', +p.day).replace('HH', p.hour.padStart(2, '0')).replace('mm', p.minute); },
      parseCsv: s => { const rows = [[]]; let f = '', q = false; for (let i = 0; i < s.length; i++) { const c = s[i];
          if (q) { if (c === '"' && s[i + 1] === '"') { f += '"'; i++; } else if (c === '"') q = false; else f += c; }
          else if (c === '"') q = true; else if (c === ',') { rows[rows.length - 1].push(f); f = ''; } else if (c === '\n') { rows[rows.length - 1].push(f); f = ''; rows.push([]); } else f += c; }
        rows[rows.length - 1].push(f); return rows; },
      unzip: b => { const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'unz')); const zp = path.join(dir, 'a.zip'); fs.writeFileSync(zp, Buffer.from(b.getBytes()));
        cp.execFileSync('unzip', ['-q', zp, '-d', dir + '/x']); const out = [];
        const walk = (d, rel) => fs.readdirSync(d).forEach(n => { const p = path.join(d, n), r = rel ? rel + '/' + n : n; if (fs.statSync(p).isDirectory()) walk(p, r); else out.push(Object.assign(blob(r, fs.readFileSync(p)), { path: p })); });
        walk(dir + '/x', ''); return out; } },
    DriveApp: { Access: { ANYONE_WITH_LINK: 1 }, Permission: { VIEW: 1 }, getRootFolder: () => root,
      getFileById: id => { if (!files[id]) throw new Error('no file ' + id); return files[id]; }, getFolderById: id => { if (!files[id]) throw new Error('no folder'); return files[id]; },
      searchFiles: q => { const m = /title contains "([^"]+)"/.exec(q); const L = Object.values(files).filter(f => f.blob && !f.trashed && f.getName().includes(m[1])); let i = 0; return { hasNext: () => i < L.length, next: () => L[i++] }; } },
    HtmlService: { XFrameOptionsMode: { ALLOWALL: 1 }, createHtmlOutput: h => { const o = { getContent: () => h, setTitle: () => o, addMetaTag: () => o, setXFrameOptionsMode: () => o }; return o; } }
  };
  G.__sheets = sheets; G.__files = files;
  G.__upload = p => mkFile(blob(path.basename(p), fs.readFileSync(p)), root);
  const ctx = vm.createContext(G);
  vm.runInContext(fs.readFileSync(code, 'utf8'), ctx, { filename: 'Code.gs' });
  return ctx;
}
module.exports = { runtime };
