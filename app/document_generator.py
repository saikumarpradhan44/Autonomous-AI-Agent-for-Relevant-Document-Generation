from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
import re

def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run()

    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")

    run._r.addnext(field)


def add_markdown_runs(paragraph, text):
    """Render Markdown bold, italic, inline code and HTML line breaks."""

    pattern = r'(<br\s*/?>|\*\*.*?\*\*|\*.*?\*|`.*?`)'
    parts = re.split(pattern, text, flags=re.IGNORECASE)

    for part in parts:
        if not part:
            continue

        if re.fullmatch(r'<br\s*/?>', part, re.IGNORECASE):
            paragraph.add_run().add_break()

        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True

        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.italic = True

        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)

        else:
            paragraph.add_run(part)


def add_formatted_content(doc, content):
    """Convert Markdown-style content into formatted Word elements."""

    lines = content.splitlines()
    in_code_block = False
    code_lines = []
    i = 0

    while i < len(lines):

        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Fenced code blocks
        if line.startswith("```"):

            if not in_code_block:
                in_code_block = True
                code_lines = []

            else:
                paragraph = doc.add_paragraph()
                paragraph.paragraph_format.left_indent = Inches(0.2)

                run = paragraph.add_run("\n".join(code_lines))
                run.font.name = "Consolas"
                run.font.size = Pt(8)

                in_code_block = False

            i += 1
            continue

        if in_code_block:
            code_lines.append(lines[i])
            i += 1
            continue

        # Horizontal separators
        if re.fullmatch(r"[-*_]{3,}", line):
            i += 1
            continue

        # Markdown tables
        if (
            line.startswith("|")
            and i + 1 < len(lines)
            and re.search(r"\|?\s*:?-{3,}:?\s*(\||$)", lines[i + 1])
        ):

            headers = [
                cell.strip()
                for cell in line.strip("|").split("|")
            ]

            i += 2
            rows = []

            while i < len(lines) and lines[i].strip().startswith("|"):

                rows.append([
                    cell.strip()
                    for cell in lines[i].strip().strip("|").split("|")
                ])

                i += 1

            table = doc.add_table(rows=1, cols=len(headers))
            table.style = "Light Shading Accent 1"

            # Table headers
            for cell, header in zip(table.rows[0].cells, headers):
                add_markdown_runs(cell.paragraphs[0], header)

                for run in cell.paragraphs[0].runs:
                    run.bold = True

            # Table rows
            for row_data in rows:

                cells = table.add_row().cells

                for cell, value in zip(cells, row_data):
                    add_markdown_runs(cell.paragraphs[0], value)

            continue

        # Markdown headings: # through ######
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if heading_match:

            heading_level = min(len(heading_match.group(1)), 4)
            heading_text = heading_match.group(2).strip()

            doc.add_heading(heading_text, level=heading_level)

        # Bullet points
        elif re.match(r"^[-*]\s+", line):

            text = re.sub(r"^[-*]\s+", "", line)

            paragraph = doc.add_paragraph(style="List Bullet")
            add_markdown_runs(paragraph, text)

        # Numbered lists
        elif re.match(r"^\d+[.)]\s+", line):

            text = re.sub(r"^\d+[.)]\s+", "", line)

            paragraph = doc.add_paragraph(style="List Number")
            add_markdown_runs(paragraph, text)

        # Normal paragraphs
        else:

            paragraph = doc.add_paragraph()
            add_markdown_runs(paragraph, line)

        i += 1

    # Handle unfinished code blocks
    if in_code_block and code_lines:

        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.2)

        run = paragraph.add_run("\n".join(code_lines))
        run.font.name = "Consolas"
        run.font.size = Pt(8)


def generate_document(title, sections, output_path):

    doc = Document()

    # Page margins
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    # Default font
    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)

    # Cover page
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run("\n\n\n\n")

    title_run = paragraph.add_run(title)
    title_run.bold = True
    title_run.font.size = Pt(26)
    title_run.font.color.rgb = RGBColor(31, 78, 121)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle_run = subtitle.add_run("AI-Generated Project Document")
    subtitle_run.font.size = Pt(14)

    doc.add_page_break()

    # Header
    header = section.header.paragraphs[0]
    header.text = title
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Footer
    footer = section.footer.paragraphs[0]
    add_page_number(footer)

    # Table of Contents (section list)
    doc.add_heading("Table of Contents", level=1)

    for index, item in enumerate(sections, start=1):
        doc.add_paragraph(f"{index}. {item['heading']}")

    doc.add_page_break()

    # Project details
    doc.add_heading("Project Details", level=1)

    for item in sections:

        doc.add_heading(item["heading"], level=2)

        add_formatted_content(
            doc,
            item["content"]
        )

    # Save document
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc.save(output_path)

    return output_path