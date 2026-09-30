"""Parse cached mechtool.cn standard pages into length/weight matrices.

mechtool.cn publishes the Chinese GB/T fastener standards (most are identical
to ISO / DIN) with a "质量 kg" table: nominal length rows x size columns,
filled with the weight per 1000 steel pieces. A filled cell means that
size x length combination is part of the standard's commercial range.
Many pages also carry an "l 的范围" (length range) column that we keep as a
cross-check.

Usage: python3 scripts/parse_mechtool.py <cache_dir> -> data/external/mechtool/*.json
"""
import glob
import json
import os
import re
import sys

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "external", "mechtool")
BASE = "https://www.mechtool.cn/stdboltsandnuts/"

SIZE_HDR = re.compile(r"^(螺纹规格|公称直径|公称规格|规格|d\b)")


def clean(t):
    t = re.sub(r"\s+", "", t.replace("\xa0", " "))
    return t.replace("Φ", "").replace("φ", "")


def num(t):
    t = clean(t).strip("()（）")
    try:
        return float(t)
    except ValueError:
        return None


def norm_size(t):
    t = clean(t)
    nonpref = t.startswith(("(", "（"))
    t = t.strip("()（）")
    t = t.replace("×", "X").replace("x", "X")
    return t, nonpref


def mass_matrix(table):
    """Return {size: {length: weight}} from a 质量 table."""
    out, sizes = {}, []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if not cells:
            continue
        if SIZE_HDR.match(clean(cells[0])) and len(cells) > 1:
            sizes = [norm_size(c) for c in cells[1:]]
            continue
        L = num(cells[0])
        if L is None or not sizes:
            continue
        for (s, _), w in zip(sizes, cells[1:]):
            if not s:
                continue
            wv = num(w)
            if wv is not None:
                out.setdefault(s, {})[L] = wv
    return out


def ranges(table):
    """Return {size: [lmin, lmax]} from a row-per-size table with a range cell."""
    out = {}
    for tr in table.find_all("tr"):
        cells = [clean(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        s, _ = norm_size(cells[0])
        if not re.match(r"^(M|ST|\d)", s):
            continue
        m = re.match(r"^(\d+(?:\.\d+)?)[～~\-](\d+(?:\.\d+)?)$", cells[-1])
        if m:
            out[s] = [float(m.group(1)), float(m.group(2))]
    return out


def parse(path):
    s = BeautifulSoup(open(path, encoding="utf-8", errors="ignore").read(), "lxml")
    lead = s.find(class_="bd-lead")
    title = lead.get_text(strip=True) if lead else ""
    m = re.search(r"GB(?:/T)?\s*[\d.]+", title)
    res = {"title": title, "gb": m.group(0).replace(" ", "") if m else "",
           "url": BASE + os.path.basename(path), "mass": {}, "range": {}}
    for t in s.find_all("table"):
        first = clean(t.get_text(" ", strip=True)[:20])
        if first.startswith("质量"):
            for k, v in mass_matrix(t).items():
                res["mass"].setdefault(k, {}).update(v)
        else:
            res["range"].update(ranges(t))
    return res


def main(cache):
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for f in sorted(glob.glob(os.path.join(cache, "stdboltsandnuts_*.html"))):
        r = parse(f)
        if not r["mass"] and not r["range"]:
            continue
        name = os.path.basename(f)[len("stdboltsandnuts_"):-5]
        r["mass"] = {k: {("%g" % L): w for L, w in sorted(v.items())} for k, v in r["mass"].items()}
        json.dump(r, open(os.path.join(OUT, name + ".json"), "w"), ensure_ascii=False, indent=1)
        n += 1
    print("pages with length data:", n)


if __name__ == "__main__":
    main(sys.argv[1])
