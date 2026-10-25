@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
    if not errorlevel 1 goto localpython
)
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if not errorlevel 1 goto pylauncher
python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if not errorlevel 1 goto systempython
echo Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo Include Tcl/Tk and the Python launcher, then run Launch.bat again.
goto failed

:localpython
".venv\Scripts\python.exe" bootstrap.py %*
goto finished
:pylauncher
py -3 bootstrap.py %*
goto finished
:systempython
python bootstrap.py %*
:finished
if errorlevel 1 goto failed
exit /b 0
:failed
echo Launcher setup or startup failed. See the error above.
if /i not "%~1"=="--setup-only" pause
exit /b 1
