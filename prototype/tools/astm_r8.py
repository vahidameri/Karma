# ASTM section rebuilt from the owner's workbook (ASTM.xlsx, 1405-08): 6 groups, one product per standard,
# grades with material, class note and priority (cell colours: blue = very common, green = common,
# red = custom, «تخصصی» colour = specialist). Product codes are made for untagged / common grades only;
# custom and specialist grades are listed «on request». Geometry, tables and images are reused from the
# previous per-grade products of the same standard. Run once on prototype/src/app.html.
import json, re, sys
P = sys.argv[1] if len(sys.argv) > 1 else 'app.html'
s = open(P, encoding='utf-8').read()
L = s.split('\n')
i = next(k for k, l in enumerate(L) if l.startswith('const ASTM={'))
A = json.loads(L[i][L[i].index('{'):L[i].rindex('}') + 1])
assert any(x['id'] == 'ASTM-A193-B7' for x in A['std']), 'already converted'
old = {x['id']: x for x in A['std']}

VH, PO, CU, SP = 'vh', 'p', 'c', 's'   # very common, common, custom, specialist
PRFA = {VH: 'فوق‌العاده پرمصرف', PO: 'پرمصرف', CU: 'سفارشی', SP: 'تخصصی'}
COND = [['AF', 'Annealed After Fabrication', 'انیل‌شده پس از ساخت'], ['A', 'Annealed', 'انیل‌شده'], ['CW', 'Cold Worked', 'کار سرد شده'],
        ['SH', 'Strain Hardened', 'کرنش‌سخت‌شده'], ['H', 'Hardened and Tempered', 'سخت‌کاری و تمپر شده'],
        ['HT', 'Hardened and Tempered', 'سخت‌کاری و تمپر شده با شرایط حرارتی متفاوت'], ['AH', 'Age Hardened', 'پیرسخت‌شده']]
SSG = lambda first: [  # F593 / F594 alloy groups
    dict(g='Group 1', m=first, t='استنلس آستنیتی', d='CW', alt='AF, A, SH'), dict(g='Group 2', m='316, 316L', t='استنلس آستنیتی', d='CW', alt='AF, A, SH'),
    dict(g='Group 3', m='321, 347', t='استنلس آستنیتی', d='CW', alt='AF, A, SH'), dict(g='Group 4', m='430', t='استنلس فریتی', d='CW', alt='A'),
    dict(g='Group 5', m='410', t='استنلس مارتنزیتی', d='H', alt='HT'), dict(g='Group 6', m='431', t='استنلس مارتنزیتی', d='H', alt='HT'),
    dict(g='Group 7', m='630 (17-4 PH)', t='استنلس رسوب‌سخت‌شونده', d='AH', alt='H')]
