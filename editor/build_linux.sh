#!/bin/bash

# Detect the operating system
OS=$(uname -s 2>/dev/null || echo "Windows")
if [ "$OS" = "Windows" ] || [ "$OS" = "MINGW64_NT" ] || [ "$OS" = "MSYS_NT" ]; then
    OS="Windows"
elif [ "$OS" = "Darwin" ]; then
    OS="macOS"
else
    OS="Linux"
fi

# Set separator for --add-data based on OS
if [ "$OS" = "Windows" ]; then
    SEP=";"
else
    SEP=":"
fi

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    if [ "$OS" = "Windows" ]; then
        pip install pyinstaller
    else
        pip3 install pyinstaller
    fi
fi

# Clean all existing builds
echo "Cleaning previous builds..."
if [ "$OS" = "Windows" ]; then
    rmdir /S /Q build dist 2>nul
    del *.spec 2>nul
else
    rm -rf build/ dist/ *.spec
fi

# Build the executable in the current directory
echo "Building Frost Editor for $OS..."
if [ "$OS" = "Windows" ]; then
    pyinstaller \
        --add-data "1.png$SEP." \
        --icon="1.ico" \
        --onefile \
        frost_editor.py
elif [ "$OS" = "macOS" ]; then
    pyinstaller \
        --add-data "1.png$SEP." \
        --icon="1.ico" \
        --onefile \
        frost_editor.py
else  # Linux
    pyinstaller \
        --add-data "1.png$SEP." \
        --onefile \
        frost_editor.py
fi

# Output remains in dist/
echo "Build complete! Executable is at './dist/frost_editor'"
if [ "$OS" = "Windows" ]; then
    echo "Run 'dist\frost_editor.exe' to test."
else
    echo "Run './dist/frost_editor' to test."
fi

# For Linux, create a .desktop file to set the icon
if [ "$OS" = "Linux" ]; then
    echo "Creating .desktop file for Linux icon support..."
    cat > frost_editor.desktop << EOL
[Desktop Entry]
Name=Frost Editor
Exec=$(pwd)/dist/frost_editor
Type=Application
Icon=$(pwd)/1.png
Terminal=false
EOL
    chmod +x frost_editor.desktop
    echo "Created 'frost_editor.desktop'. Move it to ~/.local/share/applications/ for system-wide use."
fi