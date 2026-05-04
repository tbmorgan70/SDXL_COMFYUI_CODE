@echo off
REM Image Extractor Launcher - Python 3.11 Specific
REM Use this if run_gui.bat doesn't work

echo.
echo ====================================
echo   Image Extractor - GUI Mode
echo ====================================
echo.

REM Use specific Python 3.11 installation
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" extract_images_interactive.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo ERROR: Python 3.11 not found at expected location
    echo ============================================
    echo.
    echo Expected location:
    echo   C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    echo.
    echo Please either:
    echo 1. Install Python 3.11 from https://www.python.org/downloads/
    echo 2. Edit this batch file to use your Python installation path
    echo.
    pause
)