C12 = 'Class 1 / Class 2'
SPEC = [
 dict(cat='a-stud', id='ASTM-A193', rep='ASTM-A193-B7', merge=['ASTM-A193-B7M', 'ASTM-A193-B8M1'], din='ASTM A193/A193M', imp=1,
      fa='استاد بولت و پیچ صنعتی دما و فشار بالا A193',
      long='پیچ و استاد بولت صنعتی فولاد آلیاژی و استنلس استیل مخصوص سرویس‌های فشار و دمای بالا',
      en='Alloy Steel & Stainless Steel Bolts & Studs for High-Temperature, High-Pressure & Special-Purpose Applications',
      grades=[('B7', 'فولاد آلیاژی کروم-مولیبدن', VH, ''), ('B7M', 'فولاد آلیاژی کروم-مولیبدن با سختی کنترل‌شده', PO, ''),
              ('B16', 'فولاد آلیاژی کروم-مولیبدن-وانادیوم', PO, ''), ('B8', 'استنلس استیل 304', VH, C12), ('B8M', 'استنلس استیل 316', VH, C12),
              ('B6', 'استنلس استیل مارتنزیتی 410', PO, ''), ('B8C', 'استنلس استیل 347', CU, ''), ('B8T', 'استنلس استیل 321', CU, '')]),
 dict(cat='a-stud', id='ASTM-A320', rep='ASTM-A320-L7', din='ASTM A320/A320M', imp=1,
      fa='استاد بولت و پیچ صنعتی دمای پایین A320', long='پیچ و استاد بولت صنعتی مخصوص سرویس‌های دمای پایین', en='Low-Temperature Bolts & Studs',
      grades=[('L7', 'فولاد آلیاژی کروم-مولیبدن', VH, ''), ('L7M', 'فولاد آلیاژی کروم-مولیبدن با سختی کنترل‌شده', PO, ''),
              ('L43', 'فولاد آلیاژی نیکل-کروم-مولیبدن', SP, ''), ('B8', 'استنلس استیل 304', PO, C12), ('B8M', 'استنلس استیل 316', PO, C12),
              ('B8C', 'استنلس استیل 347', CU, ''), ('B8T', 'استنلس استیل 321', CU, '')]),
 dict(cat='a-stud', id='ASTM-A307', rep='ASTM-A307-A', din='ASTM A307',
      fa='پیچ و استاد بولت فولاد کربنی A307', long='پیچ و استاد بولت فولاد کربنی با استحکام کششی 60,000 PSI',
      en='Carbon Steel Bolts & Studs — 60,000 PSI Tensile Strength',
      grades=[('Grade A', 'پیچ و استاد بولت فولاد کربنی برای کاربردهای عمومی', '', ''),
              ('Grade B', 'پیچ و استاد بولت فولاد کربنی برای اتصالات فلنجی سیستم‌های لوله‌کشی با فلنج چدنی', '', '')]),
 dict(cat='a-nut', id='ASTM-A194', rep='ASTM-A194-2H', din='ASTM A194/A194M', imp=1,
      fa='مهرهٔ صنعتی دما و فشار بالا A194', long='مهره‌های صنعتی فولاد کربنی، فولاد آلیاژی و استنلس استیل مخصوص سرویس‌های فشار و دمای بالا',
      en='Carbon Steel, Alloy Steel and Stainless Steel Nuts for High-Temperature and High-Pressure Service',
      grades=[('2H', 'فولاد کربنی', VH, ''), ('2HM', 'فولاد کربنی با سختی کنترل‌شده', PO, ''), ('4', 'فولاد آلیاژی مولیبدن‌دار', PO, ''),
              ('7', 'فولاد آلیاژی کروم-مولیبدن', PO, ''), ('7M', 'فولاد آلیاژی کروم-مولیبدن با سختی کنترل‌شده', PO, ''),
              ('8', 'استنلس استیل 304', VH, C12), ('8M', 'استنلس استیل 316', VH, C12), ('8C', 'استنلس استیل 347', CU, ''), ('8T', 'استنلس استیل 321', CU, '')]),
 dict(cat='a-nut', id='ASTM-A563', rep='ASTM-A563-DH', merge=['ASTM-A563-A'], din='ASTM A563',
      fa='مهرهٔ فولاد کربنی و آلیاژی A563', long='مهره‌های صنعتی از فولاد کربنی و فولاد آلیاژی، مخصوص اتصالات عمومی و سازه‌ای',
      en='Carbon Steel & Alloy Steel Nuts for General and Structural Applications',
      grades=[('A', 'فولاد کربنی', '', ''), ('B', 'فولاد کربنی', '', ''), ('C', 'فولاد کربنی', '', ''), ('C3', 'فولاد مقاوم به خوردگی جوی (Weathering Steel)', '', ''),
              ('D', 'فولاد کربنی', '', ''), ('DH', 'فولاد کربنی سخت‌کاری‌شده', '', ''), ('DH3', 'فولاد مقاوم به خوردگی جوی سخت‌کاری‌شده', '', '')]),
 dict(cat='a-struct', id='ASTM-F3125', rep='ASTM-F3125-A325', merge=['ASTM-F3125-A325T3', 'ASTM-F3125-A490', 'ASTM-F3125-F1852', 'ASTM-F3125-F2280'],
      din='ASTM F3125/F3125M', imp=1, fa='پیچ سازه‌ای پرمقاومت F3125',
      long='پیچ‌های سازه‌ای پرمقاومت از فولاد کربنی و فولاد آلیاژی، عملیات حرارتی‌شده، مخصوص اتصالات سازه‌ای فولادی',
      en='High-Strength Heat-Treated Carbon Steel & Alloy Steel Structural Bolts',
      grades=[('A325', 'پیچ شش‌گوش سنگین سازه‌ای — حداقل استحکام کششی 120 ksi', VH, ''), ('A490', 'پیچ شش‌گوش سنگین سازه‌ای — حداقل استحکام کششی 150 ksi', VH, ''),
              ('A325M', 'پیچ شش‌گوش سنگین سازه‌ای متریک — حداقل استحکام کششی 830 MPa', PO, ''), ('A490M', 'پیچ شش‌گوش سنگین سازه‌ای متریک — حداقل استحکام کششی 1040 MPa', PO, ''),
              ('F1852', 'پیچ کنترل کشش (TC Bolt) — 120 ksi', SP, ''), ('F2280', 'پیچ کنترل کشش (TC Bolt) — 150 ksi', SP, ''),
              ('Grade 144', 'پیچ شش‌گوش سنگین یا کنترل کشش — 144 ksi', CU, '')],
      var=dict(t='نوع (جنس)', items=[('T1', 'Type 1', 'فولاد کربنی یا آلیاژی مطابق الزامات گرید', PO), ('T3', 'Type 3', 'فولاد مقاوم به خوردگی جوی (Weathering Steel)', SP)]),
      skuGrades={'A325': ['T1'], 'A490': ['T1']},
      notes=['استاندارد مستقل ASTM F1852 در سال ۲۰۱۶ حذف و در ASTM F3125/F3125M ادغام شده است؛ عنوان فنی صحیح: ASTM F3125 — Grade F1852 — Type 1 / Type 3.',
             'استاندارد مستقل ASTM F2280 هم در سال ۲۰۱۶ در ASTM F3125/F3125M ادغام شده است؛ عنوان فنی صحیح: ASTM F3125 — Grade F2280 — Type 1 / Type 3.',
             'F1852 و F2280 به‌صورت گرید زیرمجموعهٔ F3125 ثبت شده‌اند و نامشان برای جستجوی مشتری حفظ شده است.',
             'F1852 و F2280 «مجموعهٔ پیچ، مهره و واشر» کنترل کشش با انتهای جداشونده (Twist-Off) هستند.']),
 dict(cat='a-washer', id='ASTM-F436', rep='ASTM-F436-1', din='ASTM F436/F436M', imp=1, fa='واشر تخت سخت‌کاری‌شدهٔ سازه‌ای F436',
      long='واشرهای تخت سخت‌کاری‌شده از فولاد کربنی و فولاد مقاوم به خوردگی جوی، مخصوص اتصالات صنعتی و سازه‌ای',
      en='Hardened Carbon Steel & Weathering Steel Washers for Industrial and Structural Applications',
      grades=[('Type 1', 'فولاد کربنی (Carbon Steel)', VH, ''), ('Type 3', 'فولاد مقاوم به خوردگی جوی (Weathering Steel)', SP, '')],
      var=dict(t='شکل واشر (Style)', items=[('CIR', 'Circular', 'واشر تخت گرد', VH), ('BEV', 'Beveled', 'واشر شیب‌دار مربعی یا مستطیلی', VH),
                                            ('CLP', 'Clipped', 'واشر لبه‌بریده', CU), ('XTK', 'Extra Thick', 'واشر تخت ضخیم', CU)]),
      skuGrades={'Type 1': ['CIR', 'BEV']},
      notes=['برخلاف استانداردهای پیچ و مهره، تقسیم‌بندی اصلی واشرها بر اساس Type (جنس) و Style (شکل) است.']),
 dict(cat='a-washer', id='ASTM-F959', rep='ASTM-F959-120', din='ASTM F959/F959M', fa='واشر نشانگر کشش مستقیم (DTI) F959',
      long='واشرهای نشانگر کشش مستقیم از فولاد، مخصوص کنترل نیروی پیش‌تنیدگی پیچ‌های سازه‌ای پرمقاومت',
      en='Steel Direct Tension Indicator Washers (DTI) for High-Strength Structural Bolting',
      grades=[('325-1', 'Type 1 — برای ASTM F3125 Grade A325', '', ''), ('325-3', 'Type 3 (Weathering) — برای ASTM F3125 Grade A325', '', ''),
              ('490-1', 'Type 1 — برای ASTM F3125 Grade A490', '', ''), ('490-3', 'Type 3 (Weathering) — برای ASTM F3125 Grade A490', '', ''),
              ('8.8-1', 'Type 1 — برای ASTM F3125 Grade A325M', '', 'متریک'), ('8.8-3', 'Type 3 (Weathering) — برای ASTM F3125 Grade A325M', '', 'متریک'),
              ('10.9-1', 'Type 1 — برای ASTM F3125 Grade A490M', '', 'متریک'), ('10.9-3', 'Type 3 (Weathering) — برای ASTM F3125 Grade A490M', '', 'متریک')],
      skuGrades={'325-1': ['—'], '325-3': ['—'], '490-1': ['—'], '490-3': ['—']},
      notes=['Type 1: فولاد مخصوص ساخت واشر نشانگر کشش مطابق الزامات استاندارد؛ Type 3: فولاد مقاوم به خوردگی جوی (Weathering Steel).',
             'تیپ‌های متریک (8.8 و 10.9) با استعلام عرضه می‌شوند.']),
 dict(cat='a-anchor', id='ASTM-F1554', rep='ASTM-F1554-36', merge=['ASTM-F1554-55', 'ASTM-F1554-105'], din='ASTM F1554', imp=1,
      fa='انکر بولت و پیچ فونداسیون F1554',
      long='انکربولت‌ها و پیچ‌های فونداسیون از فولاد کربنی، فولاد آلیاژی و فولاد کم‌آلیاژ پرمقاومت، مخصوص مهار سازه‌ها و تجهیزات به فونداسیون بتنی',
      en='Carbon Steel, Alloy Steel & High-Strength Low-Alloy Steel Anchor Bolts for Concrete Foundation Applications',
      grades=[('Grade 36', 'فولاد کربنی — حداقل تنش تسلیم 36 ksi (248 MPa)', PO, ''), ('Grade 55', 'فولاد کربنی یا کم‌آلیاژ — حداقل تنش تسلیم 55 ksi (380 MPa)', PO, ''),
              ('Grade 105', 'فولاد آلیاژی عملیات حرارتی‌شده — حداقل تنش تسلیم 105 ksi (724 MPa)', SP, '')],
      var=dict(t='نوع محصول', items=[('STR', 'Straight Anchor Bolt', 'انکر بولت مستقیم', ''), ('L', 'L-Bent Anchor Bolt', 'انکربولت خمیده L شکل', ''),
                                     ('J', 'J-Bent Anchor Bolt', 'انکربولت خمیده J شکل', ''), ('HD', 'Headed Anchor Bolt', 'انکر بولت سردار', ''),
                                     ('FT', 'Fully Threaded Anchor Rod', 'میل‌رزوهٔ تمام‌رزوه مخصوص فونداسیون', '')]),
      sup=[('S1', 'قابلیت جوشکاری کنترل‌شده برای Grade 55'), ('S2', 'نشانه‌گذاری دائمی سازنده'), ('S3', 'نشانه‌گذاری دائمی گرید'),
           ('S4', 'آزمون ضربه برای Grade 55 و Grade 105')], skuGrades={}),
 dict(cat='a-bolt', id='ASTM-F593', rep='ASTM-F593-304', din='ASTM F593', fa='پیچ و استاد بولت استنلس استیل F593',
      long='پیچ و استاد بولت صنعتی از فولاد زنگ‌نزن (استنلس استیل)، مخصوص اتصالات عمومی و کاربردهای مقاوم به خوردگی',
      en='Stainless Steel Bolts & Studs for General and Corrosion-Resistant Applications',
      ss=SSG('304, 304L, 305, 384 و آلیاژهای مرتبط'), pri={'Group 1': PO, 'Group 2': PO}, skuGrades={'Group 1': ['CW'], 'Group 2': ['CW']}),
 dict(cat='a-bolt', id='ASTM-F594', rep='ASTM-A563-A', din='ASTM F594', fa='مهرهٔ استنلس استیل F594', also='a-nut',
      long='مهره‌های صنعتی از فولاد زنگ‌نزن (استنلس استیل)، مخصوص اتصالات عمومی و کاربردهای مقاوم به خوردگی',
      en='Stainless Steel Nuts for General and Corrosion-Resistant Applications',
      ss=SSG('304, 304L, 305, 384, 302HQ, 304J3, 18-9LW'), pri={}, skuGrades=None),
]
CATS = [('a-stud', 'پیچ و استاد بولت صنعتی'), ('a-nut', 'مهرهٔ صنعتی'), ('a-struct', 'پیچ سازه‌ای'), ('a-washer', 'واشر سازه‌ای'), ('a-anchor', 'انکر بولت'), ('a-bolt', 'پیچ و مهرهٔ استنلس')]

