"""PDF export — executive brief (KPIs + AI narrative + breakdowns)."""
from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT

from app.services.conversion_engine import ConversionEngine
from app.services.kol_engine import KOLEngine
from app.services.opportunity_engine import OpportunityEngine
from app.data.store import DataStore
from app.ai.guardrails import build_system_prompt
from app.ai.llm import llm_service

router = APIRouter(prefix="/export", tags=["export"])

# Kiwi palette
KIWI_PRIMARY = colors.HexColor("#534666")
KIWI_ACCENT = colors.HexColor("#138086")
KIWI_LIGHT = colors.HexColor("#DC8665")
KIWI_CREAM = colors.HexColor("#EEB462")
KIWI_DARK = colors.HexColor("#352B44")
KIWI_MUTED = colors.HexColor("#6F6382")
KIWI_BG = colors.HexColor("#F5ECE8")


class ExportRequest(BaseModel):
    include_narrative: bool = True


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(name="title", parent=base["Title"], fontSize=24, leading=28,
                                textColor=KIWI_DARK, alignment=TA_LEFT, spaceAfter=4, fontName="Helvetica-Bold"),
        "eyebrow": ParagraphStyle(name="eyebrow", parent=base["Normal"], fontSize=8, leading=10,
                                  textColor=KIWI_ACCENT, spaceAfter=2, fontName="Helvetica-Bold"),
        "h2": ParagraphStyle(name="h2", parent=base["Heading2"], fontSize=14, leading=18,
                             textColor=KIWI_PRIMARY, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"),
        "h3": ParagraphStyle(name="h3", parent=base["Heading3"], fontSize=11, leading=14,
                             textColor=KIWI_DARK, spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold"),
        "body": ParagraphStyle(name="body", parent=base["BodyText"], fontSize=9.5, leading=14,
                               textColor=KIWI_DARK, spaceAfter=4, fontName="Helvetica"),
        "muted": ParagraphStyle(name="muted", parent=base["BodyText"], fontSize=8, leading=11,
                                textColor=KIWI_MUTED, fontName="Helvetica"),
        "kpi_label": ParagraphStyle(name="kpi_label", fontSize=7, leading=9, textColor=KIWI_MUTED,
                                    fontName="Helvetica-Bold", alignment=TA_LEFT),
        "kpi_value": ParagraphStyle(name="kpi_value", fontSize=22, leading=26, textColor=KIWI_PRIMARY,
                                    fontName="Helvetica-Bold", alignment=TA_LEFT),
        "kpi_sub": ParagraphStyle(name="kpi_sub", fontSize=8, leading=10, textColor=KIWI_MUTED,
                                  fontName="Helvetica"),
    }


def _md_to_paragraphs(text: str, style) -> list:
    """Convert simple markdown (paragraphs, headings, bullets, bold) to ReportLab flowables."""
    s = _styles()
    out = []
    for raw_block in re.split(r"\n\s*\n", text.strip()):
        block = raw_block.strip()
        if not block:
            continue
        # Heading
        if block.startswith("### "):
            out.append(Paragraph(_inline(block[4:]), s["h3"]))
        elif block.startswith("## "):
            out.append(Paragraph(_inline(block[3:]), s["h2"]))
        elif block.startswith("# "):
            out.append(Paragraph(_inline(block[2:]), s["h2"]))
        elif re.match(r"^[-*]\s", block.splitlines()[0]):
            for line in block.splitlines():
                line = line.strip()
                if line.startswith(("-", "*")):
                    out.append(Paragraph("• " + _inline(line[1:].strip()), style))
        else:
            for line in block.splitlines():
                out.append(Paragraph(_inline(line.strip()), style))
    return out


def _inline(text: str) -> str:
    # bold + italic
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # source IDs in brackets → colored
    text = re.sub(r"\[([A-Z]{3,4}\d+)\]", r'<font color="#028174"><b>[\1]</b></font>', text)
    return text


def _kpi_card(label, value, sub, st):
    inner = [
        [Paragraph(label.upper(), st["kpi_label"])],
        [Paragraph(value, st["kpi_value"])],
        [Paragraph(sub, st["kpi_sub"])],
    ]
    t = Table(inner, colWidths=[1.6 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.4, KIWI_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _bar(pct: float, max_pct: float = 30.0, width: float = 1.2) -> Table:
    pct = min(max(pct, 0), max_pct)
    filled = (pct / max_pct) * width
    t = Table([[""]], colWidths=[filled * inch], rowHeights=[0.12 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), KIWI_ACCENT),
        ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
    ]))
    return t


