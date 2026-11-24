#!/usr/bin/env python3
"""Draw a sheet (FORMAT.md) as a page: one self-contained HTML file, or a PDF with --pdf.

    python3 render.py SHEET.json ... [--pdf] [-o DIR] [-j N]
    python3 render.py NAME ... | all          (a file stem under datasheets/<kind>/)

The page is the HTML file: `all` writes every sheet's in a few seconds, and
index.html beside this script, which lists them. A PDF is that page printed,
about a second each; -j N prints N at a time.

Writes NAME.html (or NAME.pdf) beside the sheet, or into DIR. The page is one
file: its styles and drawings are in it, and it loads nothing. Every part of
it is a <section> with an id (NAME.html#absolute-maximum-ratings,
#circuit-<circuit id>), and every graph a <figure> with one. Graphs are
drawn here from each curve's points; a circuit's drawing is the SVG beside
the sheet, NAME.<circuit id>.svg. Python 3, standard library only; --pdf
needs Chrome or Chromium."""
import csv
import glob
import html
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import threading

ROOT =os.path.dirname(os.path.abspath(__file__))
COLOURS = ["#1b4f9c", "#c8321f", "#2a7d3f", "#7a45b5", "#c27700", "#141414", "#0e8a8a", "#a8326e"]
DASHES = ["", "6 3", "2 3", "8 3 2 3", "", "6 3", "2 3", "8 3 2 3"]

CSS = """
:root{--ink:#141414;--grey:#63635f;--hair:#d0cfcb;--faint:#f3f3f1}
*{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:#fff;color:var(--ink);font:400 14px/1.45 "Helvetica Neue",Helvetica,Arial,sans-serif;padding:32px 16px 64px}
.page{max-width:860px;margin:0 auto}
header{border-bottom:2px solid var(--ink);padding-bottom:14px;margin-bottom:6px}
header .maker{font-size:13px;color:var(--grey)}
h1{margin:2px 0 0;font:700 30px/1.15 "Helvetica Neue",Helvetica,Arial,sans-serif;letter-spacing:-.01em}
h1 span{display:block;font-weight:400;font-size:19px;color:var(--grey);margin-top:4px}
.summary{font-size:15.5px;max-width:70ch;margin:16px 0 6px}
h2{font:700 17px/1.3 "Helvetica Neue",Helvetica,Arial,sans-serif;margin:34px 0 10px;padding-top:10px;border-top:1px solid var(--ink)}
h3{font:700 14px/1.35 "Helvetica Neue",Helvetica,Arial,sans-serif;margin:20px 0 6px;break-after:avoid}
h3 .pg,h2 .pg{font-weight:400;color:var(--grey);font-size:12px;margin-left:8px}
p{margin:6px 0;max-width:74ch}
.cond{color:var(--grey);font-size:13px;margin:0 0 6px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 6px}
th{text-align:left;font-weight:700;border-bottom:1px solid var(--ink);padding:5px 8px 5px 0;vertical-align:bottom;font-size:12px;text-transform:capitalize}
td{border-bottom:1px solid var(--hair);padding:5px 8px 5px 0;vertical-align:top}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.sym{white-space:nowrap}
tr{break-inside:avoid}
.keys{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:0 18px;margin:14px 0 0}
.keys div{border-top:1px solid var(--hair);padding:6px 0}
.keys b{display:block;font-size:15px}
.keys span{font-size:12px;color:var(--grey)}
ol.notes{font-size:12.5px;color:var(--grey);margin:4px 0 0;padding-left:18px}
.curves{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:18px 24px}
figure{margin:0;break-inside:avoid}
figure svg{width:100%;height:auto;display:block}
.land{display:flex;flex-wrap:wrap;gap:18px}
.land figure{flex:0 0 auto;max-width:100%}
.land figure svg{width:auto;max-width:100%;height:auto}
.land figcaption{font-size:.85em;margin-top:4px}
figcaption{font-size:13px}
figcaption b{display:block}
figcaption .pg{font-weight:400;color:var(--grey);font-size:12px;margin-left:8px}
figcaption .cond{display:block}
.legend{display:flex;flex-wrap:wrap;gap:2px 14px;font-size:12px;margin-top:2px}
.legend svg{width:26px;height:8px;display:inline-block;vertical-align:middle;margin-right:4px}
.eq{font:15px/1.4 "SF Mono",Menlo,Consolas,monospace;background:var(--faint);padding:8px 10px;margin:6px 0 4px;overflow-x:auto;white-space:nowrap}
dl.where{display:grid;grid-template-columns:max-content 1fr;gap:1px 12px;font-size:13px;margin:0 0 10px}
dl.where dt{font-family:"SF Mono",Menlo,Consolas,monospace}
dl.where dd{margin:0;color:var(--grey)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:0 28px}
.circuit-drawing svg,.circuit-drawing img{max-width:100%;height:auto;border:1px solid var(--hair)}
footer{margin-top:44px;border-top:2px solid var(--ink);padding-top:10px;font-size:12px;color:var(--grey)}
.scroll{overflow-x:auto}
nav.toc{display:flex;flex-wrap:wrap;gap:2px 16px;font-size:13px;margin:18px 0 0}
a{color:#1b4f9c}
section,figure{scroll-margin-top:12px}
input.find{font:inherit;width:100%;max-width:420px;padding:7px 9px;border:1px solid var(--ink);margin:14px 0 4px}
.count{font-size:12px;color:var(--grey)}
@media (max-width:640px){.two{grid-template-columns:1fr}.curves{grid-template-columns:1fr}}
@media print{body{padding:0;font-size:12px}.page{max-width:none}h2{break-after:avoid}.curves{grid-template-columns:1fr 1fr;gap:14px 20px}}
@page{size:A4;margin:16mm 14mm}
"""

