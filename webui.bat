@echo off
title SadTalker Flask WebUI

IF NOT EXIST venv310 (
    python -m venv venv310
) ELSE (
    echo venv folder already exists, skipping creation...
)

call .\venv310\Scripts\activate.bat

set PYTHON=venv310\Scripts\python.exe
echo Using %PYTHON%

REM Start SadTalker Flask App in background
start "" /B %PYTHON% Launcher.py

REM Wait until port 7860 is LISTENING
:WAIT
netstat -an | find ":7860" | find "LISTENING" > nul
if errorlevel 1 (
    timeout /t 2 > nul
    goto WAIT
)

REM Open Chrome ONLY when server is fully ready
start chrome http://127.0.0.1:7860

pause
