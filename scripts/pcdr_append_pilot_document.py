"""Append the dated matching audit, preserving the previous complete edition."""
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

root=Path(__file__).resolve().parents[1]
old=root/'exports/pcdr_research_record_20260921_matching_audit/Connectome_Research_Record_2026-09-21_Matching_Audit.docx'
out=root/'exports/pcdr_research_record_20260921_pilot_results';out.mkdir(exist_ok=True)
source=root/'docs/pcdr/OPTIMIZED_PILOT_RESULTS_20260921.md'
doc=Document(old)
doc.paragraphs[4].text=('The 720-trial single-cell study and 35-trial optimized-comparison pilot are complete. '
    'In the pilot, the eigen-set had a larger within-set response and greater concentration than all five comparisons. '
    'About 77 percent of its absolute response still lay outside the support. This is an exploratory result from one selected mode and optimized sets, '
    'not confirmation. Chapter 11 reports every condition and seed, verification and limitations; earlier chapters preserve the research history.')
for paragraph in doc.paragraphs:
    if paragraph.text.startswith('Earlier chapters preserve'):
        paragraph.text='Chapter 11 records the completed pilot verified on 21 September. Chapters 1–10 preserve earlier dated decisions and findings. Source and export manifests identify this edition.'
    if paragraph.text.startswith('Read Chapter 10'):
        paragraph.text='Read Chapter 11 for the completed pilot results and limitations. Earlier chapters retain the study plan, papers, eigencircuit guide, code explanations, notebook and matching audit.'
h=doc.add_heading('11 Completed optimized comparison pilot',level=1);h.paragraph_format.page_break_before=True
lines=source.read_text(encoding='utf-8').splitlines();i=0
while i<len(lines):
    line=lines[i]
    if not line or line.startswith('# '):i+=1;continue
    if line.startswith('## '):doc.add_heading(line[3:],level=2)
    elif line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            if '---' not in lines[i]:rows.append([c.strip() for c in lines[i].strip('|').split('|')])
            i+=1
        table=doc.add_table(rows=1,cols=len(rows[0]));table.style='Table Grid'
        header_repeat=OxmlElement('w:tblHeader')
        table.rows[0]._tr.get_or_add_trPr().append(header_repeat)
        borders=OxmlElement('w:tblBorders')
        for edge in ['top','left','bottom','right','insideH','insideV']:
            el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
        table._tbl.tblPr.append(borders)
        for j,value in enumerate(rows[0]):table.rows[0].cells[j].text=value
        for row in rows[1:]:
            for j,value in enumerate(row):table.add_row() if j==0 else None;table.rows[-1].cells[j].text=value
        for cell in table.rows[0].cells:
            shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'E4EDF2');cell._tc.get_or_add_tcPr().append(shd)
            for r in cell.paragraphs[0].runs:r.bold=True
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(4)
                    for run in p.runs:run.font.size=Pt(10)
        continue
    else:doc.add_paragraph(line[2:] if line.startswith('- ') else line,style='List Bullet' if line.startswith('- ') else None)
    i+=1
doc.save(out/'Connectome_Research_Record_2026-09-21_Pilot_Results.docx')
paths=[old,source,Path(__file__),root/'results/pcdr/optimized_pilot_20260921/amendment.json',root/'results/pcdr/optimized_pilot_20260921/analysis/results.json',root/'results/pcdr/optimized_pilot_20260921/completion_audit.json']
(out/'source_manifest.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),
    'sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    'note':'Cover status updated; original chapters preserved; dated Chapter 11 appended.'},indent=2),encoding='utf-8')
print(out)
