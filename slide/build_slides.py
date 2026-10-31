"""Build Group04_CLC02_Week10.pptx in the same visual format as Group04_CLC02_Midterm (3).pdf.

Format copied from the midterm deck: 16:9, white background, serif font (Times New Roman), 30 pt bold numbered
titles at the top left, bold 18 pt column headings, 15 pt bullets, grey rounded stat cards and call-out boxes,
light-grey table header, grey italic captions, "n / N" page number at the bottom right, grey bars with the key bar black.

Run:  python build_slides.py        (needs: pip install python-pptx)
All numbers come from AFP_Project/results/*.csv, so the deck stays consistent with the Week-10 report.
"""
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "results" if (HERE.parent / "results").exists() else HERE.parent / "AFP_Project" / "results"
OUT = HERE / "Group04_CLC02_Week10.pptx"

FONT = "Times New Roman"
INK, GREY, LIGHT, BAR, LINE = RGBColor(0x11, 0x11, 0x11), RGBColor(0x66, 0x66, 0x66), RGBColor(0xF2, 0xF2, 0xF2), RGBColor(0x9E, 0x9E, 0x9E), RGBColor(0xD0, 0xD0, 0xD0)
LX, RX, CW = 0.74, 6.95, 5.65           # left column x, right column x, column width (inches)
TOTAL = 12

# ------------------------------------------------------------------ numbers
main = pd.read_csv(RES / "nb_main_gb.csv", index_col=0)
byq = pd.read_csv(RES / "w10_delta_by_length.csv")
curv = pd.read_csv(RES / "w10_corruption_summary.csv", index_col=0)
emb = pd.read_csv(RES / "step2_embed_summary.csv")
s2 = pd.read_csv(RES / "step2_improved_summary.csv")
q = lambda k: float(main.loc[k, "mean QWK / đề"])
E = emb[emb.weights == "tuned"].set_index("model"); e3, e6 = E.iloc[0], E.iloc[2]
f2 = lambda x, d=3: f"{x:.{d}f}"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def run_fmt(r, size, bold=False, italic=False, color=INK):
    r.font.name, r.font.size, r.font.bold, r.font.italic = FONT, Pt(size), bold, italic
    r.font.color.rgb = color
    rPr = r._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", FONT)


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tb, tf


def add_runs(p, parts, size, color=INK, italic=False):
    """parts: str or list of (text, bold) / (text, bold, italic)."""
    if isinstance(parts, str): parts = [(parts, False)]
    for part in parts:
        t, b = part[0], part[1]; it = part[2] if len(part) > 2 else italic
        r = p.add_run(); r.text = t; run_fmt(r, size, b, it, color)


def bullet_par(p, level_indent=0.25):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(level_indent)))); pPr.set("indent", str(-int(Inches(level_indent))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        el = pPr.find(qn(tag))
        if el is not None: pPr.remove(el)
    bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "•")


def title(slide, text, n):
    _, tf = textbox(slide, LX, 0.5, 11.8, 0.8, MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]; add_runs(p, [(text, True)], 30)
    _, tf = textbox(slide, 12.0, 6.95, 0.7, 0.25)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT; add_runs(p, f"{n} / {TOTAL}", 10, GREY)


def heading(slide, text, x, y=1.62, w=CW):
    _, tf = textbox(slide, x, y, w, 0.4)
    add_runs(tf.paragraphs[0], [(text, True)], 18)


def bullets(slide, items, x, y=2.12, w=CW, h=4.6, size=15, gap=7):
    _, tf = textbox(slide, x, y, w, h)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        bullet_par(p); p.space_after = Pt(gap)
        add_runs(p, it, size)


def caption(slide, text, x, y, w=CW, size=11):
    _, tf = textbox(slide, x, y, w, 0.5)
    add_runs(tf.paragraphs[0], text, size, GREY, italic=True)


def card(slide, x, y, w, h, big, small):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.08; s.fill.solid(); s.fill.fore_color.rgb = LIGHT; s.line.fill.background(); s.shadow.inherit = False
    tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; add_runs(p, [(big, True)], 24)
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER; add_runs(p, small, 10, GREY)


def callout(slide, x, y, w, h, parts, size=14):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.08; s.fill.solid(); s.fill.fore_color.rgb = LIGHT; s.line.fill.background(); s.shadow.inherit = False
    tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.22); tf.margin_top = tf.margin_bottom = Inches(0.08)
    tf.paragraphs[0].alignment = PP_ALIGN.LEFT
    add_runs(tf.paragraphs[0], parts, size)