NUMERIC = {"min", "typ", "max", "nom", "typical", "minimum", "maximum"}


# ---- what points at a picture the sheet does not have
# A sheet prints nothing that points at a picture it lacks. A circuit with no drawing is not printed (its parts
# stay in the data file). A figure number is kept where the sheet has that figure (a re-plotted curve or a drawn
# circuit whose title carries the number); elsewhere a bare "(Figure 12)" goes, and one inside a sentence is named as
# the maker's. A package table is printed in words: the dimension letters name an outline the sheet does not draw.
FIGREF = re.compile(r"(?<!oise )\b(?:Figures?|Figs?\.?|FIGURES?|FIGS?\.?)\s*(\d+(?:[-.]\d+)*[a-z]?)")   # a capital F: "the figure 3.3 V" is no reference
FILLER = re.compile(r"\b(?:see|also|as|in|shown|refer|to|per|and|or|through|of|the)\b|[\s,;:&.–-]+", re.I)
ANCHORS = set()


def _only_refs(text):
    return FIGREF.search(text) is not None and not FILLER.sub("", FIGREF.sub("", text))


def unfigure(text):
    if "ig" not in text or not FIGREF.search(text):
        return text
    dangling = lambda m: m.group(1) not in ANCHORS
    if _only_refs(text) and all(dangling(m) for m in FIGREF.finditer(text)):
        return ""

    def paren(m):
        inner = m.group(1)
        refs = list(FIGREF.finditer(inner))
        if refs and all(dangling(r) for r in refs) and _only_refs(inner):
            return ""
        return m.group(0)
    text = re.sub(r"\s*\(([^()]*)\)", paren, text)
    def named(m):
        if not dangling(m) or text[max(0, m.start() - 8):m.start()].lower().endswith("maker's "):
            return m.group(0)
        start = m.start() == 0 or text[:m.start()].rstrip().endswith((".", ":", ";"))
        many = m.group(0).lower().startswith(("figs", "figures"))
        return "%s maker's Figure%s %s" % ("The" if start else "the", "s" if many else "", m.group(1))
    return FIGREF.sub(named, text)


def e(s):
    return html.escape(unfigure(str(s)), quote=False)


SYMBOL = re.compile(r"[A-Za-z\u0370-\u03ff\u00d8\u00f8\u2205]{1,3}\d{0,2}[a-z]?\.?")
VALUEISH = ("min", "typ", "nom", "max", "value", "note", "tol", "inch", "mm", "mil")


