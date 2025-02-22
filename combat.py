import random
import time
from utils import load_file, parse_stats
from items import use_item

def get_weapon_damage_range(player):
    weapon = player.equipment.get("main_hand")
    damage_bonus = 0
    if "Rage" in player.skill_effects:
        skills = load_file("skills.txt")
        for skill in skills:
            parts = skill[1:-1].split()
            if parts[2] == "Rage":
                base_dmg = int(parts[3])
                stat = parts[7]
                damage_bonus = base_dmg + (int(player.stats[stat] * 0.5) if stat != "none" else 0)
                break
    if weapon:
        for g in load_file("gear.txt"):
            parts = g.split()
            if parts[0] == weapon[0]:
                bracket = parts[-1][1:-1].split()
                if bracket[-1] == "[R]":
                    bracket.pop()
                damage = bracket[3]
                if damage != "none":
                    min_dmg, max_dmg = map(float, damage.split("-"))
                    if "Sword" in weapon[0]:
                        stat_bonus = player.stats["S"] * 0.5
                    elif "Dagger" in weapon[0]:
                        stat_bonus = player.stats["A"] * 0.5
                    elif "Staff" in weapon[0]:
                        stat_bonus = player.stats["I"] * 0.5
                        if player.class_type == "2":
                            i_modifier = 1 + (player.stats["I"] * 0.008)
                            min_dmg *= i_modifier
                            max_dmg *= i_modifier
                    else:
                        stat_bonus = 0
                    return (min_dmg + stat_bonus + damage_bonus, max_dmg + stat_bonus + damage_bonus)
    return (1 + damage_bonus, 2 + damage_bonus)

def parse_monster(monster_line):
    parts = monster_line.split()
    print(f"Debug: monster_line = '{monster_line}'")
    print(f"Debug: parts = {parts}")
    if len(parts) < 5:
        print(f"Warning: Invalid monster format: '{monster_line}'")
        return {"name": "Unknown", "stats": {"S": 1, "A": 1, "I": 1, "W": 1, "L": 1}, "level": 1, "hp": 10, "mp": 2, "min_dmg": 1, "max_dmg": 2, "gold_chance": 0.5}
    
    # Find the stats string (starts with "S" and has expected length)
    name_parts = []
    stats_index = None
    for i, part in enumerate(parts):
        if part.startswith("S") and len(part) >= 10:
            stats_index = i
            break
        name_parts.append(part)
    name = " ".join(name_parts).strip("[]")
    
    if stats_index is None or stats_index + 3 >= len(parts):
        print(f"Warning: No valid stats or incomplete data in '{monster_line}'")
        return {"name": name, "stats": {"S": 1, "A": 1, "I": 1, "W": 1, "L": 1}, "level": 1, "hp": 10, "mp": 2, "min_dmg": 1, "max_dmg": 2, "gold_chance": 0.5}
    
    stats_str = parts[stats_index]      # e.g., "S6A3I2W4L4"
    level_range = parts[stats_index + 1]  # "L:5-10"
    damage_range = parts[stats_index + 2] # "D:4-8"
    gold_chance = parts[stats_index + 3]  # "G:75%"
    print(f"Debug: name = '{name}', stats_str = '{stats_str}'")  # Moved after assignment

    # Parse stats
    stats = parse_stats(stats_str, is_consumable=False)
    
    # Parse level range
    min_level, max_level = map(int, level_range[2:].split("-"))
    level = random.randint(min_level, max_level)
    
    # Parse damage range
    min_dmg, max_dmg = map(float, damage_range[2:].split("-"))
    
    # Parse gold chance
    gold_chance = float(gold_chance[2:-1]) / 100  # "75%" -> 0.75
    
    # Base HP and MP from stats
    hp = 10 + 2 * stats["S"]
    mp = 2 * stats["W"]
    
    return {
        "name": name,
        "stats": stats,
        "level": level,
        "hp": hp,
        "mp": mp,
        "min_dmg": min_dmg,
        "max_dmg": max_dmg,
        "gold_chance": gold_chance
    }

