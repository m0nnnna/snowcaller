#!/bin/bash
echo "Cleaning old builds..."
rm -rf dist build *.spec __pycache__ */__pycache__
echo "Building Snowcaller for Linux..."

# Check for Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 not found. Please install it (e.g., sudo apt install python3)."
    exit 1
fi

# Create and activate virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Ensure python3-venv is installed (e.g., sudo apt install python3-venv)."
        exit 1
    fi
fi
source "$VENV_DIR/bin/activate"

# Install dependencies in the virtual environment
pip install --upgrade pip
pip install pyinstaller requests
if [ $? -ne 0 ]; then
    echo "Failed to install PyInstaller or requests in the virtual environment."
    exit 1
fi

# Build the executable
pyinstaller --onefile \
    --add-data "art:art" \
    --add-data "consumables.json:." \
    --add-data "gear.json:." \
    --add-data "locations.txt:." \
    --add-data "lore.json:." \
    --add-data "monster.json:." \
    --add-data "quest.json:." \
    --add-data "skills.json:." \
    --add-data "treasures.json:." \
    --hidden-import "requests" \
    --name Snowcaller game.py

if [ $? -eq 0 ]; then
    echo "Build successful! Executable is in the 'dist' folder as 'Snowcaller'."
    deactivate  # Exit the virtual environment
else
    echo "Build failed. Check the output above for errors."
    deactivate
    exit 1
fi