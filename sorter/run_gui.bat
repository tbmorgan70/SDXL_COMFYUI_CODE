@echo off
setlocal EnableExtensions
chcp 65001 >nul

rem Always run from this script's own folder, however it was launched
cd /d "%~dp0"

title Sorter - ComfyUI Image Organizer

rem ---------------------------------------------------------------
rem Pick an interpreter that actually has the GUI's dependencies.
rem Several Pythons are usually installed and only one has them:
rem "py -3" follows the launcher's DEFAULT, which is often the newest
rem version and the wrong one. So probe by capability, not by name.
rem ---------------------------------------------------------------
set "PYCMD="
set "PYANY="

call :probe "python"
if not defined PYCMD call :probe "py -3.11"
if not defined PYCMD call :probe "py -3.12"
if not defined PYCMD call :probe ""%LOCALAPPDATA%\Programs\Python\Python311\python.exe""
if not defined PYCMD call :probe "py -3"

if defined PYCMD goto :launch
if defined PYANY goto :missing_deps
goto :no_python


:launch
echo Starting Sorter GUI...
%PYCMD% gui.py
if errorlevel 1 goto :crashed
rem Clean exit - close the window without making the user press a key
exit /b 0


rem --- probe: does %~1 run, and does it have the GUI packages? -----
:probe
%~1 -c "import sys" >nul 2>&1
if errorlevel 1 goto :eof
if not defined PYANY set "PYANY=%~1"
%~1 -c "import customtkinter, PIL" >nul 2>&1
if errorlevel 1 goto :eof
set "PYCMD=%~1"
goto :eof


:no_python
echo.
echo  [X] No working Python installation was found.
echo.
echo      Install Python 3.11 or newer from https://www.python.org/downloads/
echo      and tick "Add Python to PATH" during setup.
echo.
pause
exit /b 1


:missing_deps
echo.
echo  [!] Found Python, but the GUI packages are missing
echo      (customtkinter / Pillow).
echo.
set /p INSTALL="     Install them now from requirements.txt? [Y/n] "
if /i "%INSTALL%"=="n" exit /b 1
echo.
%PYANY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [X] Install failed. Try:  %PYANY% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
set "PYCMD=%PYANY%"
echo.
goto :launch


:crashed
echo.
echo  [X] The GUI exited with an error - details above.
echo.
pause
exit /b 1
