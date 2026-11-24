import os
import sys
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def markdown_to_docx(md_path: str, docx_path: str):
    """Converts a Markdown file into a styled Word Document (.docx)."""
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = Document()

    # Configure standard margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    in_code_block = False
    code_lines = []

    for line in lines:
        raw = line.rstrip("\r\n")

        # Code block handler
        if raw.strip().startswith("```"):
            if in_code_block:
                # End of code block
                in_code_block = False
                code_text = "\n".join(code_lines)
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.left_indent = Inches(0.2)
                run = p.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(30, 41, 59)
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(raw)
            continue

        # Skip horizontal dividers
        if re.match(r"^---+$", raw.strip()):
            continue

        # Headings
        if raw.startswith("# "):
            h = doc.add_heading(raw[2:].strip(), level=1)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(6)
            for r in h.runs:
                r.font.name = "Arial"
                r.font.size = Pt(16)
                r.font.bold = True
                r.font.color.rgb = RGBColor(14, 116, 144)
        elif raw.startswith("## "):
            h = doc.add_heading(raw[3:].strip(), level=2)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            for r in h.runs:
                r.font.name = "Arial"
                r.font.size = Pt(13)
                r.font.bold = True
                r.font.color.rgb = RGBColor(15, 23, 42)
        elif raw.startswith("### "):
            h = doc.add_heading(raw[4:].strip(), level=3)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            for r in h.runs:
                r.font.name = "Arial"
                r.font.size = Pt(11)
                r.font.bold = True
                r.font.color.rgb = RGBColor(51, 65, 85)

        # Bullet lists
        elif raw.strip().startswith(("* ", "- ")):
            bullet_text = re.sub(r"^[\*\-]\s+", "", raw.strip())
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            # Simple bold parsing
            parts = re.split(r"(\*\*.*?\*\*)", bullet_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                else:
                    p.add_run(part)

        # Normal paragraphs
        elif raw.strip():
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            parts = re.split(r"(\*\*.*?\*\*)", raw)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                else:
                    p.add_run(part)

    doc.save(docx_path)
    print(f"[✓] DOCX created successfully: {docx_path}")

def markdown_to_pdf(md_path: str, pdf_path: str):
    """Converts a Markdown file into a styled PDF document using ReportLab."""
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0e7490'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=4
    )
    h3_style = ParagraphStyle(
        'DocH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceBefore=8,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=4
    )
    code_style = ParagraphStyle(
        'DocCode',
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        spaceBefore=3,
        spaceAfter=4
    )

    story = []
    in_code = False
    code_lines = []

    for line in lines:
        raw = line.rstrip("\r\n")

        # Code block handler
        if raw.strip().startswith("```"):
            if in_code:
                in_code = False
                snippet = "\n".join(code_lines)
                story.append(Preformatted(snippet[:2500], code_style))
                story.append(Spacer(1, 4))
                code_lines = []
            else:
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append(raw)
            continue

        if re.match(r"^---+$", raw.strip()):
            story.append(Spacer(1, 6))
            continue

        # Format bold tags for ReportLab
        clean_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", raw)
        clean_line = clean_line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean_line = clean_line.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")

        if raw.startswith("# "):
            story.append(Paragraph(clean_line[2:].strip(), title_style))
        elif raw.startswith("## "):
            story.append(Paragraph(clean_line[3:].strip(), h2_style))
        elif raw.startswith("### "):
            story.append(Paragraph(clean_line[4:].strip(), h3_style))
        elif raw.strip().startswith(("* ", "- ")):
            bullet = re.sub(r"^[\*\-]\s+", "&bull; ", clean_line.strip())
            story.append(Paragraph(bullet, body_style))
        elif raw.strip():
            story.append(Paragraph(clean_line, body_style))

    doc.build(story)
    print(f"[✓] PDF created successfully: {pdf_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    
    target_reports = [
        "CTF_AGENT_MASTER_ARCHITECTURE_AND_OPERATIONS_MANUAL.md",
        "MASTER_SYSTEM_ARCHITECTURE.md",
        "AUTONOMOUS_REVERSE_ENGINEERING_AND_CTF_METHODOLOGY.md",
        "APEX_GAUNTLET_COMPREHENSIVE_BENCHMARK_REPORT.md",
        "FULL_SYSTEM_VERIFICATION_AND_BENCHMARK_REPORT.md",
        "GOOGLE_CTF_REPLICATION_AND_BROWSER_EXPLOIT_REPORT.md",
        "CTF_ORCHESTRATOR_HONEST_AUDIT.md",
        "PLAYWRIGHT_BROWSER_AUTOMATION_AND_EVIDENCE_DOCUMENT.md"
    ]

    for report_name in target_reports:
        md_file = os.path.join(docs_dir, report_name)
        base_name = os.path.splitext(report_name)[0]
        docx_file = os.path.join(docs_dir, f"{base_name}.docx")
        pdf_file = os.path.join(docs_dir, f"{base_name}.pdf")

        if os.path.exists(md_file):
            print(f"[*] Processing {report_name}...")
            markdown_to_docx(md_file, docx_file)
            markdown_to_pdf(md_file, pdf_file)
        else:
            print(f"[!] Warning: {md_file} not found")
