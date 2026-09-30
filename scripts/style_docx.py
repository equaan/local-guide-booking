"""Post-processes the pandoc-generated .docx: fonts, headings, table borders, cover page, page numbers.

Usage: python scripts/style_docx.py path/to/report.docx
"""
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x1F, 0x38, 0x64)
GREY = RGBColor(0x55, 0x55, 0x55)
BODY_FONT = "Calibri"
CODE_FONT = "Consolas"


def set_font(style, name=None, size=None, bold=None, color=None):
    if name:
        style.font.name = name
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), name)
    if size:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if color is not None:
        style.font.color.rgb = color


def get_style(doc, name):
    try:
        return doc.styles[name]
    except KeyError:
        return None


def style_document(doc):
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text"):
        st = get_style(doc, name)
        if st is not None:
            set_font(st, BODY_FONT, 10.5)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.line_spacing = 1.1
    compact = get_style(doc, "Compact")
    if compact is not None:
        set_font(compact, BODY_FONT, 9)
        compact.paragraph_format.space_after = Pt(2)
        compact.paragraph_format.space_before = Pt(2)

    sizes = {"Heading 1": 20, "Heading 2": 14, "Heading 3": 12}
    for name, size in sizes.items():
        st = get_style(doc, name)
        if st is not None:
            set_font(st, BODY_FONT, size, bold=True, color=NAVY)
            st.paragraph_format.space_before = Pt(14 if name != "Heading 1" else 0)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.keep_with_next = True
    h1 = get_style(doc, "Heading 1")
    if h1 is not None:
        h1.paragraph_format.page_break_before = True

    for name in ("Source Code", "Verbatim Char"):
        st = get_style(doc, name)
        if st is not None:
            set_font(st, CODE_FONT, 9)

    cover = {
        "CoverTitle": (30, True, NAVY, 130),
        "CoverSub": (16, False, GREY, 6),
        "CoverMeta": (16, True, RGBColor(0x22, 0x22, 0x22), 70),
        "CoverSmall": (11, False, GREY, 10),
    }
    for name, (size, bold, color, before) in cover.items():
        st = get_style(doc, name)
        if st is not None:
            set_font(st, BODY_FONT, size, bold=bold, color=color)
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            st.paragraph_format.space_before = Pt(before)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.page_break_before = False

    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = section.right_margin = Cm(2.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)


def shade(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def style_tables(doc):
    for table in doc.tables:
        tbl_pr = table._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "9AA5B1")
            borders.append(el)
        tbl_pr.append(borders)

        cell_mar = OxmlElement("w:tblCellMar")
        for side, w in (("top", 40), ("left", 80), ("bottom", 40), ("right", 80)):
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:w"), str(w))
            el.set(qn("w:type"), "dxa")
            cell_mar.append(el)
        tbl_pr.append(cell_mar)

        for r_idx, row in enumerate(table.rows):
            if r_idx == 0:
                tr_pr = row._tr.get_or_add_trPr()
                hdr = OxmlElement("w:tblHeader")
                tr_pr.append(hdr)
            for cell in row.cells:
                if r_idx == 0:
                    shade(cell, "1F3864")
                elif r_idx % 2 == 0:
                    shade(cell, "F2F5F9")
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(9)
                        if r_idx == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


def add_page_numbers(doc):
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label = p.add_run("Local Guide Booking System | Mohammad Equaan Kacchi | Page ")
        label.font.size = Pt(8.5)
        label.font.color.rgb = GREY
        run = p.add_run()
        run.font.size = Pt(8.5)
        run.font.color.rgb = GREY
        for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
            if kind:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), kind)
            else:
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = text
            run._r.append(el)


def scale_images(doc):
    max_width = Cm(17.0)
    for shape in doc.inline_shapes:
        if shape.width > max_width:
            ratio = max_width / shape.width
            shape.width = int(shape.width * ratio)
            shape.height = int(shape.height * ratio)


def main(path):
    doc = Document(path)
    style_document(doc)
    style_tables(doc)
    scale_images(doc)
    add_page_numbers(doc)
    doc.save(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/style_docx.py report.docx")
    main(sys.argv[1])
