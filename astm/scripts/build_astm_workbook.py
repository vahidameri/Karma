"""Build output/ASTM_fasteners.xlsx — ASTM bolts, nuts, washers: index, properties,
dimensions, compatibility, drawings and a parent/SKU list. ASTM content only.

Sources: public summaries of ASTM documents (see sheet «منابع»).
ASTM texts are copyrighted; values here are reference data and must be checked
against the purchased edition before procurement or design.
"""
import os
import sys
from fractions import Fraction

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(__file__))
from astm_drawings import build_all  # noqa: E402

OUT = "astm/ASTM_fasteners.xlsx"
DWG_DIR = "astm/drawings"

FONT = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F2A44")
SUB_FILL = PatternFill("solid", fgColor="DFE6EE")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
WARN_FILL = PatternFill("solid", fgColor="FDEBD0")
GONE_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFC7D1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


# --------------------------------------------------------------------------- helpers

def frac(x):
    """1.375 -> '1-3/8'"""
    f = Fraction(x).limit_denominator(64)
    whole, rem = divmod(f.numerator, f.denominator)
    if rem == 0:
        return f"{whole}"
    r = Fraction(rem, f.denominator)
    return f"{whole}-{r}" if whole else f"{r}"


def write_table(ws, headers, rows, start_row=1, widths=None, wrap_cols=(), freeze=True, number_formats=None):
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=start_row, column=c, value=h)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF", size=10)
        cell.fill = HDR_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    for r, row in enumerate(rows, start_row + 1):
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = Font(name=FONT, size=10)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=(c in wrap_cols))
            if number_formats and c in number_formats:
                cell.number_format = number_formats[c]
    ws.row_dimensions[start_row].height = 34
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    if freeze:
        ws.freeze_panes = ws.cell(row=start_row + 1, column=2)
    ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(headers))}{start_row + len(rows)}"
    return start_row + len(rows)


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, bold=True, size=14, color="1F2A44")
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=FONT, italic=True, size=9, color="555555")


# --------------------------------------------------------------------------- data

