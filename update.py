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

def get_git_path():
    """Get the path to git executable, checking both system and local git."""
    # Check for local git in game directory
    local_git = os.path.join(os.path.dirname(os.path.abspath(__file__)), "git", "git-cmd.exe")
    if os.path.exists(local_git):
        return local_git
    
    # Check for system git
    system_git = shutil.which("git")
    if system_git:
        return system_git
    
    return None

def initialize_git_repo():
    """Initialize a git repository if one doesn't exist."""
    git_path = get_git_path()
    if not git_path:
        print("Git not found. Please install Git or ensure git-cmd.exe is in the git folder.")
        return False
    
    try:
        # Get the game directory
        game_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check if we're already in a git repo
        result = subprocess.run([git_path, "rev-parse", "--git-dir"], 
                              cwd=game_dir,
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True  # Already a git repo
            
        # Initialize new git repo
        print("Initializing git repository...")
        subprocess.run([git_path, "init"], cwd=game_dir, check=True)
        
        # Set default branch to main
        subprocess.run([git_path, "branch", "-M", "main"], cwd=game_dir, check=True)
        
        # Add remote
        remote_url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
        subprocess.run([git_path, "remote", "add", "origin", remote_url], cwd=game_dir, check=True)
        
        # Initial commit
        subprocess.run([git_path, "add", "."], cwd=game_dir, check=True)
        subprocess.run([git_path, "commit", "-m", "Initial commit"], cwd=game_dir, check=True)
        
        print("Git repository initialized successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {e}")
        return False

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
    git_path = get_git_path()
    if not git_path:
        print("Git not found. Please install Git or ensure git-cmd.exe is in the git folder.")
        return
    
    # Get the game directory
    game_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in a git repo, initialize if not
    if not os.path.exists(os.path.join(game_dir, ".git")):
        if not initialize_git_repo():
            return
        
    try:
        # Fetch latest changes
        subprocess.run([git_path, "fetch", "origin", "main"], cwd=game_dir, check=True)
        
        # Get current and remote commit hashes
        current_commit = subprocess.check_output([git_path, "rev-parse", "HEAD"], 
                                               cwd=game_dir, text=True).strip()
        remote_commit = subprocess.check_output([git_path, "rev-parse", "origin/main"], 
                                              cwd=game_dir, text=True).strip()
        
        if current_commit != remote_commit:
            print("A new version of the game is available!")
            response = input("Would you like to update now? (y/n): ").lower()
            if response == 'y':
                # Pull the latest changes
                result = subprocess.run([git_path, "pull", "origin", "main"], 
                                     cwd=game_dir, capture_output=True, text=True)
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