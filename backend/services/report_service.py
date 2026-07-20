"""
PDF report generation using reportlab (lightweight, no browser/wkhtmltopdf).

Produces two report types:
  * candidate_report  — resume analysis, role match, AI insights
  * interview_report  — interview score, integrity, warnings, transcript
"""
from __future__ import annotations

import io
import logging
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)

logger = logging.getLogger("hiringbuddy.reports")

BRAND = colors.HexColor("#7c3aed")
BRAND_2 = colors.HexColor("#d946ef")
INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#6b7280")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("HBTitle", parent=ss["Title"], textColor=BRAND, fontSize=22, spaceAfter=4))
    ss.add(ParagraphStyle("HBSub", parent=ss["Normal"], textColor=MUTED, fontSize=10, spaceAfter=12))
    ss.add(ParagraphStyle("HBH2", parent=ss["Heading2"], textColor=INK, fontSize=13, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("HBBody", parent=ss["Normal"], textColor=INK, fontSize=10, leading=15))
    ss.add(ParagraphStyle("HBMuted", parent=ss["Normal"], textColor=MUTED, fontSize=9))
    return ss


def _header(story, ss, title, subtitle):
    story.append(Paragraph("⚡ HiringBuddy", ss["HBTitle"]))
    story.append(Paragraph(title, ss["HBH2"]))
    story.append(Paragraph(subtitle, ss["HBSub"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND))
    story.append(Spacer(1, 10))


def _kv_table(rows: List[List[str]], col_widths=(55 * mm, 110 * mm)):
    t = Table(rows, colWidths=list(col_widths))
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e5e7eb")),
    ]))
    return t


def _score_bar_table(pairs: List[tuple]):
    """Render metric rows like [('Skills', 78), ...] as a coloured table."""
    data = [["Metric", "Score"]]
    for label, val in pairs:
        data.append([label, f"{round(val)}%"])
    t = Table(data, colWidths=(90 * mm, 75 * mm))
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t


def _build(story) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm, title="HiringBuddy Report")
    doc.build(story)
    return buf.getvalue()


def candidate_report(candidate) -> bytes:
    ss = _styles()
    story = []
    _header(story, ss, "Candidate Analysis Report", candidate.name or "Candidate")

    rm = candidate.role_match_data or {}
    story.append(Paragraph("Profile", ss["HBH2"]))
    story.append(_kv_table([
        ["Name", candidate.name or "—"],
        ["Email", candidate.email or "—"],
        ["Phone", candidate.phone or "—"],
        ["Role Applied", candidate.role_applied or "—"],
        ["Experience", f"{candidate.experience_years or 0} years"],
        ["Education", ", ".join(candidate.education or []) or "—"],
        ["Languages", ", ".join(candidate.languages or []) or "—"],
        ["Skills", ", ".join(candidate.skills or []) or "—"],
    ]))

    story.append(Paragraph("Role Match", ss["HBH2"]))
    story.append(_score_bar_table([
        ("Overall Match", rm.get("overall_match", candidate.overall_score or 0)),
        ("Skills Match", rm.get("skills_match", 0)),
        ("Experience Match", rm.get("experience_match", 0)),
        ("Project Match", rm.get("project_match", 0)),
        ("Certification Match", rm.get("certification_match", 0)),
        ("Truth Score", candidate.truth_score or 0),
    ]))

    hr = candidate.hr_insights or {}
    if hr:
        story.append(Paragraph("AI Insights", ss["HBH2"]))
        story.append(Paragraph(hr.get("summary", ""), ss["HBBody"]))
        if hr.get("strengths"):
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Strengths:</b> " + "; ".join(hr["strengths"]), ss["HBBody"]))
        if hr.get("weaknesses"):
            story.append(Paragraph("<b>Weaknesses:</b> " + "; ".join(hr["weaknesses"]), ss["HBBody"]))
        if rm.get("missing_skills"):
            story.append(Paragraph("<b>Missing skills:</b> " + ", ".join(rm["missing_skills"]), ss["HBBody"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Recommendation:</b> {hr.get('recommendation', rm.get('recommendation', '—'))}", ss["HBBody"]))

    warnings = candidate.detailed_warnings or []
    if warnings:
        story.append(Paragraph("Warnings", ss["HBH2"]))
        for w in warnings:
            story.append(Paragraph(f"• <b>{w.get('skill','')}</b>: {w.get('reason','')} ({w.get('severity','')})", ss["HBBody"]))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    story.append(Paragraph("Generated by HiringBuddy AI Recruitment Platform.", ss["HBMuted"]))
    logger.info("Generated candidate report PDF for %s", candidate.id)
    return _build(story)


def interview_report(candidate, interview) -> bytes:
    ss = _styles()
    story = []
    _header(story, ss, "Interview Report", candidate.name or "Candidate")

    report = candidate.interview_report or {}
    story.append(Paragraph("Summary", ss["HBH2"]))
    story.append(_kv_table([
        ["Candidate", candidate.name or "—"],
        ["Role", candidate.role_applied or "—"],
        ["Status", candidate.interview_status or "—"],
        ["Recommendation", report.get("recommendation", "—")],
    ]))

    dims = report.get("dimensions", {})
    story.append(Paragraph("Scores", ss["HBH2"]))
    story.append(_score_bar_table([
        ("Final Score", report.get("final_score", 0)),
        ("Interview Score", report.get("interview_score", candidate.interview_score or 0)),
        ("Integrity Score", report.get("integrity_score", candidate.integrity_score or 0)),
        ("Communication", dims.get("communication", 0)),
        ("Technical", dims.get("technical", 0)),
        ("Confidence", dims.get("confidence", 0)),
    ]))

    warnings = (interview.warnings if interview else None) or candidate.proctoring_warnings or []
    story.append(Paragraph(f"Proctoring Warnings ({len(warnings)})", ss["HBH2"]))
    if warnings:
        for w in warnings[:25]:
            story.append(Paragraph(f"• [{w.get('severity','')}] {w.get('message','')}", ss["HBBody"]))
    else:
        story.append(Paragraph("No malpractice detected during the session.", ss["HBBody"]))

    transcript = (interview.transcript if interview else None) or []
    if transcript:
        story.append(Paragraph("Transcript", ss["HBH2"]))
        for i, t in enumerate(transcript, 1):
            story.append(Paragraph(f"<b>Q{i}. {t.get('question','')}</b>", ss["HBBody"]))
            story.append(Paragraph(f"A: {t.get('answer','') or '—'}", ss["HBBody"]))
            story.append(Paragraph(f"<i>Score: {t.get('score','—')}</i>", ss["HBMuted"]))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    story.append(Paragraph("Generated by HiringBuddy AI Recruitment Platform.", ss["HBMuted"]))
    logger.info("Generated interview report PDF for %s", candidate.id)
    return _build(story)