# Designation, Title (EN), عنوان فارسی, Category, Product forms, Material / heat treatment,
# Grades / classes, Size range, Key strength, Status, Replaced by / note,
# Dimension standard, Mating nut, Washer, Typical applications, Marking, Drawing
STANDARDS = [
    # ---- structural
    ("ASTM F3125/F3125M", "High Strength Structural Bolts and Assemblies, Steel and Alloy Steel, Heat Treated, Inch Dimensions 120 ksi and 150 ksi Minimum Tensile Strength, and Metric Dimensions 830 MPa and 1040 MPa",
     "پیچ‌های سازه‌ای پر‌مقاومت (جایگزین A325/A490/F1852/F2280)", "Structural bolt", "Heavy hex bolt; round-head twist-off (TC) bolt",
     "Medium-carbon / alloy steel (Type 1), weathering steel (Type 3); quenched & tempered",
     "A325, A325M, A490, A490M, F1852, F2280; Types 1 & 3", "1/2–1-1/2 in · M12–M36", "A325: 120 ksi min · A490: 150–173 ksi · A325M: 830 MPa · A490M: 1040–1210 MPa",
     "Active", "Consolidated A325, A325M, A490, A490M, F1852, F2280 (2015)", "—", "A563 C, C3, D, DH, DH3; A194 2H (heavy hex)", "F436 / F436M; F959 DTI",
     "Steel buildings, bridges, slip-critical & pretensioned joints", "Grade (A325, A490, F1852, F2280 …) + mfr ID; Type 3 grade underlined", "DWG-01, DWG-07, DWG-10, DWG-11"),
    ("ASTM A325", "Structural Bolts, Steel, Heat Treated, 120/105 ksi Minimum Tensile Strength", "پیچ سازه‌ای A325", "Structural bolt", "Heavy hex bolt",
     "Medium carbon steel, Q&T", "Type 1, Type 3", "1/2–1-1/2 in", "120 ksi (≤1 in), 105 ksi (>1 in) — legacy", "Withdrawn (2016)", "→ F3125 Grade A325 (now 120 ksi all sizes)",
     "—", "A563 C/D/DH, A194 2H", "F436", "Legacy drawings & specs still call it out", "A325 + mfr ID", "DWG-01"),
    ("ASTM A325M", "Structural Bolts, Steel, Heat Treated 830 MPa Minimum Tensile Strength [Metric]", "پیچ سازه‌ای متریک A325M", "Structural bolt", "Heavy hex bolt",
     "Carbon steel Q&T", "Type 1, Type 3", "M12–M36", "830 MPa", "Withdrawn (2016)", "→ F3125M Grade A325M", "—", "A563M 10S / 10S3", "F436M", "Metric structural steel", "A325M + mfr ID", "DWG-01"),
    ("ASTM A490", "Structural Bolts, Alloy Steel, Heat Treated, 150 ksi Minimum Tensile Strength", "پیچ سازه‌ای A490", "Structural bolt", "Heavy hex bolt",
     "Alloy steel Q&T", "Type 1, Type 3", "1/2–1-1/2 in", "150–173 ksi", "Withdrawn (2016)", "→ F3125 Grade A490", "—", "A563 DH/DH3, A194 2H", "F436", "High-load structural joints", "A490 + mfr ID", "DWG-01"),
    ("ASTM A490M", "High-Strength Steel Bolts, Classes 10.9 and 10.9.3, for Structural Steel Joints [Metric]", "پیچ سازه‌ای متریک A490M", "Structural bolt", "Heavy hex bolt",
     "Alloy steel Q&T", "10.9, 10.9.3", "M12–M36", "1040–1210 MPa", "Withdrawn (2016)", "→ F3125M Grade A490M", "—", "A563M 10S / 10S3", "F436M", "Metric structural steel", "A490M + mfr ID", "DWG-01"),
    ("ASTM F1852", "\"Twist Off\" Type Tension Control Structural Bolt/Nut/Washer Assemblies, Steel, Heat Treated, 120/105 ksi", "پیچ کنترل کشش (TC) ۱۲۰ ksi", "Structural bolt", "Round-head twist-off assembly",
     "Carbon / alloy steel Q&T", "Type 1, Type 3", "1/2–1-1/8 in", "120 ksi", "Withdrawn (2016)", "→ F3125 Grade F1852", "—", "A563 DH (supplied)", "F436 (supplied)", "Fast installation without torque wrench", "F1852 + mfr ID", "DWG-07"),
    ("ASTM F2280", "\"Twist Off\" Type Tension Control Structural Bolt/Nut/Washer Assemblies, Steel, Heat Treated, 150 ksi", "پیچ کنترل کشش (TC) ۱۵۰ ksi", "Structural bolt", "Round-head twist-off assembly",
     "Alloy steel Q&T", "Type 1, Type 3", "1/2–1-1/8 in", "150–173 ksi", "Withdrawn (2016)", "→ F3125 Grade F2280", "—", "A563 DH (supplied)", "F436 (supplied)", "High-strength TC installation", "F2280 + mfr ID", "DWG-07"),
    ("ASTM F3148", "High Strength Structural Bolt Assemblies, Steel and Alloy Steel, Heat Treated, 144 ksi Minimum Tensile Strength, Inch Dimensions", "مجموعه پیچ سازه‌ای Grade 144", "Structural bolt", "Heavy hex / TC assemblies (combined method)",
     "Alloy steel Q&T", "Grade 144, Types 1 & 3", "1/2–1-1/4 in (verify)", "144 ksi min", "Active", "Combined-method pretensioning assemblies", "Per spec", "Supplied as assembly", "Supplied as assembly", "Structural joints where higher than A325 is needed", "144 + mfr ID", "DWG-07"),
    ("ASTM F3043", "\"Twist Off\" Type Tension Control Structural Bolt/Nut/Washer Assemblies, Alloy Steel, Heat Treated, 200 ksi Minimum Tensile Strength", "مجموعه TC آلیاژی ۲۰۰ ksi", "Structural bolt", "TC assembly",
     "Alloy steel Q&T", "Grade 1, Grade 2", "1 – 1-1/2 in (verify)", "200 ksi min", "Active", "Use only per engineer approval (HE sensitive, no coatings except per spec)", "Per spec", "Supplied", "Supplied", "Very high-load structural (special)", "Per spec", "DWG-07"),
    ("ASTM F3111", "Heavy Hex Structural Bolt/Nut/Washer Assemblies, Alloy Steel, Heat Treated, 200 ksi Minimum Tensile Strength", "مجموعه پیچ سنگین آلیاژی ۲۰۰ ksi", "Structural bolt", "Heavy hex assembly",
     "Alloy steel Q&T", "Grade 1", "1 – 1-1/2 in (verify)", "200 ksi min", "Active", "Special use", "Per spec", "Supplied", "Supplied", "Very high-load structural (special)", "Per spec", "DWG-01"),
    # ---- general purpose
    ("ASTM A307", "Carbon Steel Bolts, Studs, and Threaded Rod 60 000 PSI Tensile Strength", "پیچ، استاد و میله رزوه‌ای فولاد کربنی ۶۰ ksi", "General bolt", "Hex bolt, heavy hex (Gr B), studs, threaded rod, bent bolts",
     "Low-carbon steel, not heat treated", "Grade A (general), Grade B (flanged joints, cast iron piping)", "1/4–4 in", "60 ksi min (Gr B: 60–100 ksi)", "Active", "Grade C moved to F1554 Gr 36 (2007)", "—", "A563 A (hex / heavy hex)", "F844", "General construction, timber, light steel, piping flanges (Gr B)", "307A / 307B + mfr ID", "DWG-02"),
    ("ASTM A449", "Hex Cap Screws, Bolts and Studs, Steel, Heat Treated, 120/105/90 ksi Minimum Tensile Strength, General Use", "پیچ، پیچ کلاهک و استاد عملیات حرارتی شده", "General bolt", "Hex cap screw, hex bolt, studs, rod",
     "Medium carbon steel Q&T", "Type 1 (Type 2 withdrawn)", "1/4–3 in", "120 / 105 / 90 ksi by size", "Active", "Type 2 withdrawn", "—", "A563 (grade per size)", "F436 / F844", "Machinery, anchor rods (non-structural), general high strength", "3 radial lines (± A449) + mfr ID", "DWG-02"),
    ("ASTM A354", "Quenched and Tempered Alloy Steel Bolts, Studs, and Other Externally Threaded Fasteners", "پیچ و استاد فولاد آلیاژی Q&T", "General bolt", "Bolts, studs, rod",
     "Alloy steel Q&T", "BC, BD", "1/4–4 in", "BC 125/115 ksi · BD 150/140 ksi", "Active", "BD used for high-strength anchor rods", "—", "BC: A563 C/DH · BD: A563 DH, A194 2H", "F436", "Anchor rods, machinery, high-load fasteners", "BC / BD + mfr ID", "DWG-02"),
    ("ASTM A394", "Steel Transmission Tower Bolts, Zinc-Coated and Bare", "پیچ دکل انتقال نیرو", "Tower bolt", "Hex head bolts with hex nuts",
     "Low/medium carbon (Type 0), Q&T (Type 1), weathering (Type 3)", "Type 0, 1, 3", "1/2–1 in", "Type 0: 74 ksi · Type 1/3: 120 ksi", "Active", "", "—", "A563 (per type)", "—", "Lattice transmission towers, substations", "Type mark + mfr ID", "DWG-02"),
    ("ASTM F1554", "Anchor Bolts, Steel, 36, 55, and 105-ksi Yield Strength", "میل مهار (انکر بولت) ۳۶/۵۵/۱۰۵", "Anchor rod", "Headed, bent (L/J), straight threaded rods",
     "Carbon / alloy steel; Gr 105 Q&T", "Grade 36, 55 (S1 weldable), 105", "1/2–4 in", "Yield 36 / 55 / 105 ksi", "Active", "Replaces A307 Gr C for anchor rods", "—", "A563 A/D/DH, A194 2H (per grade/finish)", "F436 / plate washers", "Column base plates, equipment foundations", "End paint: blue/yellow/red or stamped grade", "DWG-06, DWG-10"),
    ("ASTM A687", "High-Strength Nonheaded Steel Bolts and Studs", "میله / استاد پرمقاومت بدون سر", "Anchor rod", "Studs / rods",
     "Q&T steel", "—", "5/8–3 in", "150 ksi", "Withdrawn (1999)", "→ F1554 Gr 105 / A354 BD", "—", "—", "—", "Legacy anchor rods", "—", ""),
    # ---- pressure / temperature
    ("ASTM A193/A193M", "Alloy-Steel and Stainless Steel Bolting for High Temperature or High Pressure Service and Other Special Purpose Applications", "پیچ و استاد دما/فشار بالا", "Pressure bolting", "Stud bolts, hex bolts, threaded rod",
     "Cr-Mo alloy Q&T (B7, B7M, B16); austenitic SS (B8, B8M, Cl 1 solution treated / Cl 2 strain hardened)", "B5, B6, B7, B7M, B16, B8, B8C, B8M, B8T … Class 1/1A/2/2B", "1/4–7 in (varies)", "B7: 125/115/100 ksi by size", "Active", "", "—", "A194 (2H for B7, 2HM for B7M, 8/8M for B8/B8M)", "F436 / through-hardened", "Flanges, valves, pressure vessels, refinery & petrochemical", "B7, B7M, B8 … on end/head + mfr ID", "DWG-05, DWG-10"),
    ("ASTM A320/A320M", "Alloy-Steel and Stainless Steel Bolting for Low-Temperature Service", "پیچ و استاد دمای پایین", "Pressure bolting", "Stud bolts, bolts",
     "Alloy steel Q&T with Charpy impact; austenitic SS", "L7, L7A, L7B, L7C, L7M, L43, L1, B8 Cl1/2 …", "1/4–4 in (varies)", "L7: 125 ksi ≤2-1/2 in", "Active", "Impact tested at −150 °F (L7) / −100 °F (L7M)", "—", "A194 4 or 7 (S3 impact), 7M for L7M", "F436", "Cryogenic / LNG / cold-climate flanges", "L7, L7M … + mfr ID", "DWG-05"),
    ("ASTM A453/A453M", "High-Temperature Bolting, with Expansion Coefficients Comparable to Austenitic Stainless Steels", "پیچ دمای بالا (سوپر آلیاژ آهنی)", "Pressure bolting", "Bolts, studs",
     "Precipitation-hardened Fe-Ni-Cr (A-286 etc.)", "Grade 651, 660 (Class A, B, C, D), 662, 665", "per grade", "Gr 660: 130 ksi", "Active", "", "—", "A194 / same alloy", "—", "Gas turbines, high-temp joints", "Grade + class", ""),
    ("ASTM A437/A437M", "Stainless and Alloy-Steel Turbine-Type Bolting Specially Heat Treated for High-Temperature Service", "پیچ توربین دمای بالا", "Pressure bolting", "Bolts, studs",
     "Cr-Mo-V alloy, special HT", "B4B, B4C, B4D", "per grade", "per grade", "Active", "", "—", "A437 nuts", "—", "Steam turbines", "Grade", ""),
    ("ASTM A540/A540M", "Alloy-Steel Bolting for Special Applications", "پیچ آلیاژی کاربرد خاص", "Pressure bolting", "Bolts, studs",
     "Ni-Cr-Mo alloy Q&T", "B21, B22, B23, B24, B24V (Classes 1–5)", "per grade", "per class", "Active", "", "—", "A540 nuts", "—", "Nuclear & special high-strength bolting", "Grade + class", ""),
    ("ASTM A962/A962M", "Common Requirements for Bolting Intended for Use at Any Temperature from Cryogenic to the Creep Range", "الزامات مشترک پیچ‌های فشار", "General requirements", "—",
     "—", "—", "—", "—", "Active", "Umbrella spec for A193, A194, A320, A453 …", "—", "—", "—", "Ordering, testing, marking rules", "—", ""),
    # ---- socket & special
    ("ASTM A574", "Alloy Steel Socket-Head Cap Screws", "پیچ آلن سر استوانه‌ای (آلیاژی)", "Socket screw", "Socket head cap screw",
     "Alloy steel Q&T", "—", "#0–4 in", "180 ksi (≤1/2 in) · 170 ksi (>1/2 in)", "Active", "Metric version: ASTM A574M", "—", "—", "—", "Machinery, dies, tooling", "Mfr ID (+ grade on some)", "DWG-09"),
    ("ASTM F835", "Alloy Steel Socket Button and Flat Countersunk Head Cap Screws", "پیچ آلن سر گرد و سر خزینه", "Socket screw", "Button / flat head socket screws",
     "Alloy steel Q&T", "—", "#0–1 in (verify)", "145 ksi (approx.)", "Active", "", "—", "—", "—", "Machinery covers, flush mounting", "Mfr ID", "DWG-09"),
    ("ASTM F912", "Alloy Steel Socket Set Screws", "پیچ آلن تخت (مغزی)", "Socket screw", "Socket set screw (cup, flat, cone, dog points)",
     "Alloy steel Q&T", "—", "#0–1-1/2 in", "Hardness HRC 45–53", "Active", "", "—", "—", "—", "Pulleys, collars, shafts", "—", ""),
    ("ASTM F541", "Alloy Steel Eyebolts", "پیچ چشمی آلیاژی", "Lifting", "Forged eyebolts (shoulder / plain)",
     "Alloy steel forged Q&T", "Type 1, 2 …", "1/4–2-1/2 in", "per size (WLL)", "Active", "", "—", "—", "—", "Lifting & rigging", "Mfr + WLL", ""),
    ("ASTM A489", "Carbon Steel Lifting Eyes", "چشمی بالابر فولاد کربنی", "Lifting", "Eyebolts, eye nuts",
     "Carbon steel forged", "Type 1, 2", "1/4–2-1/2 in", "per size (WLL)", "Active", "", "—", "—", "—", "Lifting", "Mfr + WLL", ""),
    # ---- stainless & non-ferrous
    ("ASTM F593", "Stainless Steel Bolts, Hex Cap Screws, and Studs", "پیچ و استاد استنلس استیل", "Stainless bolt", "Hex bolts, cap screws, studs, socket screws",
     "Austenitic (303/304/305/316…), martensitic, PH (630), duplex", "Alloy Groups 1–7; Conditions A, AF, CW, SH, H, AH", "1/4–1-1/2 in", "Gr1/2 CW1: 100–150 ksi · CW2: 85–140 ksi", "Active", "Metric ASTM F738M withdrawn", "—", "F594 (same group)", "Stainless F844-style", "Corrosive environments, food, marine", "F593 + group/condition letter + mfr ID", "DWG-10"),
    ("ASTM F594", "Stainless Steel Nuts", "مهره استنلس استیل", "Nut", "Hex, heavy hex, jam nuts",
     "Austenitic / martensitic / PH", "Alloy Groups 1–7; Conditions A, CW …", "1/4–1-1/2 in", "Proof per group & condition", "Active", "", "—", "—", "—", "Mates with F593", "F594 + group + mfr ID", "DWG-03"),
    ("ASTM F738M", "Stainless Steel Metric Bolts, Screws, and Studs", "پیچ استنلس متریک", "Stainless bolt", "Metric bolts",
     "Austenitic SS", "A1-50 … A4-80", "M1.6–M36", "500/700/800 MPa", "Withdrawn (verify)", "No ASTM successor", "—", "F836M", "—", "—", "—", ""),
    ("ASTM F468", "Nonferrous Bolts, Hex Cap Screws, Socket Head Cap Screws, and Studs for General Use", "پیچ غیرآهنی (مس، نیکل، آلومینیوم، تیتانیوم)", "Nonferrous bolt", "Bolts, screws, studs",
     "Cu alloys (brass, Si-bronze, Al-bronze), Ni (Monel, Inconel), Al, Ti", "Alloy designations per table (e.g. 651, 655, 400, 625, 2024-T4, Ti Gr 2/5)", "1/4–1-1/2 in", "per alloy", "Active", "", "—", "F467", "—", "Marine, chemical, non-magnetic, electrical", "Alloy mark + mfr ID", ""),
    ("ASTM F467", "Nonferrous Nuts for General Use", "مهره غیرآهنی", "Nut", "Hex nuts", "Cu, Ni, Al, Ti alloys", "per alloy", "1/4–1-1/2 in", "per alloy", "Active", "", "—", "—", "—", "Mates with F468", "Alloy mark", "DWG-03"),
    ("ASTM F568M", "Carbon and Alloy Steel Externally Threaded Metric Fasteners", "پیچ متریک فولادی (کلاس 4.6 تا 12.9)", "General bolt", "Metric bolts, screws, studs",
     "Carbon / alloy steel", "Property classes 4.6, 4.8, 5.8, 8.8, 9.8, 10.9, 12.9", "M1.6–M100", "400–1200 MPa", "Withdrawn (2012)", "No ASTM successor", "—", "A563M", "F436M", "—", "Class number", ""),
    # ---- nuts
    ("ASTM A563/A563M", "Carbon and Alloy Steel Nuts (Inch and Metric)", "مهره فولاد کربنی و آلیاژی", "Nut", "Hex, heavy hex, square, hex jam",
     "Carbon steel; C/D/DH Q&T; C3/DH3 weathering", "O, A, B, C, C3, D, DH, DH3 · Metric: 5, 9, 10, 12, 8S, 8S3, 10S, 10S3", "1/4–4 in · M6–M100", "Proof 69–175 ksi", "Active", "A563M merged into A563/A563M (2021)", "—", "—", "—", "Mates with A307, A449, F3125, F1554 …", "Grade mark (C, D, DH …) + mfr ID", "DWG-03, DWG-10"),
    ("ASTM A194/A194M", "Carbon Steel, Alloy Steel, and Stainless Steel Nuts for Bolts for High Pressure or High Temperature Service, or Both", "مهره دما / فشار بالا", "Nut", "Heavy hex nuts",
     "Carbon Q&T (2H), alloy (4, 7), SS (8, 8M)…", "1, 2, 2H, 2HM, 3, 4, 6, 7, 7M, 8, 8M, 8T, 9, 16 …", "1/4–4 in (heavy hex)", "2H: proof 175 ksi", "Active", "", "—", "—", "—", "Mates with A193, A320, also F3125 & F1554", "Grade (2H, 2HM, 8 …) + mfr ID", "DWG-03, DWG-05, DWG-10"),
    # ---- washers & DTI
    ("ASTM F436/F436M", "Hardened Steel Washers Inch and Metric Dimensions", "واشر سخت‌کاری شده سازه‌ای", "Washer", "Circular, clipped, bevelled square (1:6) washers",
     "Carbon steel through-hardened (Type 1); weathering (Type 3)", "Type 1, Type 3", "1/4–4 in · M12–M100", "HRC 38–45 (26–45 if HDG)", "Active", "", "Spec tables", "—", "—", "Under turned element in pretensioned joints; oversized/slotted holes", "F436 + mfr ID", "DWG-04"),
    ("ASTM F844", "Washers, Steel, Plain (Flat), Unhardened for General Use", "واشر تخت معمولی (سخت نشده)", "Washer", "Plain flat washers (narrow / regular / wide)",
     "Carbon steel, unhardened", "—", "#4–3 in (verify)", "—", "Active", "", "—", "—", "—", "With A307 / general bolting", "—", "DWG-04"),
    ("ASTM F959/F959M", "Compressible-Washer-Type Direct Tension Indicators for Use with Structural Fasteners", "واشر نشانگر کشش مستقیم (DTI)", "Washer", "DTI washer with protrusions",
     "Carbon steel Q&T; Type 3 weathering", "Type 120, 150 (inch) · 8.8, 10.9 (metric)", "1/2–1-1/2 in · M12–M36", "Gap per bolt grade", "Active", "", "Spec tables", "—", "—", "Verifying pretension in A325/A490 joints", "Type + mfr ID", "DWG-08"),
    # ---- coatings
    ("ASTM F2329/F2329M", "Zinc Coating, Hot-Dip, Requirements for Application to Carbon and Alloy Steel Bolts, Screws, Washers, Nuts, and Special Threaded Fasteners", "گالوانیزه گرم (غوطه‌وری) اتصالات", "Coating", "—",
     "Zinc", "—", "—", "Avg ≥ 2.1 mil (53 µm) (verify)", "Active", "Supersedes A153 Class C for fasteners", "—", "Nuts overtapped (A563 Annex)", "—", "Outdoor structural, towers", "—", ""),
    ("ASTM A153/A153M", "Zinc Coating (Hot-Dip) on Iron and Steel Hardware", "گالوانیزه گرم قطعات", "Coating", "—", "Zinc", "Class A–D", "—", "Class C ≈ 1.7 mil (fasteners >3/8 in)", "Active", "Fasteners now usually F2329", "—", "—", "—", "Hardware", "—", ""),
    ("ASTM B695", "Coatings of Zinc Mechanically Deposited on Iron and Steel", "گالوانیزه مکانیکی", "Coating", "—", "Zinc (peened)", "Class 5–110 (thickness µm)", "—", "Class 55 for F3125 A325", "Active", "No hydrogen embrittlement risk from pickling", "—", "—", "—", "Structural bolts (A325), high-strength", "—", ""),
    ("ASTM F1941/F1941M", "Electrodeposited Coatings on Mechanical Fasteners, Inch and Metric", "آبکاری الکتریکی اتصالات", "Coating", "—", "Zn, Zn-Fe, Zn-Ni, Cd …", "Fe/Zn 3–25 µm + chromate", "—", "—", "Active", "Not for ≥ HRC 39 without HE controls", "—", "—", "—", "Commercial fasteners", "—", ""),
    ("ASTM F1136/F1136M", "Zinc/Aluminum Corrosion Protective Coatings for Fasteners", "پوشش زینک فلیک (Geomet/Dacromet)", "Coating", "—", "Zn/Al flake", "Grade 3, 5", "—", "Grade 3 allowed for F3125 A490", "Active", "Non-electrolytic → low HE risk", "—", "—", "—", "High-strength fasteners, automotive", "—", ""),
    ("ASTM F2833", "Corrosion Protective Fastener Coatings with Zinc Rich Base Coat and Aluminum Organic/Inorganic Type", "پوشش ضد خوردگی زینک‌ریچ", "Coating", "—", "Zn-rich base + top coat", "Grade 0, 1, 2", "—", "Grade 1 allowed for F3125 A490", "Active", "", "—", "—", "—", "High-strength fasteners", "—", ""),
    ("ASTM B633", "Electrodeposited Coatings of Zinc on Iron and Steel", "آبکاری روی", "Coating", "—", "Zinc", "SC1–SC4; Types I–VI", "—", "—", "Active", "", "—", "—", "—", "General", "—", ""),
    # ---- testing & general
    ("ASTM F606/F606M", "Determining the Mechanical Properties of Externally and Internally Threaded Fasteners, Washers, Direct Tension Indicators, and Rivets", "روش آزمون خواص مکانیکی اتصالات", "Test method", "—", "—", "—", "—", "Proof load, wedge tensile, hardness", "Active", "", "—", "—", "—", "QA / certification", "—", ""),
    ("ASTM A370", "Test Methods and Definitions for Mechanical Testing of Steel Products", "آزمون مکانیکی محصولات فولادی", "Test method", "—", "—", "—", "—", "Tensile, impact, hardness", "Active", "", "—", "—", "—", "QA", "—", ""),
    ("ASTM F1470", "Practice for Fastener Sampling for Specified Mechanical Properties and Performance Inspection", "نمونه‌برداری اتصالات", "Test method", "—", "—", "—", "—", "Lot sampling plans", "Active", "", "—", "—", "—", "QA", "—", ""),
    ("ASTM F788", "Surface Discontinuities of Bolts, Screws, and Studs, Inch and Metric Series", "عیوب سطحی پیچ", "Test method", "—", "—", "—", "—", "Cracks, seams, laps limits", "Active", "", "—", "—", "—", "Visual inspection", "—", ""),
    ("ASTM F812", "Surface Discontinuities of Nuts, Inch and Metric Series", "عیوب سطحی مهره", "Test method", "—", "—", "—", "—", "—", "Active", "", "—", "—", "—", "Visual inspection", "—", ""),
    ("ASTM F1789", "Terminology for F16 Mechanical Fasteners", "واژه‌نامه اتصالات", "Terminology", "—", "—", "—", "—", "—", "Active", "", "—", "—", "—", "Definitions", "—", ""),
    ("ASTM F2328", "Determining Decarburization and Carburization in Hardened and Tempered Threaded Steel Bolts, Screws, Studs, and Nuts", "تعیین دکربوره شدن", "Test method", "—", "—", "—", "—", "—", "Active", "", "—", "—", "—", "Heat-treat QA", "—", ""),
    ("ASTM F1940", "Process Control Verification to Prevent Hydrogen Embrittlement in Plated or Coated Fasteners", "کنترل تردی هیدروژنی", "Test method", "—", "—", "—", "—", "—", "Active", "", "—", "—", "—", "Coated high-strength fasteners", "—", ""),
    ("ASTM F1624", "Measurement of Hydrogen Embrittlement Threshold in Steel by the Incremental Step Loading Technique", "آستانه تردی هیدروژنی", "Test method", "—", "—", "—", "—", "—", "Active", "", "—", "—", "—", "R&D / QA", "—", ""),
]

