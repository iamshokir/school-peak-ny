"""Fill the official PES conference template (PG4 sample, supplied by the
author as .doc and converted to .docx with LibreOffice) with the paper.
Template styles are used as they are: paper title, Author, Affiliation,
Abstract, Heading 1/2/5, Body Text, equation, figure caption, table head,
table col head, table copy, table footnote, references."""
from __future__ import annotations

import copy
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template" / "pg4.docx"
FIG = ROOT / "results" / "figures"
_MARK = re.compile(r"([_^])\{([^}]*)\}")


def _rich(par, text, italic=False):
    pos = 0
    for m in _MARK.finditer(text):
        if m.start() > pos:
            r = par.add_run(text[pos:m.start()])
            r.italic = italic or None
        r = par.add_run(m.group(2))
        r.italic = italic or None
        if m.group(1) == "_":
            r.font.subscript = True
        else:
            r.font.superscript = True
        pos = m.end()
    if pos < len(text):
        r = par.add_run(text[pos:])
        r.italic = italic or None


_TOK = re.compile(r"[A-Za-z]+|[^A-Za-z]+")
_ROMAN_FUNCS = {"max", "min", "COP", "des", "bal", "hp"}


def _times(r):
    r.font.name = "Times New Roman"
    rpr = r._r.get_or_add_rPr()
    rpr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rpr.rFonts.set(qn("w:cs"), "Times New Roman")


def _eq(par, text):
    """Equation text in Times New Roman: single Latin letters italic,
    function names, digits and Greek upright; _{..}/^{..} as sub/sup."""
    pos, parts = 0, []
    for m in _MARK.finditer(text):
        parts.append((text[pos:m.start()], None))
        parts.append((m.group(2), m.group(1)))
        pos = m.end()
    parts.append((text[pos:], None))
    for chunk, kind in parts:
        for tok in _TOK.findall(chunk):
            r = par.add_run(tok)
            _times(r)
            r.italic = (tok.isalpha() and tok.isascii()
                        and tok not in _ROMAN_FUNCS and len(tok) == 1) or None
            if kind == "_":
                r.font.subscript = True
            elif kind == "^":
                r.font.superscript = True


def _clear(par):
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    for el in par._p.findall(qn("w:hyperlink")):
        par._p.remove(el)


def _borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        b.append(e)
    tblPr.append(b)


def _fix_widths(tbl, widths):
    tblPr = tbl._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for e in tblPr.findall(qn("w:tblW")):
        tblPr.remove(e)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths) * 1440)))
    tw.set(qn("w:type"), "dxa")
    tblPr.append(tw)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center")
    tblPr.append(jc)
    for j, gc in enumerate(tbl._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[j] * 1440)))
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:w"), "29")
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblPr.append(mar)
    for row in tbl.rows:
        for j, c in enumerate(row.cells):
            c.width = Inches(widths[j])


def build(blocks, out: Path, P) -> None:
    d = Document(TEMPLATE)
    paras = d.paragraphs
    body = d.element.body

    # title
    _clear(paras[0])
    paras[0].add_run(P.TITLE)
    # one affiliation: name, organization, city, e-mail; one column
    lines = [P.AUTHOR, "OFTO Energy Foundation", "Brooklyn, NY, USA",
             P.EMAIL]
    for par, text in zip(paras[2:6], lines):
        _clear(par)
        par.add_run(text)
    for par in paras[6:15]:
        par._p.getparent().remove(par._p)
    cols = d.sections[1]._sectPr.find(qn("w:cols"))
    cols.set(qn("w:num"), "1")

    # abstract and index terms (template run-in style: italic heading)
    ab, it = paras[17], paras[18]
    _clear(ab)
    ab.add_run("Abstract").italic = True
    ab.add_run("--" + P.ABSTRACT)
    _clear(it)
    it.add_run("Index Terms").italic = True
    it.add_run("--" + P.INDEX)

    # remove the template's sample body up to the section break (para 130)
    anchor = paras[130]
    el = paras[19]._p
    while el is not anchor._p:
        nxt = el.getnext()
        body.remove(el)
        el = nxt
    # empty reference lines after the break
    for par in paras[131:]:
        if not par.text.strip():
            par._p.getparent().remove(par._p)

    S = {st.name: st for st in d.styles if st.type == 1}

    def add(style, text=None, italic=False):
        p = anchor.insert_paragraph_before("")
        p._p.get_or_add_pPr()
        p.style = S[style]
        if text:
            _rich(p, text, italic)
        return p

    fig = 0
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            add("Heading 1", b[1])
        elif kind == "h2":
            add("Heading 2", b[1])
        elif kind == "p":
            add("Body Text", b[1])
        elif kind == "eq":
            p = add("equation")
            _times(p.add_run("\t"))
            _eq(p, b[1])
            _times(p.add_run(f"\t({b[2]})"))
        elif kind == "fig":
            fig += 1
            p = add("Normal")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(FIG / b[1]), width=Inches(3.45))
            add("figure caption", b[2])
        elif kind in ("table1", "table2"):
            if kind == "table1":
                hdr, rows = P.table1_rows()
                w = [0.64, 0.44, 0.36, 0.46, 0.42, 0.46, 0.42, 0.44]
            else:
                hdr, rows = P.table2_rows()
                w = [0.40, 0.80, 0.58, 0.62, 0.64, 0.52]
            add("table head", b[2])
            t = d.add_table(rows=1 + len(rows), cols=len(hdr))
            _borders(t)
            for j, h in enumerate(hdr):
                c = t.cell(0, j).paragraphs[0]
                c.style = S["table col head"]
                _rich(c, h)
            for i, r in enumerate(rows, start=1):
                for j, v in enumerate(r):
                    c = t.cell(i, j).paragraphs[0]
                    c.style = S["table copy"]
                    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    _rich(c, str(v))
            _fix_widths(t, w)
            anchor._p.addprevious(t._tbl)
            if len(b) > 3 and b[3]:
                add("table footnote", b[3])

    add("Body Text", P.DATA_NOTE)
    add("Heading 5", "Acknowledgment")
    add("Body Text", P.ACK)
    add("Heading 5", "References")
    for r in P.REFS:
        add("references", r)
    d.save(out)
