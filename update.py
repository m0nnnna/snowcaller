import os
import sys
import json
import time
import shutil
import subprocess
from packaging import version  # For version comparison

# Current game version (update this with each release)
CURRENT_VERSION = "1.0.0"  # Replace with your actual version

# GitHub repository details
GITHUB_USER = "m0nnnna"  # Replace with your GitHub username
GITHUB_REPO = "snowcaller"     # Replace with your repo name
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not installed. Internet checking will be skipped.")

def check_internet_connection():
    if not REQUESTS_AVAILABLE:
        return True
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def get_executable_path():
    """Get the directory containing the executable or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def check_for_updates_compiled():
    """Check GitHub Releases for a newer version and update if found."""
    if not REQUESTS_AVAILABLE or not check_internet_connection():
        print("Update check skipped: No internet or requests module.")
        return

    try:
        # Fetch latest release info from GitHub
        response = requests.get(RELEASES_URL, timeout=5)
        response.raise_for_status()
        release_data = response.json()
        latest_version = release_data["tag_name"].lstrip("v")  # e.g., "v1.0.1" -> "1.0.1"

        # Compare versions
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            print(f"New version {latest_version} available! Current version: {CURRENT_VERSION}")
            print("Updating game...")

            # Find assets (executable and bundled files)
            exe_asset = None
            bundled_assets = []
            for asset in release_data["assets"]:
                if asset["name"] == f"Snowcaller{'-macos' if sys.platform == 'darwin' else '-windows.exe' if os.name == 'nt' else '-linux'}":
                    exe_asset = asset
                elif asset["name"].endswith((".json", ".txt")) or asset["name"] == "art.zip":
                    bundled_assets.append(asset)

            if not exe_asset:
                print("No matching executable found in the latest release.")
                return

            # Directory setup
            base_path = get_executable_path()
            save_path = os.path.join(base_path, "save.json")
            temp_exe_path = os.path.join(base_path, f"Snowcaller_temp{'-macos' if sys.platform == 'darwin' else '-windows.exe' if os.name == 'nt' else '-linux'}")

            # Download new executable
            print(f"Downloading {exe_asset['name']}...")
            with requests.get(exe_asset["browser_download_url"], stream=True) as r:
                r.raise_for_status()
                with open(temp_exe_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Preserve save.json
            temp_save_path = os.path.join(os.path.dirname(base_path), "save.json_temp")
            if os.path.exists(save_path):
                shutil.move(save_path, temp_save_path)

            # Delete all files except save.json (already moved)
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            # Move new executable
            new_exe_name = f"Snowcaller{'-macos' if sys.platform == 'darwin' else '-windows.exe' if os.name == 'nt' else '-linux'}"
            shutil.move(temp_exe_path, os.path.join(base_path, new_exe_name))

            # Download and extract bundled files (e.g., JSON, art)
            for asset in bundled_assets:
                temp_asset_path = os.path.join(base_path, asset["name"])
                print(f"Downloading {asset['name']}...")
                with requests.get(asset["browser_download_url"], stream=True) as r:
                    r.raise_for_status()
                    with open(temp_asset_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                if asset["name"] == "art.zip":
                    shutil.unpack_archive(temp_asset_path, os.path.join(base_path, "art"))
                    os.remove(temp_asset_path)

            # Restore save.json
            if os.path.exists(temp_save_path):
                shutil.move(temp_save_path, save_path)

            print(f"Update complete! Please relaunch the game to use version {latest_version}")
            time.sleep(2)
            sys.exit(0)
        else:
            print(f"Running latest version: {CURRENT_VERSION}")
    except Exception as e:
        print(f"Update check failed: {e}")

def check_for_updates_script():
    """Original Git-based update check for non-compiled mode."""
    if not check_internet_connection():
        return
    if not os.path.exists(".git"):
        return
    if not shutil.which("git"):
        print("Warning: Git not installed. Update checking skipped.")
        return
    try:
        current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        subprocess.run(["git", "fetch"], capture_output=True, text=True)
        local_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        remote_commit = subprocess.check_output(["git", "rev-parse", f"origin/{current_branch}"], text=True).strip()
        if local_commit != remote_commit:
            print("A new version of the game is available!")
            response = input("Would you like to update now? (y/n): ").lower()
            if response == 'y':
                result = subprocess.run(["git", "pull"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Repository updated successfully!")
                    time.sleep(1)
                    print("\n*** Please restart the game to use the new version. ***")
                    sys.exit(0)
                else:
                    print("Update failed:", result.stderr)
                    print("Continuing with current version...")
        else:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()[:7]
            print(f"Running game version (commit: {commit})")
    except subprocess.CalledProcessError:
        pass

def check_for_updates():
    """Dispatch to compiled or script update logic."""
    if getattr(sys, 'frozen', False):
        check_for_updates_compiled()
    else:
        check_for_updates_script()