# Spec, Grade/Class, Size range (in), Tensile min (ksi), Tensile max (ksi), Yield min (ksi),
# Elong % min, RA % min, Hardness, Proof stress (ksi), Heat treatment, Note
BOLT_PROPS = [
    ("A307", "Grade A", "1/4–4", 60, None, None, 18, None, "HRB 69–100 (HB 121–241)", None, "None", "General purpose"),
    ("A307", "Grade B", "1/4–4", 60, 100, None, 18, None, "HRB 69–95 (HB 121–212)", None, "None", "Flanged joints, cast-iron piping"),
    ("F3125", "A325 (Type 1/3)", "1/2–1-1/2", 120, None, 92, 14, 35, "HRC 25–34 (HB 253–319)", 85, "Q&T", "Since 2015 one strength level for all sizes"),
    ("F3125", "F1852 (Type 1/3)", "1/2–1-1/8", 120, None, 92, 14, 35, "HRC 25–34", 85, "Q&T", "Twist-off TC assembly"),
    ("F3125", "A490 (Type 1/3)", "1/2–1-1/2", 150, 173, 130, 14, 40, "HRC 33–38", 120, "Q&T", "HDG / mech. galv. NOT permitted"),
    ("F3125", "F2280 (Type 1/3)", "1/2–1-1/8", 150, 173, 130, 14, 40, "HRC 33–38", 120, "Q&T", "Twist-off TC assembly"),
    ("F3125M", "A325M", "M12–M36", "830 MPa", None, "660 MPa", 14, 35, "HRC 25–34", "600 MPa", "Q&T", "Metric"),
    ("F3125M", "A490M", "M12–M36", "1040 MPa", "1210 MPa", "940 MPa", 14, 40, "HRC 33–38", "830 MPa", "Q&T", "Metric"),
    ("A325 (legacy)", "≤ 1 in", "1/2–1", 120, None, 92, 14, 35, "HRC 24–35", 85, "Q&T", "Withdrawn 2016 — for old drawings"),
    ("A325 (legacy)", "> 1 in", "1-1/8–1-1/2", 105, None, 81, 14, 35, "HRC 19–31 (HB 223–286)", 74, "Q&T", "Withdrawn 2016 — for old drawings"),
    ("F3148", "Grade 144", "1/2–1-1/4", 144, None, None, None, None, "per spec", None, "Q&T", "Values to confirm in standard"),
    ("F3043 / F3111", "Grade 1 / 2", "1–1-1/2", 200, None, None, None, None, "per spec", None, "Q&T", "Special; HE-sensitive"),
    ("A449", "Type 1", "1/4–1", 120, None, 92, 14, 35, "HRC 25–34", 85, "Q&T", ""),
    ("A449", "Type 1", "1-1/8–1-1/2", 105, None, 81, 14, 35, "HRC 19–30", 74, "Q&T", ""),
    ("A449", "Type 1", "1-3/4–3", 90, None, 58, 14, 35, "HB 183–235", 55, "Q&T", ""),
    ("A354", "BC", "1/4–2-1/2", 125, None, 109, 16, 50, "HRC 26–36", 105, "Q&T", ""),
    ("A354", "BC", "2-3/4–4", 115, None, 99, 16, 45, "HRC 22–33", 95, "Q&T", ""),
    ("A354", "BD", "1/4–2-1/2", 150, None, 130, 14, 40, "HRC 33–39", 120, "Q&T", ""),
    ("A354", "BD", "2-3/4–4", 140, None, 115, 14, 40, "HRC 31–39", 105, "Q&T", ""),
    ("A394", "Type 0", "1/2–1", 74, None, None, None, None, "HRB 65–100 (verify)", None, "None", "Zinc coated"),
    ("A394", "Type 1 / Type 3", "1/2–1", 120, None, 92, None, None, "HRC 25–34", 85, "Q&T", "Type 3 weathering"),
    ("F1554", "Grade 36", "1/2–4", 58, 80, 36, 23, 40, "—", None, "None", "End colour: blue"),
    ("F1554", "Grade 55", "1/2–4", 75, 95, 55, 21, 30, "—", None, "None", "End colour: yellow; S1 = weldable"),
    ("F1554", "Grade 105", "1/2–3", 125, 150, 105, 15, 45, "—", None, "Q&T", "End colour: red; Charpy S4/S5 optional"),
    ("A193", "B7", "≤ 2-1/2", 125, None, 105, 16, 50, "HB 321 max (HRC 35 max)", None, "Q&T (Cr-Mo 4140/4142)", "Most common stud bolt"),
    ("A193", "B7", "2-5/8–4", 115, None, 95, 16, 50, "HB 321 max", None, "Q&T", ""),
    ("A193", "B7", "4-1/8–7", 100, None, 75, 18, 50, "HB 321 max", None, "Q&T", ""),
    ("A193", "B7M", "≤ 4", 100, None, 80, 18, 50, "HB 235 max (HRB 99 max)", None, "Q&T, 100 % hardness tested", "Sour service"),
    ("A193", "B16", "≤ 2-1/2", 125, None, 105, 18, 50, "HB 321 max", None, "Q&T (Cr-Mo-V)", "Higher temperature than B7"),
    ("A193", "B16", "2-5/8–4", 110, None, 95, 17, 45, "HB 321 max", None, "Q&T", ""),
    ("A193", "B8 / B8M Class 1", "all", 75, None, 30, 30, 50, "HB 223 max", None, "Carbide solution treated", "304 / 316"),
    ("A193", "B8 Class 2", "≤ 3/4", 125, None, 100, 12, 35, "HRC 35 max", None, "Solution treated + strain hardened", ""),
    ("A193", "B8M Class 2", "≤ 3/4", 110, None, 95, 15, 45, "HRC 35 max", None, "Solution treated + strain hardened", ""),
    ("A320", "L7", "≤ 2-1/2", 125, None, 105, 16, 50, "HRC 35 max (verify)", None, "Q&T + impact −150 °F", "Charpy 20 ft·lbf avg"),
    ("A320", "L7M", "≤ 2-1/2", 100, None, 80, 18, 50, "HB 235 max", None, "Q&T + impact −100 °F", ""),
    ("A320", "L43", "≤ 4", 125, None, 105, 16, 50, "HRC 35 max (verify)", None, "Q&T (4340) + impact −150 °F", ""),
    ("A453", "660 Class A/B", "all", 130, None, 85, 15, 18, "HB 248–341", None, "Solution + age (A-286)", ""),
    ("A574", "—", "≤ 1/2", 180, None, 153, 8, 35, "HRC 39–45", 140, "Q&T", "Socket head cap screw"),
    ("A574", "—", "> 1/2", 170, None, 153, 8, 35, "HRC 37–45", 135, "Q&T", ""),
    ("F593", "Group 1/2, Cond. CW1", "1/4–5/8", 100, 150, 65, 20, None, "HRB 95 – HRC 32", None, "Cold worked", "304 / 316"),
    ("F593", "Group 1/2, Cond. CW2", "3/4–1-1/2", 85, 140, 45, 25, None, "HRB 80 – HRC 32", None, "Cold worked", ""),
    ("F593", "Group 1/2, Cond. A/AF", "1/4–1-1/2", 75, 100, 30, 20, None, "HRB 65–95 (verify)", None, "Annealed", ""),
]

