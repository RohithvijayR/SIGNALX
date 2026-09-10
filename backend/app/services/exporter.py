import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from typing import Dict, Any

def generate_pdf_report(report_data: Dict[str, Any]) -> bytes:
    """
    Generates a professional PDF signal intelligence analysis report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom Deep-Tech Theme Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'DocHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # Title Banner
    story.append(Paragraph("<b>SIGNALFUSION — RF Signal Intelligence Report</b>", title_style))
    story.append(Paragraph("National Technical Research Organisation (NTRO) | SIH 2026", body_style))
    story.append(Spacer(1, 12))

    # Signal Overview Table
    story.append(Paragraph("1. Signal Overview & Metadata", h2_style))
    meta = report_data.get("metadata", {})
    overview_data = [
        ["Filename", meta.get("filename", "N/A"), "Format", meta.get("format", "N/A")],
        ["Sample Count", str(meta.get("sample_count", "N/A")), "Duration", f"{meta.get('duration_seconds', 0.0):.4f} s"],
        ["Sampling Rate", f"{meta.get('sample_rate', 0.0)/1e6:.3f} MS/s", "SR Source", meta.get("sample_rate_source", "N/A")],
        ["Processing Mode", report_data.get("inference_mode", "N/A"), "Processing Time", f"{report_data.get('processing_time_ms', 0.0):.1f} ms"]
    ]
    t1 = Table(overview_data, colWidths=[120, 150, 120, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1E293B')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t1)
    story.append(Spacer(1, 14))

    # Parameter Extraction Summary Table
    story.append(Paragraph("2. Extracted Signal Parameters & Source Verification", h2_style))
    param_table_data = [["Parameter", "Inferred Result", "Source / Method", "Confidence", "Ground Truth (if available)"]]
    
    for row in report_data.get("parameter_table", []):
        param_table_data.append([
            row.get("parameter", ""),
            row.get("result", ""),
            row.get("source", ""),
            row.get("confidence", ""),
            row.get("ground_truth", "N/A")
        ])

    t2 = Table(param_table_data, colWidths=[110, 130, 140, 70, 90])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 14))

    # Multi-Modal ML Modulation Classification
    story.append(Paragraph("3. Multi-Modal ML Modulation Classification", h2_style))
    mod_info = report_data.get("modulation_prediction", {})
    story.append(Paragraph(f"<b>Predicted Modulation:</b> <font color='#2563EB'>{mod_info.get('prediction', 'N/A')}</font> ({mod_info.get('confidence', 0.0)}% confidence)", body_style))
    story.append(Spacer(1, 6))

    # Candidates table
    cand_data = [["Candidate Class", "Confidence Probability"]]
    for cand in mod_info.get("candidates", []):
        cand_data.append([cand.get("modulation", ""), f"{cand.get('confidence_pct', 0.0)}%"])

    t3 = Table(cand_data, colWidths=[200, 200])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 14))

    # Supporting Evidence Checklist
    story.append(Paragraph("4. Analyst Explainability & Supporting Evidence", h2_style))
    for ev in report_data.get("explainability_evidence", []):
        story.append(Paragraph(f"• <b>{ev.get('check', '')}:</b> {ev.get('detail', '')}", body_style))
        story.append(Spacer(1, 3))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
