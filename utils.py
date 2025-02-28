import sys  # Required for sys._MEIPASS and sys.frozen
import os   # Required for os.path.dirname and os.path.join

def load_file(filename):
    if getattr(sys, 'frozen', False):  # Running as .exe
        base_path = sys._MEIPASS
    else:  # Running as .py
        base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, filename)
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def parse_stats(stat_str, is_consumable=False):
    stats = {"S": 0, "A": 0, "I": 0, "W": 0, "L": 0}
    if len(stat_str) < 10:
        print(f"Warning: Invalid stat string '{stat_str}', using defaults.")
        return stats
    
    try:
        # Find indices of stat letters and extract numbers
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