def _border(cell, color="D0D0D0"):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        old = tcPr.find(qn(tag))
        if old is not None: tcPr.remove(old)
        ln = etree.SubElement(tcPr, qn(tag)); ln.set("w", "9525")
        sf = etree.SubElement(ln, qn("a:solidFill")); c = etree.SubElement(sf, qn("a:srgbClr")); c.set("val", color)
    # borders must precede the fill element in the schema
    fill = tcPr.find(qn("a:solidFill"))
    if fill is not None: tcPr.remove(fill); tcPr.append(fill)


def table(slide, x, y, w, rows, col_w, size=12, row_h=0.42, bold_rows=(), italic_cells=(), first_col_bold=True):
    n, m = len(rows), len(rows[0])
    gs = slide.shapes.add_table(n, m, Inches(x), Inches(y), Inches(w), Inches(row_h * n))
    tbl = gs.table
    tblPr = tbl._tbl.tblPr
    for a in ("firstRow", "bandRow"): tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None: sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"          # "No Style, No Grid"
    for j, cw in enumerate(col_w): tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.1); c.margin_top = c.margin_bottom = Inches(0.04)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            bold = i == 0 or i in bold_rows or (j == 0 and first_col_bold)
            add_runs(p, [(str(val), bold, (i, j) in italic_cells)], size)
            c.fill.solid(); c.fill.fore_color.rgb = LIGHT if i == 0 else RGBColor(255, 255, 255)
            _border(c)
    return gs


def style_chart(chart, size=11):
    chart.font.name = FONT; chart.font.size = Pt(size); chart.font.color.rgb = INK
    chart.has_title = False


