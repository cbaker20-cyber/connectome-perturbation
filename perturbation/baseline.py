import sys
sys.path.insert(0, "Drosophila_brain_model")
from pathlib import Path
from model import run_exp, default_params
from brian2 import ms

PARAMS = default_params.copy()
PARAMS["n_run"] = 5
PARAMS["t_run"] = 1000 * ms

PATH_COMP = "Drosophila_brain_model/2023_03_23_completeness_630_final.csv"
PATH_CON  = "Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet"
PATH_RES  = "results"

NEU_SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838,
    720575940638202345, 720575940617000768, 720575940630797113,
    720575940632889389, 720575940621754367, 720575940621502051,
    720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543,
    720575940632425919, 720575940633143833, 720575940612670570,
    720575940628853239, 720575940629176663, 720575940611875570,
]

def run_baseline(force=False):
    Path(PATH_RES).mkdir(exist_ok=True)
    print("Running baseline simulation...")
    run_exp(
        exp_name="baseline_sugar",
        neu_exc=NEU_SUGAR,
        path_res=PATH_RES,
        path_comp=PATH_COMP,
        path_con=PATH_CON,
        params=PARAMS,
        n_proc=1,
        force_overwrite=force
    )
    print("Baseline done.")

if __name__ == "__main__":
    run_baseline(force="--force" in sys.argv)