# Spec, Grade, Style, Size range, Proof stress (ksi, non-coated UNC), Proof stress zinc-coated (ksi), Hardness, Heat treatment, Note
NUT_PROPS = [
    ("A563", "O", "Hex", "1/4–1-1/2", 69, 52, "HRB 55 – HRC 32", "None", "Mates A307 (non-structural)"),
    ("A563", "A", "Hex", "1/4–1-1/2", 90, 68, "HRB 68 – HRC 32", "None", "Mates A307, F1554 Gr 36"),
    ("A563", "A", "Heavy hex", "1/4–4", 100, 75, "HRB 68 – HRC 32", "None", ""),
    ("A563", "B", "Hex", "1/4–1", 120, 90, "HRB 69 – HRC 32", "None", ""),
    ("A563", "B", "Hex", "1-1/8–1-1/2", 105, 78, "HRB 69 – HRC 32", "None", ""),
    ("A563", "B", "Heavy hex", "1/4–1", 133, 100, "HRB 69 – HRC 32", "None", ""),
    ("A563", "B", "Heavy hex", "1-1/8–1-1/2", 116, 87, "HRB 69 – HRC 32", "None", ""),
    ("A563", "C", "Heavy hex", "1/4–4", 144, None, "HRB 78 – HRC 38", "Q&T (optional)", "Plain A325"),
    ("A563", "C3", "Heavy hex", "1/4–4", 144, None, "HRB 78 – HRC 38", "Weathering", "A325 Type 3"),
    ("A563", "D", "Heavy hex", "1/4–4", 150, 150, "HRB 84 – HRC 38", "Q&T", "Plain A325"),
    ("A563", "DH", "Heavy hex", "1/4–4", 175, 150, "HRC 24–38", "Q&T", "Galvanized A325, all A490"),
    ("A563", "DH3", "Heavy hex", "1/4–4", 175, None, "HRC 24–38", "Q&T weathering", "A325/A490 Type 3"),
    ("A194", "2H", "Heavy hex", "1/4–4", 175, 150, "HB 248–327 (HRC 24–35)", "Q&T", "Mates A193 B7, F3125"),
    ("A194", "2HM", "Heavy hex", "1/4–4", 150, None, "HB 159–237", "Q&T, 100 % hardness tested", "Mates B7M (sour service)"),
    ("A194", "4", "Heavy hex", "1/4–4", 175, None, "HB 248–327", "Q&T (C-Mo)", "Mates A193 B16, A320 L7 (+S3)"),
    ("A194", "7", "Heavy hex", "1/4–4", 175, None, "HB 248–327", "Q&T (Cr-Mo)", "Mates A320 L7 (+S3)"),
    ("A194", "7M", "Heavy hex", "1/4–4", 150, None, "HB 159–237", "Q&T", "Mates L7M"),
    ("A194", "8 / 8M", "Heavy hex", "1/4–4", 80, None, "HB 126–300", "Solution treated", "Mates B8 / B8M (304/316)"),
    ("F594", "Group 1/2, CW1", "Hex", "1/4–5/8", 100, None, "HRB 85 – HRC 35 (verify)", "Cold worked", "Mates F593 CW1"),
    ("F594", "Group 1/2, CW2", "Hex", "3/4–1-1/2", 85, None, "HRB 80 – HRC 35 (verify)", "Cold worked", "Mates F593 CW2"),
]

