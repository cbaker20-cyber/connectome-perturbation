"""Explicit compute/design amendment; preserve the original 350-trial specification."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def main():
    old=ROOT/'docs/pcdr/CCR_SENSITIVITY_DESIGN.json'
    design=read(old)
    design['amends_sha256']=digest(old);design['recorded_utc']=utc()
    design['reason']='User requested a workload and allocation that make useful use of CCR beyond their local PC. No outcomes from the earlier 350-trial plan have been inspected.'
    design['network_variants']=[{'name':'default' if w==i==1 else f'w{int(w*100):03}_i{int(i*100):03}',
                               'weight_scale':w,'inhibitory_scale':i,'strong_fraction':None}
                              for w in [.8,1.,1.2] for i in [.8,1.,1.2]]
    design['seeds']=list(range(631401,631431))
    mode=next(c['ids'] for c in design['conditions'] if c['name']=='mode')
    design['conditions'] += [{'name':f'mode_cell_{j:02}','ids':[rid],'default_only':True}
                             for j,rid in enumerate(sorted(mode)) if rid!='720575940660219265']
    design['trials']=3390
    design['variants']='Full 3 x 3 grid of overall weight scale and inhibitory multiplier, each 0.8, 1.0, 1.2. The inhibitory multiplier is relative to the overall scale: negative weights receive their product. Add 50 non-MN9 single-cell lesions only in the default network; MN9-only is already included.'
    design['question']='How does the mode footprint depend jointly on weight and inhibition parameters, and which individual mode neurons produce the strongest descriptive effects?'
    design['cautions'] += ' Expanded design uses 30 paired seeds. Individual lesions describe contributions under this model, not additive parts of the combined lesion. Rank effects descriptively without p-values or post-hoc support selection; report all 51 cells.'
    write(ROOT/'docs/pcdr/CCR_EXPANDED_DESIGN.json',design)
    nb=read(ROOT/'notebooks/CCR_Preliminary_Followup.ipynb')
    for cell in nb['cells']:
        text=''.join(cell['source'])
        replacements={
            '4 cores, 16000 MB RAM, 4 hours':'32 cores, 128000 MB RAM, 8 hours',
            'at most two simulation processes':'up to 24 single-threaded simulation processes, selected by a measured concurrency ramp',
            '350 descriptive trials covering five weight settings and seven conditions, using ten shared seeds':'3,390 descriptive trials: nine joint weight settings and seven conditions with 30 shared seeds, plus 50 additional individual mode-cell lesions in the default network',
            'Weight settings are default, all weights ×0.8/×1.2, and inhibitory weights ×0.8/×1.2.':'Weight settings form a full 3 × 3 grid: overall scale and inhibitory multiplier each take 0.8, 1.0 and 1.2. Fifty additional default-network single-cell conditions complete the individual lesion map of all 51 mode cells (MN9 is already present).',
            'at most two trials at once, for at most three hours':'up to 24 trials at once after a throughput/memory calibration, for at most seven hours after calibration',
            'all 350 jobs':'all 3,390 jobs',
            '== 350':'== 3390',
            'results/sensitivity':'results/expanded_sensitivity',
            '"--workers", "2", "--hours", "3"':'"--workers", str(capacity["selected_workers"]), "--hours", "7"',
        }
        for a,b in replacements.items():text=text.replace(a,b)
        anchor='    log = (STUDY / "controller.log").open("a")'
        if anchor in text:
            text=text.replace(anchor,
                '    if not (STUDY / "capacity.json").exists() or json.loads((STUDY / "capacity.json").read_text())["slurm_job_id"] != os.environ.get("SLURM_JOB_ID"):\n'
                '        command("pcdr_ccr_capacity.py", "--study", STUDY, "--smoke", SMOKE)\n'
                '    capacity = json.loads((STUDY / "capacity.json").read_text())\n'
                '    print("Measured worker count:", capacity["selected_workers"])\n'+anchor)
        cell['source']=text.splitlines(True)
        if cell['cell_type']=='code':compile(text,'<expanded notebook>','exec')
    nb['cells'].insert(1,{'cell_type':'markdown','metadata':{},'source':[
        'This explicitly amends the earlier 350-trial package. The original design is retained in the repository. '
        'Calibration runs real planned trials at 1, 4, 8, 16 and up to 24 workers, within measured memory and allocated CPU limits. '
        'It keeps those results and chooses concurrency using throughput only. The 8-hour allocation includes setup; end the session early when finished. '
        'The larger design still does not solve the control-matching problem or turn these comparisons into a confirmatory test.\n']})
    write(ROOT/'notebooks/CCR_Expanded_Study.ipynb',nb)


if __name__=='__main__':main()
