@echo off
rem Runs the simulated PLC on a Windows laptop so other machines on the network can reach it.
rem First run creates a virtual environment and installs dependencies.
rem Extra arguments are passed through, e.g.  run-sim.bat --mode local

cd /d "%~dp0.."
if not exist gateway\.venv\Scripts\python.exe (
    echo Creating virtual environment...
    py -m venv gateway\.venv || goto :error
)
gateway\.venv\Scripts\python.exe -m pip install --quiet -r gateway\requirements.txt || goto :error
echo Simulated PLC listening on port 5020. Press Ctrl+C to stop.
gateway\.venv\Scripts\python.exe tools\sim_plc.py --host 0.0.0.0 --port 5020 --heartbeat-timeout 6 %*
goto :eof

:error
echo Setup failed. Check that Python 3.10 or newer is installed and the "py" launcher works.
exit /b 1
