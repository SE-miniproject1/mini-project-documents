#!/usr/bin/env python3
"""Build the Word submission copies of the SRS and the Test Plan.

Converts the Markdown masters in docs/ into .docx files in submission/,
applying heading styles, table grids, page numbering and the diagram images.

Usage, from the Deliverable-1 directory:

    python3 tools/build_docx.py
"""
import pathlib
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "submission"
DIAGRAMS = ROOT / "diagrams"

MONO = "Consolas"
BODY_FONT = "Calibri"

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def add_field(paragraph, instruction):
    """Insert a Word field code, used here for PAGE and NUMPAGES."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, end):
        run._r.append(element)


def set_cell_background(cell, colour):
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), colour)
    cell._tc.get_or_add_tcPr().append(shading)


def repeat_header_row(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def write_runs(paragraph, text, size=None):
    """Render inline bold, code and link markup into a paragraph."""
    text = text.replace("<br/>", "\n").replace("<br>", "\n")
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = MONO
            run.font.color.rgb = RGBColor(0xB0, 0x30, 0x60)
        elif part.startswith("["):
            label = part[1 : part.index("]")]
            run = paragraph.add_run(label)
            run.font.color.rgb = RGBColor(0x1A, 0x4E, 0x8A)
            run.underline = True
        else:
            run = paragraph.add_run(part)
        if size:
            run.font.size = Pt(size)


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_separator(cells):
    return bool(cells) and all(set(c) <= set("-: ") for c in cells)


def add_table(document, rows, font_size):
    columns = max(len(r) for r in rows)
    table = document.add_table(rows=0, cols=columns)
    table.style = "Table Grid"
    table.autofit = True
    for index, cells in enumerate(rows):
        cells = cells + [""] * (columns - len(cells))
        row = table.add_row()
        for cell, text in zip(row.cells, cells):
            cell.text = ""
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            write_runs(paragraph, text, size=font_size)
            if index == 0:
                for run in paragraph.runs:
                    run.bold = True
                set_cell_background(cell, "DCE6F1")
        if index == 0:
            repeat_header_row(row)
    document.add_paragraph()
    return table


def add_code_block(document, lines):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.3)
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run("\n".join(lines))
    run.font.name = MONO
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def configure(document, landscape, title, subtitle):
    section = document.sections[0]
    if landscape:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = section.page_height, section.page_width
    for margin in ("left_margin", "right_margin"):
        setattr(section, margin, Inches(0.7))
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)

    normal = document.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(10.5)

    header = section.header.paragraphs[0]
    header.text = title
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(f"{subtitle}    Page ")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)
    add_field(footer, "PAGE")
    run = footer.add_run(" of ")
    run.font.size = Pt(8)
    add_field(footer, "NUMPAGES")
    for run in footer.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x70, 0x70, 0x70)


# Diagram images are inserted immediately after these headings in the SRS.
DIAGRAM_ANCHOR = "## 4. Analysis Models"
DIAGRAM_FIGURES = [
    ("use-case.png", "Figure 1. Use case diagram, grouped by system feature."),
    ("er-diagram.png", "Figure 2. Entity relationship diagram."),
    ("dfd-level0.png", "Figure 3. Data flow diagram, Level 0, the context diagram."),
    ("dfd-level1a-supply.png", "Figure 4. Data flow diagram, Level 1, Sheet A, supply side."),
    ("dfd-level1b-demand.png", "Figure 5. Data flow diagram, Level 1, Sheet B, demand, camps and reporting."),
    ("architecture.png", "Figure 6. System architecture."),
]


def insert_figures(document, usable_width):
    for filename, caption in DIAGRAM_FIGURES:
        path = DIAGRAMS / filename
        if not path.exists():
            print(f"  warning: {filename} missing, figure skipped")
            continue
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run().add_picture(str(path), width=usable_width)
        caption_paragraph = document.add_paragraph()
        caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = caption_paragraph.add_run(caption)
        run.italic = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        document.add_paragraph()


def convert(source, target, title, subtitle, landscape, table_font, with_figures):
    document = Document()
    configure(document, landscape, title, subtitle)
    section = document.sections[0]
    usable_width = section.page_width - section.left_margin - section.right_margin

    lines = source.read_text(encoding="utf-8").split("\n")
    index = 0
    pending_table = []
    figures_done = not with_figures
    last_heading = ""

    def flush_table():
        nonlocal pending_table
        if pending_table:
            add_table(document, pending_table, table_font)
            pending_table = []

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("|"):
            cells = split_row(stripped)
            if not is_separator(cells):
                pending_table.append(cells)
            index += 1
            continue
        flush_table()

        if stripped.startswith("```"):
            block = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            add_code_block(document, block)
            index += 1
            continue

        if not stripped:
            index += 1
            continue

        if stripped == "---":
            index += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            if with_figures and not figures_done and last_heading == DIAGRAM_ANCHOR:
                insert_figures(document, usable_width)
                figures_done = True
            if level == 1:
                heading = document.add_heading(level=0)
                write_runs(heading, text)
                heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                heading = document.add_heading(level=min(level - 1, 4))
                write_runs(heading, text)
            last_heading = stripped
            index += 1
            continue

        if re.match(r"^[-*] ", stripped):
            paragraph = document.add_paragraph(style="List Bullet")
            write_runs(paragraph, stripped[2:])
            index += 1
            continue

        if re.match(r"^\d+\. ", stripped):
            paragraph = document.add_paragraph(style="List Number")
            write_runs(paragraph, re.sub(r"^\d+\.\s*", "", stripped))
            index += 1
            continue

        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(6)
        write_runs(paragraph, stripped)
        index += 1

    flush_table()
    if with_figures and not figures_done:
        insert_figures(document, usable_width)

    OUT.mkdir(exist_ok=True)
    document.save(target)
    return target


def main():
    OUT.mkdir(exist_ok=True)
    jobs = [
        (DOCS / "SRS.md", OUT / "SRS-Blood-Bank-Management-System.docx",
         "Software Requirements Specification", "Blood Bank Management System, Version 1.0",
         False, 9, True),
        (DOCS / "Test-Plan.md", OUT / "Test-Plan-Blood-Bank-Management-System.docx",
         "Test Plan", "Blood Bank Management System, Version 1.0",
         True, 7.5, False),
    ]
    for source, target, title, subtitle, landscape, table_font, figures in jobs:
        if not source.exists():
            print(f"missing source: {source}")
            return 1
        convert(source, target, title, subtitle, landscape, table_font, figures)
        print(f"built {target.relative_to(ROOT)}  ({target.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
