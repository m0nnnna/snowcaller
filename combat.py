import random
import time
import json
import os
from utils import load_json, parse_stats
from items import use_item

def load_art(art_file):
    art_path = os.path.join("art", art_file)
    if os.path.exists(art_path):
        with open(art_path, "r") as f:
            return f.read()
    return None  # Return None if file doesn’t exist, no error message

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
        gear_data = load_json("gear.json")
        weapon_data = next((g for g in gear_data if g["name"] == weapon_name and g["slot"] == "main_hand"), None)
        if weapon_data and weapon_data["damage"]:
            try:
                min_dmg, max_dmg = map(float, weapon_data["damage"].split("-"))
                # Use the modifier to scale damage with the player's stat
                stat_bonus = player.stats[modifier] * 0.5  # Scale by 0.5 per point of the modifier stat
                # Add any additional bonuses from the weapon's own stats (if applicable)
                for stat, value in stats.items():
                    if value > 0:
                        stat_bonus += player.stats[stat] * 0.5
                return (min_dmg + stat_bonus + damage_bonus, max_dmg + stat_bonus + damage_bonus)
            except (ValueError, AttributeError):
                pass
    
    return (1 + damage_bonus, 2 + damage_bonus)

def load_monster_from_json(monster_name=None, boss_fight=False, player_level=None):
    monsters = load_json("monster.json")["monsters"]
    
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
    
    # Monster skill setup
    monster_skills = monster_stats.get("skills", []) if monster_stats.get("skills") is not None else []
    monster_skill_effects = {}
    monster_status = {"sleep": 0, "curse": 0}  # Track status effects

    # Player status setup
    player_status = {"curse": 0}  # Only curse affects players for now

    # Temporary bonuses
    player_armor_bonus = 0
    player_dodge_bonus = 0
    monster_armor_bonus = 0
    monster_dodge_bonus = 0
    
    # Display monster appearance with optional art
    print(f"\nA {name} appears!")
    if "art_file" in monster_stats:
        art = load_art(monster_stats["art_file"])
        if art:
            print(art)
    print(f"HP: {round(monster_hp, 1)}")

    while monster_hp > 0 and player.hp > 0:
        # Player skill effect durations
        for skill_name, turns in list(player.skill_effects.items()):
            if turns > 0:
                player.skill_effects[skill_name] -= 1
                if player.skill_effects[skill_name] == 0:
                    del player.skill_effects[skill_name]
                    print(f"{skill_name} effect has worn off!")
                    if skill_name in ["Iron Skin", "Nimble Step"]:  # Reset bonuses
                        if skill_name == "Iron Skin":
                            player_armor_bonus = 0
                        elif skill_name == "Nimble Step":
                            player_dodge_bonus = 0

        # Monster skill effect durations
        for skill_name, turns in list(monster_skill_effects.items()):
            if turns > 0:
                monster_skill_effects[skill_name] -= 1
                if monster_skill_effects[skill_name] == 0:
                    del monster_skill_effects[skill_name]
                    print(f"{name}'s {skill_name} effect has worn off!")
                    if skill_name in ["Iron Skin", "Nimble Step"]:
                        if skill_name == "Iron Skin":
                            monster_armor_bonus = 0
                        elif skill_name == "Nimble Step":
                            monster_dodge_bonus = 0

        # Status effect durations
        for status, turns in list(player_status.items()):
            if turns > 0:
                player_status[status] -= 1
                if player_status[status] == 0:
                    del player_status[status]
                    print(f"Your {status} has lifted!")

        for status, turns in list(monster_status.items()):
            if turns > 0:
                monster_status[status] -= 1
                if monster_status[status] == 0:
                    del monster_status[status]
                    print(f"{name} wakes up from {status}!")

        # Player damage bonus display
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
        status_display = f" | Status: {', '.join([f'{k} {v}' for k, v in player_status.items()])}" if player_status else ""
        print(f"\n{monster_stats['name']}: {round(monster_hp, 1)} HP | {player.name}: {round(player.hp, 1)}/{player.max_hp} HP, {player.mp}/{player.max_mp} MP{bonus_display}{status_display}")
        print("1. Attack | 2. Item | 3. Skills | 4. Flee")
        choice = input("Selection: ")

        if choice == "1":  # Attack
            min_dmg, max_dmg = get_weapon_damage_range(player)
            dodge_chance = (monster_stats["stats"]["A"] * 0.02) + (monster_dodge_bonus / 100)
            crit_chance = player.stats["A"] * 0.02
            damage = random.uniform(min_dmg, max_dmg)
            if random.random() < dodge_chance:
                print(f"{name} dodges your attack!")
            else:
                if random.random() < crit_chance:
                    damage *= 1.5
                    print("Critical hit!")
                armor_reduction = (monster_stats["armor_value"] + monster_armor_bonus) / 100
                reduced_damage = damage * (1 - armor_reduction)
                monster_hp -= reduced_damage
                if damage != reduced_damage:
                    print(f"You deal {round(reduced_damage, 1)} damage to {name} (reduced from {round(damage, 1)} by armor)!")
                else:
                    print(f"You deal {round(reduced_damage, 1)} damage to {name}!")

        elif choice == "2":  # Item
            if not player.inventory:
                print("No items available!")
                continue
            print("\nInventory:", ", ".join(player.inventory))
            item = input("Select item (or 'back'): ")
            if item == "back":
                continue
            if item in player.inventory:
                if not use_item(player, item, monster_stats):
                    print(f"{item} cannot be used here!")
                    continue
                if "effects" in monster_stats and monster_stats["effects"]:
                    for effect, turns in list(monster_stats["effects"].items()):
                        if turns > 0:
                            monster_hp -= 5
                            monster_stats["effects"][effect] -= 1
                            if monster_stats["effects"][effect] <= 0:
                                del monster_stats["effects"][effect]
                print(f"Used {item}!")
            else:
                print("Item not found!")
                continue

        elif choice == "3":  # Skills
            if not player.skills or player_status.get("curse", 0) > 0:
                print("No skills available!" if not player.skills else "You are cursed and cannot use skills!")
                continue
            print("\nAvailable Skills:")
            for i, skill_name in enumerate(player.skills, 1):
                print(f"{i}. {skill_name}")
            print("0. Back")
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
                                elif effect == "heal" or effect == "heal_over_time":
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                                elif effect == "damage_over_time":
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.2)
                                elif effect in ["armor_bonus", "dodge_bonus"]:
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)

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
                            elif effect == "heal_over_time":
                                player.skill_effects[skill_name] = duration
                                print(f"{skill_name} restores {scaled_dmg} HP per turn for {duration} turns!")
                            elif effect == "armor_bonus":
                                player.skill_effects[skill_name] = duration
                                player_armor_bonus = scaled_dmg
                                print(f"{skill_name} increases your armor by {scaled_dmg}% for {duration} turns!")
                            elif effect == "dodge_bonus":
                                player.skill_effects[skill_name] = duration
                                player_dodge_bonus = scaled_dmg
                                print(f"{skill_name} increases your dodge chance by {scaled_dmg}% for {duration} turns!")
                            elif effect == "sleep":
                                breakout_chance = max(0.1, min(0.5, monster_stats["stats"]["I"] * 0.05 - player.stats["I"] * 0.02))
                                if random.random() > breakout_chance:
                                    monster_status["sleep"] = min(duration, 5)
                                    print(f"{skill_name} puts {name} to sleep for up to {duration} turns!")
                                else:
                                    print(f"{name} resists {skill_name}!")
                            elif effect == "curse":
                                monster_status["curse"] = duration
                                print(f"{skill_name} curses {name}, blocking skills for {duration} turns!")
                            break
                    if not skill_found:
                        print(f"Skill '{skill_name}' not found in skills.json!")
                else:
                    print("Invalid skill number!")
            except ValueError as e:
                print(f"ValueError occurred: {e}")
            continue

        elif choice == "4":  # Flee
            flee_chance = 0.5 + (player.stats["A"] - monster_stats["stats"]["A"]) * 0.05
            if random.random() < flee_chance:
                print("You flee successfully, ending your adventure!")
                return "FleeAdventure"
            else:
                print("You fail to flee!")

        # Monster's turn
        if monster_hp > 0:
            if monster_status.get("sleep", 0) > 0:
                breakout_chance = monster_stats["stats"]["I"] * 0.05
                if random.random() < breakout_chance:
                    del monster_status["sleep"]
                    print(f"{name} breaks free from sleep!")
                else:
                    print(f"{name} is asleep and cannot act!")
            elif monster_skills and monster_mp > 0 and not monster_status.get("curse", 0) > 0:
                skills = load_json("skills.json")["skills"]
                for skill in skills:
                    if (skill["name"] in monster_skills and skill["class_type"] == "monster" and 
                        skill["mp_cost"] <= monster_mp and random.random() < 0.5):
                        monster_mp -= skill["mp_cost"]
                        base_dmg = skill["base_dmg"]
                        duration = skill["duration"]
                        effect = skill["effect"]
                        stat = skill["stat"]
                        scaled_dmg = base_dmg
                        if stat != "none":
                            if effect == "damage_bonus":
                                scaled_dmg = base_dmg + int(monster_stats["stats"][stat] * 0.5)
                            elif effect == "direct_damage":
                                scaled_dmg = base_dmg + int(monster_stats["stats"][stat] * 1.0)
                            elif effect == "damage_over_time":
                                scaled_dmg = base_dmg + int(monster_stats["stats"][stat] * 0.2)
                            elif effect in ["armor_bonus", "dodge_bonus"]:
                                scaled_dmg = base_dmg + int(monster_stats["stats"][stat] * 0.5)

                        if effect == "damage_bonus":
                            monster_skill_effects[skill["name"]] = duration
                            print(f"{name} uses {skill['name']}! +{scaled_dmg} damage for {duration} turns.")
                        elif effect == "direct_damage":
                            player.hp -= scaled_dmg
                            print(f"{name} uses {skill['name']}, dealing {scaled_dmg} damage to you!")
                        elif effect == "damage_over_time":
                            monster_skill_effects[skill["name"]] = duration
                            player.hp -= scaled_dmg
                            print(f"{name} uses {skill['name']}, applying {scaled_dmg} damage per turn for {duration} turns!")
                        elif effect == "armor_bonus":
                            monster_skill_effects[skill["name"]] = duration
                            monster_armor_bonus = scaled_dmg
                            print(f"{name} uses {skill['name']}, increasing armor by {scaled_dmg}% for {duration} turns!")
                        elif effect == "dodge_bonus":
                            monster_skill_effects[skill["name"]] = duration
                            monster_dodge_bonus = scaled_dmg
                            print(f"{name} uses {skill['name']}, increasing dodge chance by {scaled_dmg}% for {duration} turns!")
                        elif effect == "curse":
                            player_status["curse"] = duration
                            print(f"{name} uses {skill['name']}, cursing you and blocking skills for {duration} turns!")
                        break
                else:
                    # Basic attack if no skill used
                    dodge_chance = (player.stats["A"] * 0.02) + (player_dodge_bonus / 100)
                    monster_bonus = sum(
                        base_dmg + int(monster_stats["stats"][stat] * 0.5)
                        for s_name, turns in monster_skill_effects.items()
                        for s in skills
                        if s["name"] == s_name and s["effect"] == "damage_bonus" and turns > 0
                    )
                    damage = random.uniform(monster_min_dmg, monster_max_dmg) + monster_bonus
                    if random.random() < dodge_chance:
                        print(f"You dodge {name}'s attack!")
                    else:
                        armor_reduction = (player.get_total_armor_value() + player_armor_bonus) / 100
                        reduced_damage = damage * (1 - armor_reduction)
                        player.hp -= reduced_damage
                        print(f"{name} deals {round(reduced_damage, 1)} damage to you (reduced from {round(damage, 1)} by armor)!")
            else:
                # Basic attack with skill bonus
                dodge_chance = (player.stats["A"] * 0.02) + (player_dodge_bonus / 100)
                monster_bonus = sum(
                    base_dmg + int(monster_stats["stats"][stat] * 0.5)
                    for s_name, turns in monster_skill_effects.items()
                    for s in skills
                    if s["name"] == s_name and s["effect"] == "damage_bonus" and turns > 0
                )
                damage = random.uniform(monster_min_dmg, monster_max_dmg) + monster_bonus
                if random.random() < dodge_chance:
                    print(f"You dodge {name}'s attack!")
                else:
                    armor_reduction = (player.get_total_armor_value() + player_armor_bonus) / 100
                    reduced_damage = damage * (1 - armor_reduction)
                    player.hp -= reduced_damage
                    print(f"{name} deals {round(reduced_damage, 1)} damage to you (reduced from {round(damage, 1)} by armor)!")

            # Apply monster damage-over-time effects to player
            for skill_name, turns in list(monster_skill_effects.items()):
                if turns > 0:
                    for skill in skills:
                        if skill["name"] == skill_name and skill["effect"] == "damage_over_time":
                            base_dmg = skill["base_dmg"]
                            stat = skill["stat"]
                            dot_dmg = base_dmg + (int(monster_stats["stats"][stat] * 0.2) if stat != "none" else 0)
                            player.hp -= dot_dmg
                            print(f"{name}'s {skill_name} deals {dot_dmg} damage to you!")
                            break

            # Apply player effects: DOT and HOT to monster/player
            for skill_name, turns in list(player.skill_effects.items()):
                if turns > 0:
                    for skill in skills:
                        if skill["name"] == skill_name:
                            base_dmg = skill["base_dmg"]
                            stat = skill["stat"]
                            scaled_dmg = base_dmg + (int(player.stats[stat] * (0.2 if skill["effect"] == "damage_over_time" else 0.5)) if stat != "none" else 0)
                            if skill["effect"] == "damage_over_time":
                                monster_hp -= scaled_dmg
                                print(f"{skill_name} deals {scaled_dmg} damage to {name}!")
                            elif skill["effect"] == "heal_over_time":
                                player.hp = min(player.hp + scaled_dmg, player.max_hp)
                                print(f"{skill_name} heals you for {scaled_dmg} HP!")
                            break

    # Combat resolution
    if player.hp <= 0:
        return "Defeat"
    elif monster_hp <= 0:
        xp = level * 2 * (1.5 if monster_stats["rare"] or boss_fight else 1)
        gold = random.randint(level * 2, level * 5) * (2 if monster_stats["rare"] or boss_fight else 1)
        if random.random() < monster_stats["gold_chance"] / 100:
            player.gold += gold
        player.pending_xp += xp
        
        # Update quest kill counts
        quests = load_json("quest.json")["quests"]
        for quest in player.active_quests[:]:
            quest_data = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
            if quest_data:
                for stage in quest["stages"]:
                    if stage["type"] in ["kill", "boss"]:
                        if "kill_count" not in stage:
                            stage["kill_count"] = 0
                        if stage["target_monster"] in monster_stats["name"]:
                            stage["kill_count"] = min(stage["kill_count"] + 1, stage["kill_count_required"])
                            print(f"Quest '{quest['quest_name']}': {stage['target_monster']} killed ({stage['kill_count']}/{stage['kill_count_required']})")

        # Handle key item drops tied to active quests
        key_items = load_json("keyitems.json")["key_items"]
        for item in key_items:
            if item["drop_from"] in monster_stats["name"] and item["quest"] in [q["quest_name"] for q in player.active_quests]:
                for quest in player.active_quests:
                    if quest["quest_name"] == item["quest"]:
                        kill_stages = [s for s in quest["stages"] if s["type"] in ["kill", "boss"] and s["target_monster"] in monster_stats["name"]]
                        collect_stage = next((s for s in quest["stages"] if s["type"] == "collect" and s["target_item"] == item["name"]), None)
                        if kill_stages and collect_stage:
                            if "item_count" not in collect_stage:
                                collect_stage["item_count"] = 0
                            all_kills_done = all(s["kill_count"] >= quest_data["stages"][quest["stages"].index(s)]["kill_count_required"] for s in kill_stages)
                            if all_kills_done and collect_stage["item_count"] < quest_data["stages"][quest["stages"].index(collect_stage)]["item_count_required"]:
                                player.inventory.append(item["name"])
                                print(f"You found a {item['name']}! {item['description']}")
                            elif random.random() < item["drop_chance"] / 100 and item["name"] not in player.inventory:
                                player.inventory.append(item["name"])
                                print(f"You found a {item['name']}! {item['description']}")
                            collect_stage["item_count"] = player.inventory.count(item["name"])
                            if collect_stage["item_count"] > 0:
                                print(f"Quest '{quest['quest_name']}': {item['name']} collected ({collect_stage['item_count']}/{quest_data['stages'][quest['stages'].index(collect_stage)]['item_count_required']})")

        # Check quest progress (do not complete here)
        for quest in player.active_quests[:]:
            quest_data = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
            if quest_data:
                all_stages_complete = True
                for i, stage in enumerate(quest["stages"]):
                    if stage["type"] in ["kill", "boss"]:
                        if "kill_count" not in stage or stage["kill_count"] < quest_data["stages"][i]["kill_count_required"]:
                            all_stages_complete = False
                            break
                    elif stage["type"] == "collect":
                        if "item_count" not in stage or stage["item_count"] < quest_data["stages"][i]["item_count_required"]:
                            all_stages_complete = False
                            break
                    elif stage["type"] not in ["kill", "boss", "collect"]:
                        all_stages_complete = False
                        print(f"Warning: Unknown stage type '{stage['type']}' in quest '{quest['quest_name']}'")
                if all_stages_complete:
                    print(f"Quest '{quest['quest_name']}' objectives met! Return to the tavern to turn it in.")
                    if quest_data["npc_trigger"] and quest_data["npc_trigger"] not in [n["name"] for n in player.tavern_npcs]:
                        trigger_npc_event(player, quest_data["npc_trigger"])
        
        print(f"\nVictory! Gained {xp} XP and {gold} gold!")
        return f"Victory against {monster_stats['name']}"

def trigger_npc_event(player, npc_name):
    """Trigger special NPC appearance based on event, quest, or item."""
    if not hasattr(player, "tavern_npcs"):
        player.tavern_npcs = []
    if npc_name and npc_name not in [n["name"] for n in player.tavern_npcs]:
        player.tavern_npcs.append({"name": npc_name, "room": False})
        print(f"{npc_name} has appeared at the tavern!")