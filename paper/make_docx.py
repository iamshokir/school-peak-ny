"""Word layout following the IEEE/PES conference paper format (US letter,
two columns, Times New Roman). Approximation of the PES PG4 template: the
official .doc could not be downloaded from the cloud workspace; paste the
content into it before submission if formatting differs."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]


def _run(par, text, size=10, bold=False, italic=False, caps=False):
    r = par.add_run(text)
    r.font.name = "Times New Roman"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    r.font.size = Pt(size)
    r.bold, r.italic = bold, italic
    r.font.small_caps = caps
    return r


import re
_MARK = re.compile(r"([_^])\{([^}]*)\}")


def _rich(par, text, size=10, bold=False, italic=False):
    """Run text with _{sub} and ^{sup} markup."""
    pos = 0
    for m in _MARK.finditer(text):
        if m.start() > pos:
            _run(par, text[pos:m.start()], size, bold, italic)
        r = _run(par, m.group(2), size, bold, italic)
        if m.group(1) == "_":
            r.font.subscript = True
        else:
            r.font.superscript = True
        pos = m.end()
    if pos < len(text):
        _run(par, text[pos:], size, bold, italic)


def _par(doc, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=0,
         indent=None):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing = 1.0
    if indent is not None:
        pf.first_line_indent = Inches(indent)
    return p


def _columns(section, n, space_in=0.25):
    cols = section._sectPr.xpath("./w:cols")
    c = cols[0] if cols else OxmlElement("w:cols")
    c.set(qn("w:num"), str(n))
    c.set(qn("w:space"), str(int(space_in * 1440)))
    if not cols:
        section._sectPr.append(c)


def _table(doc, hdr, rows, caption, num, widths=None, note=None):
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, before=6, after=0)
    _run(p, f"TABLE {ROMAN[num - 1]}", 8, caps=True)
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, after=3)
    _run(p, caption, 8, caps=True)
    t = doc.add_table(rows=1 + len(rows), cols=len(hdr))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    t.autofit = False
    widths = widths or [3.4 / len(hdr)] * len(hdr)
    for j, h in enumerate(hdr):
        c = t.cell(0, j)
        c.text = ""
        _rich(c.paragraphs[0], h, 7, bold=True)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, r in enumerate(rows, start=1):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = ""
            _run(c.paragraphs[0], str(v), 7)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in t.rows:
        for j, c in enumerate(row.cells):
            c.width = Inches(widths[j])
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths) * 1440)))
    tw.set(qn("w:type"), "dxa")
    for e in tblPr.findall(qn("w:tblW")):
        tblPr.remove(e)
    tblPr.append(tw)
    ind = OxmlElement("w:tblInd")
    ind.set(qn("w:w"), "0")
    ind.set(qn("w:type"), "dxa")
    tblPr.append(ind)
    grid = t._tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[j] * 1440)))
    for row in t.rows:
        for c in row.cells:
            pr = c._tc.get_or_add_tcPr()
            mar = OxmlElement("w:tcMar")
            for side in ("left", "right"):
                e = OxmlElement(f"w:{side}")
                e.set(qn("w:w"), "40")
                e.set(qn("w:type"), "dxa")
                mar.append(e)
            pr.append(mar)
    p = _par(doc, after=4)
    if note:
        _run(p, note, 7)


def build(blocks, out: Path, P) -> None:
    doc = Document()
    s0 = doc.sections[0]
    s0.page_width, s0.page_height = Inches(8.5), Inches(11)
    s0.top_margin, s0.bottom_margin = Inches(0.75), Inches(1.0)
    s0.left_margin = s0.right_margin = Inches(0.625)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", Pt(10)

    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, after=10)
    _run(p, P.TITLE, 22)
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER)
    _run(p, P.AUTHOR, 11)
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER)
    _run(p, P.AFFIL, 10, italic=True)
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, after=12)
    _run(p, P.EMAIL, 10)

    s1 = doc.add_section(WD_SECTION.CONTINUOUS)
    _columns(s1, 2)

    p = _par(doc, after=6)
    _run(p, "Abstract", 9, bold=True, italic=True)
    _run(p, "—" + P.ABSTRACT, 9, bold=True)
    p = _par(doc, after=8)
    _run(p, "Index Terms", 9, bold=True, italic=True)
    _run(p, "—" + P.INDEX, 9, bold=True)

    sec = sub = fig = tab = 0
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, before=8, after=4)
            _run(p, f"{ROMAN[sec]}. {b[1]}", 10, caps=True)
            sec += 1
            sub = 0
        elif kind == "h2":
            p = _par(doc, WD_ALIGN_PARAGRAPH.LEFT, before=4, after=2)
            _run(p, f"{chr(65 + sub)}. {b[1]}", 10, italic=True)
            sub += 1
        elif kind == "p":
            p = _par(doc, indent=0.14)
            _rich(p, b[1], 10)
        elif kind == "eq":
            p = _par(doc, WD_ALIGN_PARAGRAPH.LEFT, before=3, after=3)
            ts = p.paragraph_format.tab_stops
            ts.add_tab_stop(Inches(1.7), WD_TAB_ALIGNMENT.CENTER)
            ts.add_tab_stop(Inches(3.45), WD_TAB_ALIGNMENT.RIGHT)
            _run(p, "\t", 9)
            _rich(p, b[1], 9, italic=True)
            _run(p, f"\t({b[2]})", 9)
        elif kind == "fig":
            fig += 1
            p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, before=4)
            p.add_run().add_picture(str(FIG / b[1]), width=Inches(3.4))
            p = _par(doc, after=6)
            _run(p, f"Fig. {fig}. ", 8)
            _run(p, b[2], 8)
        elif kind in ("table1", "table2"):
            tab += 1
            if kind == "table1":
                hdr, rows = P.table1_rows()
                w = [0.62, 0.42, 0.36, 0.40, 0.36, 0.44, 0.40, 0.40]
            else:
                hdr, rows = P.table2_rows()
                w = [0.30, 0.72, 0.56, 0.60, 0.62, 0.60]
            _table(doc, hdr, rows, b[2], tab, w, b[3] if len(b) > 3 else None)

    p = _par(doc, before=6, indent=0.14)
    _run(p, P.DATA_NOTE, 9)
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, before=8, after=4)
    _run(p, "Acknowledgment", 10, caps=True)
    p = _par(doc, indent=0.14)
    _run(p, P.ACK, 9)
    p = _par(doc, WD_ALIGN_PARAGRAPH.CENTER, before=8, after=4)
    _run(p, "References", 10, caps=True)
    for i, r in enumerate(P.REFS, start=1):
        p = _par(doc, WD_ALIGN_PARAGRAPH.JUSTIFY)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        _run(p, f"[{i}] ", 8)
        _run(p, r, 8)
    doc.save(out)
