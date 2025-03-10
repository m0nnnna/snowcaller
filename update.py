import os
import subprocess
import sys
import shutil
import time

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

def check_repo_status():
    if not shutil.which("git"):
        print("Warning: Git not installed. Update checking skipped.")
        return False
    if not os.path.exists(".git"):
        print("Warning: Not a git repository. Update checking skipped.")
        return False
    try:
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()
        subprocess.run(["git", "fetch"], capture_output=True, text=True)
        local_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()
        remote_commit = subprocess.check_output(
            ["git", "rev-parse", f"origin/{current_branch}"],
            text=True
        ).strip()
        return local_commit != remote_commit
    except subprocess.CalledProcessError:
        return False

def update_repo():
    try:
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Repository updated successfully!")
            time.sleep(1)
            print("\n*** Please restart the game to use the new version. ***")
            return True
        else:
            print("Update failed:", result.stderr)
            return False
    except Exception as e:
        print(f"Error updating repository: {e}")
        return False

def check_for_updates():
    if not check_internet_connection():
        return
    if not os.path.exists(".git"):
        return
    if check_repo_status():
        print("A new version of the game is available!")
        response = input("Would you like to update now? (y/n): ").lower()
        if response == 'y':
            if update_repo():
                sys.exit(0)
            else:
                print("Continuing with current version...")
    else:
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()[:7]
            print(f"Running game version (commit: {commit})")
        except:
            pass