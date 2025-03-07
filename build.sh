#!/bin/bash
echo "Cleaning old builds..."
rm -rf dist build *.spec __pycache__ */__pycache__
echo "Building Snowcaller for Linux..."

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller. Please install it manually with 'pip install pyinstaller'."
        exit 1
    fi
fi

pyinstaller --onefile \
    --add-data "art:art" \
    --add-data "consumables.json:." \
    --add-data "gear.json:." \
    --add-data "locations.txt:." \
    --add-data "lore.json:." \
    --add-data "monster.json:." \
    --add-data "quest.json:." \
    --add-data "skills.txt:." \
    --add-data "treasures.json:." \
    --name Snowcaller game.py

if [ $? -eq 0 ]; then
    echo "Build successful! Executable is in the 'dist' folder as 'Snowcaller'."
else
    echo "Build failed. Check the output above for errors."
    exit 1
fi