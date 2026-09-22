"""Render the new record and verify preserved historical pages pixel for pixel."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'exports/pcdr_research_record_20260922_motor_composition'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--poppler', required=True, help='Path to pdftoppm executable')
    args = parser.parse_args()
    pdf = OUT/'Connectome_Research_Record_2026-09-22_Motor_Composition.pdf'
    manifest = json.loads((OUT/'export_manifest.json').read_text())
    qa = OUT/'qa'
    qa.mkdir(exist_ok=True)
    subprocess.run([args.poppler, '-r', '115', '-png', str(pdf), str(qa/'page')], check=True)
    previous = ROOT/'exports/pcdr_research_record_20260922_fullpool/qa'
    digest = lambda p: hashlib.sha256(Image.open(p).convert('RGB').tobytes()).hexdigest()
    historical_equal = []
    for n in range(1, manifest['old_pages']+1):
        assert digest(previous/f'page-{n:02}.png') == digest(qa/f'page-{n+1:02}.png'), n
        historical_equal.append(n+1)
    pages = manifest['new_physical_pages']
    for i in range(0, len(pages), 2):
        images = [Image.open(qa/f'page-{n:02}.png').convert('RGB') for n in pages[i:i+2]]
        montage = Image.new('RGB', (sum(im.width for im in images), max(im.height for im in images)), 'white')
        x = 0
        for im in images:
            montage.paste(im, (x, 0))
            x += im.width
        montage.save(qa/f'review-{i//2:02}.png')
    reader = PdfReader(pdf)
    (qa/'extracted.txt').write_text('\n'.join(p.extract_text() for p in reader.pages), encoding='utf-8')
    result = {'pages': len(reader.pages), 'historical_pages_pixel_identical': historical_equal,
              'new_pages_for_visual_review': pages, 'dpi': 115,
              'qa_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (qa/'comparison.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
