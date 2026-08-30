@echo off
REM Run_Nulls.bat - runs degree + distance matched nulls sequentially
REM Survives Antigravity restarts because it's registered with Windows Task Scheduler.
REM Logs to results\null_run.log

cd /d "c:\Users\Baker\Drosophila_Data"
echo ===== NULL RUN STARTED %DATE% %TIME% ===== >> results\null_run.log

echo [degree] starting %DATE% %TIME% >> results\null_run.log
.venv\Scripts\python.exe scripts/run_degree_matched_nulls.py ^
    --config configs/jo_ground_truth_n20.yaml ^
    --n-perms 30 ^
    --groups AN descending LO Kenyon_Cell motor >> results\null_run.log 2>&1
echo [degree] done exit=%ERRORLEVEL% %DATE% %TIME% >> results\null_run.log

echo [distance] starting %DATE% %TIME% >> results\null_run.log
.venv\Scripts\python.exe scripts/run_distance_matched_nulls.py ^
    --config configs/jo_ground_truth_n20.yaml ^
    --n-perms 30 ^
    --groups AN descending LO Kenyon_Cell motor >> results\null_run.log 2>&1
echo [distance] done exit=%ERRORLEVEL% %DATE% %TIME% >> results\null_run.log

echo [verify] starting %DATE% %TIME% >> results\null_run.log
.venv\Scripts\python.exe scripts/verify_and_combine_nulls.py ^
    --results-dir results/jo_ground_truth_n20 >> results\null_run.log 2>&1
echo [verify] done exit=%ERRORLEVEL% %DATE% %TIME% >> results\null_run.log

echo ===== NULL RUN COMPLETE %DATE% %TIME% ===== >> results\null_run.log