# Bolt spec/grade, Finish, Recommended nut (preferred), Alternate nut(s), Washer, Note
COMPAT = [
    ("A307 Gr A", "Plain / HDG", "A563 A hex", "A563 O (hex), A563 A heavy hex", "F844 (if required)", ""),
    ("A307 Gr B", "Plain / HDG", "A563 A heavy hex", "A563 B heavy hex", "F844", "Flanged joints"),
    ("F3125 A325 Type 1", "Plain", "A563 DH heavy hex", "A563 C, D; A194 2H", "F436 Type 1", "Per F3125 / A563"),
    ("F3125 A325 Type 1", "Hot-dip / mech. galvanized", "A563 DH (galv., lubricated, overtapped)", "A194 2H galv.", "F436 Type 1 galv.", "Bolt, nut & washer galvanized by same process; rotational-capacity test"),
    ("F3125 A325 Type 3", "Weathering", "A563 DH3", "A563 C3", "F436 Type 3", ""),
    ("F3125 A490 Type 1", "Plain", "A563 DH heavy hex", "A194 2H", "F436 Type 1", "No hot-dip / mech. galvanizing"),
    ("F3125 A490 Type 1", "F1136 Gr 3 / F2833 Gr 1 zinc-flake", "A563 DH (same coating)", "A194 2H", "F436 (same coating)", "Only these coatings allowed for A490"),
    ("F3125 A490 Type 3", "Weathering", "A563 DH3", "—", "F436 Type 3", ""),
    ("F3125 F1852", "Plain / mech. galv.", "Supplied A563 DH", "—", "Supplied F436", "Use only as a manufacturer-matched assembly"),
    ("F3125 F2280", "Plain", "Supplied A563 DH", "—", "Supplied F436", "Use only as a manufacturer-matched assembly"),
    ("A449 (≤ 1-1/2)", "Plain", "A563 DH heavy hex", "A563 B hex / C heavy hex (verify per size)", "F436", ""),
    ("A354 BC", "Plain", "A563 C heavy hex", "A563 DH", "F436", ""),
    ("A354 BD", "Plain", "A563 DH heavy hex", "A194 2H", "F436", ""),
    ("F1554 Gr 36", "Plain / HDG", "A563 A heavy hex", "A563 A hex", "F436 / F844 / plate washer", "F1554 Table 'Recommended nuts'"),
    ("F1554 Gr 55", "Plain", "A563 A heavy hex", "A563 DH, A194 2H", "F436 / plate washer", ""),
    ("F1554 Gr 55", "HDG", "A563 DH heavy hex (verify)", "A194 2H", "F436 galv.", ""),
    ("F1554 Gr 105", "Plain / HDG", "A563 DH heavy hex", "A563 D (plain), A194 2H", "F436", ""),
    ("A193 B7", "Plain / PTFE / HDG", "A194 2H heavy hex", "A194 4, 7", "F436 / through-hardened", "Pipe flanges"),
    ("A193 B7M", "Plain", "A194 2HM", "A194 7M", "—", "Sour service"),
    ("A193 B16", "Plain", "A194 4 or 7", "—", "—", "High temp"),
    ("A193 B8 / B8M", "Plain", "A194 8 / 8M", "F594 Gr 1/2", "SS washer", "Material grade should match"),
    ("A320 L7", "Plain", "A194 4 or 7 + S3 (impact)", "—", "—", "Low temp"),
    ("A320 L7M", "Plain", "A194 7M + S3", "—", "—", "Low temp, sour"),
    ("F593 Group 1/2", "Plain", "F594 same group & condition", "—", "SS washer", "Anti-seize recommended (galling)"),
    ("A394 Type 0", "HDG", "A563 A (galv.)", "—", "—", "Towers"),
    ("A394 Type 1 / 3", "HDG / weathering", "A563 DH / DH3", "A563 C/C3", "—", "Towers"),
]

# UNC threads per inch
UNC = {0.25: 20, 0.3125: 18, 0.375: 16, 0.4375: 14, 0.5: 13, 0.5625: 12, 0.625: 11, 0.75: 10, 0.875: 9, 1.0: 8,
       1.125: 7, 1.25: 7, 1.375: 6, 1.5: 6, 1.75: 5, 2.0: 4.5, 2.25: 4.5, 2.5: 4, 2.75: 4, 3.0: 4, 3.25: 4, 3.5: 4, 3.75: 4, 4.0: 4}

# Heavy hex structural bolt (F3125) — D: (F, H head, thread length), nominal values (in)
STRUCT = {
    0.5: (0.875, 0.3125, 1.0), 0.625: (1.0625, 0.390625, 1.25), 0.75: (1.25, 0.46875, 1.375),
    0.875: (1.4375, 0.546875, 1.5), 1.0: (1.625, 0.609375, 1.75), 1.125: (1.8125, 0.6875, 2.0),
    1.25: (2.0, 0.78125, 2.0), 1.375: (2.1875, 0.84375, 2.25), 1.5: (2.375, 0.9375, 2.25),
}
# F436 circular washer (nominal ID, OD, thickness min, max) in
F436 = {0.5: (0.53125, 1.0625, 0.097, 0.177), 0.625: (0.6875, 1.3125, 0.122, 0.177), 0.75: (0.8125, 1.46875, 0.122, 0.177),
        0.875: (0.9375, 1.75, 0.136, 0.177), 1.0: (1.125, 2.0, 0.136, 0.177), 1.125: (1.25, 2.25, 0.136, 0.177),
        1.25: (1.375, 2.5, 0.136, 0.177), 1.375: (1.5, 2.75, 0.136, 0.177), 1.5: (1.625, 3.0, 0.136, 0.177)}
# Hex bolt (A307 / A449) D: (F, H)
HEXBOLT = {0.25: (0.4375, 0.171875), 0.3125: (0.5, 0.21875), 0.375: (0.5625, 0.25), 0.4375: (0.625, 0.296875),
           0.5: (0.75, 0.34375), 0.625: (0.9375, 0.421875), 0.75: (1.125, 0.5), 0.875: (1.3125, 0.578125),
           1.0: (1.5, 0.671875), 1.125: (1.6875, 0.75), 1.25: (1.875, 0.84375), 1.375: (2.0625, 0.90625),
           1.5: (2.25, 1.0), 1.75: (2.625, 1.15625), 2.0: (3.0, 1.34375), 2.25: (3.375, 1.5), 2.5: (3.75, 1.65625),
           2.75: (4.125, 1.8125), 3.0: (4.5, 2.0)}
# Hex nut (A563) D: (F, thickness)
HEXNUT = {0.25: (0.4375, 0.21875), 0.3125: (0.5, 0.265625), 0.375: (0.5625, 0.328125), 0.4375: (0.6875, 0.375),
          0.5: (0.75, 0.4375), 0.5625: (0.875, 0.484375), 0.625: (0.9375, 0.546875), 0.75: (1.125, 0.640625),
          0.875: (1.3125, 0.75), 1.0: (1.5, 0.859375), 1.125: (1.6875, 0.96875), 1.25: (1.875, 1.0625),
          1.375: (2.0625, 1.171875), 1.5: (2.25, 1.28125)}


# --------------------------------------------------------------------------- sheets

