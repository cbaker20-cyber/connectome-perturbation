"""Render the audit edition and compare prior page bodies pixel by pixel."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
out=root/'exports/pcdr_research_record_20260922_design_audit';qa=out/'qa';qa.mkdir(exist_ok=True)
pdf=out/'Connectome_Research_Record_2026-09-22_Design_Audit.pdf'
poppler='C:/Users/Baker/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
subprocess.run([poppler,'-r','115','-png',str(pdf),str(qa/'page')],check=True)
def body(p):
    im=Image.open(p).convert('RGB');return hashlib.sha256(im.crop((0,0,im.width,1170)).tobytes()).hexdigest()
old={body(p):int(p.stem.split('-')[-1]) for p in (root/'exports/pcdr_research_record_20260922_replication/qa').glob('page-*.png')}
same={};changed=[];reader=PdfReader(pdf)
for n in range(1,len(reader.pages)+1):
    p=qa/f'page-{n:02}.png';h=body(p)
    if h in old:same[n]=old[h]
    else:changed.append(n)
for i in range(0,len(changed),2):
    ims=[Image.open(qa/f'page-{n:02}.png').convert('RGB') for n in changed[i:i+2]]
    image=Image.new('RGB',(sum(im.width for im in ims),max(im.height for im in ims)),'white');x=0
    for im in ims:image.paste(im,(x,0));x+=im.width
    image.save(qa/f'review-{i//2:02}.png')
(qa/'extracted.txt').write_text('\n'.join(p.extract_text() for p in reader.pages),encoding='utf-8')
result={'pages':len(reader.pages),'unchanged_bodies':same,'changed_pages':changed,'render_dpi':115}
(qa/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
