import random
import time
import json
from utils import load_json, parse_stats  # Removed load_file since we’re not using skills.txt
from items import use_item

def get_weapon_damage_range(player):
    weapon = player.equipment.get("main_hand")
    damage_bonus = 0
    if "Rage" in player.skill_effects:
        skills = load_json("skills.json")["skills"]
        for skill in skills:
            if skill["name"] == "Rage":
                base_dmg = skill["base_dmg"]
                stat = skill["stat"]
                damage_bonus = base_dmg + (int(player.stats[stat] * 0.5) if stat != "none" else 0)
                break
    
    if weapon:
        weapon_name, stats, modifier, armor_value = weapon
        gear_data = load_json("gear.json")  # Use load_json instead of with open
        weapon_data = next((g for g in gear_data if g["name"] == weapon_name and g["slot"] == "main_hand"), None)
        if weapon_data and weapon_data["damage"]:
            try:
                min_dmg, max_dmg = map(float, weapon_data["damage"].split("-"))
                stat_bonus = 0
                for stat, value in stats.items():
                    if value > 0:
                        stat_bonus += player.stats[stat] * 0.5
                return (min_dmg + stat_bonus + damage_bonus, max_dmg + stat_bonus + damage_bonus)
            except (ValueError, AttributeError):
                pass
    
    return (1 + damage_bonus, 2 + damage_bonus)

def load_monster_from_json(monster_name=None, boss_fight=False, player_level=None):
    monsters = load_json("monster.json")["monsters"]  # Use load_json instead of with open
    
    if monster_name:
        monster = next((m for m in monsters if m["name"] == monster_name), None)
        if not monster:
            print(f"Warning: Monster '{monster_name}' not found in monster.json. Using fallback.")
            monster = monsters[0]
    else:
        pool = [m for m in monsters if m["rare"] == boss_fight]
        if not pool:
            print(f"Warning: No {'rare' if boss_fight else 'regular'} monsters found. Using full pool.")
            pool = monsters
        monster = random.choices(pool, weights=[m["spawn_chance"] for m in pool], k=1)[0]
    
    return monster