def bar_chart(slide, x, y, w, h, cats, vals, hi=None, horizontal=True, fmt="0.000", vmin=0.5, vmax=0.8):
    cd = CategoryChartData(); cd.categories = cats; cd.add_series("QWK", vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    ch = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    style_chart(ch); ch.has_legend = False
    pl = ch.plots[0]; pl.gap_width = 45; pl.has_data_labels = True
    dl = pl.data_labels; dl.number_format = fmt; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(11); dl.font.name = FONT
    va, ca = ch.value_axis, ch.category_axis
    va.minimum_scale, va.maximum_scale = vmin, vmax; va.has_major_gridlines = False; va.visible = False
    ca.format.line.color.rgb = GREY; ca.tick_labels.font.size = Pt(11)
    if horizontal: ca.reverse_order = True
    ser = pl.series[0]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb = BAR
    for i in range(len(vals)):
        pt = ser.points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = INK if i == hi else BAR
    return ch


def new_slide(num, text):
    s = prs.slides.add_slide(BLANK); title(s, text, num); return s


# ================================================================== 1. title
s = prs.slides.add_slide(BLANK)
_, tf = textbox(s, 0.74, 1.75, 11.5, 1.6)
p = tf.paragraphs[0]; add_runs(p, [("Does Argument Structure Help Essay Scoring?", True)], 34)
p = tf.add_paragraph(); add_runs(p, [("RQ1 and RQ2 on PERSUADE 2.0 · Week 10 progress", True)], 34)
_, tf = textbox(s, 0.74, 3.95, 11.5, 2.4)
p = tf.paragraphs[0]; add_runs(p, [("Teacher", True), (": Bùi Quốc Khánh", False)], 16); p.space_after = Pt(8)
p = tf.add_paragraph(); add_runs(p, [("Group 04", True)], 16); p.space_after = Pt(2)
for t in ("Member 1: Nguyễn Xuân Hòa - 2301140035", "Member 2: Hoàng Tùng - 2301140099", "Member 3: Nguyễn Duy Anh - 2301140006"):
    p = tf.add_paragraph(); p.level = 0; add_runs(p, t, 14); p.space_after = Pt(2)
    p._p.get_or_add_pPr().set("marL", str(int(Inches(0.25))))

# ================================================================== 2. scope
s = new_slide(2, "1. Scope and what we answered")
heading(s, "Scope after the feedback", LX)
bullets(s, [
    [("Core: ", True), ("Step 3, essay scoring, RQ1 and RQ2", False)],
    [("Fixed design: ", True), ("8 independent prompts, leave-one-prompt-out, Gradient Boosting, 3 seeds", False)],
    [("Side result: ", True), ("Step 2 (segment effectiveness). Fairness (RQ3) only after RQ1 and RQ2", False)],
    [("Claim we make: ", True), ("gold structure adds a little (+0.02 QWK); predicted roles add nothing beyond segment boundaries", False)],
], LX)
heading(s, "Data in this study", RX)
for i, (big, small) in enumerate([("7,869", "essays · 8 prompts"), ("77,639", "labelled segments"), ("1.9%", "segments Ineffective")]):
    card(s, RX + i * 1.9, 2.12, 1.8, 1.05, big, small)
bullets(s, [
    "Essay: holistic score 1–6. Segment: role + effectiveness",
    "Seven source-based prompts excluded: their scores depend on the source text",
    "Official test set untouched until the end",
], RX, y=3.45, h=3, size=15)

# ================================================================== 3. data workflow
s = new_slide(3, "2. Data workflow")
heading(s, "From raw file to model input", LX)
bullets(s, [
    "Raw CSV: one row per segment, full essay text repeated on every row (about 600 MB)",
    [("Essay table: ", True), ("drop duplicates → 15,594 essays, one score each", False)],
    [("Segment table: ", True), ("173,266 segments with role, effectiveness, position", False)],
    [("Filter: ", True), ("task = Independent → 7,869 essays, 8 prompts", False)],
    [("Features: ", True), ("43 text features per essay (regular expressions) + 28 structure features from roles", False)],
], LX, size=15)
heading(s, "Why each choice", RX)
table(s, RX, 2.12, CW, [
    ["Choice", "Reason"],
    ["One row per essay", "the essay is the unit that gets a score"],
    ["Independent prompts only", "do not mix with source-based scoring"],
    ["Regex features", "each feature is countable and can be explained"],
    ["Split by prompt", "the question is a new prompt, not a new essay"],
    ["Role features only in M2, M3", "so M2/M3 differ from M1 in one block"],
], [2.35, 3.3], size=12, row_h=0.5)
caption(s, "Ineffective is 1.9% of segments in these 8 prompts (4.5% in all 15).", RX, 5.3)

# ================================================================== 4. worked example
s = new_slide(4, "3. One essay, step by step")
heading(s, "Essay F3CB6601CF24 · Seeking multiple opinions", LX)
bullets(s, [
    [("Segments (gold): ", True), ("Lead 203 · Position 20 · Claim 18 · Evidence 120 · Claim 21 · Evidence 112 · Claim 17 · Evidence 110 · Concluding 117 words", False)],
    [("M1 features: ", True), ("741 words and 3,928 characters (8-prompt mean: 464 and 2,591)", False)],
    [("Structure: ", True), ("3 Claims, 3 Evidence → evidence_per_claim = 3 / 3 = 1.0", False)],
    [("Length shortcut: ", True), ("mean essay length rises from 272 words (score 1) to 854 words (score 6)", False)],
], LX, size=14, gap=8)
heading(s, "What each model predicts (true score 5)", RX)
table(s, RX, 2.12, CW, [
    ["Model", "Input", "Prediction"],
    ["M0a", "word count", "5.07"],
    ["M1", "43 features", "4.62"],
    ["M2", "+ gold roles", "4.33"],
    ["M3", "+ predicted roles", "4.10"],
], [1.1, 2.75, 1.8], size=13, row_h=0.46)
caption(s, "A case where structure moves the score away from the truth. One case shows the mechanism, it is not evidence.", RX, 4.65)

# ================================================================== 5. models and formulas
s = new_slide(5, "4. Models and formulas")
heading(s, "Formulas", LX)
bullets(s, [
    [("QWK", True), (" = 1 − Σ w·O / Σ w·E, w = (i − j)² / 25: big misses cost more", False)],
    [("Macro-F1", True), (" = mean F1 over classes: Ineffective is rare", False)],
    [("evidence_per_claim", True), (" = n_Evidence / max(n_Claim, 1)", False)],
    [("Flesch", True), (" = 206.835 − 1.015·(words / sentences) − 84.6·(syllables / words)", False)],
    [("Class weights", True), (": ŷ = argmax w_k·P(k), w tuned on training prompts only", False)],
], LX, size=14, gap=8)
heading(s, "Models and length controls", RX)
table(s, RX, 2.12, CW, [
    ["", "Input", "Role"],
    ["M0a", "word count", "old baseline"],
    ["M0b", "7 length features", "length-only ceiling"],
    ["M1", "43 features", "baseline"],
    ["M1 + B", "M1 + boundaries", "what M3 still knows"],
    ["M2", "M1 + gold roles", "oracle"],
    ["M3", "M1 + predicted roles", "realistic"],
], [1.0, 2.55, 2.1], size=12, row_h=0.44, bold_rows=(6,))
caption(s, "Same algorithm, same prompt-based folds: only the inputs differ.", RX, 5.4)

# ================================================================== 6. length explains most
s = new_slide(6, "5. Length explains most of M1")
heading(s, "From word count to structure", LX)
bullets(s, [
    [("M1 − M0a = 0.090: ", True), ("0.077 (86%) is already in the length group", False)],
    [("M1 − M0b = +0.013: ", True), ("language beyond length is small", False)],
    [("M2 − M1 = +0.023: ", True), ("gold structure, positive in 8 of 8 prompts", False)],
    [("M3 − M1 = +0.012: ", True), ("predicted roles, 7 of 8 prompts, p = 0.07", False)],
    [("M1 + B − M1 = +0.012: ", True), ("boundaries alone give as much as M3", False)],
], LX, size=15)
heading(s, "Mean QWK per held-out prompt", RX)
names = [("M0a words", "M0a  words"), ("M0b length group", "M0b  length-group"), ("M1", "M1"), ("M1 + boundaries", "M1 +B(boundary only)"),
         ("M3 predicted", "M3 (pred)"), ("M2 gold", "M2 (gold)")]
bar_chart(s, RX, 2.05, CW, 3.9, [a for a, _ in names], [q(b) for _, b in names], hi=5, vmin=0.5, vmax=0.82)
caption(s, "Gradient Boosting, 3 seeds, 8 held-out prompts.", RX, 6.05)

# ================================================================== 7. length groups
s = new_slide(7, "6. Structure inside length groups")
heading(s, "Five groups of equal size by word count", LX)
d_m2 = byq[byq.comparison == "M2 - M1"].dQWK.tolist(); d_b = byq[byq.comparison == "M1+boundary - M1"].dQWK.tolist()
d_x = byq[byq.comparison == "M2 - M1+boundary"].reset_index(drop=True)
bullets(s, [
    "About 1,570 essays per group (Q1 shortest, Q5 longest)",
    [("Gold structure helps in all five groups: ", True), (f"+{min(d_m2):.3f} to +{max(d_m2):.3f} QWK", False)],
    "In the shorter groups, boundaries alone give most of the gain",
    [("In the longest group ", True), (f"roles add +{d_x.dQWK.iloc[-1]:.3f} beyond boundaries (95% CI {d_x.ci_lo.iloc[-1]:.3f} to {d_x.ci_hi.iloc[-1]:.3f})", False)],
    "Length control is partial: score still varies inside each group",
], LX, size=15)
heading(s, "ΔQWK against M1 in each group", RX)
cd = CategoryChartData(); cd.categories = ["Q1", "Q2", "Q3", "Q4", "Q5"]
cd.add_series("M2 − M1 (gold roles)", d_m2); cd.add_series("M1 + boundaries − M1", d_b)
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(RX), Inches(2.05), Inches(CW), Inches(3.9), cd).chart
style_chart(ch); ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(11)
pl = ch.plots[0]; pl.gap_width = 60; pl.overlap = 0; pl.has_data_labels = True
pl.data_labels.number_format = "0.000"; pl.data_labels.number_format_is_linked = False; pl.data_labels.font.size = Pt(10)
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
ch.value_axis.has_major_gridlines = False; ch.value_axis.visible = False; ch.value_axis.minimum_scale = 0; ch.value_axis.maximum_scale = 0.10
ch.category_axis.format.line.color.rgb = GREY
for ser, col in zip(pl.series, (INK, BAR)): ser.format.fill.solid(); ser.format.fill.fore_color.rgb = col
caption(s, "Bootstrap over essays, 500 draws; GB predictions from leave-one-prompt-out.", RX, 6.05)

