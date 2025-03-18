@echo off
setlocal

:: Ensure PyInstaller is installed
where pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo Failed to install PyInstaller. Ensure pip is in PATH.
        exit /b 1
    )
)

:: Clean all existing builds
echo Cleaning previous builds...
rmdir /S /Q build dist 2>nul
del *.spec 2>nul

:: Build the executable in the current directory
echo Building Frost Editor for Windows...
pyinstaller ^
    --add-data "1.png;." ^
    --icon="1.ico" ^
    --onefile ^
    frost_editor.py

:: Check if build succeeded
if %ERRORLEVEL% equ 0 (
    echo Build complete! Executable is at 'dist\frost_editor.exe'
    echo Run 'dist\frost_editor.exe' to test.
) else (
    echo Build failed. Check PyInstaller output for errors.
    exit /b 1
)

endlocal