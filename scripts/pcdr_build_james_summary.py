"""Build a short, plain-text research update from its separately editable source."""
from pathlib import Path
import hashlib
import json
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,PageBreak
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/pcdr/JAMES_EIGENCIRCUIT_UPDATE_20260923.md'
OUT=ROOT/'output/pdf/Eigencircuit_Update_for_James_2026-09-23.pdf'


def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    font=Path('C:/Windows/Fonts/times.ttf')
    if font.exists():
        pdfmetrics.registerFont(TTFont('ResearchSerif',str(font)))
        family='ResearchSerif'
    else:family='Times-Roman'
    body=ParagraphStyle('Body',fontName=family,fontSize=10.7,leading=12.8,spaceAfter=6.5)
    heading=ParagraphStyle('Heading',parent=body,fontSize=12.0,leading=14.5,spaceBefore=5,spaceAfter=6)
    title=ParagraphStyle('Title',parent=body,fontSize=17,leading=20,spaceAfter=5)
    small=ParagraphStyle('Small',parent=body,fontSize=9.1,leading=11,spaceAfter=5)
    headings={'Procedure and checks','Results so far','Proposed CCR work','Python environment','References and record'}
    blocks=SOURCE.read_text(encoding='utf-8').strip().split('\n\n')
    story=[]
    for index,text in enumerate(blocks):
        if text=='---PAGE---':story.append(PageBreak());continue
        if index==0:
            name,date=text.split('\n')
            story.extend([Paragraph(escape(name),title),Paragraph(escape(date),small)])
            continue
        style=heading if text in headings else small if text.startswith('[') or text.startswith('Code and detailed') else body
        encoded=escape(text)
        for doi in ['10.1038/s41586-024-07982-0','10.1038/s41586-024-07763-9','10.1002/sim.3697']:
            encoded=encoded.replace('doi:'+doi,'<link href="https://doi.org/'+doi+'">doi:'+doi+'</link>')
        story.append(Paragraph(encoded,style))
    def footer(canvas,doc):
        canvas.setFont(family,9)
        canvas.drawString(48,28,'Eigencircuit update | 23 September 2026')
        canvas.drawRightString(letter[0]-48,28,str(doc.page))
    SimpleDocTemplate(str(OUT),pagesize=letter,leftMargin=48,rightMargin=48,
        topMargin=40,bottomMargin=43,title='Eigencircuit update for James',
        author='Copeland Baker; prepared with Codex assistance').build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(OUT)
    if len(reader.pages)!=2:raise ValueError(f'Expected two pages; found {len(reader.pages)}')
    text='\n'.join(page.extract_text() for page in reader.pages)
    for required in ['3,390','22.604','NetworkX','19.1','not run']:
        if required not in text:raise ValueError('Missing text: '+required)
    record={'pdf':OUT.name,'pages':len(reader.pages),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'pdf_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'visual_review':'pending'}
    (OUT.parent/'James_summary_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))


if __name__=='__main__':main()
