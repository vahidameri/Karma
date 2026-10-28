"""Build a self-contained offline demo using sanitized catalog data, never live accounts."""
import base64
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / 'platform/data/legacy'
rows = list(csv.DictReader((base / 'skus.csv').open(encoding='utf-8-sig')))
mapping = json.loads((base / 'asset-map.json').read_text())
products = []
images = {}
counts = {}
for row in rows:
    standard = row['استاندارد']
    counts[standard] = counts.get(standard, 0) + 1
    if counts[standard] > 2:
        continue
    key = standard.replace(' ', '')
    photo = mapping.get(key, {}).get('p')
    if photo and key not in images:
        path = base / 'images' / photo
        mime = 'image/webp' if path.suffix == '.webp' else 'image/png'
        images[key] = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()
    products.append(dict(code=row['کد محصول'], tech=row['کد فنی'], name=row['نام کالا'],
                         standard=standard, size=row['سایز'], grade=row['گرید'], image=key))
template = (root / 'prototype/template.html').read_text()
font = base64.b64encode((root / 'platform/backend/documents/fonts/Vazirmatn.woff2').read_bytes()).decode()
html = template.replace('__FONT__', font).replace('__PRODUCTS__', json.dumps(products, ensure_ascii=False).replace('<', '\\u003c')).replace('__IMAGES__', json.dumps(images))
(root / 'prototype/Karma-prototype-2.0.0.html').write_text(html)
print(f'Built offline prototype: {len(products)} sample variants, {len(images)} embedded photographs')