# ================================================================== 8. corruption
s = new_slide(8, "7. How good must the role tagger be?")
heading(s, "Corrupt gold role labels, keep boundaries", LX)
bullets(s, [
    "Change 10, 20, 40, 60, 80% of role labels at random; rerun M2 on the same folds; 3 draws per level",
    [("At 20% ", True), ("M2 falls below M1 + boundaries", False)],
    [("From 40% ", True), ("the curve is flat, still above M1 because boundaries are intact", False)],
    [("Our tagger ", True), ("(macro-F1 0.675) is already in this zone", False)],
], LX, size=15)
callout(s, LX, 5.15, CW, 1.15, [("RQ2: ", True), ("with the current tagger, predicted roles do not beat \"count the paragraphs\".", False)])
heading(s, "M2 mean QWK by % labels corrupted", RX)
cats = ["0%", "10%", "20%", "40%", "60%", "80%"]
vals = [float(curv.loc[k, "meanQWK"]) for k in (0.0, 0.1, 0.2, 0.4, 0.6, 0.8)]
cd = CategoryChartData(); cd.categories = cats
cd.add_series("M2, corrupted roles", vals)
cd.add_series("M1 + boundaries", [q("M1 +B(boundary only)")] * 6)
cd.add_series("M1", [q("M1")] * 6)
ch = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(RX), Inches(2.05), Inches(CW), Inches(3.9), cd).chart
style_chart(ch); ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(11)
ch.value_axis.minimum_scale, ch.value_axis.maximum_scale = 0.745, 0.780
ch.value_axis.has_major_gridlines = False; ch.value_axis.tick_labels.font.size = Pt(10); ch.value_axis.tick_labels.number_format = "0.000"
ch.value_axis.tick_labels.number_format_is_linked = False; ch.category_axis.format.line.color.rgb = GREY
for ser, col, dash in zip(ch.plots[0].series, (INK, GREY, BAR), (False, True, True)):
    ser.format.line.color.rgb = col; ser.format.line.width = Pt(2.25 if not dash else 1.5); ser.smooth = False
    if dash: ser.format.line.dash_style = 4
    ser.marker.format.fill.solid(); ser.marker.format.fill.fore_color.rgb = col; ser.marker.format.line.color.rgb = col
    ser.marker.size = 7 if not dash else 2