def sheet_guide(wb, drawings):
    ws = wb.active
    ws.title = "راهنما"
    ws.sheet_view.rightToLeft = True
    rows = [
        ("استانداردهای ASTM پیچ، مهره و واشر — مرجع فنی و فهرست محصول", None),
        (None, None),
        ("هدف", "دیسکاوری کامل استانداردهای ASTM اتصالات (پیچ، مهره، واشر، میل‌مهار، پوشش و روش آزمون) برای کاتالوگ/فروشگاه و مهندسی فروش."),
        ("مبنا", "خلاصه‌های عمومی منتشرشده از استانداردهای ASTM و تولیدکنندگان معتبر (شیت «منابع»). متن رسمی ASTM کپی‌رایت است؛ اعداد مرجع‌اند و پیش از خرید/طراحی باید با نسخهٔ خریداری‌شدهٔ استاندارد کنترل شوند."),
        ("نقشه‌ها", "نقشه‌های DWG-01 تا DWG-11 شماتیک (بدون مقیاس) با نمادهای ابعادی هستند؛ اندازهٔ واقعی هر سایز در شیت‌های Dim_ آمده است."),
        ("علامت (verify)", "هر جا «verify» آمده، منابع عمومی ناهمخوان یا ناقص بودند — حتماً با متن استاندارد تطبیق دهید."),
        (None, None),
        ("شیت", "محتوا"),
        ("Standards", "فهرست جامع استانداردها: عنوان، دسته، جنس، گریدها، بازهٔ سایز، مقاومت، وضعیت (فعال/منسوخ و جایگزین)، استاندارد ابعادی، مهره و واشر سازگار، کاربرد، نشانه‌گذاری، شمارهٔ نقشه"),
        ("Bolt_Properties", "خواص مکانیکی پیچ/استاد به تفکیک گرید و سایز: کشش، تسلیم، ازدیاد طول، کاهش سطح، سختی، تنش بار اثبات"),
        ("Nut_Properties", "خواص مهره‌ها (A563, A194, F594): تنش بار اثبات بدون پوشش و گالوانیزه، سختی"),
        ("Compatibility", "ماتریس سازگاری پیچ ↔ مهره ↔ واشر بر اساس پوشش"),
        ("Dim_Structural", "ابعاد پیچ سازه‌ای F3125، مهرهٔ سنگین A563/A194 و واشر F436"),
        ("Dim_HexBolt_Nut", "ابعاد پیچ شش‌گوش (A307/A449)، مهرهٔ شش‌گوش و مهرهٔ سنگین (A563/A194)"),
        ("Threads_Loads", "رزوهٔ UNC، سطح تنش کششی (فرمول) و ظرفیت کششی/بار اثبات برای گریدهای اصلی — ستون‌های زرد قابل‌ویرایش‌اند"),
        ("Selector", "انتخابگر: سایز و گرید را از لیست انتخاب کنید (سلول‌های زرد)؛ ابعاد، مهره، واشر و ظرفیت خودکار نمایش داده می‌شود"),
        ("Coatings_Tests", "پوشش‌ها و روش‌های آزمون/کیفیت"),
        ("Drawings", "نقشه‌های فنی شماتیک (تصاویر) با شرح"),
        ("Parents / SKUs", "ساختار والد/فرزند: والد = استاندارد+گرید+محصول؛ SKU = سایز × طول (طول‌ها بازهٔ رایج انبار، فرض شده)"),
        ("منابع", "لینک منابع استفاده‌شده"),
        (None, None),
        ("قرارداد واحدها", "اینچ (in) و ksi مگر خلاف آن ذکر شود. 1 ksi = 6.895 MPa، 1 in = 25.4 mm. سایزها به صورت کسری متنی (مثل 1-1/8) و ستون اعشاری کنارشان."),
        ("وضعیت تا تاریخ", "اکتبر ۲۰۲۶ — سال ویرایش‌ها را از ASTM Store بررسی کنید."),
    ]
    for r, (a, b) in enumerate(rows, 1):
        ws.cell(row=r, column=1, value=a).font = Font(name=FONT, bold=True, size=14 if r == 1 else 10, color="1F2A44")
        if b:
            c = ws.cell(row=r, column=2, value=b)
            c.font = Font(name=FONT, size=10, bold=(a == "شیت"))
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in (8,):
        ws.cell(row=r, column=1).fill = SUB_FILL
        ws.cell(row=r, column=2).fill = SUB_FILL
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 120


def sheet_standards(wb):
    ws = wb.create_sheet("Standards")
    headers = ["Designation", "Title (EN)", "عنوان فارسی", "Category", "Product forms", "Material / heat treatment",
               "Grades / classes", "Size range", "Key strength", "Status", "Replaced by / note",
               "Mating nut", "Washer", "Typical applications", "Marking", "Drawing"]
    data = [row[:11] + row[12:] for row in STANDARDS]
    end = write_table(ws, headers, data, widths=[20, 55, 34, 16, 30, 36, 34, 18, 30, 16, 36, 30, 22, 38, 32, 16],
                      wrap_cols=set(range(2, 17)))
    for r in range(2, end + 1):
        st = ws.cell(row=r, column=10).value or ""
        if st.startswith("Withdrawn"):
            for c in range(1, 17):
                ws.cell(row=r, column=c).fill = GONE_FILL
            ws.cell(row=r, column=10).font = Font(name=FONT, size=10, color="C0392B", bold=True)
        if any("verify" in str(ws.cell(row=r, column=c).value) for c in range(1, 17)):
            ws.cell(row=r, column=1).fill = WARN_FILL
        ws.cell(row=r, column=1).font = Font(name=FONT, size=10, bold=True)


def sheet_bolt_props(wb):
    ws = wb.create_sheet("Bolt_Properties")
    headers = ["Spec", "Grade / class", "Size range (in)", "Tensile min (ksi)", "Tensile max (ksi)", "Yield min (ksi)",
               "Elong. min %", "RA min %", "Hardness", "Proof stress (ksi)", "Heat treatment", "Note", "Tensile min (MPa)"]
    rows = []
    for row in BOLT_PROPS:
        rows.append(list(row) + [None])
    end = write_table(ws, headers, rows, widths=[16, 24, 16, 13, 13, 13, 11, 10, 26, 13, 30, 40, 14], wrap_cols={9, 11, 12})
    for r in range(2, end + 1):
        if isinstance(ws.cell(row=r, column=4).value, (int, float)):
            ws.cell(row=r, column=13, value=f"=ROUND(D{r}*6.894757,0)").font = Font(name=FONT, size=10)
        else:
            ws.cell(row=r, column=13, value="(metric)").font = Font(name=FONT, size=10, color="888888")
        if any("verify" in str(ws.cell(row=r, column=c).value) for c in range(1, 13)):
            ws.cell(row=r, column=1).fill = WARN_FILL
    note_r = end + 2
    ws.cell(row=note_r, column=1, value="Notes: ksi→MPa column is a formula (×6.894757). Proof stress × tensile stress area = proof load (see Threads_Loads). "
            "Values from public spec summaries (Portland Bolt, Fastenal); rows highlighted orange contain items to verify.").font = Font(name=FONT, italic=True, size=9)


def sheet_nut_props(wb):
    ws = wb.create_sheet("Nut_Properties")
    headers = ["Spec", "Grade", "Style", "Size range (in)", "Proof stress – plain (ksi)", "Proof stress – zinc coated, overtapped (ksi)",
               "Hardness", "Heat treatment", "Typical mate / note"]
    end = write_table(ws, headers, NUT_PROPS, widths=[10, 18, 12, 16, 16, 20, 26, 26, 36], wrap_cols={7, 8, 9})
    for r in range(2, end + 1):
        if any("verify" in str(ws.cell(row=r, column=c).value) for c in range(1, 10)):
            ws.cell(row=r, column=1).fill = WARN_FILL
    ws.cell(row=end + 2, column=1, value="A563 proof stresses are for UNC / 8UN / 6UN coarse threads; fine threads have lower values. Zinc-coated column applies to nuts overtapped for hot-dip galvanized bolts. A194 values for heavy hex style.").font = Font(name=FONT, italic=True, size=9)


def sheet_compat(wb):
    ws = wb.create_sheet("Compatibility")
    headers = ["Bolt spec / grade", "Finish", "Recommended nut", "Alternate nut(s)", "Washer", "Note"]
    write_table(ws, headers, COMPAT, widths=[24, 30, 36, 34, 26, 48], wrap_cols={2, 3, 4, 5, 6})


def sheet_dim_struct(wb):
    ws = wb.create_sheet("Dim_Structural")
    title(ws, "Heavy hex structural bolts (ASTM F3125) · heavy hex nuts (A563 / A194) · washers (F436)",
          "Nominal dimensions in inches. G (across corners) and nut thickness are formulas.")
    headers = ["Size (in)", "D (dec.)", "UNC TPI", "Bolt F across flats", "Bolt G across corners (≈F×2/√3)", "Bolt head H", "Thread length LT",
               "Nut F", "Nut thickness H (≈D−1/64)", "F436 ID", "F436 OD", "F436 T min", "F436 T max"]
    rows = []
    for i, (d, (F, H, LT)) in enumerate(sorted(STRUCT.items())):
        r = 4 + i
        idd, od, tmin, tmax = F436[d]
        rows.append([frac(d), d, UNC[d], F, f"=ROUND(D{r}*2/SQRT(3),3)", H, LT, F, f"=B{r}-1/64",
                     idd, od, tmin, tmax])
    end = write_table(ws, headers, rows, start_row=3, widths=[10, 9, 9, 12, 16, 11, 12, 10, 14, 10, 10, 11, 11],
                      number_formats={4: "0.000", 5: "0.000", 6: "0.000", 7: "0.000", 8: "0.000", 9: "0.000", 10: "0.000", 11: "0.000", 12: "0.000", 13: "0.000"})
    r = end + 2
    ws.cell(row=r, column=1, value="Bolt length selection: L = grip + allowance (≈ nut thickness + washer + ~1 thread stick-out); round up to next 1/4 in (≤5 in) or 1/2 in (>5 in).").font = Font(name=FONT, italic=True, size=9)
    ws.cell(row=r + 1, column=1, value="F436 thickness and OD from distributor-published tables (sizes ≤1/2 in thinner); verify against F436/F436M current edition.").font = Font(name=FONT, italic=True, size=9)