async def _generate_narrative_text() -> str:
    eng = ConversionEngine()
    overall = eng.overall()
    by_specialty = eng.breakdown("specialty_group").head(5).to_dict("records")
    by_territory = eng.breakdown("territory").head(5).to_dict("records")
    trend = eng.trend(freq="W").tail(12).to_dict("records")
    import json as _json
    payload = {
        "conversion_overall": overall.__dict__,
        "trend_last_12w": [{"bucket": str(t["bucket"]), "rate": t["conversion_rate"]} for t in trend],
        "by_specialty_top5": by_specialty,
        "by_territory_top5": by_territory,
    }
    system = build_system_prompt("exec")
    prompt = f"""Write a 4-paragraph executive narrative for a board-ready PDF.

Structure:
1) Headline KPI status (1 paragraph)
2) Where we are winning (1 paragraph)
3) Where we need attention (1 paragraph)
4) Recommended next 30 days actions (3 bullet points)

DATA:
{_json.dumps(payload, default=str)}"""
    resp = await llm_service.chat(messages=[{"role": "user", "content": prompt}], system=system, max_tokens=900)
    return resp.text


@router.post("/exec_brief_pdf")
async def export_pdf(req: ExportRequest):
    eng = ConversionEngine()
    kol_eng = KOLEngine()
    opp = OpportunityEngine()
    store = DataStore.instance()
    overall = eng.overall()
    kol = kol_eng.dashboard()
    by_specialty = eng.breakdown("specialty_group").head(6).to_dict("records")
    by_territory = eng.breakdown("territory").head(6).to_dict("records")
    top_reps = eng.breakdown("rep_name").head(6).to_dict("records")
    top_opps = opp.score_all().head(8)[["hcp_id", "hcp_name", "specialty_group", "territory",
                                        "opportunity_score", "consent_status"]].to_dict("records")

    narrative = ""
    if req.include_narrative:
        try:
            narrative = await _generate_narrative_text()
        except Exception as e:
            narrative = f"_AI narrative unavailable: {e}_"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
        title="Physical Engagement — Executive Brief",
        author="Vyntrix Intelligence",
    )
    st = _styles()
    story = []

    # Header
    now = datetime.now(timezone.utc)
    story.append(Paragraph("KIWI · COMMERCIAL INTELLIGENCE", st["eyebrow"]))
    story.append(Paragraph("Executive Brief", st["title"]))
    story.append(Paragraph(now.strftime("Generated %B %d, %Y · %H:%M UTC"), st["muted"]))
    story.append(Spacer(1, 0.18 * inch))

    # Divider
    divider = Table([[""]], colWidths=[7.3 * inch], rowHeights=[0.04 * inch])
    divider.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), KIWI_LIGHT)]))
    story.append(divider)
    story.append(Spacer(1, 0.18 * inch))

    # KPI cards
    cv_uplift = round(overall.conversion_rate - 12.0, 2)
    cards = [
        _kpi_card("ConversionRate_30d", f"{overall.conversion_rate:.1f}%",
                  f"Target 12% · uplift {cv_uplift:+.1f}", st),
        _kpi_card("Calls", f"{overall.total_calls}", f"Converted: {overall.converted_calls}", st),
        _kpi_card("Attribution Conf.", f"{overall.avg_confidence * 100:.0f}%", "Avg across links", st),
        _kpi_card("KOLs Tracked", f"{kol['summary']['total_kols']}",
                  f"Tier 1: {kol['summary']['tier1']} · Rising: {kol['summary']['rising_stars']}", st),
    ]
    kpi_table = Table([cards], colWidths=[1.85 * inch] * 4)
    kpi_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.2 * inch))

    # AI narrative
    if narrative:
        story.append(Paragraph("AI Executive Narrative", st["h2"]))
        story.extend(_md_to_paragraphs(narrative, st["body"]))
        story.append(Spacer(1, 0.15 * inch))

    # Therapy area table
    story.append(Paragraph("Conversion by Therapy Area", st["h2"]))
    data = [["Therapy Area", "Calls", "Converted", "Rate"]]
    for r in by_specialty:
        data.append([
            r["specialty_group"], str(r["total_calls"]), str(r["converted_calls"]),
            f"{r['conversion_rate']:.1f}%",
        ])
    t = Table(data, colWidths=[2.8 * inch, 1.0 * inch, 1.4 * inch, 1.0 * inch])
    t.setStyle(_table_style(highlight_col=3))
    story.append(t)
    story.append(Spacer(1, 0.12 * inch))

    # Territory table
    story.append(Paragraph("Conversion by Territory", st["h2"]))
    data = [["Territory", "Calls", "Converted", "Rate"]]
    for r in by_territory:
        data.append([r["territory"], str(r["total_calls"]), str(r["converted_calls"]),
                     f"{r['conversion_rate']:.1f}%"])
    t = Table(data, colWidths=[2.8 * inch, 1.0 * inch, 1.4 * inch, 1.0 * inch])
    t.setStyle(_table_style(highlight_col=3))
    story.append(t)
    story.append(PageBreak())

    # Page 2: Top Opportunities + Top Reps + footer
    story.append(Paragraph("Top HCP Opportunities", st["h2"]))
    data = [["HCP", "Specialty", "Territory", "Consent", "Score"]]
    for r in top_opps:
        data.append([
            r["hcp_name"], r["specialty_group"], r["territory"],
            r["consent_status"] or "—", f"{r['opportunity_score']:.0f}",
        ])
    t = Table(data, colWidths=[2.0 * inch, 1.6 * inch, 0.9 * inch, 1.1 * inch, 0.7 * inch])
    t.setStyle(_table_style(highlight_col=4))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Field Leaderboard", st["h2"]))
    data = [["Rep", "Calls", "Converted", "Rate"]]
    for r in top_reps:
        data.append([r["rep_name"], str(r["total_calls"]), str(r["converted_calls"]),
                     f"{r['conversion_rate']:.1f}%"])
    t = Table(data, colWidths=[2.8 * inch, 1.0 * inch, 1.4 * inch, 1.0 * inch])
    t.setStyle(_table_style(highlight_col=3))
    story.append(t)
    story.append(Spacer(1, 0.25 * inch))

    # Footer band
    story.append(Spacer(1, 0.3 * inch))
    footer = Table([[Paragraph(
        "<font color='#5C746F' size='8'>Source-only synthetic data · Compliance: source-grounded, no off-label claims, AI outputs auditable in /api/audit · Kiwi · Commercial Intelligence</font>",
        st["muted"]
    )]], colWidths=[7.3 * inch])
    footer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), KIWI_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(footer)

    doc.build(story)
    buf.seek(0)
    filename = f"kiwi-exec-brief-{now.strftime('%Y%m%d-%H%M')}.pdf"
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _table_style(highlight_col: int = -1) -> TableStyle:
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), KIWI_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, KIWI_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, KIWI_PRIMARY),
    ])
    if highlight_col >= 0:
        style.add("TEXTCOLOR", (highlight_col, 1), (highlight_col, -1), KIWI_PRIMARY)
        style.add("FONTNAME", (highlight_col, 1), (highlight_col, -1), "Helvetica-Bold")
    return style