caption(s, "Random replacement among the 7 roles is not how a real tagger errs (Claim and Evidence get confused).", RX, 6.05)

# ================================================================== 9. step 2
s = new_slide(9, "8. Step 2: segment effectiveness")
heading(s, "Better, but not a teacher flag", LX)
bullets(s, [
    [("Baseline: ", True), ("macro-F1 0.433, F1 of Ineffective 0.07", False)],
    [("Improved: ", True), ("role, length, position, essay context, text signal, class weights tuned on training prompts → 0.510 pooled, 0.477 per prompt", False)],
    [("Embeddings and context similarity add nothing ", True), (f"({f2(e6.macroF1_mean_prompts)} vs {f2(e3.macroF1_mean_prompts)} per prompt)", False)],
    [("Ranking: ", True), (f"flag the top 5% of segments → {e6.prec_top5*100:.1f}% correct ({e6.lift_top5:.1f}× chance), catches {e6.recall_top5*100:.0f}% of Ineffective", False)],
], LX, size=14, gap=8)
heading(s, "Step 2, leave-one-prompt-out", RX)
mj = s2[s2.model.str.startswith("S0")].iloc[0]
table(s, RX, 2.12, CW, [
    ["Model", "Macro-F1 pooled", "per prompt", "F1 Ineff.", "PR-AUC"],
    ["Majority class", f2(mj.macroF1_pooled), f2(mj.macroF1_mean_prompts), "0.000", "n/a"],
    ["Week-8 baseline", "0.433", "0.413", "0.070", "n/a"],
    ["S3 tuned", f2(e3.macroF1_pooled), f2(e3.macroF1_mean_prompts), f2(e3.F1_Ineffective), f2(e3.PR_AUC)],
    ["S6 tuned", f2(e6.macroF1_pooled), f2(e6.macroF1_mean_prompts), f2(e6.F1_Ineffective), f2(e6.PR_AUC)],
], [1.75, 1.15, 0.95, 0.9, 0.9], size=12, row_h=0.5)
callout(s, RX, 4.9, CW, 1.3, [("Above 0.5 only pooled. ", True), (f"Precision of Ineffective is about {e6.P_Ineffective:.2f}: nine flags in ten are wrong. Chance for PR-AUC is {e6.base_rate:.3f}.", False)], size=13)