def package_table(p):
    """The package's dimensions in words: a row is kept where it says what it measures, without its letter."""
    cols = p.get("columns", [])
    val = [i for i, c in enumerate(cols) if any(c.lower().startswith(v) or ("(" + v) in c.lower() for v in VALUEISH)]
    lab = [i for i in range(len(cols)) if i not in val]
    rows, letters = [], set()
    for r in p.get("rows", []):
        cells = [str(r[i]).strip() if i < len(r) else "" for i in range(len(cols))]
        words = [cells[i] for i in lab if cells[i] and not SYMBOL.fullmatch(cells[i])]
        letters |= {cells[i] for i in lab if cells[i] and SYMBOL.fullmatch(cells[i])}
        if words and any(cells[i] for i in val):
            rows.append(["; ".join(words)] + [cells[i] for i in val])
    if not rows:
        return None
    notes = [n for n in p.get("notes", []) if not any(re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(x), n) for x in letters)]
    return {"columns": ["dimension"] + [cols[i] for i in val], "rows": rows, "notes": notes}


def pg(item):
    p = item.get("page")
    return ' <span class="pg">p. %s</span>' % e(p) if p not in (None, "") else ""


# ---- ids: every part of a page can be linked to (NAME.html#id) or lifted out by its id
IDS = {}
LOCK = threading.Lock()         # a page is written with this held: ANCHORS and IDS are one page's


def ident(text, prefix=""):
    """An id for a part of the page: its title's words in lower case joined by hyphens, after `prefix`;
    the second of a name on one page ends -2."""
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:64].strip("-")
    s = "-".join(x for x in (prefix, s) if x) or "section"
    IDS[s] = IDS.get(s, 0) + 1
    return s if IDS[s] == 1 else "%s-%d" % (s, IDS[s])


def sec(i, *content):
    return '<section id="%s">%s</section>' % (i, "".join(content))


def table(t):
    cols = t.get("columns", [])
    out = ['<div class="scroll"><table><thead><tr>']
    for c in cols:
        out.append('<th%s>%s</th>' % (' class="n"' if c.lower() in NUMERIC else "", e(c)))
    out.append("</tr></thead><tbody>")
    for r in t.get("rows", []):
        out.append("<tr>")
        for c, v in zip(cols, r):
            cls = "n" if c.lower() in NUMERIC else ("sym" if c.lower() in ("symbol", "unit", "pin") else "")
            out.append("<td%s>%s</td>" % (' class="%s"' % cls if cls else "", e(v)))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    if t.get("notes"):
        out.append('<ol class="notes">%s</ol>' % "".join("<li>%s</li>" % e(n) for n in t["notes"]))
    return "".join(out)


# ---- graphs

def nice_ticks(lo, hi, want=6):
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / want
    mag = 10 ** math.floor(math.log10(raw))
    step = min((1, 2, 2.5, 5, 10), key=lambda m: abs(m * mag - raw)) * mag
    a = math.floor(lo / step + 1e-9) * step
    b = math.ceil(hi / step - 1e-9) * step
    n = int(round((b - a) / step))
    return [a + i * step for i in range(n + 1)]


def fmt(v):
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 1e6 or a < 1e-3:
        m, x = ("%.2e" % v).split("e")
        m = m.rstrip("0").rstrip(".")
        return "%s×10^%d" % (m, int(x)) if m not in ("1", "-1") else "%s10^%d" % ("-" if v < 0 else "", int(x))
    s = "%.6g" % v
    return s


def log_fmt(v):
    a = abs(v)
    if 1e-3 <= a < 1e5:
        return "%g" % v
    return "10^%d" % round(math.log10(v))