new_std, desc, full, key, own, gl, imgmap = [], {}, {}, {}, {}, {}, {}
for d in SPEC:
    r = json.loads(json.dumps(old[d['rep']]))
    ids = [d['rep']] + d.get('merge', [])
    if 'ss' in d:
        G = [dict(g=x['g'], m=x['m'], t=x['t'], pr=d['pri'].get(x['g'], ''), cls='', d=x['d'], alt=x['alt']) for x in d['ss']]
        sg = d['skuGrades'] if d['skuGrades'] is not None else {x['g']: [x['d']] for x in d['ss']}
    else:
        G = [dict(g=g, m=m, pr=pr, cls=c) for g, m, pr, c in d['grades']]
        sg = d.get('skuGrades')
        if sg is None: sg = {g['g']: ['—'] for g in G if g['pr'] in ('', VH, PO)}
    a = r['astm']
    for k in ('pr', 'nu', 'pa'):
        a[k] = sorted(set(sum((old[x]['astm'][k] for x in ids), [])))
    a.update(code=d['id'][5:], spec=d['din'], grade='، '.join(g['g'] for g in G))
    r.update(id=d['id'], din=d['din'], fa=d['fa'], en=d['en'], cat=d['cat'], equiv=sorted(e for e in set(sum((old[x].get('equiv', []) for x in ids), [])) if not re.match(r'ASTM [AF]\d', e) or (e.split()[1] in d['din'] + ' A325 A490 F1852 F2280' or (e.split()[1].endswith('M') and e.split()[1][:-1] in d['din'] and d['id'] != 'ASTM-F594'))),
             ag=dict(long=d['long'], imp=bool(d.get('imp')), grades=G, var=d.get('var') and dict(t=d['var']['t'], items=[dict(c=c, en=e, fa=f, pr=p) for c, e, f, p in d['var']['items']]),
                     sup=d.get('sup'), notes=d.get('notes', []), cond=COND if 'ss' in d else None, also=d.get('also')), sg=sg)
    al = set(r.get('aliases') or [])
    for x in ids: al.update(old[x].get('aliases') or [])
    al.update([g['g'] for g in G]); al.add(d['din'].replace('ASTM ', '')); al.add(d['din'].split('/')[0].replace('ASTM ', ''))
    r['aliases'] = sorted(al)
    new_std.append(r)
    desc[d['id']] = d['long'] + '. ' + A['desc'].get(d['rep'], '')
    if d['rep'] in A['full']: full[d['id']] = A['full'][d['rep']]
    if d['rep'] in A['key']: key[d['id']] = A['key'][d['rep']]
    own[d['id']] = dict(fa=d['fa'], g=[g['g'] for g in G], bz=[])
    for g in G: gl[g['g']] = dict(fa=g['g'] + ' — ' + (g.get('m') or ''), short=g['g'])
    imgmap[d['id']] = d['rep']
