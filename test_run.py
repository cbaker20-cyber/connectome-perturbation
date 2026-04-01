import sys
sys.path.insert(0, 'Drosophila_brain_model')

from pathlib import Path
from model import run_exp, default_params
from brian2 import ms

params = default_params.copy()
params['n_run'] = 1
params['t_run'] = 500 * ms

path_comp = 'Drosophila_brain_model/2023_03_23_completeness_630_final.csv'
path_con  = 'Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet'
path_res  = 'results'

Path(path_res).mkdir(exist_ok=True)

neu_sugar = [
    720575940624963786, 720575940630233916, 720575940637568838,
    720575940638202345, 720575940617000768, 720575940630797113,
    720575940632889389, 720575940621754367, 720575940621502051,
    720575940640649691,
]

run_exp(
    exp_name='test_sugar',
    neu_exc=neu_sugar,
    path_res=path_res,
    path_comp=path_comp,
    path_con=path_con,
    params=params,
    n_proc=1,
    force_overwrite=True
)

print('SUCCESS - check results/test_sugar.parquet')