def plot(c):
    W, H, L, R, T, B = 440, 300, 62, 14, 12, 46
    pw, ph = W - L - R, H - T - B
    series = [s for s in c.get("series", []) if s.get("points")]
    axes = {}
    two = "y2" in c and any(s.get("axis") == "y2" for s in series)
    if two:
        R = 58
        pw = W - L - R
    for key, idx in (("x", 0), ("y", 1)) + ((("y2", 1),) if two else ()):
        ax = c.get(key, {})
        vals = [p[idx] for s in series for p in s["points"] if key == "x" or s.get("axis", "y") == key]
        logs = ax.get("scale") == "log"
        if logs:
            vals = [v for v in vals if v > 0]
            lo, hi = math.floor(math.log10(min(vals)) + 1e-9), math.ceil(math.log10(max(vals)) - 1e-9)
            if hi <= lo:
                hi = lo + 1
            ticks = [10.0 ** k for k in range(lo, hi + 1)]
            minor = [m * 10.0 ** k for k in range(lo, hi) for m in range(2, 10)]
            f = (lambda lo, hi: lambda v: (math.log10(v) - lo) / (hi - lo))(lo, hi)
        else:
            lo, hi = (ax.get("min"), ax.get("max"))
            lo = min(vals) if lo is None else lo
            hi = max(vals) if hi is None else hi
            ticks = nice_ticks(lo, hi)
            minor = []
            f = (lambda a, b: lambda v: (v - a) / (b - a))(ticks[0], ticks[-1])
        axes[key] = (ticks, minor, f, logs)
    fx, fy = axes["x"][2], axes["y"][2]
    X = lambda v: L + fx(v) * pw
    Y = lambda v: T + ph - fy(v) * ph
    Y2 = (lambda f2: lambda v: T + ph - f2(v) * ph)(axes["y2"][2]) if two else Y
    o = ['<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica Neue,Helvetica,Arial,sans-serif" font-size="11">' % (W, H)]
    for v in axes["x"][1]:
        o.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="#ececea"/>' % (X(v), X(v), T, T + ph))
    for v in axes["y"][1]:
        o.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#ececea"/>' % (L, L + pw, Y(v), Y(v)))
    for v in axes["x"][0]:
        o.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="#d0cfcb"/>' % (X(v), X(v), T, T + ph))
        o.append('<text x="%.1f" y="%d" text-anchor="middle" fill="#141414">%s</text>' % (X(v), T + ph + 15, e(log_fmt(v) if axes["x"][3] else fmt(v))))
    for v in axes["y"][0]:
        o.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#d0cfcb"/>' % (L, L + pw, Y(v), Y(v)))
        o.append('<text x="%d" y="%.1f" text-anchor="end" fill="#141414">%s</text>' % (L - 6, Y(v) + 4, e(log_fmt(v) if axes["y"][3] else fmt(v))))
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#141414"/>' % (L, T, pw, ph))
    if two:
        for v in axes["y2"][0]:
            o.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#141414"/>' % (L + pw, L + pw + 4, Y2(v), Y2(v)))
            o.append('<text x="%d" y="%.1f" text-anchor="start" fill="#141414">%s</text>' % (L + pw + 7, Y2(v) + 4, e(log_fmt(v) if axes["y2"][3] else fmt(v))))
    for i, s in enumerate(series):
        ak = s.get("axis", "y") if two else "y"
        YY = Y2 if ak == "y2" else Y
        pts = [p for p in s["points"] if (not axes["x"][3] or p[0] > 0) and (not axes[ak][3] or p[1] > 0)]
        d = " ".join("%.1f,%.1f" % (X(p[0]), YY(p[1])) for p in pts)
        dash = ' stroke-dasharray="%s"' % DASHES[i % 8] if DASHES[i % 8] else ""
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.8" stroke-linejoin="round"%s/>' % (d, COLOURS[i % 8], dash))
    xl = c.get("x", {})
    yl = c.get("y", {})
    lab = lambda a: a.get("label", "") + (" (%s)" % a["unit"] if a.get("unit") else "")
    o.append('<text x="%.1f" y="%d" text-anchor="middle" fill="#141414" font-size="12">%s</text>' % (L + pw / 2, H - 8, e(lab(xl))))
    o.append('<text transform="translate(14 %.1f) rotate(-90)" text-anchor="middle" fill="#141414" font-size="12">%s</text>' % (T + ph / 2, e(lab(yl))))
    if two:
        o.append('<text transform="translate(%d %.1f) rotate(90)" text-anchor="middle" fill="#141414" font-size="12">%s</text>' % (W - 10, T + ph / 2, e(lab(c["y2"]))))
    o.append("</svg>")
    leg = ""
    if len(series) > 1 or (series and series[0].get("label")):
        items = []
        for i, s in enumerate(series):
            dash = ' stroke-dasharray="%s"' % DASHES[i % 8] if DASHES[i % 8] else ""
            items.append('<span><svg viewBox="0 0 26 8"><line x1="0" x2="26" y1="4" y2="4" stroke="%s" stroke-width="2"%s/></svg>%s%s</span>'
                         % (COLOURS[i % 8], dash, e(s.get("label", "")), " (right axis)" if two and s.get("axis") == "y2" else ""))
        leg = '<div class="legend">%s</div>' % "".join(items)
    cap = "<figcaption><b>%s%s</b>%s%s</figcaption>" % (
        e(c.get("title", "")), pg(c), '<span class="cond">%s</span>' % e(c["conditions"]) if c.get("conditions") else "", leg)
    return '<figure id="%s">%s%s</figure>' % (ident(c.get("title", ""), "curve"), "".join(o), cap)


