"""Match DIN parents to the REYHER catalogue drawings and embed them in a sheet.

data/drawings/reyher/images_index.csv lists one drawing per catalogue entry
(standard, title, page, REYHER article codes). A standard can have several
drawings, one per form; the form is named in the title as "A = without
chamfer", "ISR = hexalobular socket", ... and is matched to the parent's form
(DIN125A -> A, DIN912TX -> ISR, DIN6797J -> I). "(~similar)" in the catalogue
means the drawing shows a close variant, not the exact standard.
"""

import csv
import os
import re

from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.styles import Alignment
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "drawings", "reyher")
INDEX = os.path.join(DIR, "images_index.csv")

MAX_W, MAX_H = 150, 80  # px inside the sheet cell
PAD = 6  # px around the image
CODE = re.compile(r"(?:^|[\s,~])([A-Z][A-Za-z]{0,2}) =")
# parent form suffix -> catalogue form codes
SUFFIX = {"tx": "ISR", "j": "I"}


def load():
    out = {}
    with open(INDEX, encoding="utf-8-sig") as f:
        for i, r in enumerate(csv.DictReader(f)):
            m = re.match(r"DIN (\d+)", r["standard"])
            if not m:
                continue
            r["order"] = i
            r["similar"] = "similar" in r["standard"]
            r["codes"] = set(CODE.findall(r["title"]))
            out.setdefault(m.group(1), []).append(r)
    return out


def wanted(form):
    if not form:
        return set()
    if form in SUFFIX:
        return {SUFFIX[form]}
    if form.endswith("tx"):
        return {form[:-2].upper(), "ISR"}
    if form.endswith("sq"):
        return {form[:-2].upper()}
    return {form.upper()}


def match(standard, catalogue):
    """'DIN 125 a' -> (catalogue row, match label) or (None, '')."""
    m = re.match(r"DIN (\d+)\s*(\S*)", standard)
    cands = catalogue.get(m.group(1)) if m else None
    if not cands:
        return None, ""
    want = wanted(m.group(2).lower())

    def score(r):
        hit = len(want & r["codes"])
        return (-hit, r["similar"], "*" in r["title"], len(r["codes"]), r["order"])

    best = min(cands, key=score)
    hit = want & best["codes"]
    if not want:
        label = "استاندارد"
    elif hit == want:
        label = "فرم دقیق"
    elif hit:
        label = "فرم نزدیک"
    else:
        label = "استاندارد (فرم دیگر)"
    if best["similar"]:
        label += " · مشابه"
    return best, label


def annotate(standards):
    """Add drawing fields to each parent dict; return number matched."""
    catalogue = load()
    n = 0
    for s in standards:
        r, label = match(s["standard"], catalogue)
        s["drawing"] = ""
        s["drawing_file"] = r["image_file"] if r else ""
        s["drawing_title"] = r["title"] if r else ""
        s["drawing_match"] = label or "بدون نقشه"
        s["reyher_codes"] = r["reyher_codes"] if r else ""
        n += bool(r)
    return n


def embed(ws, col, file_col):
    """Place the image named in `file_col` into column `col` of each data row."""
    ws.column_dimensions[get_column_letter(col)].width = (MAX_W + 2 * PAD) / 7
    for row in range(2, ws.max_row + 1):
        name = ws.cell(row=row, column=file_col).value
        if not name:
            continue
        img = XLImage(os.path.join(DIR, "images", name))
        k = min(MAX_W / img.width, MAX_H / img.height, 1.0)
        w, h = round(img.width * k), round(img.height * k)
        img.width, img.height = w, h
        marker = AnchorMarker(
            col=col - 1,
            colOff=pixels_to_EMU(PAD + (MAX_W - w) // 2),
            row=row - 1,
            rowOff=pixels_to_EMU(PAD + (MAX_H - h) // 2),
        )
        size = XDRPositiveSize2D(pixels_to_EMU(w), pixels_to_EMU(h))
        img.anchor = OneCellAnchor(_from=marker, ext=size)
        ws.add_image(img)
        ws.row_dimensions[row].height = (MAX_H + 2 * PAD) * 0.75
        for cell in ws[row]:
            cell.alignment = Alignment(vertical="center", wrap_text=cell.alignment.wrap_text)
