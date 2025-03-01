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
        weapon_name, stats, scaling_stat, armor_value = weapon  # Unpack the tuple
        for g in load_file("gear.txt"):
            if '[' in g:
                gear_name, bracket_part = g.split('[', 1)
                gear_name = gear_name.strip()
                bracket = bracket_part.rstrip(']').split()
                if gear_name == weapon_name:
                    if bracket[-1] == "[R]":
                        bracket.pop()
                    damage = bracket[4]  # e.g., "1-3" or "none"
                    if damage != "none":
                        try:
                            min_dmg, max_dmg = map(float, damage.split("-"))
                            # Sum scaling from all stats in the item
                            stat_bonus = 0
                            for stat, value in stats.items():
                                if value > 0:  # Only scale if the stat has a bonus
                                    stat_bonus += player.stats[stat] * 0.5
                            return (min_dmg + stat_bonus + damage_bonus, max_dmg + stat_bonus + damage_bonus)
                        except ValueError:
                            pass  # Silently fall back if parsing fails
    return (1 + damage_bonus, 2 + damage_bonus)

def parse_monster(monster_line):
    parts = monster_line.split()
    if len(parts) < 5:
        print(f"Warning: Invalid monster format: '{monster_line}'")
        return {"name": "Unknown", "stats": {"S": 1, "A": 1, "I": 1, "W": 1, "L": 1}, "level_range": (1, 1), "hp": 10, "mp": 2, "min_dmg": 1, "max_dmg": 2, "gold_chance": 0.5, "spawn_chance": 1.0, "armor_value": 0}
    
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
        return {"name": name, "stats": {"S": 1, "A": 1, "I": 1, "W": 1, "L": 1}, "level_range": (1, 1), "hp": 10, "mp": 2, "min_dmg": 1, "max_dmg": 2, "gold_chance": 0.5, "spawn_chance": 1.0, "armor_value": 0}
    
    stats_str = parts[stats_index]
    level_range = parts[stats_index + 1]
    damage_range = parts[stats_index + 2]
    
    # Adjusted parsing for optional spawn_chance and required gold_chance + new armor_value
    spawn_chance_part = None
    gold_chance = None
    armor_value = 0  # Default armor value
    if len(parts) > stats_index + 3:
        if parts[stats_index + 3].endswith("%") and not parts[stats_index + 3].startswith("G:"):
            spawn_chance_part = parts[stats_index + 3]
            gold_chance = parts[stats_index + 4] if len(parts) > stats_index + 4 else "G:50%"
        else:
            gold_chance = parts[stats_index + 3]
        if len(parts) > stats_index + 4 and parts[stats_index + 4].startswith("AV:"):
            armor_value = parts[stats_index + 4]
        elif len(parts) > stats_index + 5 and parts[stats_index + 5].startswith("AV:"):
            armor_value = parts[stats_index + 5]

    stats = parse_stats(stats_str, is_consumable=False)
    min_level, max_level = map(int, level_range[2:].split("-"))
    min_dmg, max_dmg = map(float, damage_range[2:].split("-"))
    
    if spawn_chance_part and spawn_chance_part.endswith("%"):
        try:
            spawn_chance = float(spawn_chance_part[:-1]) / 100
        except ValueError as e:
            print(f"Error parsing spawn chance '{spawn_chance_part}' in '{monster_line}': {e}. Using default 1.0.")
            spawn_chance = 1.0
    else:
        spawn_chance = 1.0
    
    try:
        if not gold_chance.startswith("G:") or gold_chance[-1] != "%":
            raise ValueError("Invalid gold chance format")
        gold_chance_value = gold_chance[2:-1]
        if not gold_chance_value:
            raise ValueError("Gold chance is empty")
        gold_chance = float(gold_chance_value) / 100
    except (ValueError, IndexError) as e:
        print(f"Error parsing gold chance '{gold_chance}' in '{monster_line}': {e}. Using default 0.5.")
        gold_chance = 0.5
    
    # Parse armor value
    try:
        if armor_value and armor_value.startswith("AV:"):
            armor_value = int(armor_value[3:])
            if not (0 <= armor_value <= 100):
                raise ValueError("Armor value must be between 0 and 100")
        else:
            armor_value = 0
    except (ValueError, IndexError) as e:
        print(f"Error parsing armor value '{armor_value}' in '{monster_line}': {e}. Using default 0.")
        armor_value = 0

    hp = 10 + 2 * stats["S"]
    mp = 2 * stats["W"]
    
    return {
        "name": name,
        "stats": stats,
        "level_range": (min_level, max_level),
        "hp": hp,
        "mp": mp,
        "min_dmg": min_dmg,
        "max_dmg": max_dmg,
        "gold_chance": gold_chance,
        "spawn_chance": spawn_chance,
        "armor_value": armor_value  # New field
    }

