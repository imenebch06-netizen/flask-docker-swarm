import os
import re
import time
from xml.sax.saxutils import escape
from celery import Celery
import psycopg2
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/cvdb"
)
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY", "/shared_pdf")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

def database_connection():
    return psycopg2.connect(DATABASE_URL.replace(
        "postgresql+psycopg2://", "postgresql://", 1
    ))


def update_user_status(user_id, status, filename=None):
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET pdf_status = %s, pdf_filename = %s WHERE id = %s",
                (status, filename, user_id)
            )


def safe_filename(value):
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return normalized or "user"


def paragraph_text(value, fallback):
    return escape(value or fallback).replace("\n", "<br/>")

@celery_app.task(name="compile_pdf_task")
def compile_pdf_task(user_id, user_data):
    try:
        time.sleep(3)
        os.makedirs(PDF_DIRECTORY, exist_ok=True)
        first_name = user_data.get("first_name") or user_data.get("username", "")
        last_name = user_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        filename = f"cv_{user_id}_{safe_filename(full_name)}.pdf"
        output_path = os.path.join(PDF_DIRECTORY, filename)

        try:
            title_color = colors.HexColor(user_data.get("theme_color") or "#2C3E50")
        except ValueError:
            title_color = colors.HexColor("#2C3E50")

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CvTitle", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=27, leading=31, textColor=colors.HexColor("#17212B"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "CvSubtitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=title_color
        )
        contact_style = ParagraphStyle(
            "CvContact", parent=styles["Normal"], fontSize=9, leading=12,
            textColor=colors.HexColor("#66727E")
        )
        section_style = ParagraphStyle(
            "CvSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=10, leading=12, textColor=colors.HexColor("#66727E"),
            spaceBefore=13, spaceAfter=7
        )
        body_style = ParagraphStyle(
            "CvBody", parent=styles["BodyText"], fontSize=10, leading=15,
            textColor=colors.HexColor("#2D3748")
        )
        badge_style = ParagraphStyle(
            "CvBadge", parent=body_style, fontSize=8.5, leading=11,
            textColor=colors.HexColor("#2D3748")
        )
        document = SimpleDocTemplate(
            output_path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=18 * mm, bottomMargin=18 * mm
        )
        contact = " | ".join(value for value in [
            user_data.get("email", ""), user_data.get("phone", "")
        ] if value)
        header = Table([[
            [Paragraph(escape(full_name or "Candidat"), title_style),
             Paragraph(paragraph_text(user_data.get("job_title"), ""), subtitle_style),
             Spacer(1, 5), Paragraph(escape(contact), contact_style)],
            Paragraph("EXPRESS<br/>PDF", ParagraphStyle(
                "Mark", parent=contact_style, alignment=2, fontName="Helvetica-Bold",
                fontSize=9, leading=11, textColor=title_color
            ))
        ]], colWidths=[135 * mm, 25 * mm])
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LINEBEFORE", (0, 0), (0, 0), 5, title_color),
        ]))
        skills = [item.strip() for item in (user_data.get("skills") or "").split(",") if item.strip()]
        skill_cells = [Paragraph(escape(skill), badge_style) for skill in skills] or [
            Paragraph("Aucune compétence renseignée", body_style)
        ]
        skill_rows = [skill_cells[index:index + 3] for index in range(0, len(skill_cells), 3)]
        for row in skill_rows:
            row.extend([""] * (3 - len(row)))
        skill_table = Table(skill_rows, colWidths=[55 * mm] * 3)
        skill_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE4DF")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story = [
            header,
            Spacer(1, 12),
            HRFlowable(width="100%", thickness=1.5, color=title_color),
            Paragraph("EXPÉRIENCES PROFESSIONNELLES", section_style),
            Paragraph(
                paragraph_text(user_data.get("experiences"), "Aucune expérience renseignée"),
                body_style
            ),
            Paragraph("COMPÉTENCES", section_style),
            skill_table,
        ]
        document.build(story)
        update_user_status(user_id, "READY", filename)
        return {"status": "SUCCESS", "file": filename}
    except Exception:
        update_user_status(user_id, "FAILED")
        raise