def sheet_dim_hex(wb):
    ws = wb.create_sheet("Dim_HexBolt_Nut")
    title(ws, "Hex bolts (ASTM A307 / A449) · hex & heavy hex nuts (ASTM A563 / A194)",
          "Nominal (basic) dimensions in inches. Heavy hex nut F and thickness are formula-generated (F = 1.5D + 1/8, H = D − 1/64).")
    sizes = sorted(set(HEXBOLT) | set(HEXNUT) | {3.25, 3.5, 3.75, 4.0})
    headers = ["Size (in)", "D (dec.)", "UNC TPI", "Hex bolt F", "Hex bolt H", "Thread length L≤6 in (2D+1/4)", "Thread length L>6 in (2D+1/2)",
               "Hex nut F", "Hex nut thickness", "Heavy hex nut F (1.5D+1/8)", "Heavy hex nut thickness (D−1/64)", "Heavy hex G across corners"]
    rows = []
    for i, d in enumerate(sizes):
        r = 4 + i
        hb = HEXBOLT.get(d)
        hn = HEXNUT.get(d)
        rows.append([frac(d), d, UNC.get(d), hb[0] if hb else None, hb[1] if hb else None,
                     f"=2*B{r}+0.25", f"=2*B{r}+0.5", hn[0] if hn else None, hn[1] if hn else None,
                     f"=1.5*B{r}+0.125", f"=B{r}-1/64", f"=ROUND(J{r}*2/SQRT(3),3)"])
    write_table(ws, headers, rows, start_row=3, widths=[10, 9, 9, 11, 11, 16, 16, 11, 13, 16, 18, 16],
                number_formats={c: "0.000" for c in range(4, 13)})


def sheet_threads(wb):
    ws = wb.create_sheet("Threads_Loads")
    title(ws, "UNC threads · tensile stress area · tensile & proof capacity",
          "As = 0.7854 × (D − 0.9743/n)² (UNC tensile stress area). Edit the yellow stress row to add grades; loads in kips = stress (ksi) × As.")
    grades = [("A307 Gr A tensile", 60), ("F1554 Gr 36 yield", 36), ("F1554 Gr 55 yield", 55), ("A325 tensile", 120),
              ("A325 proof", 85), ("A490 tensile", 150), ("A490 proof", 120), ("A193 B7 tensile (≤2-1/2)", 125), ("A354 BD tensile", 150)]
    hdr_row = 4
    base = ["Size (in)", "D (dec.)", "TPI (UNC)", "Pitch (in)", "Minor-ish d − 0.9743/n", "As (in²)", "As (mm²)"]
    ws.cell(row=3, column=1, value="Stress (ksi) →").font = Font(name=FONT, bold=True)
    for j, (g, s) in enumerate(grades):
        c = ws.cell(row=3, column=len(base) + 1 + j, value=s)
        c.fill = INPUT_FILL
        c.font = Font(name=FONT, bold=True, color="0000FF")
        c.alignment = Alignment(horizontal="center")
        c.border = BORDER
    headers = base + [f"{g} (kips)" for g, _ in grades]
    rows = []
    for i, d in enumerate(sorted(UNC)):
        r = hdr_row + 1 + i
        row = [frac(d), d, UNC[d], f"=1/C{r}", f"=B{r}-0.9743/C{r}", f"=ROUND(0.7854*E{r}^2,4)", f"=ROUND(F{r}*645.16,1)"]
        for j in range(len(grades)):
            col = get_column_letter(len(base) + 1 + j)
            row.append(f"=ROUND({col}$3*$F{r},1)")
        rows.append(row)
    write_table(ws, headers, rows, start_row=hdr_row, widths=[10, 9, 9, 9, 13, 10, 10] + [14] * len(grades),
                number_formats={4: "0.0000", 5: "0.0000", 6: "0.0000", 7: "0.0", **{8 + j: "0.0" for j in range(len(grades))}})
    ws.freeze_panes = "B5"
    n = hdr_row + len(rows) + 2
    ws.cell(row=n, column=1, value="Legend: yellow/blue cells in row 3 are inputs (ksi). Everything else is calculated. Values are capacity indicators, not design strengths.").font = Font(name=FONT, italic=True, size=9)
    return hdr_row + 1, hdr_row + len(rows)


def sheet_selector(wb, t_first, t_last):
    ws = wb.create_sheet("Selector")
    title(ws, "Structural bolt selector — F3125 heavy hex", "Pick size and grade in the yellow cells; everything else updates.")
    labels = [("Size (in)", "3/4"), ("Grade", "A325"), ("Finish", "Plain")]
    for i, (k, v) in enumerate(labels):
        ws.cell(row=4 + i, column=1, value=k).font = Font(name=FONT, bold=True)
        c = ws.cell(row=4 + i, column=2, value=v)
        c.fill = INPUT_FILL
        c.font = Font(name=FONT, color="0000FF", bold=True)
        c.border = BORDER
    dv1 = DataValidation(type="list", formula1="=Dim_Structural!$A$4:$A$12", allow_blank=False)
    dv2 = DataValidation(type="list", formula1='"A325,A490"', allow_blank=False)
    dv3 = DataValidation(type="list", formula1='"Plain,Galvanized,Weathering (Type 3)"', allow_blank=False)
    for dv, ref in ((dv1, "B4"), (dv2, "B5"), (dv3, "B6")):
        ws.add_data_validation(dv)
        dv.add(ref)
    m = "MATCH($B$4,Dim_Structural!$A$4:$A$12,0)"
    out = [
        ("D (in)", f"=INDEX(Dim_Structural!$B$4:$B$12,{m})", "0.000"),
        ("UNC threads per inch", f"=INDEX(Dim_Structural!$C$4:$C$12,{m})", "0"),
        ("Bolt head across flats F (in)", f"=INDEX(Dim_Structural!$D$4:$D$12,{m})", "0.000"),
        ("Bolt head height H (in)", f"=INDEX(Dim_Structural!$F$4:$F$12,{m})", "0.000"),
        ("Thread length LT (in)", f"=INDEX(Dim_Structural!$G$4:$G$12,{m})", "0.000"),
        ("Heavy hex nut thickness (in)", f"=INDEX(Dim_Structural!$I$4:$I$12,{m})", "0.000"),
        ("F436 washer ID / OD (in)", f'=TEXT(INDEX(Dim_Structural!$J$4:$J$12,{m}),"0.000")&" / "&TEXT(INDEX(Dim_Structural!$K$4:$K$12,{m}),"0.000")', None),
        ("Tensile stress area As (in²)", f"=INDEX(Threads_Loads!$F${t_first}:$F${t_last},MATCH($B$4,Threads_Loads!$A${t_first}:$A${t_last},0))", "0.000"),
        ("Min tensile strength (ksi)", '=IF($B$5="A325",120,150)', "0"),
        ("Min tensile load (kips)", "=ROUND(B16*B15,1)", "0.0"),
        ("Recommended nut", '=IF($B$6="Weathering (Type 3)","A563 DH3",IF(AND($B$5="A490",$B$6="Galvanized"),"NOT PERMITTED — use zinc-flake F1136 Gr3 / F2833 Gr1","A563 DH heavy hex"&IF($B$6="Galvanized"," (galv., lubricated)","")))', None),
        ("Washer", '=IF($B$6="Weathering (Type 3)","F436 Type 3","F436 Type 1"&IF($B$6="Galvanized"," galv.",""))', None),
        ("Head marking", '=$B$5&IF($B$6="Weathering (Type 3)"," (underlined)","")&" + mfr ID"', None),
        ("Drawing", "DWG-01 / DWG-11", None),
    ]
    for i, (k, f, fmt) in enumerate(out):
        r = 8 + i
        ws.cell(row=r, column=1, value=k).font = Font(name=FONT)
        c = ws.cell(row=r, column=2, value=f)
        c.font = Font(name=FONT, bold=True)
        c.border = BORDER
        if fmt:
            c.number_format = fmt
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 58
    ws.cell(row=8 + len(out) + 1, column=1, value="Example shown: 3/4 in A325 plain. Change only yellow cells.").font = Font(name=FONT, italic=True, size=9)
    img = XLImage(os.path.join(DWG_DIR, "DWG-01.png"))
    img.width, img.height = 620, 430
    ws.add_image(img, "D3")


def sheet_coat_tests(wb):
    ws = wb.create_sheet("Coatings_Tests")
    rows = [s for s in STANDARDS if s[3] in ("Coating", "Test method", "Terminology", "General requirements")]
    headers = ["Designation", "Title (EN)", "عنوان فارسی", "Category", "Key data", "Note", "Applies to"]
    data = [(s[0], s[1], s[2], s[3], s[8] if s[8] != "—" else s[6], s[10], s[14]) for s in rows]
    write_table(ws, headers, data, widths=[20, 60, 30, 18, 34, 40, 30], wrap_cols={2, 3, 5, 6, 7})


def sheet_drawings(wb, drawings):
    ws = wb.create_sheet("Drawings")
    title(ws, "Technical drawings (schematic) — DWG-01 … DWG-11",
          "Proportional schematics with dimension symbols (D, F, G, H, L, LT, T …). Real sizes: see Dim_ sheets. PNG originals: output/astm_drawings/")
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 44
    row = 4
    for code, ttl, path in drawings:
        ws.cell(row=row, column=1, value=code).font = Font(name=FONT, bold=True, size=12, color="1F2A44")
        ws.cell(row=row, column=2, value=ttl).font = Font(name=FONT, size=11)
        img = XLImage(path)
        scale = 760 / img.width
        img.width, img.height = int(img.width * scale), int(img.height * scale)
        ws.add_image(img, f"C{row}")
        rows_needed = int(img.height / 20) + 2
        row += rows_needed


# --------------------------------------------------------------------------- parents & SKUs

