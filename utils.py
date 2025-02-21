def load_file(filename):
    with open(filename, "r") as f:
        # Filter out empty lines and comments starting with '#'
        return [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]

def parse_stats(stat_str, is_consumable=False):
    stats = {}
    stats["S"] = int(stat_str[1:2])
    stats["A"] = int(stat_str[3:4])
    stats["I"] = int(stat_str[5:6])
    stats["W"] = int(stat_str[7:8])
    stats["L"] = int(stat_str[9:10])
    if is_consumable and len(stat_str) > 10:  # Only add T and E for consumables
        stats["T"] = int(stat_str[11:12])
        stats["E"] = "E" in stat_str[12:]
    return stats
