@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

rem Creates a "Sorter" shortcut on the Desktop pointing at run_gui.bat,
rem so the GUI is genuinely one click from anywhere.

set "TARGET=%~dp0run_gui.bat"
set "SHORTCUT=%USERPROFILE%\Desktop\Sorter.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
  "$s.TargetPath = '%TARGET%';" ^
  "$s.WorkingDirectory = '%~dp0';" ^
  "$s.Description = 'Sorter - Advanced ComfyUI Image Organizer';" ^
  "$s.IconLocation = 'imageres.dll,76';" ^
  "$s.Save()"

if errorlevel 1 (
    echo.
    echo  [X] Could not create the shortcut.
    echo.
    pause
    exit /b 1
)

echo.
echo  [OK] Created:  %SHORTCUT%
echo.
echo  Double-click "Sorter" on your Desktop to launch the GUI.
echo.
pause
