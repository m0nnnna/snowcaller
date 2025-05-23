import os
import sys
import json
import time
import shutil
import requests
import zipfile
import io

# GitHub repository details
GITHUB_USER = "m0nnnna"
GITHUB_REPO = "snowcaller"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits/main"
ZIP_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/main.zip"

def check_internet_connection():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def get_latest_commit():
    """Get the latest commit hash from GitHub."""
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()['sha']
        return None
    except Exception:
        return None

def get_current_commit():
    """Get the current commit hash from the game directory."""
    try:
        commit_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit.txt")
        if os.path.exists(commit_file):
            with open(commit_file, 'r') as f:
                return f.read().strip()
        return None
    except Exception:
        return None

def save_current_commit(commit_hash):
    """Save the current commit hash to a file."""
    try:
        commit_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit.txt")
        with open(commit_file, 'w') as f:
            f.write(commit_hash)
        return True
    except Exception:
        return False

def download_and_extract_update(game_dir):
    """Download the latest files and extract them to the game directory."""
    try:
        print("Downloading update...")
        
        # Download the zip file
        response = requests.get(ZIP_URL)
        if response.status_code != 200:
            print("Failed to download update.")
            return False
            
        # Create a temporary directory for extraction
        temp_dir = os.path.join(game_dir, "temp_update")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Get the extracted directory name (it's usually the first directory)
        extracted_dir = os.path.join(temp_dir, os.listdir(temp_dir)[0])
        
        # Copy all files except .git directory
        for item in os.listdir(extracted_dir):
            if item != '.git':
                src = os.path.join(extracted_dir, item)
                dst = os.path.join(game_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.copy2(src, dst)
        
        # Clean up
        shutil.rmtree(temp_dir)
        print("Update completed successfully!")
        return True
        
    except Exception as e:
        print(f"Update failed: {e}")
        return False

def check_for_updates():
    """Check for updates and apply them if available."""
    # Get the game directory
    game_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Check internet connection first
        if not check_internet_connection():
            print("No internet connection. Skipping update check.")
            return
            
        # Get current and latest commit hashes
        current_commit = get_current_commit()
        latest_commit = get_latest_commit()
        
        if not latest_commit:
            print("Could not check for updates.")
            return
            
        # If we don't have a current commit or it's different from the latest
        if not current_commit or current_commit != latest_commit:
            print("New update available!")
            if download_and_extract_update(game_dir):
                # Save the new commit hash
                save_current_commit(latest_commit)
                print("Update completed. Please restart the game.")
                sys.exit(0)
        else:
            print("Game is up to date.")
            
    except Exception as e:
        print(f"Update check failed: {e}")

if __name__ == "__main__":
    check_for_updates()