# ---- the page

def circuit(c, sheet_path):
    o = []
    stem = os.path.splitext(sheet_path)[0]
    drawing = "%s.%s.svg" % (stem, c.get("id", ""))
    if not (c.get("id") and os.path.isfile(drawing)):
        return ""
    if c.get("id") and os.path.isfile(drawing):
        with open(drawing, encoding="utf-8") as f:
            svg = f.read()
        o.append("<h3>%s%s</h3>" % (e(c.get("title", "")), pg(c)))
        if c.get("description"):
            o.append("<p>%s</p>" % e(c["description"]))
        o.append('<div class="circuit-drawing">%s</div>' % svg[svg.find("<svg"):])
    if c.get("drawn_with"):
        dw = c["drawn_with"]
        if all(isinstance(d, str) for d in dw):
            o.append('<ul class="drawn-with">%s</ul>' % "".join("<li>%s</li>" % e(d) for d in dw))
        else:
            o.append(table({"columns": ["ref", "datasheet", "drawing"],
                            "rows": [[d.get("ref", ""), d.get("maker", ""), d.get("drawn", "")] if isinstance(d, dict) else [d, "", ""] for d in dw]}))
    parts = {"columns": ["ref", "part", "value", "note"],
             "rows": [[p.get("ref", ""), p.get("type", ""), p.get("value", ""), p.get("note", "")] for p in c.get("parts", [])]}
    if c.get("nets"):
        nets = {"columns": ["net", "pins"], "rows": [[n.get("net", ""), "  ".join(n.get("pins", []))] for n in c["nets"]]}
        o.append('<div class="two"><div>%s</div><div>%s</div></div>' % (table(parts), table(nets)))
    elif parts["rows"]:
        o.append(table(parts))
    if c.get("notes"):
        o.append('<ol class="notes">%s</ol>' % "".join("<li>%s</li>" % e(n) for n in c["notes"]))
    return sec(ident(c["id"], "circuit"), *o)


