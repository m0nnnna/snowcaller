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
            # Check both old and new skill formats
            if skill["name"] == "Rage":
                if "effects" in skill:
                    for effect in skill["effects"]:
                        if effect["type"] == "damage_bonus":
                            base_dmg = effect["base_dmg"]
                            stat = effect["stat"]
                            damage_bonus = base_dmg + (int(player.stats[stat] * 0.5) if stat != "none" else 0)
                            break
                else:
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
                stat_bonus = player.stats[modifier] * 0.5
                for stat, value in stats.items():
                    if value > 0:
                        stat_bonus += player.stats[stat] * 0.5
                return (min_dmg + stat_bonus + damage_bonus, max_dmg + stat_bonus + damage_bonus)
            except (ValueError, AttributeError):
                pass

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
    monster_max_mp = 2 * monster_stats["stats"]["W"] * level_scale  # Moved here from line 404
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

    # Player skill effects setup
    player_skill_effects = {}

    # Temporary bonuses
    player_armor_bonus = 0
    player_dodge_bonus = 0
    monster_armor_bonus = 0
    monster_dodge_bonus = 0
    
    # Initiative
    player_initiative = (player.stats["A"] * 0.5 + player.stats["L"] * 0.5) / 100
    monster_initiative = (monster_stats["stats"]["A"] * 0.5 + monster_stats["stats"]["L"] * 0.5) / 100
    total_initiative = player_initiative + monster_initiative
    player_goes_first = random.random() < (player_initiative / total_initiative) if total_initiative > 0 else random.random() < 0.5
    print(f"{'You strike first!' if player_goes_first else f'{name} takes the initiative!'}")

    turn = "player" if player_goes_first else "monster"
    player_mp_regenerated = False  # Flag to track MP regeneration for the current player turn

    # Display monster appearance
    print(f"\nA {name} appears!")
    if "art_file" in monster_stats:
        art = load_art(monster_stats["art_file"])
        if art:
            print(art)
    print(f"HP: {round(monster_hp, 1)}")

    while monster_hp > 0 and player.hp > 0:
        # Update effects at the start of each full turn cycle (before either turn)
        for skill_name, turns in list(player.skill_effects.items()):
            # Update player skill effects (implementation needed)
            pass
        for skill_name, turns in list(monster_skill_effects.items()):
            # Update monster skill effects (implementation needed)
            pass
        for status, turns in list(player_status.items()):
            # Update player status effects (implementation needed)
            pass
        for status, turns in list(monster_status.items()):
            # Update monster status effects (implementation needed)
            pass

        if turn == "monster":
            # Monster turn
            if monster_mp < monster_max_mp:
                monster_mp_regeneration = monster_stats["stats"]["W"] * 0.3
                monster_mp = min(monster_mp + monster_mp_regeneration, monster_max_mp)

            if monster_hp > 0:
                if monster_status.get("sleep", 0) > 0:
                    breakout_chance = monster_stats["stats"]["I"] * 0.05
                    if random.random() < breakout_chance:
                        del monster_status["sleep"]
                        print(f"{name} breaks free from sleep!")
                    else:
                        print(f"{name} is asleep and cannot act!")
                elif monster_skills and monster_mp > 0 and not monster_status.get("curse", 0) > 0:
                    try:
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
                    except Exception as e:
                        print(f"ERROR: Monster skill processing failed: {e}")
                else:
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

            turn = "player"  # Switch to player turn after monster acts
            player_mp_regenerated = False  # Reset MP regen flag when switching to player turn

        # Player Turn
        elif turn == "player":
            # Regenerate MP only once per turn
            if not player_mp_regenerated and player.mp < player.max_mp:
                mp_regen = player.stats["W"] * 0.3
                player.mp = min(player.mp + mp_regen, player.max_mp)
                print(f"\nYou regenerate {round(mp_regen, 1)} MP Current MP: {round(player.mp, 1)}/{player.max_mp}")
                player_mp_regenerated = True
            elif not player_mp_regenerated:
                print(f"\nMP is full: {round(player.mp, 1)}/{player.max_mp}")
                player_mp_regenerated = True

            # Combat UI
            bonus_display = ""  # Define bonus_display as an empty string or assign its appropriate value
            status_display = f" | Status: {', '.join([f'{k} {v}' for k, v in player_status.items()])}" if player_status else ""
            print(f"\n{monster_stats['name']}: {round(monster_hp, 1)} HP | {player.name}: {round(player.hp, 1)}/{player.max_hp} HP, {round(player.mp, 1)}/{player.max_mp} MP{bonus_display}{status_display}")
            print("1. Attack | 2. Item | 3. Skills | 4. Flee")
            choice = input("Selection: ")

            action_taken = False  # Track if an action completes the turn

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
                action_taken = True

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
                    action_taken = True
                else:
                    print("Item not found!")
                    continue

            elif choice == "3":  # Skills
                if not player.skills or player_status.get("curse", 0) > 0:
                    print("No skills available!" if not player.skills else "You are cursed and cannot use skills!")
                else:
                    print("\nAvailable Skills:")
                    for i, skill_name in enumerate(player.skills, 1):
                        print(f"{i}. {skill_name}")
                    print("0. Back")
                    skill_choice = input("Select skill number (0 to back): ")
                    try:
                        skill_idx = int(skill_choice)
                        if skill_idx == 0:
                            continue  # Back out without ending turn
                        if 1 <= skill_idx <= len(player.skills):
                            skill_name = player.skills[skill_idx - 1]
                            skills = load_json("skills.json")["skills"]
                            skill = next((s for s in skills if s["name"] == skill_name), None)
                            if not skill or player.mp < skill["mp_cost"]:
                                print("Not enough MP!" if skill else f"Skill '{skill_name}' not found!")
                                continue
                            player.mp -= skill["mp_cost"]
                            effects = skill.get("effects", [{"type": skill.get("effect", "direct_damage"), 
                                                            "base_dmg": skill.get("base_dmg", 0), 
                                                            "duration": skill.get("duration", 0), 
                                                            "stat": skill.get("stat", "none")}])
                        for effect in effects:
                            base_dmg = effect["base_dmg"]
                            duration = effect["duration"]
                            effect_type = effect["type"]
                            stat = effect["stat"]
                            scaled_dmg = base_dmg
                            if stat != "none":
                                if effect_type == "damage_bonus":
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                                elif effect_type == "direct_damage":
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 1.0)
                                elif effect_type == "heal" or effect_type == "heal_over_time":
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                                elif effect_type == "damage_over_time":
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.2)
                                elif effect_type in ["armor_bonus", "dodge_bonus"]:
                                    scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                                elif effect_type == "life-steal":
                                    scaled_dmg = 0
                            if effect_type == "damage_bonus":
                                player_skill_effects[skill_name] = duration + 1
                                print(f"{skill_name} activated! +{scaled_dmg} damage for {duration} turns.")
                            elif effect_type == "direct_damage":
                                monster_hp -= scaled_dmg
                                print(f"{skill_name} deals {scaled_dmg} damage to {name}!")
                            # Handle other effects here if needed
                        action_taken = True
                    except ValueError:
                        print("Please enter a valid number!")
                continue

            elif choice == "4":  # Flee
                flee_chance = 0.5 + (player.stats["A"] - monster_stats["stats"]["A"]) * 0.05
                if random.random() < flee_chance:
                    print("You flee successfully, ending your adventure!")
                    return "FleeAdventure"
                else:
                    print("You fail to flee!")
                    action_taken = True
            if action_taken:
                turn = "monster"  # Switch to monster turn only after a real action


        # Apply DOT/HOT effects
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

        for skill_name, turns in list(player_skill_effects.items()):
            if turns > 0:
                skill = next((s for s in skills if s["name"] == skill_name), None)
                if skill and "effects" in skill:
                    for effect in skill["effects"]:
                        if effect["type"] == "damage_over_time":
                            scaled_dmg = effect["base_dmg"] + (player.stats[effect["stat"]] * 0.5 if effect["stat"] != "none" else 0)
                            armor_reduction = (monster_stats["armor_value"] + monster_armor_bonus) / 100
                            reduced_damage = scaled_dmg * (1 - armor_reduction)
                            monster_hp -= reduced_damage
                            print(f"{skill_name} deals {round(reduced_damage, 1)} damage to {name}!")
                            life_steal_effect = next((e for e in skill["effects"] if e["type"] == "life-steal"), None)
                            if life_steal_effect:
                                stat = life_steal_effect["stat"]
                                base_percent = 0.10 + (player.stats[stat] * 0.02 if stat != "none" else 0.02)
                                life_steal_percent = random.uniform(base_percent, 0.25)
                                hp_restored = reduced_damage * life_steal_percent
                                player.hp = min(player.hp + hp_restored, player.max_hp)
                                print(f"{skill_name} steals {round(hp_restored, 1)} HP from {name}!")
                        elif effect["type"] == "heal_over_time":
                            scaled_dmg = effect["base_dmg"] + (player.stats[effect["stat"]] * 0.5 if effect["stat"] != "none" else 0)
                            player.hp = min(player.hp + scaled_dmg, player.max_hp)
                            print(f"{skill_name} heals you for {round(scaled_dmg, 1)} HP!")

    # Combat resolution
    if player.hp <= 0:
        return "Defeat"
    elif monster_hp <= 0:
        xp = level * 2 * (1.5 if monster_stats["rare"] or boss_fight else 1)
        gold = random.randint(level * 2, level * 5) * (2 if monster_stats["rare"] or boss_fight else 1)
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