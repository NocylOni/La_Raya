"""PDF export for patient summaries and visit notes (QoL: PDF export/printing)."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from app.db.database import Database
from app.db.dao import reporting as reporting_dao
from app.db.dao import visits as visits_dao


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=13, spaceBefore=12,
                               spaceAfter=6, textColor=colors.HexColor("#1a3d5c")))
    return styles


def export_patient_summary_pdf(db: Database, patient_id: int, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    summary = reporting_dao.patient_summary(db, patient_id)
    patient = summary["patient"]
    styles = _styles()

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    story = [
        Paragraph(f"Patient Summary: {patient['first_name']} {patient['last_name']}", styles["Title"]),
        Paragraph(f"MRN: {patient['mrn']}  |  DOB: {patient['dob']}  |  Sex: {patient.get('sex') or 'N/A'}",
                  styles["Normal"]),
        Spacer(1, 0.2 * inch),
    ]

    story.append(Paragraph("Active Problems", styles["SectionHeader"]))
    if summary["active_problems"]:
        data = [["ICD Code", "Description"]] + [
            [p["icd_code"], p["description"]] for p in summary["active_problems"]
        ]
        story.append(_table(data))
    else:
        story.append(Paragraph("None recorded.", styles["Normal"]))

    story.append(Paragraph("Active Medications", styles["SectionHeader"]))
    if summary["active_medications"]:
        data = [["Medication", "Dosage"]] + [
            [m["medication_name"], m["dosage"] or ""] for m in summary["active_medications"]
        ]
        story.append(_table(data))
    else:
        story.append(Paragraph("None recorded.", styles["Normal"]))

    story.append(Paragraph("Allergies", styles["SectionHeader"]))
    if summary["allergies"]:
        data = [["Substance", "Severity"]] + [
            [a["substance"], a["severity"] or ""] for a in summary["allergies"]
        ]
        story.append(_table(data))
    else:
        story.append(Paragraph("No known allergies recorded.", styles["Normal"]))

    story.append(Paragraph("Record Counts", styles["SectionHeader"]))
    counts = summary["counts"]
    data = [["Category", "Count"]] + [[k.title(), str(v)] for k, v in counts.items()]
    story.append(_table(data))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Balance Due: ${summary['balance_due']:.2f}", styles["Normal"]))

    doc.build(story)
    return output_path


def export_visit_note_pdf(db: Database, visit_id: int, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    visit = visits_dao.get_visit(db, visit_id)
    if visit is None:
        raise ValueError(f"No visit with id {visit_id}")
    from app.db.dao import patients as patients_dao
    patient = patients_dao.get_patient(db, visit["patient_id"])
    styles = _styles()

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    story = [
        Paragraph(f"Visit Note: {patient['first_name']} {patient['last_name']} (MRN {patient['mrn']})",
                  styles["Title"]),
        Paragraph(f"Date: {visit['visit_date']}  |  Provider: {visit['provider'] or 'N/A'}  |  "
                  f"Type: {visit['visit_type']}", styles["Normal"]),
        Spacer(1, 0.15 * inch),
    ]
    for label, field in (
        ("Chief Complaint", "chief_complaint"),
        ("History of Present Illness", "hpi"),
        ("Review of Systems", "ros"),
        ("Physical Examination", "physical_exam"),
        ("Assessment", "assessment"),
        ("Plan", "plan"),
        ("Notes", "notes"),
    ):
        story.append(Paragraph(label, styles["SectionHeader"]))
        story.append(Paragraph(visit[field] or "—", styles["Normal"]))

    doc.build(story)
    return output_path


def _table(data: list[list[str]]) -> Table:
    table = Table(data, hAlign="LEFT", colWidths=[2.5 * inch, 3.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table