def page(sheet, sheet_path):
    src = sheet.get("source", {})
    stem = os.path.splitext(sheet_path)[0]
    ANCHORS.clear()
    for c in sheet.get("curves") or []:
        ANCHORS.update(m.group(1) for m in FIGREF.finditer(str(c.get("title", ""))))
    for c in sheet.get("circuits") or []:
        if c.get("id") and os.path.isfile("%s.%s.svg" % (stem, c["id"])):
            ANCHORS.update(m.group(1) for m in FIGREF.finditer(str(c.get("title", ""))))
    o = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>%s</title><style>%s</style></head><body><div class=\"page\">" % (e(sheet.get("name", "")), CSS)]
    family = sheet.get("family") or sheet.get("name", "")
    o.append('<header><div class="maker">%s</div><h1>%s<span>%s</span></h1></header>' % (e(sheet.get("manufacturer", "")), e(family), e(sheet.get("title", ""))))
    o.append('<p class="summary">%s</p>' % e(sheet.get("summary", "")))
    if sheet.get("key_figures"):
        o.append('<div class="keys">%s</div>' % "".join("<div><b>%s</b><span>%s</span></div>" % (e(v), e(k)) for k, v in sheet["key_figures"]))
    IDS.clear()
    parts = []                  # the page's parts in order: (id, heading, [what is under it])

    def part(i, heading, extra=""):
        parts.append((ident(i), heading, ["<h2>%s%s</h2>" % (heading, extra)]))
        return parts[-1][2]

    pn = sheet.get("part_numbers")
    if pn:
        part("part-numbers", "Part numbers", pg(pn)).append(table(pn))
    if sheet.get("pins"):
        b = part("pins", "Pins")
        pinout = stem + ".pinout.html"
        if os.path.isfile(pinout):
            with open(pinout, encoding="utf-8") as f:
                b.append('<div class="land">%s</div>' % f.read())
        for g in sheet["pins"]:
            t = {"columns": ["pin", "name", "type", "function"],
                 "rows": [[p.get("pin", ""), p.get("name", ""), p.get("type", ""), p.get("function", "")] for p in g.get("pins", [])]}
            b.append(sec(ident(g.get("package", ""), "pins"), "<h3>%s%s</h3>" % (e(g.get("package", "")), pg(g)), table(t)))
    if sheet.get("tables"):
        b = part("ratings-and-characteristics", "Ratings and characteristics")
        for t in sheet["tables"]:
            b.append(sec(ident(t.get("title", "")), "<h3>%s%s</h3>" % (e(t.get("title", "")), pg(t)),
                         '<p class="cond">%s</p>' % e(t["conditions"]) if t.get("conditions") else "", table(t)))
    if sheet.get("curves"):
        part("typical-characteristics", "Typical characteristics").append('<div class="curves">%s</div>' % "".join(plot(c) for c in sheet["curves"]))
    drawn = "".join(circuit(c, sheet_path) for c in sheet.get("circuits") or [])
    if drawn:
        part("application-circuits", "Application circuits").append(drawn)
    if sheet.get("equations"):
        b = part("design-equations", "Design equations")
        for q in sheet["equations"]:
            b.append(sec(ident(q.get("name", ""), "equation"),
                         '<h3>%s%s</h3><div class="eq">%s</div>' % (e(q.get("name", "")), pg(q), e(q.get("expr", ""))),
                         '<dl class="where">%s</dl>' % "".join("<dt>%s</dt><dd>%s</dd>" % (e(k), e(v)) for k, v in q["where"].items()) if q.get("where") else "",
                         '<p class="cond">%s</p>' % e(q["note"]) if q.get("note") else ""))
    if sheet.get("operation"):
        b = part("operation", "Operation")
        for s in sheet["operation"]:
            b.append(sec(ident(s.get("topic", ""), "operation"), "<h3>%s%s</h3>" % (e(s.get("topic", "")), pg(s)),
                         "".join("<p>%s</p>" % e(x) for x in s.get("text", "").split("\n\n"))))
    packs = [(p, package_table(p)) for p in sheet.get("packages") or []]
    land = stem + ".land.html"
    if any(t for _, t in packs) or os.path.isfile(land):
        b = part("packages", "Packages")
        for p, t in packs:
            if not t:
                continue
            b.append(sec(ident(p.get("name", ""), "package"), "<h3>%s%s</h3>" % (e(p.get("name", "")), pg(p)),
                         '<p class="cond">Dimensions in %s</p>' % e(p["unit"]) if p.get("unit") else "", table(t)))
        if os.path.isfile(land):
            with open(land, encoding="utf-8") as f:
                b.append(sec(ident("land-pattern"), '<h3>Land pattern</h3><p class="cond">The footprint the parts library gives the part, with its dimensions in mm read from that footprint. It is not the maker\'s drawing.</p><div class="land">%s</div>' % f.read()))
    if len(parts) > 1:
        o.append('<nav class="toc">%s</nav>' % "".join('<a href="#%s">%s</a>' % (i, h) for i, h, _ in parts))
    o.extend(sec(i, *b) for i, _, b in parts)
    ref = " ".join(x for x in (src.get("document", ""), src.get("revision", "")) if x)
    o.append("<footer>Source: %s datasheet%s. p. N is a page of it, and a figure called the maker's is a figure of it.</footer>" % (e(sheet.get("manufacturer", "")), e(" " + ref if ref else "")))
    o.append("</div></body></html>")
    return "".join(o)


