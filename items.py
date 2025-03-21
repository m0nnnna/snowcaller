import time
from utils import load_json, parse_stats 

def parse_consumable(item_line):
    parts = item_line.split()
    if not parts or not parts[-1].startswith("[") or not parts[-1].endswith("]"):
        return None
    name = " ".join(parts[:-1])
    bracket = parts[-1][1:-1].split()
    is_rare = False
    if bracket[-1] == "[R]":
        bracket.pop()
        is_rare = True
    if len(bracket) != 7:
        print(f"Warning: Invalid consumable format: {item_line}")
        return None
    level_part, effect_type, value, stat, duration, drop_rate, gold = bracket
    if not level_part.startswith("L:") or not drop_rate.endswith("%"):
        print(f"Warning: Invalid level range or drop rate: {item_line}")
        return None
    try:
        min_level, max_level = map(int, level_part[2:].split("-"))
        value = int(value)
        duration = int(duration)
        drop_rate = float(drop_rate[:-1]) / 100
        gold = int(gold)
        if effect_type not in ["HP", "MP", "Buff", "Offense"]:
            print(f"Warning: Invalid effect type {effect_type} in {item_line}")
            return None
        if effect_type == "Buff" and stat not in ["S", "A", "I", "W", "L"]:
            print(f"Warning: Invalid stat {stat} for Buff in {item_line}")
            return None
        if effect_type in ["HP", "MP"] and stat != "none":
            print(f"Warning: HP/MP items should use 'none' for stat, got {stat} in {item_line}")
            # Still allow it to proceed, treating unexpected stat as 'none'
        if effect_type == "Offense" and stat not in ["Poison", "none"]:
            print(f"Warning: Invalid stat {stat} for Offense in {item_line}")
            return None
        return {
            "name": name,
            "level_range": (min_level, max_level),
            "type": effect_type,
            "value": value,
            "stat": stat if effect_type in ["Buff", "Offense"] else None,  # Only keep stat for Buff/Offense
            "duration": duration,
            "drop_rate": drop_rate,
            "gold": gold,
            "is_rare": is_rare
        }
    except (ValueError, IndexError):
        print(f"Warning: Could not parse consumable: {item_line}")
        return None

def use_item(player, item_name, monster_stats=None):
    consumables = load_json("consumables.json")
    gear = load_json("gear.json")

    if not hasattr(player, "active_effects"):
        player.active_effects = {}
    if monster_stats and "effects" not in monster_stats:
        monster_stats["effects"] = {}

    for consumable in consumables:
        if consumable["name"] == item_name:
            if player.level < consumable["level_range"]["min"] or player.level > consumable["level_range"]["max"]:
                print(f"{item_name} is not suitable for your level ({player.level})!")
                time.sleep(0.5)
                return False

            level_block = ((consumable["level_range"]["min"] - 1) // 10) + 1
            scale = level_block
            effect_value = consumable["value"] * scale

            if consumable["type"] == "HP":
                if consumable["duration"] > 0:
                    player.active_effects[item_name] = consumable["duration"]
                    print(f"{item_name} will restore {effect_value} HP over {consumable['duration']} turns.")
                else:
                    player.hp = min(player.hp + effect_value, player.max_hp)
                    print(f"{item_name} restores {effect_value} HP!")
            elif consumable["type"] == "MP":
                if consumable["duration"] > 0:
                    player.active_effects[item_name] = consumable["duration"]
                    print(f"{item_name} will restore {effect_value} MP over {consumable['duration']} turns.")
                else:
                    player.mp = min(player.mp + effect_value, player.max_mp)
                    print(f"{item_name} restores {effect_value} MP!")
            elif consumable["type"] == "Buff":
                if consumable["duration"] > 0:
                    player.active_effects[item_name] = consumable["duration"]
                    player.stats[consumable["stat"]] += effect_value
                    print(f"{item_name} boosts {consumable['stat']} by {effect_value} for {consumable['duration']} turns!")
                else:
                    print(f"{item_name} has no duration; Buff requires turns!")
                    time.sleep(0.5)
                    return False
            elif consumable["type"] == "Offense":
                if not monster_stats:
                    print(f"{item_name} requires a target monster!")
                    time.sleep(0.5)
                    return False
                if consumable["duration"] > 0:
                    monster_stats["effects"][item_name] = consumable["duration"]
                    print(f"{item_name} applies {effect_value} damage per turn to the monster for {consumable['duration']} turns!")
                else:
                    monster_stats["hp"] -= effect_value
                    print(f"{item_name} deals {effect_value} damage to the monster!")

            player.inventory.remove(item_name)
            time.sleep(0.5)
            return True

    for g in gear:
        if g["name"] == item_name:
            slot = g["slot"]
            if player.level < g["level_range"]["min"] or player.level > g["level_range"]["max"]:
                print(f"{item_name} is not suitable for your level ({player.level})!")
                time.sleep(0.5)
                return False
            if player.equipment[slot]:
                old_item = player.equipment[slot][0]
                for stat, val in player.equipment[slot][1].items():
                    player.stats[stat] -= val
                player.inventory.append(old_item)
            player.equipment[slot] = (item_name, g["stats"], g["modifier"], g["armor_value"])
            for stat, val in g["stats"].items():
                player.stats[stat] += val
            player.inventory.remove(item_name)
            player.hp = min(player.hp + 2 * player.stats["S"], player.max_hp)
            player.mp = min(player.mp + 2 * player.stats["W"], player.max_mp)
            print(f"Equipped {item_name} to {slot}!")
            time.sleep(0.5)
            return True

    print(f"Item {item_name} not found!")
    time.sleep(0.5)
    return False

    for g in gear:
        parts = g.split()
        if parts[0] == item:
            matched = True
            bracket = parts[-1][1:-1].split()
            if bracket[-1] == "[R]":
                bracket.pop()
            level_part, slot, stats_str, damage, drop_rate, gold = bracket
            min_level, max_level = map(int, level_part[2:].split("-"))
            if player.level < min_level or player.level > max_level:
                print(f"{item} is not suitable for your level ({player.level})!")
                time.sleep(0.5)
                return False
            stats = parse_stats(stats_str, is_consumable=False)
            if player.equipment[slot]:
                old_item = player.equipment[slot][0]
                for stat, val in player.equipment[slot][1].items():
                    player.stats[stat] -= val
                player.inventory.append(old_item)
            player.equipment[slot] = (item, stats)
            for stat, val in stats.items():
                player.stats[stat] += val
            player.inventory.remove(item)
            player.hp = min(player.hp + 2 * player.stats["S"], player.max_hp)
            player.mp = min(player.mp + 2 * player.stats["W"], player.max_mp)
            print(f"Equipped {item} to {slot}!")
            time.sleep(0.5)
            return True

    # This block should be indented under the function
    if not matched:
        print(f"Item {item} not found!")
        time.sleep(0.5)
        return False