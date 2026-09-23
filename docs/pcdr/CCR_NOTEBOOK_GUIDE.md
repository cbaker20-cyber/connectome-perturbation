# Start here

Upload `Connectome_CCR_Notebook.zip` to CCR OnDemand, extract it, and open `connectome/CCR_Preliminary_Followup.ipynb`. The archive includes the data; it does not depend on paths on the local PC. It is about 95 MB compressed because the connectivity and annotation inputs are included. No old trial outputs or virtual environment are included.

Suggested first allocation from the supplied form:

| Field | Value |
|---|---|
| App | JupyterLab |
| Cluster | UB-HPC |
| Account | smuldoon |
| Partition | general-compute |
| Hours | 4 |
| Cores | 4 |
| Memory per node | 16000 MB |
| GPUs | None |
| QoS | Use the valid choice for this allocation; ignore the form's stale `normal` display as its help text instructs |
| Extra modules | Blank unless needed for an available Python 3.11 executable |
| Node features | Keep the Jupyter app's supported AVX512 architecture; do not guess an additional feature label |

The request reserves room for two single-threaded simulations plus Jupyter. A local worker peaked at about 2.84 GB, so the default 2.8 GB allocation is insufficient. Four hours includes environment setup, smoke checks and a three-hour follow-up budget. These are initial requests, not measured CCR requirements. No GPU code is used.

The notebook uses a separate Python 3.11 virtual environment. Exact versions, including dependencies, are in `requirements-ccr.txt`. Required libraries are NumPy, SciPy, pandas, PyArrow, Brian2, Cython, matplotlib and joblib; pytest and statsmodels are retained to match the recorded environment. Dependencies include SymPy, Jinja2, packaging, plotting/font libraries and date/time libraries; the notebook saves the complete installed list with `pip freeze`. Psutil was not installed locally and is not required. The notebook kernel itself needs only its normal IPython environment and the standard library. Linux wheel installation remains to be checked on CCR.

Run the notebook in order. Four technical trials precede the prepared 350-trial descriptive study. The study covers five weight settings, seven conditions, and ten shared seeds. It includes mode-minus-MN9 and MN9-only diagnostics and three representatives of the existing comparator response groups. These imperfect controls do not support a random-reference p-value. Read `sensitivity_design.json` for the frozen research choices and limitations.

The notebook runs inside your existing OnDemand allocation; it does not submit other Slurm jobs. It records failures and can resume completed trials after checking their hashes. If the session is forcibly killed, confirm all old processes have ended before removing stale locks. Do not edit immutable source/data files; the notebook and optional shell config are editable and their original hashes are recorded separately.

Transfer verification uses `transfer_manifest.json`; the separately provided `archive.json` records the ZIP hash. `initialize` creates a technical Git snapshot for provenance, not a replacement for the GitHub project's history.

Sources checked 22 September 2026: [CCR OnDemand](https://docs.ccr.buffalo.edu/en/latest/portals/ood/), [jobs and resource requests](https://docs.ccr.buffalo.edu/en/latest/hpc/jobs/), [architecture-aware modules](https://docs.ccr.buffalo.edu/en/latest/software/modules/). The account and form details above came from the user. Code, documentation and notebook preparation used Codex assistance.
