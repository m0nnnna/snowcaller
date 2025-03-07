#!/bin/bash
echo "Cleaning old builds..."
rm -rf dist build *.spec __pycache__ */__pycache__
echo "Building Snowcaller for macOS..."

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller. Please install it manually with 'pip3 install pyinstaller'."
        exit 1
    fi
fi

# Build the executable with all files
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

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo "Build successful! Executable is in the 'dist' folder as 'Snowcaller'."
    
    # Optional: Create a .app bundle
    echo "Creating macOS .app bundle..."
    mkdir -p dist/Snowcaller.app/Contents/MacOS
    mv dist/Snowcaller dist/Snowcaller.app/Contents/MacOS/
    cat > dist/Snowcaller.app/Contents/Info.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Snowcaller</string>
    <key>CFBundleIdentifier</key>
    <string>com.m0nnnna.snowcaller</string>
    <key>CFBundleName</key>
    <string>Snowcaller</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
EOL
    echo "App bundle created at 'dist/Snowcaller.app'."
else
    echo "Build failed. Check the output above for errors."
    exit 1
fi