A.update(std=new_std, desc=desc, full=full, key=key, own=own, gl=gl, prfa=PRFA, cats=CATS)
L[i] = 'const ASTM=' + json.dumps(A, ensure_ascii=False) + ';'
s = '\n'.join(L)

def R(o, n, c=1):
    global s
    assert s.count(o) == c, (o[:80], s.count(o)); s = s.replace(o, n)
# images: new ids use the photos and drawings of the product they replace
fi = s.index('const FEIMG=KSU({'); fk = s.index('}); /* per-standard photo', fi) + 3
s = s[:fk] + "Object.entries(" + json.dumps(imgmap) + ").forEach(([n,o])=>{if(FEIMG[o])FEIMG[n]=FEIMG[o]});" + s[fk:]
R("STD.forEach(s=>{if(s.astm){s._key=ASTM.key[s.id]||null;",
  "Object.assign(GRADES,ASTM.gl);\n"
  "STD.forEach(s=>{if(s.astm&&s.sg)s.grades=Object.keys(s.sg).length?s.sg:{'—':['—']};if(s.ag)s.aliases=[...new Set([...(s.aliases||[]),...s.ag.grades.map(g=>g.g).filter(g=>/[a-z]/i.test(g)&&g.length>=2),...(s.ag.var?s.ag.var.items.map(v=>v.en):[])])]});\n"
  "STD.forEach(s=>{if(s.astm){s._key=ASTM.key[s.id]||null;")
