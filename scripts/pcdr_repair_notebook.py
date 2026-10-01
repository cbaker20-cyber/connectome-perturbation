"""Repair the released notebook hash check without replacing research data."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import shutil

EXPECTED_ZIP = 'febd84bee15037b4e0dffeb644956c42d2e314f25e234bb2dbe22ff7c8f77667'

NEW_VERIFY = "def notebook_content(document):\n    return [[cell['cell_type'], ''.join(cell['source'])] for cell in document['cells']]\n\n\ndef verify_package():\n    manifest = read(ROOT / 'package_manifest.json')\n    for name, expected in manifest.items():\n        if name == 'CCR_Fine_Steps.ipynb':\n            continue\n        if digest(ROOT / name) != expected:\n            raise ValueError('Changed package file: ' + name)\n    if 'notebook_content.json' not in manifest:\n        raise ValueError('Missing frozen notebook source record')\n    if notebook_content(read(ROOT / 'CCR_Fine_Steps.ipynb')) != read(ROOT / 'notebook_content.json'):\n        raise ValueError('Notebook cell source changed; saved outputs and metadata are allowed')\n"


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def repair(root, upload):
    if sha(upload)!=EXPECTED_ZIP:raise ValueError('Upload ZIP differs from the released version; do not change its manifest manually.')
    import fcntl
    with (root/'.run_all.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with zipfile.ZipFile(upload) as archive:
            manifest=json.loads(archive.read('connectome_fine/package_manifest.json'))
            document=json.loads(archive.read('connectome_fine/CCR_Fine_Steps.ipynb'))
            source=archive.read('connectome_fine/scripts/pcdr_fine_ccr.py').decode('utf-8').replace('\r\n','\n')
        content=lambda doc:[[c['cell_type'], ''.join(c['source'])] for c in doc['cells']]
        actual=json.loads((root/'CCR_Fine_Steps.ipynb').read_text(encoding='utf-8'))
        if content(actual)!=content(document):raise ValueError('Notebook source differs; repair allows output/metadata changes only.')
        current=json.loads((root/'package_manifest.json').read_text(encoding='utf-8'))
        if current!=manifest:raise ValueError('Manifest already changed or repair already applied; inspect before retrying.')
        for name,expected in manifest.items():
            if name!='CCR_Fine_Steps.ipynb' and sha(root/name)!=expected:raise ValueError('Changed file: '+name)
        backup=root/'fine_results/repair_20261001'
        backup.mkdir(parents=True,exist_ok=False)
        for name in ['scripts/pcdr_fine_ccr.py','package_manifest.json','CCR_Fine_Steps.ipynb']:
            shutil.copy2(root/name,backup/Path(name).name)
        start=source.index('def verify_package():');end=source.index('\n\ndef checked',start)
        patched=source[:start]+NEW_VERIFY+source[end:]
        (root/'scripts/pcdr_fine_ccr.py').write_text(patched,encoding='utf-8')
        (root/'notebook_content.json').write_text(json.dumps(content(document),indent=2)+'\n',encoding='utf-8')
        for name in ['scripts/pcdr_fine_ccr.py','notebook_content.json']:manifest[name]=sha(root/name)
        temporary=root/'package_manifest.json.tmp'
        temporary.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        temporary.replace(root/'package_manifest.json')
        print('Repaired. Original files retained in fine_results/repair_20261001. Now use Run All in the allocated Jupyter session.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/user/cbaker4/connectome_fine'))
    p.add_argument('--zip',type=Path,default=Path('/user/cbaker4/CCR_Fine_Steps.zip'))
    args=p.parse_args();repair(args.root,args.zip)
