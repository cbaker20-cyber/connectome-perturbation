"""Draw a selected actual-event timeline; no mixed spike histories."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def run():
    out=ROOT/'results/pcdr/cb4058_timeline_20261010';out.mkdir(parents=True,exist_ok=False)
    cross_path=ROOT/'results/pcdr/count_crossings_20261010/results.json'
    posts_path=ROOT/'docs/pcdr/evidence/2026-10-09/baseline_count_replay/results.json'
    cross=read(cross_path)['records'];seed=min(r['seed'] for r in cross if r['selected'])
    r=next(r for r in cross if r['seed']==seed)
    p=next(p for p in read(posts_path)['records'] if p['seed']==seed)
    event_path=ROOT/f'results/pcdr/baseline_gating_20261010/{seed}_events.parquet'
    expected=read(ROOT/'results/pcdr/baseline_gating_20261010/verification.json')['outputs'][event_path.name]
    if digest(event_path)!=expected:raise ValueError('Changed events')
    gap=r['gap']['tick']*.0001
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(x):digest(x) for x in [Path(__file__),cross_path,posts_path,event_path]},
        selection='Smallest prior selected seed, fixed before plotting. Show gap-25ms through gap+5ms using actual archived events; not a representative-case claim.',seed=seed))
    events=pd.read_parquet(event_path)
    fig,axes=plt.subplots(2,1,figsize=(10,5.5),sharex=True)
    for ax,label,dt in zip(axes,['coarse','fine'],[.0002,.0001]):
        post=np.array(p[label+'_actual'])*.0001
        for t in post:
            if t+2.2>=gap-25 and t<=gap+5:ax.axvspan(t,t+2.2,color='#dadfe5',alpha=.8)
        visible=post[(post>=gap-25)&(post<=gap+5)]
        ax.scatter(visible,np.full(len(visible),.75),marker='|',s=260,c='#172f46',label='Target spike',zorder=3)
        f=events[(events.source_id=='720575940643867296')&events['weight_mv_'+label].notna()]
        f=f[(f.tick*.0001>=gap-25)&(f.tick*.0001<=gap+5)]
        for allow,color,marker,name in [(True,'#007f79','v','CB4058 arrival: accepted'),(False,'#c14c32','x','CB4058 arrival: blocked')]:
            picked=f[f['accept_'+label].eq(allow)]
            ax.scatter(picked.tick*.0001,np.full(len(picked),.25),marker=marker,c=color,s=65,label=name,zorder=4)
        ax.axvline(gap,color='#775191',ls='--',lw=1.3)
        ax.set(ylim=(0,1),yticks=[.25,.75],yticklabels=['Source arrival','Target spike'],xlim=(gap-25,gap+5))
        ax.set_title(f'{label.capitalize()} run, dt = {dt} ms',loc='left',fontsize=11)
        ax.spines[['top','right']].set_visible(False)
    axes[0].legend(loc='upper left',bbox_to_anchor=(0,1.48),ncol=3,frameon=False,fontsize=9)
    axes[1].set_xlabel('Simulated time (ms)')
    fig.suptitle(f'Actual arrivals and target resets — seed {seed}',x=.12,ha='left',fontsize=14,y=.99)
    fig.text(.12,.02,'Grey: target refractory intervals. Dashed: first two-spike count gap.\nSelected example only; different source timings and reset histories are not a controlled intervention.',fontsize=9)
    fig.subplots_adjust(left=.14,right=.98,top=.77,bottom=.17,hspace=.48)
    path=out/'timeline.png';fig.savefig(path,dpi=170);plt.close(fig)
    write(out/'complete.json',dict(status='complete',outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))


if __name__=='__main__':run()