def combat(player, boss_fight=False):
    monsters = load_file("monsters.txt")
    print(f"Debug: all monsters = {monsters}")  # Add this to see full list
    monster = random.choice(monsters)
    monster_stats = parse_monster(monster)
    
    # Scale stats based on level
    level_scale = 1 + (monster_stats["level"] - 1) * 0.05 if not boss_fight else 1 + (monster_stats["level"] - 1) * 0.1
    monster_hp = monster_stats["hp"] * level_scale
    monster_mp = monster_stats["mp"] * level_scale
    monster_min_dmg = monster_stats["min_dmg"] * level_scale
    monster_max_dmg = monster_stats["max_dmg"] * level_scale
    
    if boss_fight:
        monster_hp *= 1.5
        monster_min_dmg *= 1.2
        monster_max_dmg *= 1.2
        name = "Boss " + monster_stats["name"]
    else:
        name = monster_stats["name"]
    
    print(f"\nA {name} appears! HP: {round(monster_hp, 1)}")
    time.sleep(0.5)

    while monster_hp > 0 and player.hp > 0:
        # Apply active skill effects
        for skill_name, turns in list(player.skill_effects.items()):
            if turns > 0:
                player.skill_effects[skill_name] -= 1
                if player.skill_effects[skill_name] == 0:
                    del player.skill_effects[skill_name]
                    print(f"{skill_name} effect has worn off!")
                    time.sleep(0.5)

        print(f"\n{name}: {round(monster_hp, 1)} HP | {player.name}: {round(player.hp, 1)}/{player.max_hp} HP, {player.mp}/{player.max_mp} MP")
        print("1. Attack | 2. Item | 3. Flee | 4. Skill" if player.level >= 5 else "1. Attack | 2. Item | 3. Flee")
        time.sleep(0.5)
        choice = input("Selection: ")

        if choice == "1":
            min_dmg, max_dmg = get_weapon_damage_range(player)
            dodge_chance = monster_stats["stats"]["A"] * 0.02  # Access nested stats
            crit_chance = player.stats["A"] * 0.02
            damage = random.uniform(min_dmg, max_dmg)
            if random.random() < dodge_chance:
                print(f"{name} dodges your attack!")
            else:
                if random.random() < crit_chance:
                    damage *= 1.5
                    print("Critical hit!")
                monster_hp -= damage
                print(f"You deal {round(damage, 1)} damage to {name}!")
            time.sleep(0.5)

        elif choice == "2":
            if not player.inventory:
                print("No items available!")
                time.sleep(0.5)
                continue
            print("\nInventory:", ", ".join(player.inventory))
            item = input("Select item (or 'back'): ")
            if item == "back":
                continue
            if item in player.inventory:
                if not use_item(player, item, monster_stats):
                    print(f"{item} cannot be used here!")
                    time.sleep(0.5)
                    continue
                # Simplified effect handling (adjust as needed)
                if "effects" in monster_stats and monster_stats["effects"]:
                    for effect, turns in list(monster_stats["effects"].items()):
                        if turns > 0:
                            monster_hp -= 5  # Example damage from items
                            monster_stats["effects"][effect] -= 1
                            if monster_stats["effects"][effect] <= 0:
                                del monster_stats["effects"][effect]
                print(f"Used {item}!")
                time.sleep(0.5)
            else:
                print("Item not found!")
                time.sleep(0.5)
                continue

        elif choice == "3":
            flee_chance = 0.5 + (player.stats["A"] - monster_stats["stats"]["A"]) * 0.05
            if random.random() < flee_chance:
                print("You flee successfully!")
                time.sleep(0.5)
                return "Fled"
            else:
                print("You fail to flee!")
                time.sleep(0.5)

        elif choice == "4" and player.level >= 5:
            if not player.skills:
                print("No skills available!")
                time.sleep(0.5)
                continue
            print("\nSkills:", ", ".join(player.skills))
            skill_choice = input("Select skill (or 'back'): ")
            if skill_choice == "back":
                continue
            if skill_choice in player.skills:
                skills = load_file("skills.txt")
                for skill in skills:
                    parts = skill[1:-1].split()
                    if parts[2] == skill_choice:
                        mp_cost = int(parts[5])
                        if player.mp < mp_cost:
                            print("Not enough MP!")
                            time.sleep(0.5)
                            break
                        player.mp -= mp_cost
                        base_dmg = int(parts[3])
                        effect = parts[4]
                        duration = int(parts[6])
                        stat = parts[7]
                        scaled_dmg = base_dmg
                        if stat != "none":
                            if effect == "damage_bonus":
                                scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                            elif effect == "direct_damage":
                                scaled_dmg = base_dmg + int(player.stats[stat] * 1.0)
                            elif effect == "heal":
                                scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                            elif effect == "damage_over_time":
                                scaled_dmg = base_dmg + int(player.stats[stat] * 0.2)

                        if effect == "damage_bonus":
                            player.skill_effects[skill_choice] = duration
                            print(f"{skill_choice} activated! +{scaled_dmg} damage for {duration} turns.")
                        elif effect == "direct_damage":
                            monster_hp -= scaled_dmg
                            print(f"{skill_choice} deals {scaled_dmg} damage to {name}!")
                        elif effect == "heal":
                            player.hp = min(player.hp + scaled_dmg, player.max_hp)
                            print(f"{skill_choice} heals you for {scaled_dmg} HP!")
                        elif effect == "damage_over_time":
                            player.skill_effects[skill_choice] = duration
                            print(f"{skill_choice} applies {scaled_dmg} damage per turn to {name} for {duration} turns!")
                            monster_hp -= scaled_dmg
                        time.sleep(0.5)
                        break
                else:
                    print("Skill not found!")
                    time.sleep(0.5)
            else:
                print("Invalid skill!")
                time.sleep(0.5)
                continue

        else:
            print("Invalid choice!")
            time.sleep(0.5)
            continue

        # Monster turn
        if monster_hp > 0:
            dodge_chance = player.stats["A"] * 0.02
            damage = random.uniform(monster_min_dmg, monster_max_dmg)
            if random.random() < dodge_chance:
                print(f"You dodge {name}'s attack!")
            else:
                player.hp -= damage
                print(f"{name} deals {round(damage, 1)} damage to you!")
            time.sleep(0.5)

            # Apply damage-over-time effects
            for skill_name, turns in list(player.skill_effects.items()):
                if turns > 0 and "damage_over_time" in skill_name.lower():
                    skills = load_file("skills.txt")
                    for skill in skills:
                        parts = skill[1:-1].split()
                        if parts[2] == skill_name:
                            base_dmg = int(parts[3])
                            stat = parts[7]
                            dot_dmg = base_dmg + (int(player.stats[stat] * 0.2) if stat != "none" else 0)
                            monster_hp -= dot_dmg
                            print(f"{skill_name} deals {dot_dmg} damage to {name}!")
                            time.sleep(0.5)
                            break

    if player.hp <= 0:
        return "Defeat"
    elif monster_hp <= 0:
        xp = monster_stats["level"] * 10 * (1.5 if boss_fight else 1)
        gold = random.randint(monster_stats["level"] * 2, monster_stats["level"] * 5) * (2 if boss_fight else 1)
        if random.random() < monster_stats["gold_chance"]:
            player.gold += gold
        player.pending_xp += xp
        print(f"\nVictory! Gained {xp} XP and {gold} gold!")
        time.sleep(0.5)
        return "Victory"