# categories: the six groups of the workbook, in its order
cs = s.index("{id:'a-struct',fa:'پیچ و مهرهٔ سازه‌ای ASTM'")
ce = s.index('];', cs)
s = s[:cs] + ','.join("{id:'%s',fa:'%s',g:'%s',fam:'astm'}" % (c, f, {'a-stud': 'p-stud', 'a-anchor': 'p-stud', 'a-nut': 'p-nut', 'a-washer': 'p-washer'}.get(c, 'p-hex')) for c, f in CATS) + s[ce:]
# product codes: a variant code takes the finish slot; «—» is left out of the code
R("function techCode(sid,size,len,grade,fin){return `${sid}-${size}${len?'X'+fmtL(len):''}`+(grade==='—'?'':`-${grade}-${fin}`)}",
  "function techCode(sid,size,len,grade,fin){return `${sid}-${size}${len?'X'+fmtL(len):''}`+(grade==='—'?'':`-${String(grade).replace(/\\s+/g,'')}`+(fin&&fin!=='—'?`-${fin}`:''))}")
R("const FINISH={ZN:'گالوانیزه سرد',HDG:'گالوانیزه گرم',BK:'سیاه',PL:'بدون پوشش','—':'جنس و پوشش در استعلام'};",
  "const FINISH={ZN:'گالوانیزه سرد',HDG:'گالوانیزه گرم',BK:'سیاه',PL:'بدون پوشش','—':'جنس و پوشش در استعلام',T1:'Type 1 (فولاد کربنی یا آلیاژی)',T3:'Type 3 (Weathering)',CIR:'Circular — واشر تخت گرد',BEV:'Beveled — واشر شیب‌دار',CW:'Condition CW (کار سرد)',H:'Condition H',AH:'Condition AH'};")
# search test set: the merged products
for o, n in [("{std:'ASTM-F3125-A325',size:'3/4'}", "{std:'ASTM-F3125',size:'3/4'}"), ("{std:'ASTM-F3125-A490'}", "{std:'ASTM-F3125'}"),
             ("{std:'ASTM-A193-B7',", "{std:'ASTM-A193',"), ("{std:'ASTM-F436-1'}", "{std:'ASTM-F436'}")]:
    R(o, n)
open(P, 'w', encoding='utf-8').write(s)
print('ASTM products', len(new_std))
