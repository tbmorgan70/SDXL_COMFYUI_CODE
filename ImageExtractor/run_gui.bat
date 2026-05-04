@echo off
REM Image Extractor Launcher
REM Double-click this file to run the GUI

echo.
echo ====================================
echo   Image Extractor - GUI Mode
echo ====================================
echo.

REM Try to find a working Python installation
set PYTHON_EXE=

REM First, try the Python launcher (py.exe) - most reliable on Windows
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 extract_images_interactive.py
    goto :end
)

REM Try common Python installation paths
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" extract_images_interactive.py
    goto :end
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" extract_images_interactive.py
    goto :end
)

if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" extract_images_interactive.py
    goto :end
)

if exist "C:\Python311\python.exe" (
    "C:\Python311\python.exe" extract_images_interactive.py
    goto :end
)

if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" extract_images_interactive.py
    goto :end
)

if exist "C:\Python313\python.exe" (
    "C:\Python313\python.exe" extract_images_interactive.py
    goto :end
)

REM Last resort - try python from PATH (might be Inkscape's or another)
python extract_images_interactive.py

:end
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo ERROR: Could not find working Python
    echo ============================================
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo Or manually run with full path:
    echo   C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe extract_images_interactive.py
    echo.
    pause
)
