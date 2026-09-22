"""Render PDF pages and identify unchanged page bodies against the prior edition."""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
out=root/'exports/pcdr_research_record_20260921_completed'
qa=out/'qa_release';qa.mkdir(exist_ok=True)
poppler=Path('C:/Users/Baker/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
pdf=out/'Connectome_Research_Record_2026-09-21_Completed.pdf'
subprocess.run([str(poppler),'-r','115','-png',str(pdf),str(qa/'page')],check=True)
def body_hash(p):
    im=Image.open(p).convert('RGB')
    return hashlib.sha256(im.crop((0,0,im.width,1170)).tobytes()).hexdigest()
old={body_hash(p):int(p.stem.split('-')[-1]) for p in (root/'exports/pcdr_research_record_20260921/qa').glob('page-??.png')}
files=sorted(qa.glob('page-*.png'))
same={};changed=[]
for i,p in enumerate(files,1):
    h=body_hash(p)
    if h in old:same[i]=old[h]
    else:changed.append(i)
for i in range(0,len(files),2):
    ims=[Image.open(p).convert('RGB') for p in files[i:i+2]]
    pair=Image.new('RGB',(sum(im.width for im in ims),max(im.height for im in ims)),'white')
    x=0
    for im in ims:pair.paste(im,(x,0));x+=im.width
    pair.save(qa/f'review-{i//2+1:02}.png')
reader=PdfReader(pdf)
(qa/'extracted.txt').write_text('\n\n'.join(f'PAGE {i+1}\n'+p.extract_text() for i,p in enumerate(reader.pages)),encoding='utf-8')
record={'pages':len(reader.pages),'unchanged_page_bodies':same,'changed_pages':changed,'excluded_area':'Bottom footer with page number only; full pages retained for visual review'}
(qa/'comparison.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
