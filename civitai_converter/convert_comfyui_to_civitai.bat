@echo off
REM ComfyUI to Civitai Metadata Converter - Windows Batch Script
REM This script helps you convert ComfyUI output to Civitai-compatible format

echo ========================================
echo ComfyUI to Civitai Metadata Converter
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if PIL is available
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependency: Pillow
    pip install pillow
    if errorlevel 1 (
        echo Error: Failed to install Pillow
        pause
        exit /b 1
    )
)

REM Set default paths (modify these to match your setup)
set "DEFAULT_CHECKPOINTS=%~dp0models\checkpoints"
set "DEFAULT_LORAS=%~dp0models\loras"
set "DEFAULT_VAES=%~dp0models\vae"
set "DEFAULT_EMBEDDINGS=%~dp0models\embeddings"

echo Default model paths:
echo   Checkpoints: %DEFAULT_CHECKPOINTS%
echo   LoRAs:       %DEFAULT_LORAS%
echo   VAEs:        %DEFAULT_VAES%
echo   Embeddings:  %DEFAULT_EMBEDDINGS%
echo.

REM Get input directory
set /p "INPUT_DIR=Enter the directory containing your ComfyUI output images: "
if not exist "%INPUT_DIR%" (
    echo Error: Directory "%INPUT_DIR%" does not exist
    pause
    exit /b 1
)

REM Ask if user wants to specify custom model paths
set /p "USE_CUSTOM=Do you want to specify custom model paths? (y/n): "
set "CUSTOM_ARGS="

if /i "%USE_CUSTOM%"=="y" (
    set /p "CHECKPOINTS_PATH=Enter checkpoints directory (or press Enter for default): "
    if not "!CHECKPOINTS_PATH!"=="" (
        set "CUSTOM_ARGS=!CUSTOM_ARGS! --checkpoints "!CHECKPOINTS_PATH!""
    )
    
    set /p "LORAS_PATH=Enter LoRAs directory (or press Enter for default): "
    if not "!LORAS_PATH!"=="" (
        set "CUSTOM_ARGS=!CUSTOM_ARGS! --loras "!LORAS_PATH!""
    )
    
    set /p "VAES_PATH=Enter VAEs directory (or press Enter for default): "
    if not "!VAES_PATH!"=="" (
        set "CUSTOM_ARGS=!CUSTOM_ARGS! --vaes "!VAES_PATH!""
    )
    
    set /p "EMBEDDINGS_PATH=Enter embeddings directory (or press Enter for default): "
    if not "!EMBEDDINGS_PATH!"=="" (
        set "CUSTOM_ARGS=!CUSTOM_ARGS! --embeddings "!EMBEDDINGS_PATH!""
    )
) else (
    REM Use default paths if they exist
    if exist "%DEFAULT_CHECKPOINTS%" (
        set "CUSTOM_ARGS=%CUSTOM_ARGS% --checkpoints "%DEFAULT_CHECKPOINTS%""
    )
    if exist "%DEFAULT_LORAS%" (
        set "CUSTOM_ARGS=%CUSTOM_ARGS% --loras "%DEFAULT_LORAS%""
    )
    if exist "%DEFAULT_VAES%" (
        set "CUSTOM_ARGS=%CUSTOM_ARGS% --vaes "%DEFAULT_VAES%""
    )
    if exist "%DEFAULT_EMBEDDINGS%" (
        set "CUSTOM_ARGS=%CUSTOM_ARGS% --embeddings "%DEFAULT_EMBEDDINGS%""
    )
)

REM Ask about output directory
set /p "CREATE_BACKUP=Do you want to create backups and modify originals? (y/n): "
set "OUTPUT_ARGS="

if /i not "%CREATE_BACKUP%"=="y" (
    set /p "OUTPUT_DIR=Enter output directory for converted images: "
    set "OUTPUT_ARGS=-o "%OUTPUT_DIR%""
)

echo.
echo Starting conversion...
echo Command: python comfyui_to_civitai_converter.py "%INPUT_DIR%" %OUTPUT_ARGS% %CUSTOM_ARGS%
echo.

REM Run the converter
python "%~dp0comfyui_to_civitai_converter.py" "%INPUT_DIR%" %OUTPUT_ARGS% %CUSTOM_ARGS%

echo.
echo Conversion completed!
echo.
echo Your images now have Civitai-compatible metadata with SHA256 hashes.
echo You can upload them to Civitai and the resources will be automatically detected.
echo.
pause
