@echo off
REM ---------------------------------------------------------------------
REM viz3d launcher (2026-09-13)
REM
REM viz3d.py needs pyvista/vtk, which are installed in the conda env `lbm`
REM -- NOT in the base env that a bare `python` resolves to on this machine
REM (base = C:\Users\yangc\anaconda3\python.exe, no pyvista).
REM
REM Usage from PowerShell / cmd, in this directory:
REM     viz3d.cmd explore --series results_pcs_cg3d/<tag>/frames
REM     viz3d.cmd figset  --run results_pcs_cg3d/p3b_finney
REM
REM It picks the current conda env only if that env actually imports
REM pyvista; otherwise it falls back to the known lbm env.
REM ---------------------------------------------------------------------
setlocal

set "PY=%CONDA_PREFIX%\python.exe"
if not exist "%PY%" goto fallback
"%PY%" -c "import pyvista" >nul 2>&1
if errorlevel 1 goto fallback
goto run

:fallback
set "PY=C:\Users\yangc\anaconda3\envs\lbm\python.exe"
if not exist "%PY%" (
  echo viz3d.cmd: no interpreter with pyvista found.
  echo   tried %%CONDA_PREFIX%%\python.exe and %PY%
  echo   install it with:  conda run -n lbm pip install pyvista
  exit /b 1
)

:run
"%PY%" "%~dp0viz3d.py" %*
exit /b %ERRORLEVEL%