def index(root):
    """index.html under `root`: every sheet of its index.csv, with its part numbers and a link to its page."""
    with open(os.path.join(root, "index.csv"), encoding="utf-8", newline="") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: (r["kind"], os.path.basename(r["sheet"]).lower()))
    esc = lambda s: html.escape(str(s), quote=True)
    o = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>cloud-sheets</title><style>%s</style></head><body><div class="page">' % CSS,
         '<header><h1>Reference sheets<span>%d sheets, by kind</span></h1></header>' % len(rows),
         '<input class="find" id="q" type="search" placeholder="part number, maker or kind" autofocus><div class="count" id="n"></div>',
         '<div class="scroll"><table><thead><tr><th>sheet</th><th>part numbers</th><th>maker</th><th>kind</th><th></th></tr></thead><tbody>']
    for r in rows:
        name = os.path.basename(r["sheet"])[:-5]
        mpns = [m for m in r["mpns"].split(";") if m]
        shown = ", ".join(mpns[:4]) + (" and %d more" % (len(mpns) - 4) if len(mpns) > 4 else "")
        reg = "registers/%s/%s.html" % (r["kind"], name)
        o.append('<tr data-k="%s"><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            esc(" ".join([name, r["manufacturer"], r["kind"]] + mpns).lower()), esc(r["sheet"][:-5] + ".html"), esc(name),
            esc(shown), esc(r["manufacturer"]), esc(r["kind"]),
            '<a href="%s">registers</a>' % esc(reg) if os.path.isfile(os.path.join(root, reg)) else ""))
    o.append("</tbody></table></div></div><script>"
             "const q=document.getElementById('q'),n=document.getElementById('n'),rows=[...document.querySelectorAll('tbody tr')];"
             "function f(){const w=q.value.toLowerCase().split(/\\s+/).filter(Boolean);let c=0;"
             "for(const r of rows){r.hidden=!w.every(x=>r.dataset.k.includes(x));c+=!r.hidden}"
             "n.textContent=w.length?c+' of '+rows.length:''}"
             "q.addEventListener('input',f);f()</script></body></html>")
    dest = os.path.join(root, "index.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("".join(o))
    return dest


def main(argv):
    out_dir = None
    if "-o" in argv:
        k = argv.index("-o")
        out_dir = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    jobs = 1
    if "-j" in argv:
        k = argv.index("-j")
        jobs = max(1, int(argv[k + 1]))
        argv = argv[:k] + argv[k + 2:]
    names = [a for a in argv if not a.startswith("--")]
    if not names:
        print(__doc__)
        return 2
    paths = []
    for n in names:
        if n.endswith(".json") and os.path.isfile(n):
            paths.append(os.path.abspath(n))
        else:
            for top in ("sheets", "datasheets"):
                paths += sorted(glob.glob(os.path.join(ROOT, top, "**", ("*" if n == "all" else glob.escape(n)) + ".json"), recursive=True))

    def one(path):
        with open(path, encoding="utf-8") as f:
            sheet = json.load(f)
        if "sheet" not in sheet:
            return
        kind = os.path.basename(os.path.dirname(path))
        out = out_dir or (os.path.join(ROOT, "out", kind) if os.path.basename(os.path.dirname(os.path.dirname(path))) == "sheets" else os.path.dirname(path))
        os.makedirs(out, exist_ok=True)
        dest = os.path.join(out, os.path.basename(path)[:-5] + ".html")
        with LOCK:
            text = page(sheet, path)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        if "--pdf" in argv:
            pdf = dest[:-5] + ".pdf"
            if os.path.exists(pdf):
                os.remove(pdf)
            # Chrome gets a profile folder of its own (one sharing a running browser's profile can wait
            # on it forever) and two minutes; a run that hangs is stopped and tried once more.
            code = 0
            for _ in (1, 2):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
                    try:
                        code = subprocess.run([chrome(), "--headless", "--disable-gpu", "--no-first-run", "--user-data-dir=" + profile,
                                               "--no-pdf-header-footer", "--print-to-pdf=" + pdf, pathlib.Path(dest).as_uri()],
                                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120).returncode
                    except subprocess.TimeoutExpired:
                        code = -1
                # Chrome can exit nonzero on a teardown watchdog after writing the PDF.
                if os.path.exists(pdf) and os.path.getsize(pdf) > 0:
                    break
            else:
                raise subprocess.CalledProcessError(code, "chrome --print-to-pdf")
            if "--keep-html" not in argv and out_dir is None and not out.startswith(os.path.join(ROOT, "out")):
                os.remove(dest)
            print(pdf)
        else:
            print(dest)

    if jobs > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(jobs) as pool:
            list(pool.map(one, paths))
    else:
        for path in paths:
            one(path)
    if "all" in names and out_dir is None and "--pdf" not in argv and os.path.isfile(os.path.join(ROOT, "index.csv")):
        print(index(ROOT))
    return 0


def chrome():
    for c in (os.environ.get("CHROME", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"):
        if c and os.path.isfile(c):
            return c
    raise SystemExit("render.py --pdf needs Chrome or Chromium (set CHROME to its path)")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
