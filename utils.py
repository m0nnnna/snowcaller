import sys
import os
import json
import shutil

def get_base_path():
    """Get the directory containing the executable or script."""
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)  # Use raw sys.executable
        return path
    path = os.path.dirname(os.path.abspath(__file__))
    print(f"Base path (script): {path}")
    return path

def setup_game_files():
    """Install bundled files: JSON in base directory, art in art/ subdirectory."""
    base_path = get_base_path()
    art_path = os.path.join(base_path, "art")
    os.makedirs(art_path, exist_ok=True)

    if getattr(sys, 'frozen', False):
        bundled_path = sys._MEIPASS
        bundled_files = {
            "art": ["rogue.txt", "warrior.txt", "mage.txt", "kobold.txt", "goblin.txt", 
                    "skeleton.txt", "dragon.txt"],
            "json": ["consumables.json", "gear.json", "locations.txt", "lore.json", 
                     "monster.json", "quest.json", "skills.json", "treasures.json"]
        }
        for art_file in bundled_files["art"]:
            src = os.path.join(bundled_path, "art", art_file)
            dst = os.path.join(art_path, art_file)
            if not os.path.exists(dst) and os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Installed {art_file} to {dst}")
        for json_file in bundled_files["json"]:
            src = os.path.join(bundled_path, json_file)
            dst = os.path.join(base_path, json_file)
            if not os.path.exists(dst) and os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Installed {json_file} to {dst}")

def get_resource_path(filename, subfolder=None):
    """Get the absolute path to a resource file, ensuring base_path consistency."""
    base_path = get_base_path()
    if subfolder:
        full_path = os.path.join(base_path, subfolder, filename)
    else:
        full_path = os.path.join(base_path, filename)
    print(f"Resource path for {filename}: {full_path}")  # Debug, no abspath
    return full_path  # Return raw path without abspath

def load_json(filename):
    file_path = get_resource_path(filename)
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def load_file(filename):
    file_path = get_resource_path(filename)
    try:
        with open(file_path, "r") as f:
            return f.read().splitlines()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def load_art_file(filename):
    file_path = get_resource_path(filename, subfolder="art")
    try:
        with open(file_path, "r") as f:
            return [line.rstrip('\n') for line in f if not line.startswith("#")]
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def save_json(filename, data):
    base_path = get_base_path()
    file_path = os.path.join(base_path, filename)
    print(f"Saving to: {file_path}")  # Debug
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False


def parse_stats(stat_str, is_consumable=False):
    stats = {"S": 0, "A": 0, "I": 0, "W": 0, "L": 0}
    if len(stat_str) < 10:
        print(f"Warning: Invalid stat string '{stat_str}', using defaults.")
        return stats
    
    try:
        s_val = stat_str[1:stat_str.index("A")]
        a_val = stat_str[stat_str.index("A")+1:stat_str.index("I")]
        i_val = stat_str[stat_str.index("I")+1:stat_str.index("W")]
        w_val = stat_str[stat_str.index("W")+1:stat_str.index("L")]
        l_val = stat_str[stat_str.index("L")+1:]
        
        stats["S"] = int(s_val)
        stats["A"] = int(a_val)
        stats["I"] = int(i_val)
        stats["W"] = int(w_val)
        stats["L"] = int(l_val)
        
        if is_consumable and len(stat_str) > stat_str.index("L") + 1:
            t_idx = stat_str.index("L") + 1
            stats["T"] = int(stat_str[t_idx:t_idx+1]) if stat_str[t_idx:t_idx+1].isdigit() else 0
            stats["E"] = "E" in stat_str[t_idx+1:]
    except (ValueError, IndexError) as e:
        print(f"Error parsing stats '{stat_str}': {e}. Using defaults.")
        stats = {"S": 0, "A": 0, "I": 0, "W": 0, "L": 0}
        if is_consumable:
            stats["T"] = 0
            stats["E"] = False
    
    return stats

setup_game_files()