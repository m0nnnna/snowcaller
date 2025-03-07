@echo off
echo Cleaning old builds...
rd /s /q dist 2>nul
rd /s /q build 2>nul
del /q *.spec 2>nul
rd /s /q __pycache__ 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo Building Snowcaller for Windows...

:: Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install PyInstaller. Please install it manually with 'pip install pyinstaller'.
        pause
        exit /b 1
    )
)

:: Build the executable with all files
pyinstaller --onefile ^
    --add-data "art;art" ^
    --add-data "consumables.json;." ^
    --add-data "gear.json;." ^
    --add-data "locations.txt;." ^
    --add-data "lore.json;." ^
    --add-data "monster.json;." ^
    --add-data "quest.json;." ^
    --add-data "skills.txt;." ^
    --add-data "treasures.json;." ^
    --name Snowcaller game.py

:: Check if build succeeded
if %ERRORLEVEL% EQU 0 (
    echo Build successful! Executable is in the 'dist' folder as 'Snowcaller.exe'.
) else (
    echo Build failed. Check the output above for errors.
)

pause