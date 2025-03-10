import os
import subprocess
import sys

# Try to import requests, but continue if it's not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not installed. Internet checking will be skipped.")

def check_internet_connection():
    """Check if there's an active internet connection"""
    if not REQUESTS_AVAILABLE:
        # Assume online if requests isn't available
        return True
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def check_repo_status():
    """Check if the local git repository needs updating"""
    try:
        # Get current branch
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()

        # Fetch remote info without merging
        subprocess.run(["git", "fetch"], capture_output=True, text=True)
        
        # Compare local and remote HEAD
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
    """Perform git pull to update the repository"""
    try:
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Repository updated successfully!")
            return True
        else:
            print("Update failed:", result.stderr)
            return False
    except Exception as e:
        print(f"Error updating repository: {e}")
        return False

def check_for_updates():
    """Main function to check and handle updates"""
    # Only proceed if online
    if not check_internet_connection():
        return
    
    # Check if we're in a git repository
    if not os.path.exists(".git"):
        return
    
    # Check if repo needs updating
    if check_repo_status():
        print("A new version of the game is available!")
        response = input("Would you like to update now? (y/n): ").lower()
        if response == 'y':
            if update_repo():
                print("Please restart the game to use the new version.")
                sys.exit(0)
            else:
                print("Continuing with current version...")
