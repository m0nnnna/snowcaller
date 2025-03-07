import sys
import os
import json

def load_json(filename):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, filename)
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def load_file(filename):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, filename)
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def load_art_file(filename):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, filename)
    with open(file_path, "r") as f:
        # Preserve all whitespace, optionally filter comments
        return [line.rstrip('\n') for line in f if not line.startswith("#")]
        
def get_resource_path(filename):
    """Get the correct path for a resource file, whether running as script or frozen executable."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, filename)

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