def combat(player, boss_fight=False):
    monsters = load_file("monsters.txt")
    
    boss_monsters = []
    regular_monsters = []
    special_monsters = []  # New list for special monsters
    is_boss_section = False
    is_special_section = False
    for monster in monsters:
        if monster.startswith("# Boss Monsters"):
            is_boss_section = True
            is_special_section = False
        elif monster.startswith("# Regular Monsters"):
            is_boss_section = False
            is_special_section = False
        elif monster.startswith("# Special Monsters"):
            is_boss_section = False
            is_special_section = True
        elif monster.strip():
            if is_boss_section:
                boss_monsters.append(monster)
            elif is_special_section:
                special_monsters.append(monster)
            else:
                regular_monsters.append(monster)
    
    monster_pool = boss_monsters if boss_fight else regular_monsters
    if not monster_pool:
        print(f"Warning: No {'boss' if boss_fight else 'regular'} monsters found!")
        monster_pool = ["[Fallback] S1A1I1W1L1 L:1-1 D:1-2 G:50%]"]
    
    parsed_monsters = [parse_monster(m) for m in monster_pool]
    valid_monsters = [m for m in parsed_monsters if m["level_range"][0] <= player.level <= m["level_range"][1]]
    
    if not valid_monsters:
        print(f"No suitable {'boss' if boss_fight else 'regular'} monsters for level {player.level}. Using fallback.")
        valid_monsters = [parse_monster(monster_pool[0])]
    
    if not boss_fight:  # Only apply special monster chance for regular encounters
        if random.random() < 0.01:  # 1% chance for a special monster to spawn
            if not special_monsters:
                print("Warning: No special monsters defined! Falling back to regular monster.")
                monster = random.choices(
                    valid_monsters,
                    weights=[m["spawn_chance"] for m in valid_monsters],
                    k=1
                )[0]
            else:
                parsed_specials = [parse_monster(m) for m in special_monsters]
                monster = random.choices(
                    parsed_specials,
                    weights=[m["spawn_chance"] for m in parsed_specials],
                    k=1
                )[0]
        else:
            # Existing random.choices logic for regular monsters
            monster = random.choices(
                valid_monsters,
                weights=[m["spawn_chance"] for m in valid_monsters],
                k=1
            )[0]
    else:
        # For boss fights, use random.choice as before
        monster = random.choice(valid_monsters)
    
    monster_stats = monster
    level = random.randint(monster_stats["level_range"][0], monster_stats["level_range"][1])
    
    level_scale = 1 + (level - 1) * 0.05 if not boss_fight else 1 + (level - 1) * 0.1
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
            dodge_chance = monster_stats["stats"]["A"] * 0.02
            crit_chance = player.stats["A"] * 0.02
            damage = random.uniform(min_dmg, max_dmg)
            if random.random() < dodge_chance:
                print(f"{name} dodges your attack!")
            else:
                if random.random() < crit_chance:
                    damage *= 1.5
                    print("Critical hit!")
                # Apply monster armor reduction
                armor_reduction = monster_stats["armor_value"] / 100
                reduced_damage = damage * (1 - armor_reduction)
                monster_hp -= reduced_damage
                if damage != reduced_damage:
                    print(f"You deal {round(reduced_damage, 1)} damage to {name} (reduced from {round(damage, 1)} by armor)!")
                else:
                    print(f"You deal {round(reduced_damage, 1)} damage to {name}!")
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
                if "effects" in monster_stats and monster_stats["effects"]:
                    for effect, turns in list(monster_stats["effects"].items()):
                        if turns > 0:
                            monster_hp -= 5
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
                print("You flee successfully, ending your adventure!")
                time.sleep(0.5)
                return "FleeAdventure"
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

        if monster_hp > 0:
            dodge_chance = player.stats["A"] * 0.02
            damage = random.uniform(monster_min_dmg, monster_max_dmg)
            if random.random() < dodge_chance:
                print(f"You dodge {name}'s attack!")
            else:
                armor_reduction = player.get_total_armor_value() / 100
                reduced_damage = damage * (1 - armor_reduction)
                player.hp -= reduced_damage
                print(f"{name} deals {round(reduced_damage, 1)} damage to you (reduced from {round(damage, 1)} by armor)!")
            time.sleep(0.5)

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
        xp = level * 10 * (1.5 if boss_fight else 1)
        gold = random.randint(level * 2, level * 5) * (2 if boss_fight else 1)
        if random.random() < monster_stats["gold_chance"]:
            player.gold += gold
        player.pending_xp += xp
        print(f"\nVictory! Gained {xp} XP and {gold} gold!")
        time.sleep(0.5)
        return "Victory"