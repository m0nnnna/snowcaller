import os
import sys
import json
import time
import shutil
import subprocess
import requests
import ctypes
from packaging import version

# Current game version (update this with each release)
CURRENT_VERSION = "0.0.5"

# GitHub repository details
GITHUB_USER = "m0nnnna"
GITHUB_REPO = "snowcaller"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

def is_admin():
    """Check if the program is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunch the program with admin privileges."""
    if sys.platform == "win32":
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def get_git_path():
    """Get the path to git executable, trying portable git first, then falling back to system git."""
    # First try portable git with the correct path
    local_git = os.path.join(os.path.dirname(os.path.abspath(__file__)), "git", "App", "Git", "cmd", "git.exe")
    if os.path.exists(local_git):
        try:
            # Test if the portable git works by running a simple command
            result = subprocess.run([local_git, "--version"], 
                                 capture_output=True, 
                                 text=True, 
                                 timeout=5)  # Add timeout to prevent hanging
            if result.returncode == 0:
                return local_git
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            # If portable git fails, fall back to system git
            pass
    
    # Fall back to system git
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
        print("Git not found. Skipping update check.")
        return
    
    # Get the game directory
    game_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Check internet connection first
        if not check_internet_connection():
            print("No internet connection. Skipping update check.")
            return
            
        # If this is first run (no .git directory), clone the repository
        if not os.path.exists(os.path.join(game_dir, ".git")):
            print("First run detected. Downloading latest version...")
            try:
                # Create .gitignore file to exclude system directories
                gitignore_content = """# System directories
git/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
env.bak/
venv.bak/
*.log
.DS_Store
Thumbs.db
"""
                with open(os.path.join(game_dir, ".gitignore"), "w") as f:
                    f.write(gitignore_content)
                
                # Clone the repository
                subprocess.run([git_path, "clone", "https://github.com/m0nnnna/snowcaller.git", "."], 
                             cwd=game_dir, check=True)
                print("Latest version downloaded successfully!")
                return
                
            except subprocess.CalledProcessError as e:
                if sys.platform == "win32" and not is_admin():
                    print("Update requires admin privileges. Restarting with admin rights...")
                    run_as_admin()
                    return
                print(f"Failed to download latest version: {e}")
                return
        
        # For subsequent runs, force pull the latest changes
        print("Checking for updates...")
        try:
            # First fetch the latest changes
            subprocess.run([git_path, "fetch", "origin", "main"], cwd=game_dir, check=True)
            # Then reset hard to origin/main to force overwrite all files
            subprocess.run([git_path, "reset", "--hard", "origin/main"], cwd=game_dir, check=True)
            print("Game is up to date!")
        except subprocess.CalledProcessError as e:
            if sys.platform == "win32" and not is_admin():
                print("Update requires admin privileges. Restarting with admin rights...")
                run_as_admin()
                return
            print(f"Update check failed: {e}")
            
    except subprocess.CalledProcessError as e:
        print(f"Update check failed: {e}")

if __name__ == "__main__":
    check_for_updates()