def combat(player, boss_fight=False, monster_name=None):
    monster_stats = load_monster_from_json(monster_name, boss_fight, player.level)
    
    is_quest_boss = monster_stats["spawn_chance"] == 0
    if not is_quest_boss:
        base_min = monster_stats["level_range"]["min"]
        base_max = monster_stats["level_range"]["max"]
        min_level = max(base_min, player.level - 2)
        max_level = min(base_max, player.level + 2)
        if min_level > max_level:
            min_level, max_level = max_level, min_level
    else:
        min_level = monster_stats["level_range"]["min"]
        max_level = monster_stats["level_range"]["max"]
    
    level = random.randint(min_level, max_level)
    level_scale = 1 + (level - 1) * 0.1 if monster_stats["rare"] else 1 + (level - 1) * 0.05
    monster_hp = random.uniform(monster_stats["hp_range"]["min"], monster_stats["hp_range"]["max"]) * level_scale
    monster_mp = 2 * monster_stats["stats"]["W"] * level_scale
    monster_min_dmg = monster_stats["damage_range"]["min"] * level_scale
    monster_max_dmg = monster_stats["damage_range"]["max"] * level_scale
    
    if monster_stats["rare"] or boss_fight:
        monster_hp *= 1.5
        monster_min_dmg *= 1.2
        monster_max_dmg *= 1.2
        name = "Boss " + monster_stats["name"] if not monster_stats["rare"] else monster_stats["name"]
    else:
        name = monster_stats["name"]
    
    print(f"\nA {name} appears! HP: {round(monster_hp, 1)}")
    time.sleep(0.5)

    while monster_hp > 0 and player.hp > 0:
        # Handle skill effect durations
        for skill_name, turns in list(player.skill_effects.items()):
            if turns > 0:
                player.skill_effects[skill_name] -= 1
                if player.skill_effects[skill_name] == 0:
                    del player.skill_effects[skill_name]
                    print(f"{skill_name} effect has worn off!")
                    time.sleep(0.5)

        # Calculate damage bonus display
        bonus_display = ""
        skills = load_json("skills.json")["skills"]
        total_dmg_bonus = 0
        for skill_name, turns in player.skill_effects.items():
            if turns > 0:
                for skill in skills:
                    if skill["name"] == skill_name and skill["effect"] == "damage_bonus":
                        base_dmg = skill["base_dmg"]
                        stat = skill["stat"]
                        scaled_dmg = base_dmg + (int(player.stats[stat] * 0.5) if stat != "none" else 0)
                        total_dmg_bonus += scaled_dmg
                        break
        if total_dmg_bonus > 0:
            bonus_display = f" | Bonus: +{total_dmg_bonus} dmg ({', '.join([f'{k} {v}' for k, v in player.skill_effects.items()])})"

        # Combat UI
        print(f"\n{monster_stats['name']}: {round(monster_hp, 1)} HP | {player.name}: {round(player.hp, 1)}/{player.max_hp} HP, {player.mp}/{player.max_mp} MP{bonus_display}")
        print("1. Attack | 2. Item | 3. Skills | 4. Flee")
        time.sleep(0.5)
        choice = input("Selection: ")

        if choice == "1":  # Attack
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
                armor_reduction = monster_stats["armor_value"] / 100
                reduced_damage = damage * (1 - armor_reduction)
                monster_hp -= reduced_damage
                if damage != reduced_damage:
                    print(f"You deal {round(reduced_damage, 1)} damage to {name} (reduced from {round(damage, 1)} by armor)!")
                else:
                    print(f"You deal {round(reduced_damage, 1)} damage to {name}!")
            time.sleep(0.5)

        elif choice == "2":  # Item
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

        elif choice == "3":  # Skills
            if not player.skills:
                print("No skills available!")
                time.sleep(0.5)
                continue
            print("\nAvailable Skills:")
            for i, skill_name in enumerate(player.skills, 1):
                print(f"{i}. {skill_name}")
            print("0. Back")
            time.sleep(0.5)
            skill_choice = input("Select skill number (0 to back): ")
            try:
                skill_idx = int(skill_choice)
                if skill_idx == 0:
                    continue
                if 1 <= skill_idx <= len(player.skills):
                    skill_name = player.skills[skill_idx - 1]
                    skills = load_json("skills.json")["skills"]
                    skill_found = False
                    for skill in skills:
                        if skill["name"] == skill_name:
                            skill_found = True
                            mp_cost = skill["mp_cost"]
                            if player.mp < mp_cost:
                                print("Not enough MP!")
                                time.sleep(0.5)
                                break
                            player.mp -= mp_cost
                            base_dmg = skill["base_dmg"]
                            duration = skill["duration"]
                            effect = skill["effect"]
                            stat = skill["stat"]
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
                                player.skill_effects[skill_name] = duration
                                print(f"{skill_name} activated! +{scaled_dmg} damage for {duration} turns.")
                            elif effect == "direct_damage":
                                monster_hp -= scaled_dmg
                                print(f"{skill_name} deals {scaled_dmg} damage to {name}!")
                            elif effect == "heal":
                                player.hp = min(player.hp + scaled_dmg, player.max_hp)
                                print(f"{skill_name} heals you for {scaled_dmg} HP!")
                            elif effect == "damage_over_time":
                                player.skill_effects[skill_name] = duration
                                print(f"{skill_name} applies {scaled_dmg} damage per turn to {name} for {duration} turns!")
                                monster_hp -= scaled_dmg
                            time.sleep(0.5)
                            break
                    if not skill_found:
                        print(f"Skill '{skill_name}' not found in skills.json!")
                        time.sleep(0.5)
                else:
                    print("Invalid skill number!")
                    time.sleep(0.5)
            except ValueError as e:
                print(f"ValueError occurred: {e}")
                time.sleep(0.5)
            continue

        elif choice == "4":  # Flee
            flee_chance = 0.5 + (player.stats["A"] - monster_stats["stats"]["A"]) * 0.05
            if random.random() < flee_chance:
                print("You flee successfully, ending your adventure!")
                time.sleep(0.5)
                return "FleeAdventure"
            else:
                print("You fail to flee!")
                time.sleep(0.5)

        # Monster's turn
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

            # Apply damage-over-time effects
            for skill_name, turns in list(player.skill_effects.items()):
                if turns > 0 and "damage_over_time" in skill["effect"]:  # Check effect type
                    skills = load_json("skills.json")["skills"]
                    for skill in skills:
                        if skill["name"] == skill_name:
                            base_dmg = skill["base_dmg"]
                            stat = skill["stat"]
                            dot_dmg = base_dmg + (int(player.stats[stat] * 0.2) if stat != "none" else 0)
                            monster_hp -= dot_dmg
                            print(f"{skill_name} deals {dot_dmg} damage to {name}!")
                            time.sleep(0.5)
                            break

    # Combat resolution
    if player.hp <= 0:
        return "Defeat"
    elif monster_hp <= 0:
        xp = level * 2 * (1.5 if monster_stats["rare"] or boss_fight else 1)
        gold = random.randint(level * 2, level * 5) * (2 if monster_stats["rare"] or boss_fight else 1)
        if random.random() < monster_stats["gold_chance"]:
            player.gold += gold
        player.pending_xp += xp
        print(f"\nVictory! Gained {xp} XP and {gold} gold!")
        time.sleep(0.5)
        return f"Victory against {monster_stats['name']}"
