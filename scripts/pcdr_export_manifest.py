"""Record hashes and page comparisons for the completed research record."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from PIL import Image
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
out = root / 'exports/pcdr_research_record_20260921_completed'
stem = 'Connectome_Research_Record_2026-09-21_Completed'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
reader = PdfReader(out / (stem + '.pdf'))
changed = []
for n in range(1, len(reader.pages) + 1):
    name = f'page-{n:02}.png'
    current = Image.open(out / 'qa_release' / name).convert('RGB')
    previous = Image.open(out / 'qa_verified' / name).convert('RGB')
    if current.size != previous.size or current.tobytes() != previous.tobytes():
        changed.append(n)
paths = [out / (stem + ext) for ext in ('.docx', '.pdf')]
paths += [out / 'source_snapshot.json', root / 'scripts/build_pcdr_research_document.py',
          root / 'scripts/pcdr_document_qa.py', Path(__file__),
          root / 'results/pcdr/exploratory80_20260921/completion_record.json']
record = {
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'pages': len(reader.pages),
    'sources_captured_utc': json.loads((out / 'source_snapshot.json').read_text(encoding='utf-8'))['captured_utc'],
    'sha256': {str(p.relative_to(root)): sha(p) for p in paths},
    'render': 'Hidden Microsoft Word COM; fields and TOC updated; ExportAsFixedFormat; Poppler 115 DPI',
    'renderer_fallback': 'Canonical renderer lacked LibreOffice, diagnosed in earlier edition renderer_log.txt; reused Word fallback.',
    'qa': {
        'changed_pages_from_reviewed_draft': changed,
        'unchanged_pages': 'Full PNG pixels identical to visually reviewed qa_verified draft',
        'prior_edition_comparison': 'qa_release/comparison.json',
        'editorial_repairs': 'Corrected UTF-8 encoding after visual review; removed empty chapter-break page; shortened final export note.',
        'visual_review': 'All page bodies reviewed across prior edition, qa_verified and changed final pages; no clipping, overlap or missing glyphs.'
    },
    'outcome': '720 single-cell trials complete; original first-20 selection failed; exploratory 80-pair search selected a mode but accepted 0/5 controls in 50000 proposals; no mode lesions.',
    'monitor': 'Paused after terminal handoff; no protocol relaxation or extra simulation launched.'
}
(out / 'export_manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'pages': len(reader.pages), 'changed_pages': changed}))
