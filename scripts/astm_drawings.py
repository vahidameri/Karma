"""Schematic technical drawings for the ASTM fastener workbook.

Drawings are proportional schematics (not to a specific size) labelled with the
dimension symbols used in the dimension tables (ASME B18.2.x conventions).
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, RegularPolygon, FancyBboxPatch, Arc

INK = "#1f2a44"
DIM = "#c0392b"
FILL = "#dfe6ee"
THREAD = "#8a97a8"
CENTER = "#7f8c8d"


def new(title, w=10, h=6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=110)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.suptitle(title, fontsize=13, fontweight="bold", color=INK, y=0.97)
    return fig, ax


def footer(fig, txt):
    fig.text(0.5, 0.02, txt, ha="center", fontsize=8, color="#555", style="italic")


def centerline(ax, p1, p2):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=CENTER, lw=0.8, ls=(0, (8, 3, 2, 3)))


def dim(ax, p1, p2, off, text, vertical=False, fs=10):
    """Linear dimension between p1 and p2, offset perpendicular by `off`."""
    (x1, y1), (x2, y2) = p1, p2
    if vertical:
        xd = x1 + off
        ax.plot([x1, xd + 0.15 * math.copysign(1, off)], [y1, y1], color=DIM, lw=0.6)
        ax.plot([x2, xd + 0.15 * math.copysign(1, off)], [y2, y2], color=DIM, lw=0.6)
        ax.annotate("", (xd, y1), (xd, y2), arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.9, mutation_scale=9))
        ax.text(xd + 0.12 * math.copysign(1, off), (y1 + y2) / 2, text, color=DIM, fontsize=fs,
                ha="left" if off > 0 else "right", va="center", fontweight="bold")
    else:
        yd = y1 + off
        ax.plot([x1, x1], [y1, yd + 0.15 * math.copysign(1, off)], color=DIM, lw=0.6)
        ax.plot([x2, x2], [y2, yd + 0.15 * math.copysign(1, off)], color=DIM, lw=0.6)
        ax.annotate("", (x1, yd), (x2, yd), arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.9, mutation_scale=9))
        ax.text((x1 + x2) / 2, yd + 0.12 * math.copysign(1, off), text, color=DIM, fontsize=fs,
                ha="center", va="bottom" if off > 0 else "top", fontweight="bold")


def threads(ax, x0, x1, yb, yt, pitch=0.22):
    x = x0
    while x < x1 - 1e-6:
        ax.plot([x, min(x + pitch / 2, x1)], [yt, yt + 0.06], color=THREAD, lw=0.6)
        ax.plot([x, min(x + pitch / 2, x1)], [yb, yb - 0.06], color=THREAD, lw=0.6)
        ax.plot([x, x + pitch * 0.6], [yb + 0.07, yt - 0.07], color=THREAD, lw=0.5)
        x += pitch
    ax.plot([x0, x1], [yb + 0.09, yb + 0.09], color=THREAD, lw=0.5, ls="--")
    ax.plot([x0, x1], [yt - 0.09, yt - 0.09], color=THREAD, lw=0.5, ls="--")


def hex_side(ax, x0, w, half_corner, half_flat_face):
    """Hex head side view (across corners), width w along x, centred on y=0."""
    c = half_corner
    ax.add_patch(Rectangle((x0, -c), w, 2 * c, fc=FILL, ec=INK, lw=1.4))
    # face lines of hex seen across corners
    f = half_flat_face
    ax.plot([x0, x0 + w], [f, f], color=INK, lw=0.8)
    ax.plot([x0, x0 + w], [-f, -f], color=INK, lw=0.8)
    # chamfer arcs
    for s in (1, -1):
        ax.add_patch(Arc((x0 + w, s * (c + f) / 2), 0.25, (c - f), theta1=-90, theta2=90, color=INK, lw=0.6))


def hex_top(ax, cx, cy, F, label=None, fs=9, washer_face=True):
    r = F / math.sqrt(3)  # circumradius from across-flats
    ax.add_patch(RegularPolygon((cx, cy), 6, radius=r, orientation=0, fc=FILL, ec=INK, lw=1.4))
    if washer_face:
        ax.add_patch(Circle((cx, cy), F / 2 * 0.97, fc="none", ec=INK, lw=0.7))
    if label:
        ax.text(cx, cy, label, ha="center", va="center", fontsize=fs, color=INK, fontweight="bold")
    return r


def save(fig, path):
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------

def dwg_heavy_hex_bolt(path):
    fig, ax = new("DWG-01  Heavy Hex Structural Bolt — ASTM F3125 (A325 / A490)  ·  dims: ASME B18.2.6")
    D, H, L, LT, F = 1.0, 0.62, 5.0, 1.9, 1.625
    G = F * 2 / math.sqrt(3)
    hex_side(ax, -H, H, G / 2, F / 2 * 0.5)
    ax.add_patch(Rectangle((0, -D / 2), L, D, fc=FILL, ec=INK, lw=1.4))
    threads(ax, L - LT, L, -D / 2, D / 2)
    ax.plot([L, L], [-D / 2, D / 2], color=FILL, lw=2)
    ax.add_patch(Polygon([[L - 0.08, -D / 2], [L, -D / 2 + 0.08], [L, D / 2 - 0.08], [L - 0.08, D / 2]], fc=FILL, ec=INK, lw=1.2))
    centerline(ax, (-H - 0.4, 0), (L + 0.4, 0))
    dim(ax, (0, D / 2), (L, D / 2), 0.9, "L  (nominal length: under head → end)")
    dim(ax, (L - LT, -D / 2), (L, -D / 2), -0.55, "LT  thread length")
    dim(ax, (-H, -G / 2), (0, -G / 2), -0.45, "H")
    dim(ax, (L, -D / 2), (L, D / 2), 0.45, "D  (nominal dia.)", vertical=True)
    dim(ax, (-H, -G / 2), (-H, G / 2), -0.35, "G (corners)", vertical=True)
    # top view
    cx, cy = -3.3, 0
    r = hex_top(ax, cx, cy, F, "A325\nXYZ", fs=8)
    dim(ax, (cx - F / 2, cy - r - 0.05), (cx + F / 2, cy - r - 0.05), -0.35, "F  (across flats)")
    ax.plot([cx - F / 2, cx - F / 2], [cy, cy - r - 0.4], color=DIM, lw=0.6)
    ax.plot([cx + F / 2, cx + F / 2], [cy, cy - r - 0.4], color=DIM, lw=0.6)
    ax.text(cx, cy + r + 0.25, "Top view — grade mark + manufacturer ID\n(Type 3 weathering: grade mark underlined)", ha="center", fontsize=8, color=INK)
    ax.text(L - LT / 2, D / 2 + 0.15, "UNC 2A", ha="center", fontsize=8, color=THREAD)
    ax.set_xlim(-5, L + 1.6); ax.set_ylim(-2.3, 2.6)
    footer(fig, "Schematic, not to scale. F = 1.5D + 1/8 in · heavy hex · washer face optional · threads per ASME B1.1 UNC class 2A (galvanized: overtapped nut)")
    save(fig, path)


def dwg_hex_bolt(path):
    fig, ax = new("DWG-02  Hex Bolt / Hex Cap Screw — ASTM A307, A449, A354, A394  ·  dims: ASME B18.2.1")
    D, H, L, F = 0.8, 0.55, 5.4, 1.2
    G = F * 2 / math.sqrt(3)
    LT = 2 * D + 0.4
    hex_side(ax, -H, H, G / 2, F / 2 * 0.5)
    ax.add_patch(Rectangle((0, -D / 2), L, D, fc=FILL, ec=INK, lw=1.4))
    threads(ax, L - LT, L, -D / 2, D / 2)
    centerline(ax, (-H - 0.4, 0), (L + 0.4, 0))
    dim(ax, (0, D / 2), (L, D / 2), 0.8, "L")
    dim(ax, (L - LT, -D / 2), (L, -D / 2), -0.5, "LT = 2D + 1/4\" (L ≤ 6\")  ·  2D + 1/2\" (L > 6\")")
    dim(ax, (-H, -G / 2), (0, -G / 2), -0.4, "H")
    dim(ax, (L, -D / 2), (L, D / 2), 0.4, "D", vertical=True)
    cx = -2.6
    r = hex_top(ax, cx, 0, F, "307A", fs=9)
    dim(ax, (cx - F / 2, -r - 0.05), (cx + F / 2, -r - 0.05), -0.35, "F")
    hex_top(ax, cx - 1.8, 0, F, "", fs=9)
    for a in (90, 210, 330):
        ax.plot([cx - 1.8, cx - 1.8 + 0.42 * math.cos(math.radians(a))], [0, 0.42 * math.sin(math.radians(a))], color=INK, lw=1.6)
    ax.text(cx - 1.8, -r - 0.25, "A449 (3 radial lines)", ha="center", va="top", fontsize=8)
    ax.text(cx, r + 0.2, "A307 Gr A", ha="center", fontsize=8)
    ax.set_xlim(-5.4, L + 1.4); ax.set_ylim(-2.0, 2.2)
    footer(fig, "Schematic, not to scale. Hex cap screw (finished) has tighter tolerances and washer face; hex bolt is the general (unfinished) style.")
    save(fig, path)


def dwg_nuts(path):
    fig, ax = new("DWG-03  Hex & Heavy Hex Nuts — ASTM A563, A194, F594, F467  ·  dims: ASME B18.2.2")
    for i, (F, T, name, mark) in enumerate([(1.5, 0.86, "Hex nut", "A"), (1.625, 0.98, "Heavy hex nut", "DH")]):
        ox = i * 5.0
        G = F * 2 / math.sqrt(3)
        r = hex_top(ax, ox, 0, F, None)
        ax.add_patch(Circle((ox, 0), 0.45, fc="white", ec=INK, lw=1.0))
        ax.text(ox, 0.6, mark, ha="center", va="center", fontsize=9, fontweight="bold", color=INK)
        ax.add_patch(Circle((ox, 0), 0.5, fc="none", ec=THREAD, lw=0.6, ls="--"))
        dim(ax, (ox - F / 2, -r - 0.05), (ox + F / 2, -r - 0.05), -0.3, "F")
        ax.plot([ox - F / 2] * 2, [0, -r - 0.35], color=DIM, lw=0.6)
        ax.plot([ox + F / 2] * 2, [0, -r - 0.35], color=DIM, lw=0.6)
        ax.annotate("", (ox - G / 2 * math.cos(0), 0), (ox + G / 2, 0), arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.6, mutation_scale=7))
        ax.text(ox + G / 2 + 0.08, 0.08, "G", color=DIM, fontsize=9, fontweight="bold")
        sx = ox + 1.6
        ax.add_patch(Rectangle((sx, -G / 2), T, G, fc=FILL, ec=INK, lw=1.4))
        ax.plot([sx, sx + T], [F / 4, F / 4], color=INK, lw=0.7)
        ax.plot([sx, sx + T], [-F / 4, -F / 4], color=INK, lw=0.7)
        ax.plot([sx, sx + T], [0.5, 0.5], color=THREAD, lw=0.6, ls="--")
        ax.plot([sx, sx + T], [-0.5, -0.5], color=THREAD, lw=0.6, ls="--")
        dim(ax, (sx, G / 2), (sx + T, G / 2), 0.3, "H (thickness)")
        ax.text(ox + 0.8, r + 0.75, name, ha="center", fontsize=11, fontweight="bold", color=INK)
    ax.set_xlim(-1.4, 8.2); ax.set_ylim(-2.0, 2.4)
    footer(fig, "Heavy hex: F = 1.5D + 1/8\", H ≈ D − 1/64\"  ·  Hex: F ≈ 1.5D (≤5/8\"), H ≈ 7/8 D  ·  marking on one face (grade + mfr ID)")
    save(fig, path)


def dwg_washer(path):
    fig, ax = new("DWG-04  Hardened Steel Washer — ASTM F436 (Type 1 / Type 3)  ·  plain washer F844", 10, 5)
    OD, ID, T = 2.0, 1.125, 0.18
    ax.add_patch(Circle((0, 0), OD / 2, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Circle((0, 0), ID / 2, fc="white", ec=INK, lw=1.4))
    ax.text(0, OD / 2 - 0.22, "F436  XYZ", ha="center", fontsize=8, fontweight="bold", color=INK)
    dim(ax, (-OD / 2, 0), (OD / 2, 0), -1.25, "OD")
    ax.plot([-OD / 2] * 2, [0, -1.35], color=DIM, lw=0.6); ax.plot([OD / 2] * 2, [0, -1.35], color=DIM, lw=0.6)
    ax.annotate("", (-ID / 2, 0), (ID / 2, 0), arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.8, mutation_scale=8))
    ax.text(0, 0.08, "ID", color=DIM, ha="center", fontsize=10, fontweight="bold")
    sx = 2.2
    ax.add_patch(Rectangle((sx, -OD / 2), T * 2.5, OD / 2 - ID / 2, fc=FILL, ec=INK, lw=1.4, hatch="///"))
    ax.add_patch(Rectangle((sx, ID / 2), T * 2.5, OD / 2 - ID / 2, fc=FILL, ec=INK, lw=1.4, hatch="///"))
    dim(ax, (sx, OD / 2), (sx + T * 2.5, OD / 2), 0.3, "T")
    ax.text(sx + 0.25, -1.4, "Section", ha="center", fontsize=9)
    # clipped washer
    cx = 5.0
    ax.add_patch(Circle((cx, 0), OD / 2, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Rectangle((cx + 0.7, -1.1), 0.5, 2.2, fc="white", ec="none"))
    ax.plot([cx + 0.7, cx + 0.7], [-math.sqrt(1 - 0.49), math.sqrt(1 - 0.49)], color=INK, lw=1.4)
    ax.add_patch(Circle((cx, 0), ID / 2, fc="white", ec=INK, lw=1.4))
    ax.text(cx, -1.35, "Clipped (one side) — for tight\ngauge near web/flange", ha="center", va="top", fontsize=8)
    ax.text(cx + 0.95, 0, "E", color=DIM, fontsize=10, fontweight="bold", va="center")
    ax.set_xlim(-1.6, 6.6); ax.set_ylim(-2.0, 1.6)
    footer(fig, "F436 Type 1 through-hardened HRC 38–45 (26–45 if hot-dip galvanized) · bevelled square washers for sloped flanges also covered")
    save(fig, path)


def dwg_stud(path):
    fig, ax = new("DWG-05  Stud Bolt / All-Thread Stud with Heavy Hex Nuts — ASTM A193 B7 + A194 2H")
    D, L = 0.9, 7.0
    ax.add_patch(Rectangle((0, -D / 2), L, D, fc=FILL, ec=INK, lw=1.4))
    threads(ax, 0, L, -D / 2, D / 2)
    for x in (0, L):
        s = 1 if x == 0 else -1
        ax.add_patch(Polygon([[x, -D / 2 + 0.1], [x + s * 0.1, -D / 2], [x + s * 0.1, D / 2], [x, D / 2 - 0.1]], fc=FILL, ec=INK, lw=1.0))
    F = 1.5 * D + 0.125; G = F * 2 / math.sqrt(3); T = D - 0.02
    for nx in (0.6, L - 0.6 - T):
        ax.add_patch(Rectangle((nx, -G / 2), T, G, fc="#c9d3df", ec=INK, lw=1.4))
        ax.text(nx + T / 2, 0, "2H", ha="center", va="center", fontsize=9, fontweight="bold")
    centerline(ax, (-0.4, 0), (L + 0.4, 0))
    dim(ax, (0, D / 2), (L, D / 2), 1.1, "L  (first thread to first thread, excl. chamfer points)")
    dim(ax, (L, -D / 2), (L, D / 2), 0.4, "D", vertical=True)
    ax.text(L / 2, -1.3, "B7: 8-UN thread series for D ≥ 1\"  ·  end marking 'B7' on one end (≥ 3/8\")", ha="center", fontsize=9, color=INK)
    ax.set_xlim(-0.8, L + 1.4); ax.set_ylim(-1.8, 2.2)
    footer(fig, "Pressure / flange bolting (ASME B16.5 flanges). Heavy hex nuts per ASME B18.2.2. Coatings: plain/black oxide, PTFE, HDG (A153/F2329), zinc-nickel.")
    save(fig, path)


def dwg_anchor(path):
    fig, ax = new("DWG-06  Anchor Rods — ASTM F1554 (Gr 36 / 55 / 105)", 11, 6.5)
    D = 0.5
    cfgs = [("Headed", 0), ("Bent (L / 90° hook)", 3.2), ("Threaded both ends + nut", 6.4)]
    for name, x in cfgs:
        top, bot = 5.0, 0.3
        ax.add_patch(Rectangle((x - D / 2, bot), D, top - bot, fc=FILL, ec=INK, lw=1.4))
        threads_v = [(x - D / 2, top - 1.5, top)]
        for (xx, y0, y1) in threads_v:
            y = y0
            while y < y1:
                ax.plot([xx - 0.05, xx + D + 0.05], [y, y + 0.08], color=THREAD, lw=0.6); y += 0.18
        ax.add_patch(Rectangle((x - 0.45, top - 1.1), 0.9, 0.45, fc="#c9d3df", ec=INK, lw=1.2))
        ax.add_patch(Rectangle((x - D / 2, top - 0.12), D, 0.12, fc="#2e64c8" if x == 0 else ("#f1c40f" if x == 3.2 else "#c0392b"), ec=INK, lw=0.8))
        if name.startswith("Headed"):
            ax.add_patch(Rectangle((x - 0.45, bot - 0.3), 0.9, 0.3, fc="#c9d3df", ec=INK, lw=1.2))
        elif name.startswith("Bent"):
            ax.add_patch(Rectangle((x - D / 2, bot - 0.4), 1.6, D, fc=FILL, ec=INK, lw=1.4))
            dim(ax, (x - D / 2, bot - 0.4), (x + 1.35, bot - 0.4), -0.35, "hook")
        else:
            y = bot
            while y < bot + 1.2:
                ax.plot([x - D / 2 - 0.05, x + D / 2 + 0.05], [y, y + 0.08], color=THREAD, lw=0.6); y += 0.18
            ax.add_patch(Rectangle((x - 0.45, bot + 0.3), 0.9, 0.45, fc="#c9d3df", ec=INK, lw=1.2))
        ax.text(x, top + 0.45, name, ha="center", fontsize=10, fontweight="bold")
    dim(ax, (0.25, 0.3), (0.25, 5.0), 0.7, "L", vertical=True)
    dim(ax, (6.4 + 0.25, 3.5), (6.4 + 0.25, 5.0), 0.7, "thread\nlength", vertical=True, fs=8)
    ax.add_patch(Rectangle((-1.2, 3.0), 9.8, 0.05, fc="#7f8c8d", ec="none"))
    ax.text(8.7, 3.05, "top of\nconcrete", fontsize=8, va="bottom")
    lx = 9.3
    for i, (c, t) in enumerate([("#2e64c8", "Gr 36  → blue"), ("#f1c40f", "Gr 55  → yellow"), ("#c0392b", "Gr 105 → red")]):
        ax.add_patch(Rectangle((lx, 4.6 - i * 0.5), 0.3, 0.3, fc=c, ec=INK))
        ax.text(lx + 0.45, 4.75 - i * 0.5, t, va="center", fontsize=9)
    ax.text(lx, 5.2, "End colour code (F1554)", fontsize=9, fontweight="bold")
    ax.set_xlim(-1.4, 12.2); ax.set_ylim(-0.9, 5.8)
    footer(fig, "Projecting end painted per grade (or stamped on end). Gr 55 S1 = weldable. Nuts A563 / A194; washers F436 or plate washers.")
    save(fig, path)


def dwg_tc(path):
    fig, ax = new("DWG-07  Tension-Control (Twist-Off) Bolt — F3125 Grade F1852 / F2280  ·  F3148 / F3043")
    D, L, LT = 0.9, 5.0, 1.8
    ax.add_patch(Polygon([[0, -1.0], [-0.35, -0.85], [-0.5, -0.5], [-0.55, 0], [-0.5, 0.5], [-0.35, 0.85], [0, 1.0]], fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Rectangle((0, -D / 2), L, D, fc=FILL, ec=INK, lw=1.4))
    threads(ax, L - LT, L, -D / 2, D / 2)
    ax.add_patch(Polygon([[L, -0.22], [L + 0.15, -0.12], [L + 0.15, 0.12], [L, 0.22]], fc="#c0392b", ec=INK, lw=1.0))
    ax.add_patch(Rectangle((L + 0.15, -0.32), 0.7, 0.64, fc="#c9d3df", ec=INK, lw=1.2))
    for y in (-0.2, -0.07, 0.07, 0.2):
        ax.plot([L + 0.15, L + 0.85], [y, y], color=INK, lw=0.5)
    centerline(ax, (-0.8, 0), (L + 1.2, 0))
    dim(ax, (0, D / 2), (L, D / 2), 0.95, "L")
    dim(ax, (L - LT, -D / 2), (L, -D / 2), -0.6, "LT")
    ax.annotate("break-neck groove\n(shears at target tension)", (L + 0.08, 0.2), (L - 1.0, 1.9), fontsize=8, color=DIM,
                arrowprops=dict(arrowstyle="->", color=DIM))
    ax.annotate("spline (held by\ninner socket)", (L + 0.5, -0.3), (L + 0.3, -1.6), fontsize=8, color=DIM,
                arrowprops=dict(arrowstyle="->", color=DIM))
    ax.annotate("round / button head\n(no wrench needed on head side)", (-0.45, -0.6), (-2.6, -1.7), fontsize=8, color=DIM,
                arrowprops=dict(arrowstyle="->", color=DIM))
    ax.set_xlim(-3.0, L + 1.5); ax.set_ylim(-2.0, 2.3)
    footer(fig, "Supplied as a pre-lubricated assembly (bolt + A563 DH nut + F436 washer) from one manufacturing lot. Head marked 'F1852' or 'F2280' (or S1852/S2280 style per mfr).")
    save(fig, path)


def dwg_dti(path):
    fig, ax = new("DWG-08  Direct Tension Indicator (DTI) — ASTM F959 (Type 120 / 150 ksi)", 10, 5)
    ax.add_patch(Circle((0, 0), 1.0, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Circle((0, 0), 0.55, fc="white", ec=INK, lw=1.4))
    for k in range(6):
        a = math.radians(k * 60 + 30)
        ax.add_patch(FancyBboxPatch((0.77 * math.cos(a) - 0.09, 0.77 * math.sin(a) - 0.05), 0.18, 0.1,
                                    boxstyle="round,pad=0.02", fc="#c9d3df", ec=INK, lw=0.8))
        ax.add_patch(Circle((0.77 * math.cos(a), 0.77 * math.sin(a)), 0.03, fc="#e67e22", ec="none"))
    ax.text(0, -1.25, "Protrusions (bumps) + optional orange squirt silicone", ha="center", fontsize=8)
    sx = 2.2
    ax.add_patch(Rectangle((sx, -1.0), 0.18, 0.45, fc=FILL, ec=INK, lw=1.2))
    ax.add_patch(Rectangle((sx, 0.55), 0.18, 0.45, fc=FILL, ec=INK, lw=1.2))
    for y in (-0.8, 0.75):
        ax.add_patch(Polygon([[sx + 0.18, y - 0.1], [sx + 0.32, y], [sx + 0.18, y + 0.1]], fc="#c9d3df", ec=INK))
    ax.add_patch(Rectangle((sx + 0.32, -1.0), 0.12, 2.0, fc="#ecf0f1", ec=INK, lw=1.0))
    ax.text(sx + 0.38, 1.15, "gap measured with\nfeeler gauge (refusal)", fontsize=8, ha="center")
    ax.text(sx + 0.15, -1.3, "Section", ha="center", fontsize=9)
    ax.text(4.2, 0.3, "Installed under bolt head\n(bumps toward head)\nor under nut with\nhardened washer.\nType 3 = weathering.", fontsize=9, va="center")
    ax.set_xlim(-1.4, 6.6); ax.set_ylim(-1.6, 1.6)
    footer(fig, "F959 Type 120 (for F3125 Gr A325 / F1852) and Type 150 (for A490 / F2280). Metric F959M: 8.8 and 10.9.")
    save(fig, path)


def dwg_shcs(path):
    fig, ax = new("DWG-09  Socket Head Cap Screw — ASTM A574  ·  dims: ASME B18.3", 10, 5)
    A, H, D, L, J = 1.5, 1.0, 1.0, 4.5, 0.6
    ax.add_patch(Rectangle((-H, -A / 2), H, A, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Rectangle((-H, -J / 2 * 1.15), H * 0.55, J * 1.15, fc="white", ec=INK, lw=0.8, ls="--"))
    ax.add_patch(Rectangle((0, -D / 2), L, D, fc=FILL, ec=INK, lw=1.4))
    threads(ax, L - 2.0, L, -D / 2, D / 2)
    centerline(ax, (-H - 0.3, 0), (L + 0.3, 0))
    dim(ax, (-H, -A / 2), (-H, A / 2), -0.35, "A (head dia.)", vertical=True)
    dim(ax, (-H, A / 2), (0, A / 2), 0.3, "H")
    dim(ax, (0, D / 2), (L, D / 2), 0.7, "L")
    dim(ax, (L, -D / 2), (L, D / 2), 0.35, "D", vertical=True)
    cx = -3.5
    ax.add_patch(Circle((cx, 0), A / 2, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(RegularPolygon((cx, 0), 6, radius=J / math.sqrt(3), orientation=0, fc="white", ec=INK, lw=1.2))
    ax.text(cx, -A / 2 - 0.25, "J = hex socket size (across flats)", ha="center", va="top", fontsize=8, color=DIM)
    ax.set_xlim(-5, L + 1.2); ax.set_ylim(-1.6, 1.6)
    footer(fig, "A574: alloy steel Q&T, 180 ksi (≤1/2\") / 170 ksi (>1/2\"), HRC 39–45 / 37–45. Knurled head; black oxide + oil typical.")
    save(fig, path)


def dwg_markings(path):
    fig, ax = new("DWG-10  Grade Head / Face Markings — ASTM bolts & nuts (top views)", 12, 7)
    items = [
        ("A307 Gr A", "307A"), ("A307 Gr B", "307B"), ("F3125 A325\nType 1", "A325"), ("F3125 A325\nType 3", "A325_"),
        ("F3125 A490\nType 1", "A490"), ("F3125 A490\nType 3", "A490_"), ("A449", "|||"), ("A354 BC", "BC"),
        ("A354 BD", "BD"), ("A193 B7", "B7"), ("A193 B7M", "B7M"), ("A193 B8", "B8"),
        ("A194 2H nut", "2H"), ("A194 2HM nut", "2HM"), ("A563 DH nut", "DH"), ("A563 DH3 nut", "DH3"),
        ("F1554 Gr 36\n(rod end)", "36"), ("F1554 Gr 55", "55"), ("F1554 Gr 105", "105"), ("F593 / F594\nstainless", "F593"),
    ]
    F = 1.25
    for i, (name, mark) in enumerate(items):
        r, c = divmod(i, 5)
        cx, cy = c * 2.4, -r * 2.3
        if mark in ("36", "55", "105"):
            col = {"36": "#2e64c8", "55": "#f1c40f", "105": "#c0392b"}[mark]
            ax.add_patch(Circle((cx, cy), 0.55, fc=col, ec=INK, lw=1.4))
            ax.text(cx, cy, mark, ha="center", va="center", fontsize=10, fontweight="bold", color="white" if mark != "55" else INK)
        elif mark == "|||":
            hex_top(ax, cx, cy, F, None)
            for a in (90, 210, 330):
                ax.plot([cx, cx + 0.45 * math.cos(math.radians(a))], [cy, cy + 0.45 * math.sin(math.radians(a))], color=INK, lw=2)
        else:
            underline = mark.endswith("_")
            m = mark.rstrip("_")
            hex_top(ax, cx, cy, F, m, fs=10)
            if underline:
                ax.plot([cx - 0.3, cx + 0.3], [cy - 0.15, cy - 0.15], color=INK, lw=1.5)
            ax.text(cx, cy - 0.33, "XYZ", ha="center", fontsize=6, color="#555")
        ax.text(cx, cy - 0.95, name, ha="center", va="top", fontsize=8.5, color=INK)
    ax.set_xlim(-1.2, 10.8); ax.set_ylim(-10.0, 1.2)
    footer(fig, "XYZ = manufacturer identification mark (required). Underline = Type 3 weathering steel. A449 marking per spec: three radial lines (optionally with 'A449').")
    save(fig, path)


def dwg_joint(path):
    fig, ax = new("DWG-11  Structural Bolted Joint Assembly — bolt + F436 washer + heavy hex nut (RCSC)", 11, 6)
    D, Hh = 0.75, 0.47
    plate_w = 3.0
    ax.add_patch(Rectangle((-plate_w / 2, 0), plate_w, 0.75, fc="#bdc3c7", ec=INK, hatch="//", lw=1.2))
    ax.add_patch(Rectangle((-plate_w / 2, -0.75), plate_w, 0.75, fc="#d5dbdb", ec=INK, hatch="\\\\", lw=1.2))
    ax.add_patch(Rectangle((-D / 2 - 0.03, -0.75), D + 0.06, 1.5, fc="white", ec="none"))
    ax.add_patch(Rectangle((-D / 2, -1.45), D, 2.6, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Rectangle((-0.65, 0.75 + 0.0), 1.3, Hh, fc=FILL, ec=INK, lw=1.4))
    ax.add_patch(Rectangle((-0.75, -0.89), 1.5, 0.14, fc="#95a5a6", ec=INK, lw=1.2))
    ax.add_patch(Rectangle((-0.68, -0.89 - 0.73), 1.36, 0.73, fc="#c9d3df", ec=INK, lw=1.4))
    y = -1.45
    while y < -0.45:
        ax.plot([-D / 2 - 0.05, D / 2 + 0.05], [y, y + 0.07], color=THREAD, lw=0.6); y += 0.13
    dim(ax, (0.9, -0.75), (0.9, 0.75), 1.0, "Grip (material thickness)", vertical=True, fs=9)
    ax.text(-0.0, 0.75 + Hh + 0.15, "bolt head (turn the nut, not the head)", ha="center", fontsize=8)
    ax.text(-1.0, -0.82, "F436 washer\n(under turned element)", ha="right", va="center", fontsize=8)
    ax.text(-1.0, -1.3, "A563 DH heavy hex nut", ha="right", va="center", fontsize=8)
    ax.text(-0.0, -1.85, "stick-out ≥ flush with nut face", ha="center", fontsize=8)
    tx = 3.6
    rows = ["Joint types (RCSC 2020):", "• Snug-tight (ST)", "• Pretensioned (PT)", "• Slip-critical (SC) — Class A / B faying surfaces", "",
            "Pretension methods:", "• Turn-of-nut  (1/3, 1/2, 2/3 turn by L/D)", "• Calibrated wrench", "• Twist-off TC bolt (F1852/F2280)",
            "• DTI (F959)", "", "Thread condition in shear plane:", "• N = threads iNcluded", "• X = threads eXcluded"]
    for i, t in enumerate(rows):
        ax.text(tx, 1.3 - i * 0.24, t, fontsize=9, fontweight="bold" if t.endswith(":") else "normal", color=INK)
    ax.set_xlim(-3.2, 8.6); ax.set_ylim(-2.2, 1.6)
    footer(fig, "Schematic. Select length so that threads stick out of nut and nut does not bottom on thread run-out (L = grip + table allowance).")
    save(fig, path)


DRAWINGS = [
    ("DWG-01", "Heavy hex structural bolt (F3125)", dwg_heavy_hex_bolt),
    ("DWG-02", "Hex bolt / hex cap screw (A307, A449, A354)", dwg_hex_bolt),
    ("DWG-03", "Hex & heavy hex nuts (A563, A194)", dwg_nuts),
    ("DWG-04", "Hardened washer (F436) & clipped washer", dwg_washer),
    ("DWG-05", "Stud bolt with nuts (A193 B7 + A194 2H)", dwg_stud),
    ("DWG-06", "Anchor rods (F1554) & colour code", dwg_anchor),
    ("DWG-07", "Tension-control twist-off bolt (F1852/F2280)", dwg_tc),
    ("DWG-08", "Direct tension indicator (F959)", dwg_dti),
    ("DWG-09", "Socket head cap screw (A574)", dwg_shcs),
    ("DWG-10", "Grade markings gallery", dwg_markings),
    ("DWG-11", "Structural bolted joint assembly", dwg_joint),
]


def build_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for code, title, fn in DRAWINGS:
        p = os.path.join(out_dir, f"{code}.png")
        fn(p)
        paths.append((code, title, p))
    return paths


if __name__ == "__main__":
    for c, t, p in build_all(sys.argv[1] if len(sys.argv) > 1 else "output/astm_drawings"):
        print(c, p)
