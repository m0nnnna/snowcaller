import os
import sys
import json
import time
import shutil
import subprocess
import requests
from packaging import version

# Current game version (update this with each release)
CURRENT_VERSION = "0.0.5"

# GitHub repository details
GITHUB_USER = "m0nnnna"
GITHUB_REPO = "snowcaller"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

def check_internet_connection():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def get_game_path():
    """Get the directory containing the game files."""
    return os.path.dirname(os.path.abspath(__file__))

def check_for_updates():
    """Check for updates from the main branch and apply them if available."""
    if not os.path.exists(".git"):
        print("Not in a Git repository. Update check skipped.")
        return
        
    if not shutil.which("git"):
        print("Git not installed. Update check skipped.")
        return
        
    try:
        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        
        # Get current and remote commit hashes
        current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        remote_commit = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
        
        if current_commit != remote_commit:
            print("A new version of the game is available!")
            response = input("Would you like to update now? (y/n): ").lower()
            if response == 'y':
                # Pull the latest changes
                result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Game updated successfully!")
                    time.sleep(1)
                    print("\n*** Please restart the game to use the new version. ***")
                    sys.exit(0)
                else:
                    print("Update failed:", result.stderr)
        else:
            print("Game is up to date!")
            
    except subprocess.CalledProcessError as e:
        print(f"Update check failed: {e}")

if __name__ == "__main__":
    check_for_updates()