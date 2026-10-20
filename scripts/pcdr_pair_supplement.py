"""Check saved reference prefixes, process exits and refractory intervals."""
import io
import argparse
import json
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
from pcdr_verify_downloaded_pairs import digest, require

ROOT=Path(__file__).resolve().parents[1]


def main(folder=None):
    folder=Path(folder) if folder is not None else ROOT/'results/pcdr/pairs_verified_20261019'
    prior=json.loads((folder/'verification.json').read_text())
    report=[]
    for record in prior['archives']:
        path=folder/record['archive']
        require(digest(path.read_bytes())==record['sha256'],'Archive changed')
        with zipfile.ZipFile(path) as z, zipfile.ZipFile(ROOT/'exports/CCR_Four_Trial.zip') as upload:
            processes=[n for n in z.namelist() if n.endswith('/process.json')]
            require(len(processes)==6,'Expected six worker records')
            for name in processes:
                process=json.loads(z.read(name))
                require(process['status']=='complete' and process['returncode']==0,'Worker did not complete')
            for condition in ('baseline','mode'):
                base='results/reference_'+condition+'/'
                measure=json.loads(z.read(base+'measurement.json'))
                require(measure['duration_s']==.01 and measure['dt_ms']==.0001,'Wrong reference interval')
                for name,h in measure['outputs'].items():
                    require(digest(z.read(base+name))==h,'Reference hash mismatch')
                anchor=ROOT/f'results/pcdr/fine_download_20261005/trials/fine_0p0001_default_{condition}_631401'
                expected=pd.read_parquet(anchor/'spikes.parquet')
                actual=pd.read_parquet(io.BytesIO(z.read(base+'spikes.parquet')))
                pd.testing.assert_frame_equal(actual,expected.loc[expected.t<.01,['t','flywire_id']].reset_index(drop=True),check_dtype=False,check_exact=True)
                delivered=pd.read_parquet(anchor/'delivered_events.parquet')
                actual=pd.read_parquet(io.BytesIO(z.read(base+'delivered.parquet')))
                pd.testing.assert_frame_equal(actual,delivered.loc[delivered.tick<100000].reset_index(drop=True),check_dtype=False,check_exact=True)
            for trial in record['trials']:
                base='results/trials/'+trial['id']+'/'
                m=json.loads(z.read(base+'manifest.json')); spec=m['spec']
                source=json.loads(upload.read('connectome_four_trial/original/trials/'+spec['source_trial']+'/manifest.json'))
                spikes=pd.read_parquet(io.BytesIO(z.read(base+'spikes.parquet'))).sort_values(['flywire_id','t'])
                gaps=spikes.groupby('flywire_id').t.diff().to_numpy()
                minimum=np.where(spikes.flywire_id.isin(source['input_ids']),spec['dt_ms']/1000,.0022)
                require(not np.any(gaps<minimum-1e-10),'Refractory violation')
            report.append(dict(archive=record['archive'],processes_passed=6,exact_reference_prefixes=2,refractory_trials=2))
    target=folder/'supplement_20261020.json'
    with target.open('x') as f:
        json.dump(dict(checks=report,scope='Saved output checks only; no simulation rerun.'),f,indent=2)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--folder',type=Path)
    main(parser.parse_args().folder)