PARENTS = [
    # code, standard, grade, product, sizes, lengths rule, finish options, nut, washer, drawing
    ("F3125-A325", "ASTM F3125", "A325 Type 1", "Heavy hex structural bolt", list(STRUCT), "struct", "Plain, HDG (F2329), Mech. galv. (B695 Cl 55)", "A563 DH", "F436 Type 1", "DWG-01"),
    ("F3125-A325T3", "ASTM F3125", "A325 Type 3", "Heavy hex structural bolt — weathering", list(STRUCT), "struct", "Weathering (bare)", "A563 DH3", "F436 Type 3", "DWG-01"),
    ("F3125-A490", "ASTM F3125", "A490 Type 1", "Heavy hex structural bolt", list(STRUCT), "struct", "Plain, Zinc-flake F1136 Gr3 / F2833 Gr1", "A563 DH", "F436 Type 1", "DWG-01"),
    ("F3125-F1852", "ASTM F3125", "F1852 Type 1", "TC twist-off assembly 120 ksi", [0.5, 0.625, 0.75, 0.875, 1.0, 1.125], "struct", "Plain lubricated, Mech. galv.", "Supplied A563 DH", "Supplied F436", "DWG-07"),
    ("F3125-F2280", "ASTM F3125", "F2280 Type 1", "TC twist-off assembly 150 ksi", [0.75, 0.875, 1.0, 1.125], "struct", "Plain lubricated", "Supplied A563 DH", "Supplied F436", "DWG-07"),
    ("A307-A", "ASTM A307", "Grade A", "Hex bolt", [d for d in HEXBOLT if d <= 1.5], "hex", "Plain, Zinc plated (F1941), HDG", "A563 A", "F844", "DWG-02"),
    ("A449-1", "ASTM A449", "Type 1", "Hex cap screw / bolt", [d for d in HEXBOLT if d <= 1.5], "hex", "Plain, Zinc plated, HDG", "A563 DH", "F436", "DWG-02"),
    ("A193-B7", "ASTM A193", "B7", "All-thread stud bolt (2 × A194 2H)", [0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.375, 1.5], "stud", "Black, PTFE, HDG, Zn-Ni", "A194 2H", "—", "DWG-05"),
    ("A193-B7M", "ASTM A193", "B7M", "All-thread stud bolt (sour service)", [0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.5], "stud", "Black, PTFE", "A194 2HM", "—", "DWG-05"),
    ("A193-B8M1", "ASTM A193", "B8M Class 1", "All-thread stud bolt 316", [0.5, 0.625, 0.75, 0.875, 1.0], "stud", "Plain", "A194 8M", "—", "DWG-05"),
    ("A320-L7", "ASTM A320", "L7", "All-thread stud bolt (low temp)", [0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.5], "stud", "Black, PTFE", "A194 7 (S3)", "—", "DWG-05"),
    ("F1554-36", "ASTM F1554", "Grade 36", "Anchor rod (headed / L / straight)", [0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0], None, "Plain, HDG", "A563 A heavy hex", "F436 / plate", "DWG-06"),
    ("F1554-55", "ASTM F1554", "Grade 55", "Anchor rod", [0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0], None, "Plain, HDG", "A563 A / DH heavy hex", "F436 / plate", "DWG-06"),
    ("F1554-105", "ASTM F1554", "Grade 105", "Anchor rod", [0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0], None, "Plain, HDG", "A563 DH heavy hex", "F436 / plate", "DWG-06"),
    ("A574", "ASTM A574", "—", "Socket head cap screw", [0.25, 0.3125, 0.375, 0.5, 0.625, 0.75, 1.0], None, "Black oxide", "—", "—", "DWG-09"),
    ("F593-304", "ASTM F593", "Group 1 (304) CW", "Stainless hex bolt", [0.25, 0.3125, 0.375, 0.5, 0.625, 0.75, 1.0], "hex", "Passivated", "F594 Gr 1", "SS flat", "DWG-02"),
    ("A563-DH", "ASTM A563", "DH", "Heavy hex nut", list(STRUCT) + [1.75, 2.0], "nut", "Plain, HDG (overtapped), Mech. galv.", "—", "—", "DWG-03"),
    ("A563-A", "ASTM A563", "A", "Hex nut", [d for d in HEXNUT], "nut", "Plain, Zinc, HDG", "—", "—", "DWG-03"),
    ("A194-2H", "ASTM A194", "2H", "Heavy hex nut", [0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.375, 1.5, 1.75, 2.0], "nut", "Black, PTFE, HDG", "—", "—", "DWG-03"),
    ("F436-1", "ASTM F436", "Type 1", "Hardened round washer", list(F436), "nut", "Plain, HDG, Mech. galv.", "—", "—", "DWG-04"),
    ("F959-120", "ASTM F959", "Type 120", "Direct tension indicator", list(STRUCT), "nut", "Plain, Mech. galv.", "—", "—", "DWG-08"),
]


def lengths_for(rule, d):
    if rule == "struct":
        ls = [x / 4 for x in range(4, 25)] + [x / 2 for x in range(13, 17)]  # 1"–6" by 1/4, 6.5"–8" by 1/2
        return [L for L in ls if L >= max(1.0, 1.25 * d + 0.75)]
    if rule == "hex":
        ls = [x / 4 for x in range(2, 25)] + [x / 2 for x in range(13, 25)]  # 1/2"–6" by 1/4, 6.5"–12" by 1/2
        return [L for L in ls if L >= max(0.5, 2 * d)]
    if rule == "stud":
        ls = [x / 4 for x in range(8, 49)]  # 2"–12" by 1/4
        return [L for L in ls if L >= 4 * d]
    return []


def sheet_parents_skus(wb):
    wp = wb.create_sheet("Parents")
    ws = wb.create_sheet("SKUs")
    p_rows, s_rows = [], []
    for code, std, grade, prod, sizes, rule, finish, nut, washer, dwg in PARENTS:
        n_sku = 0
        for d in sizes:
            Ls = lengths_for(rule, d)
            tpi = UNC.get(d)
            thread = f"{frac(d)}-{tpi:g} UNC" if tpi else ""
            if rule in ("nut",) or rule is None:
                if rule == "nut":
                    s_rows.append([f"{code}-{frac(d)}", code, f"{std} {grade} {frac(d)}\" {prod}", std, grade, prod,
                                   frac(d), d, None, None, thread, finish, nut, washer, dwg, "سایز (بدون طول)"])
                    n_sku += 1
                continue
            for L in Ls:
                s_rows.append([f"{code}-{frac(d)}X{frac(L)}", code, f"{std} {grade} {frac(d)}\" × {frac(L)}\" {prod}", std, grade, prod,
                               frac(d), d, frac(L), L, thread, finish, nut, washer, dwg, "قطر × طول (بازهٔ رایج — فرض)"])
                n_sku += 1
        role = "والد + فرزند" if n_sku else "فقط والد (طول پروژه‌ای / سفارشی)"
        p_rows.append([code, std, grade, prod, role, len(sizes), n_sku, ", ".join(frac(d) for d in sizes),
                       {"struct": "1–6 in ×1/4, 6.5–8 in ×1/2", "hex": "1/2–6 in ×1/4, 6.5–12 in ×1/2", "stud": "2–12 in ×1/4 (L ≥ 4D)", "nut": "—"}.get(rule, "پروژه‌ای"),
                       finish, nut, washer, dwg])
    write_table(wp, ["Parent code", "Standard", "Grade", "Product name (EN)", "نقش", "# sizes", "# SKU فرزند", "Sizes (in)", "Length rule",
                     "Finish options", "Mating nut", "Washer", "Drawing"], p_rows,
                widths=[16, 14, 18, 36, 26, 8, 11, 50, 26, 40, 20, 16, 10], wrap_cols={8, 10})
    write_table(ws, ["SKU Code", "Parent code", "SKU title", "Standard", "Grade", "Product name (EN)", "Size (in)", "D (dec.)", "Length L (in)",
                     "L (dec.)", "Thread", "Finish options", "Mating nut", "Washer", "Drawing", "مبنا"], s_rows,
                widths=[26, 16, 52, 13, 16, 34, 9, 8, 11, 8, 16, 34, 18, 14, 10, 28])
    return len(p_rows), len(s_rows)


def sheet_sources(wb):
    ws = wb.create_sheet("منابع")
    src = [
        ("ASTM Store / Compass (official texts, editions)", "https://store.astm.org"),
        ("ASTM F3125/F3125M listing", "https://store.astm.org/f3125_f3125m-23.html"),
        ("ASTM F436/F436M listing", "https://store.astm.org/f0436_f0436m-19.html"),
        ("Portland Bolt — F3125 mechanical properties", "https://portlandbolt.com/print/?table=6728"),
        ("Portland Bolt — A325 changes under F3125", "https://www.portlandbolt.com/?p=8898"),
        ("Portland Bolt — ASTM A563", "https://www.portlandbolt.com/technical/specifications/astm-a563/"),
        ("Portland Bolt — specs & tables index", "https://www.portlandbolt.com/category/tables/"),
        ("Portland Bolt — F436 hardened washers", "https://portlandbolt.com/products/washers/hardened-round"),
        ("Fastenal — Mechanical properties of inch fasteners (PDF)", "https://crafter.fastenal.com/static-assets/pdfs/Mechanical_Properties_of_Inch_Fasteners.pdf"),
        ("AFT Fasteners — F436 dimensions", "https://aftfasteners.com/astm-f436-round-structural-washers-dimensions-mechanical-properties"),
    ]
    write_table(ws, ["Source", "URL"], src, widths=[70, 90], freeze=False)
    for r in range(2, len(src) + 2):
        c = ws.cell(row=r, column=2)
        c.hyperlink = c.value
        c.font = Font(name=FONT, size=10, color="0563C1", underline="single")


def main():
    drawings = build_all(DWG_DIR)
    wb = Workbook()
    sheet_guide(wb, drawings)
    sheet_standards(wb)
    sheet_bolt_props(wb)
    sheet_nut_props(wb)
    sheet_compat(wb)
    sheet_dim_struct(wb)
    sheet_dim_hex(wb)
    t_first, t_last = sheet_threads(wb)
    sheet_selector(wb, t_first, t_last)
    sheet_coat_tests(wb)
    sheet_drawings(wb, drawings)
    n_p, n_s = sheet_parents_skus(wb)
    sheet_sources(wb)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"saved {OUT}: {len(STANDARDS)} standards, {n_p} parents, {n_s} SKUs, {len(drawings)} drawings")


if __name__ == "__main__":
    main()
