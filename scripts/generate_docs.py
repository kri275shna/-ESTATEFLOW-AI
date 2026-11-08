import os
import zipfile
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DOCS_DIR = Path("docs")
ROOT_DIR = Path(".")

TDD_MD_PATH = DOCS_DIR / "TDD.md"
TDD_PDF_PATH = DOCS_DIR / "TDD.pdf"
TDD_DOCX_PATH = DOCS_DIR / "TDD.docx"
DEPLOYMENT_MD_PATH = ROOT_DIR / "deployment.md"
ZIP_SUBMISSION_PATH = ROOT_DIR / "estateflow-ai-submission.zip"


def generate_docx():
    print("Generating TDD.docx...")
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Styles
    emerald = RGBColor(5, 150, 105)
    slate_dark = RGBColor(15, 23, 42)
    slate_muted = RGBColor(71, 85, 105)

    with open(TDD_MD_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block = False
    code_lines = []

    for line in lines:
        line_strip = line.strip()

        if line_strip.startswith("```"):
            if in_code_block:
                # End of code block
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                run = p.add_run("\n".join(code_lines))
                run.font.name = "Courier New"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(30, 41, 59)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line.rstrip())
            continue

        if not line_strip:
            continue

        if line_strip.startswith("# "):
            title = doc.add_paragraph()
            title.alignment = WD_ALIGN_PARAGRAPH.LEFT
            title.paragraph_format.space_before = Pt(12)
            title.paragraph_format.space_after = Pt(6)
            run = title.add_run(line_strip[2:])
            run.font.name = "Calibri"
            run.font.size = Pt(22)
            run.font.bold = True
            run.font.color.rgb = slate_dark
        elif line_strip.startswith("## "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(4)
            run = h.add_run(line_strip[3:])
            run.font.name = "Calibri"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = emerald
        elif line_strip.startswith("### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(3)
            run = h.add_run(line_strip[4:])
            run.font.name = "Calibri"
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = slate_dark
        elif line_strip.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(line_strip[2:])
            run.font.name = "Calibri"
            run.font.size = Pt(10)
            run.font.color.rgb = slate_muted
        elif line_strip.startswith("1. ") or line_strip.startswith("2. ") or line_strip.startswith("3. ") or line_strip.startswith("4. ") or line_strip.startswith("5. ") or line_strip.startswith("6. ") or line_strip.startswith("7. ") or line_strip.startswith("8. "):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(line_strip[3:])
            run.font.name = "Calibri"
            run.font.size = Pt(10)
            run.font.color.rgb = slate_muted
        elif line_strip.startswith("---"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run("____________________________________________________________________")
            run.font.size = Pt(6)
            run.font.color.rgb = RGBColor(226, 232, 240)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(line_strip)
            run.font.name = "Calibri"
            run.font.size = Pt(10)
            run.font.color.rgb = slate_muted

    doc.save(str(TDD_DOCX_PATH))
    print(f"Saved: {TDD_DOCX_PATH}")


def generate_pdf():
    print("Generating TDD.pdf...")
    pdf = SimpleDocTemplate(
        str(TDD_PDF_PATH),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TDDTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        "TDDH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#059669"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "TDDH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "TDDBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        "TDDBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        "TDDCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#E2E8F0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )

    elements = []

    with open(TDD_MD_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block = False
    code_lines = []

    for line in lines:
        line_strip = line.strip()

        if line_strip.startswith("```"):
            if in_code_block:
                code_text = "<br/>".join(
                    c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
                    for c in code_lines
                )
                elements.append(Paragraph(code_text, code_style))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line.rstrip())
            continue

        if not line_strip:
            continue

        # Format markdown bold & links
        cleaned_line = line_strip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Replace **bold** with <b>bold</b>
        import re
        cleaned_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", cleaned_line)
        cleaned_line = re.sub(r"\*(.*?)\*", r"<i>\1</i>", cleaned_line)

        if line_strip.startswith("# "):
            elements.append(Paragraph(cleaned_line[2:], title_style))
            elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceBefore=4, spaceAfter=8))
        elif line_strip.startswith("## "):
            elements.append(Paragraph(cleaned_line[3:], h1_style))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=2, spaceAfter=4))
        elif line_strip.startswith("### "):
            elements.append(Paragraph(cleaned_line[4:], h2_style))
        elif line_strip.startswith("- "):
            elements.append(Paragraph(f"• {cleaned_line[2:]}", bullet_style))
        elif re.match(r"^\d+\.\s", line_strip):
            elements.append(Paragraph(cleaned_line, bullet_style))
        elif line_strip.startswith("---"):
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=6))
        else:
            elements.append(Paragraph(cleaned_line, body_style))

    pdf.build(elements)
    print(f"Saved: {TDD_PDF_PATH}")


def create_submission_zip():
    print(f"Packaging submission ZIP: {ZIP_SUBMISSION_PATH}...")
    with zipfile.ZipFile(ZIP_SUBMISSION_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        # Include TDD.pdf
        if TDD_PDF_PATH.exists():
            z.write(TDD_PDF_PATH, arcname="TDD.pdf")
            print("  Added TDD.pdf")
        # Include TDD.docx
        if TDD_DOCX_PATH.exists():
            z.write(TDD_DOCX_PATH, arcname="TDD.docx")
            print("  Added TDD.docx")
        # Include deployment.md
        if DEPLOYMENT_MD_PATH.exists():
            z.write(DEPLOYMENT_MD_PATH, arcname="deployment.md")
            print("  Added deployment.md")

    zip_size_mb = os.path.getsize(ZIP_SUBMISSION_PATH) / (1024 * 1024)
    print(f"Created {ZIP_SUBMISSION_PATH} (Size: {zip_size_mb:.2f} MB - Limit is 25 MB).")


if __name__ == "__main__":
    generate_docx()
    generate_pdf()
    create_submission_zip()
