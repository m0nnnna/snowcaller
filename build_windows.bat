@echo off
echo Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del /q *.spec
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Building Snowcaller for Windows...

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Please install it from python.org and ensure it's in PATH.
    exit /b 1
)

REM Create and activate virtual environment
set VENV_DIR=venv
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo Failed to create virtual environment. Ensure venv module is available.
        exit /b 1
    )
)
call "%VENV_DIR%\Scripts\activate"

REM Install dependencies
pip install --upgrade pip
pip install pyinstaller requests
if %ERRORLEVEL% neq 0 (
    echo Failed to install PyInstaller or requests.
    call deactivate
    exit /b 1
)

REM Build the executable
pyinstaller --onefile ^
    --add-data "art;art" ^
    --add-data "NPC;NPC" ^
    --add-data "consumables.json;." ^
    --add-data "event.json;." ^
    --add-data "gear.json;." ^
    --add-data "keyitems.json;." ^
    --add-data "lore.json;." ^
    --add-data "monster.json;." ^
    --add-data "npcs.json;." ^
    --add-data "quest.json;." ^
    --add-data "skills.json;." ^
    --add-data "treasures.json;." ^
    --add-data "locations.txt;." ^
    --hidden-import "requests" ^
    --name Snowcaller game.py

if %ERRORLEVEL% equ 0 (
    echo Build successful! Executable is in the 'dist' folder as 'Snowcaller.exe'.
    call deactivate
) else (
    echo Build failed. Check the output above for errors.
    call deactivate
    exit /b 1
)