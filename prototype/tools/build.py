# Build the deliverables from prototype/src:
#   dist/Karma-prototype.html          one file, images embedded, runs offline with sample data
#   dist/Karma-GoogleSheets-v<ver>.zip install guide + Code.gs + appsscript.json + karma-assets.zip
# usage: python3 build.py   (from prototype/tools; needs node + playwright for the seed dump)
import base64, json, os, re, shutil, subprocess, zipfile
T = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(T, '..', 'src'); GAS = os.path.join(T, '..', 'gas'); OUT = os.path.join(T, '..', 'dist')
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT + '/pkg')
app = open(SRC + '/app.html', encoding='utf-8').read()
for n, sc in enumerate(re.findall(r'<script>(.*?)</script>', app, re.S)):   # every script must parse
    open(OUT + '/chk.js', 'w', encoding='utf-8').write(sc); subprocess.run(['node', '--check', OUT + '/chk.js'], check=True)
os.remove(OUT + '/chk.js')
VER = re.search(r"KARMA_VERSION = '([\d.]+)'", open(GAS + '/Code.gs', encoding='utf-8').read()).group(1)

# ---- standalone prototype: image files become data: URLs looked up by name ----
used = sorted(set(re.findall(r'[0-9a-f]{12}\.(?:webp|png|jpg)', app)))
mime = {'webp': 'image/webp', 'png': 'image/png', 'jpg': 'image/jpeg'}
imgs = {f: 'data:%s;base64,%s' % (mime[f.split('.')[1]], base64.b64encode(open(SRC + '/img/' + f, 'rb').read()).decode()) for f in used if os.path.exists(SRC + '/img/' + f)}
missing = [f for f in used if f not in imgs]
ksa = "window.KSA=function(n){var id=M[n];return id?'https://lh3.googleusercontent.com/d/'+id:'img/'+n};"
assert app.count(ksa) == 1
one = app.replace(ksa, "window.KSA=function(n){var id=M[n];return (window.__KSIMG&&__KSIMG[n])||(id?'https://lh3.googleusercontent.com/d/'+id:'img/'+n)};")
i = one.index('<script>')
one = one[:i] + '<script>window.__KSIMG=' + json.dumps(imgs) + ';</script>\n' + one[i:]
open(OUT + '/Karma-prototype.html', 'w', encoding='utf-8').write(one)
print('prototype', len(one.encode()) // 1024, 'KB;', len(imgs), 'images', ('missing ' + str(missing)) if missing else '')

# ---- Google Sheets package ----
P = OUT + '/pkg'
shutil.copy(SRC + '/app.html', P + '/app.html'); shutil.copy(SRC + '/loader.html', P + '/loader.html')
subprocess.run(['node', T + '/dump.js', SRC + '/app.html', P], check=True)
json.dump({'version': VER, 'images': len(os.listdir(SRC + '/img'))}, open(P + '/manifest.json', 'w'))
with zipfile.ZipFile(OUT + '/karma-assets.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in ['app.html', 'loader.html', 'seed.json', 'skus.csv', 'standards.csv', 'manifest.json']: z.write(P + '/' + f, f)
    for f in sorted(os.listdir(SRC + '/img')): z.write(SRC + '/img/' + f, 'img/' + f)
# the server falls back to the app's built-in roles until the "iam" part exists
iam = json.load(open(P + '/seed.json', encoding='utf-8'))['iam']
cg = open(GAS + '/Code.gs', encoding='utf-8').read()
cg, k = re.subn(r'^var DEFAULT_IAM = .*;$', lambda m: 'var DEFAULT_IAM = ' + json.dumps(iam, ensure_ascii=False) + ';', cg, count=1, flags=re.M); assert k == 1
open(OUT + '/Code.gs', 'w', encoding='utf-8').write(cg)
shutil.copy(OUT + '/Code.gs', OUT + '/chk.js'); subprocess.run(['node', '--check', OUT + '/chk.js'], check=True); os.remove(OUT + '/chk.js')
shutil.copy(GAS + '/appsscript.json', OUT); shutil.copy(GAS + '/راهنمای نصب.txt', OUT)
B = OUT + '/Karma-GoogleSheets-v' + VER + '.zip'
with zipfile.ZipFile(B, 'w', zipfile.ZIP_STORED) as z:
    for f in ['راهنمای نصب.txt', 'Code.gs', 'appsscript.json', 'karma-assets.zip']: z.write(OUT + '/' + f, f)
print('bundle', os.path.basename(B), os.path.getsize(B) // 1024, 'KB')
