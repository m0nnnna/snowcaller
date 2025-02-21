from utils import load_file, parse_stats

def use_item(player, item, monster_stats=None):
    consumables = load_file("consumables.txt")
    gear = load_file("gear.txt")
    
    for c in consumables:
        if c.split()[0] == item:
            stats = parse_stats(c.split()[1], is_consumable=True)  # Consumables need T and E
            if stats.get("E"):
                if player.active_enemy_effect:
                    if player.active_enemy_effect[0] == item:
                        print(f"{item} is already active!")
                        return True
                    else:
                        print("Another enemy effect is active!")
                        return True
                else:
                    for stat, val in stats.items():
                        if stat not in ["T", "E"] and monster_stats:
                            monster_stats[stat] += val
                    player.active_enemy_effect = [item, stats["T"]]
                    print(f"Used {item} on the enemy! Effect lasts {stats['T']} turns.")
                    player.inventory.remove(item)
                    return False
            else:
                for stat, val in stats.items():
                    if stat not in ["T", "E"]:
                        player.stats[stat] += val
                if stats["T"] > 0:
                    print(f"{item} active for {stats['T']} turns (not fully tracked).")
                player.hp = min(player.hp + 2 * player.stats["S"], 10 + 2 * player.stats["S"])
                player.mp = min(player.mp + 2 * player.stats["W"], 2 * player.stats["W"])
                player.inventory.remove(item)
                return True
    
    for g in gear:
        if g.split()[0] == item:
            slot = g.split()[2]
            stats = parse_stats(g.split()[1], is_consumable=False)  # Gear doesn’t need T/E
            if player.equipment[slot]:
                old_item, old_stats = player.equipment[slot]
                for stat, val in old_stats.items():
                    player.stats[stat] -= val
                player.inventory.append(old_item)
            player.equipment[slot] = (item, stats)
            for stat, val in stats.items():
                player.stats[stat] += val
            player.hp = min(player.hp + 2 * player.stats["S"], 10 + 2 * player.stats["S"])
            player.mp = min(player.mp + 2 * player.stats["W"], 2 * player.stats["W"])
            player.inventory.remove(item)
            print(f"Equipped {item} in {slot} slot.")
            return True
    return True
