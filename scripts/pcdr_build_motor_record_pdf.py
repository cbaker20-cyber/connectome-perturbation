"""Append verified motor-matching work to a new edition of the research PDF."""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Preformatted

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'exports/pcdr_research_record_20260922_motor_composition'
OLD = ROOT/'exports/pcdr_research_record_20260922_fullpool/Connectome_Research_Record_2026-09-22_Fullpool.pdf'
SOURCES = [ROOT/'docs/pcdr/FULLPOOL_FEASIBILITY_20260922.md', ROOT/'docs/pcdr/MOTOR_SET_AUDIT_20260922.md',
           ROOT/'docs/pcdr/MOTOR_COMPOSITION_RESULTS_20260922.md']

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ResearchBody', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name='ResearchCell', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_LEFT))


def clean(text):
    return text.replace('\u2014', '-').replace('\u2013', '-').replace('\u2011', '-').replace('\u2264', '<=').replace('\u0394', 'Delta')


def inline(text):
    text = html.escape(clean(text))
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#234f73">\1</link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)
    return text


def footer(canvas, doc):
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#555555'))
    canvas.drawString(42, 25, 'Connectome research record - 22 September 2026 supplement')
    canvas.drawRightString(570, 25, str(doc.page))


def markdown(path, heading):
    story = [Paragraph(heading, styles['Heading1'])]
    lines = path.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith('# '):
            i += 1
            continue
        if line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                # Long reproducibility commands wrap rather than crossing margins.
                import textwrap
                code.extend(textwrap.wrap(lines[i], 84, break_long_words=True, break_on_hyphens=False) or [''])
                i += 1
            story.append(Preformatted('\n'.join(code), ParagraphStyle('Code', fontName='Courier', fontSize=8, leading=11, spaceAfter=8)))
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                if not re.fullmatch(r'[|:\-\s]+', lines[i]):
                    rows.append([Paragraph(inline(c.strip()), styles['ResearchCell']) for c in lines[i].strip('|').split('|')])
                i += 1
            table = Table(rows, colWidths=[528/len(rows[0])]*len(rows[0]), repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5edf3')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#c6d0d8')),
                ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
            story.extend([table, Spacer(1, 9)])
            continue
        elif line.startswith('## '):
            story.append(Paragraph(inline(line[3:]), styles['Heading2']))
        else:
            text = line[2:] if line.startswith('- ') else line
            if line.startswith('- '):
                text = '- '+text
            story.append(Paragraph(inline(text), styles['ResearchBody']))
        i += 1
    return story


def build(path, story):
    SimpleDocTemplate(str(path), pagesize=(612, 792), leftMargin=42, rightMargin=42,
                      topMargin=42, bottomMargin=44, title='Connectome Research Record: Motor Composition',
                      author='Research support prepared with Codex assistance').build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    assert OLD.is_file() and all(p.is_file() for p in SOURCES)
    OUT.mkdir(exist_ok=True)
    evidence = ROOT/'docs/pcdr/evidence/2026-09-22/motor_composition_pilot_20260922'
    audit = json.loads((evidence/'completion_audit.json').read_text())
    assert audit['trials_verified'] == 55 and audit['scheduled_input_pairs_verified'] == 50
    cover = [Paragraph('Connectome research record', styles['Title']),
             Paragraph('22 September 2026 - motor-matched comparison update', styles['Heading2']),
             Paragraph('This edition adds the full-pool matching result, the baseline distribution audit and the completed 55-trial motor-composition pilot. It preserves the earlier 66-page record as dated history.', styles['ResearchBody']),
             Paragraph('Read the appended Chapters 15-17 for the latest findings. The earlier cover and contents are retained with their original dates; they do not describe the current end of the record.', styles['ResearchBody']),
             Paragraph('The new comparison sets satisfy the original mean-balance and motor-count rules, but remain optimized, strongly overlapping and different in feature distributions. The pilot is descriptive. It does not establish a calibrated random-reference result or behavior in an animal.', styles['ResearchBody']),
             Paragraph('Research notes, code explanations and a lab notebook are also maintained in docs/pcdr. Compact machine-readable evidence is in docs/pcdr/evidence/2026-09-22. Full trial archives remain local and are identified by hashes.', styles['ResearchBody']),
             Paragraph('Prepared with Codex assistance. This is supporting research documentation, not a student-authored STS submission. Git commits use the repository owner\'s configured identity; assistance remains recorded in the research notes.', styles['ResearchBody']),
             Spacer(1, 12), Paragraph('Included in this edition', styles['Heading2']),
             Paragraph('Previous record: original protocols, papers, code explanations, dated notebook, single-cell study, optimized-comparison pilot, separate seed replication and early matching audits.', styles['ResearchBody']),
             Paragraph('Chapter 15: nine valid binary motor-matched sets.<br/>Chapter 16: distribution and cell-composition differences before lesions.<br/>Chapter 17: all motor-composition pilot results, paired-seed contrasts and limitations.', styles['ResearchBody'])]
    build(OUT/'cover.pdf', cover)
    supplement = []
    for i, (path, title) in enumerate(zip(SOURCES, ['15 Motor-balanced sets found', '16 Baseline distribution audit', '17 Motor-composition pilot results'])):
        if i:
            supplement.append(PageBreak())
        supplement.extend(markdown(path, title))
    supplement.append(PageBreak())
    supplement.append(Paragraph('Figure: outcomes and remaining baseline spread', styles['Heading1']))
    figure = ROOT/'docs/pcdr/figures/motor_composition_20260922.png'
    supplement.append(Image(str(figure), width=528, height=528*7.5/12))
    supplement.append(Paragraph('A and F are shown for every fixed set with per-set conditional paired-seed intervals. The right panel shows log1p incoming-degree quartiles and min/max values before lesions. Broad comparison distributions remain despite passing the original pooled mean-balance criterion. Detailed numerical values and paired contrasts appear in Chapter 17 and the committed evidence tables.', styles['ResearchBody']))
    build(OUT/'supplement.pdf', supplement)
    writer = PdfWriter()
    for source in [OUT/'cover.pdf', OLD, OUT/'supplement.pdf']:
        writer.append(str(source))
    final = OUT/'Connectome_Research_Record_2026-09-22_Motor_Composition.pdf'
    with final.open('wb') as stream:
        writer.write(stream)
    old_reader, reader = PdfReader(OLD), PdfReader(final)
    assert all(old_reader.pages[i].extract_text() == reader.pages[i+1].extract_text() for i in range(len(old_reader.pages)))
    paths = [OLD, *SOURCES, Path(__file__), figure, evidence/'completion_audit.json', ROOT/'docs/pcdr/LAB_NOTEBOOK.md', ROOT/'docs/pcdr/CODE_GUIDE.md']
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    record = {'created_utc': datetime.now(timezone.utc).isoformat(), 'pages': len(reader.pages),
              'old_pages': len(old_reader.pages), 'old_page_text_unchanged': True,
              'new_physical_pages': [1]+list(range(len(old_reader.pages)+2, len(reader.pages)+1)),
              'source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in paths},
              'pdf_sha256': digest(final), 'visual_review': 'pending'}
    (OUT/'export_manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps({'path': str(final), 'pages': len(reader.pages), 'new_pages': record['new_physical_pages']}))


if __name__ == '__main__':
    main()