# ================================================================== 10. literature
s = new_slide(10, "9. Related work, 2024–2026")
heading(s, "What recent papers say", LX, w=6.9)
bullets(s, [
    [("Yang et al. (2024), AAAI: ", True), ("9 scorers, accuracy and fairness; feature-based models generalise well", False)],
    [("Wang et al. (2026), ArguLens: ", True), ("gold discourse features +0.055 QWK, an oracle diagnostic", False)],
    [("Gui (2026), AIME-Con: ", True), ("effectiveness signal tracks length and elaboration", False)],
    [("Ormerod (2025): ", True), ("argument annotations help encoder scorers", False)],
    [("Keramati & Warschauer (2026): ", True), ("sequential LoRA fine-tuning on discourse elements", False)],
    [("Chen, Wu & Zhang (2026): ", True), ("conditional disparity ratio and difference at the same true score; our plan for RQ3", False)],
], LX, w=6.9, size=14, gap=7)
heading(s, "How we use them", 8.1, w=4.6)
bullets(s, [
    "Hand-made features + trees, prompt-based split: the setting Yang et al. recommend",
    "M2 = oracle, M3 = intermediate: the ArguLens distinction",
    "Step 2 result matches Gui: little beyond role, length, position",
], 8.1, w=4.6, size=14, gap=7, h=2.8)
callout(s, 8.1, 5.05, 4.6, 1.5, [("Not compared: ", True), ("our QWK 0.753–0.776 and ArguLens 0.813 use different data, features and splits.", False)], size=13)

# ================================================================== 11. group 6
s = new_slide(11, "10. Working with Group 6")
heading(s, "Their reply and our decision", LX)
bullets(s, [
    [("They: ", True), ("Step 2 with DeBERTa, random 80/20 split on 15 prompts, macro-F1 0.577", False)],
    [("We: ", True), ("Step 3, leave-one-prompt-out on 8 prompts", False)],
    [("Copy the procedure, not the numbers: ", True), ("different splits", False)],
    [("Their validation file would leak: ", True), ("their model saw our held-out prompts", False)],
    [("No GPU on our side: ", True), ("ask for 1–2 DeBERTa folds", False)],
], LX, size=15)
heading(s, "What we exchange", RX)
table(s, RX, 2.12, CW, [
    ["We send", "They send"],
    ["List of our 8 prompts", "Leave-one-prompt-out probabilities (RF / LR) on those 8 prompts"],
    ["Predicted roles (macro-F1 0.675)", "DeBERTa on 1–2 folds"],
    ["Essay-level features", "Their error-propagation result with predicted roles"],
], [2.6, 3.05], size=12, row_h=0.72)
caption(s, "Draft minutes in the report; Group 6 still has to confirm.", RX, 5.15)

# ================================================================== 12. limits and next
s = new_slide(12, "11. Limits and next steps")
heading(s, "Limits", LX)
bullets(s, [
    "Only 8 prompts; more seeds do not add independent prompts",
    "Segment boundaries are gold: M3 is not an end-to-end tool",
    "Corruption test: one GB seed per draw, uniform random errors",
    "Step 2 gain is mostly a changed decision threshold",
    "Six cases not yet checked against the rubric",
], LX, size=15)
heading(s, "Next steps", RX)
bullets(s, [
    "Re-read the six cases with the rubric; add an essay with Claim and Evidence in few paragraphs",
    "Replace gold boundaries with predicted ones",
    "Confirm which kappa the human ceiling 0.75 is (ETS treats QWK around 0.70 as acceptable, via Chen et al.)",
    "DeBERTa fold from Group 6; then RQ3",
], RX, size=15)
callout(s, RX, 5.1, CW, 1.4, [("Claim: ", True), ("on 8 prompts, gold structure adds about +0.02 QWK; predicted roles add nothing beyond boundaries yet.", False)], size=14)

prs.save(OUT)
print("saved", OUT)
