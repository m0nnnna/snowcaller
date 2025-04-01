import random
import time
import json
import os
from utils import load_json, parse_stats
from items import use_item
from player import save_game
from colorama import init, Fore, Back, Style

# Initialize colorama
init()

# Color constants
RED = Fore.RED
GREEN = Fore.GREEN
BLUE = Fore.BLUE
YELLOW = Fore.YELLOW
MAGENTA = Fore.MAGENTA
CYAN = Fore.CYAN
WHITE = Fore.WHITE
RESET = Style.RESET_ALL

def load_art(art_file):
    art_path = os.path.join("art", art_file)
    if os.path.exists(art_path):
        with open(art_path, "r") as f:
            return f.read()
    return None  # Return None if file doesn't exist, no error message

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
    monster_max_mp = 2 * monster_stats["stats"]["W"] * level_scale
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
    monster_status = {"sleep": 0, "curse": 0, "poison": 0}  # Track status effects

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
    print(f"{f'{GREEN}You strike first!{RESET}' if player_goes_first else f'{RED}{name} takes the initiative!{RESET}'}")

    turn = "player" if player_goes_first else "monster"
    player_mp_regenerated = False  # Flag to track MP regeneration for the current player turn

    # Display monster appearance with level
    print(f"\nA Level {level} {name} appears!")
    if "art_file" in monster_stats:
        art = load_art(monster_stats["art_file"])
        if art:
            print(art)
    print(f"{RED}HP: {round(monster_hp, 1)}{RESET}")

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
                        print(f"{GREEN}{name} breaks free from sleep!{RESET}")
                    else:
                        print(f"{GREEN}{name} is asleep and cannot act!{RESET}")
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
                                    print(f"{GREEN}{name} uses {skill['name']}! +{scaled_dmg} damage for {duration} turns.{RESET}")
                                elif effect == "direct_damage":
                                    player.hp -= scaled_dmg
                                    print(f"{RED}{name} uses {skill['name']}, dealing {scaled_dmg} damage to you!{RESET}")
                                elif effect == "damage_over_time":
                                    monster_skill_effects[skill["name"]] = duration
                                    print(f"{RED}{name} uses {skill['name']}, applying {scaled_dmg} damage per turn for {duration} turns!{RESET}")
                                elif effect == "armor_bonus":
                                    monster_skill_effects[skill["name"]] = duration
                                    monster_armor_bonus = scaled_dmg
                                    print(f"{GREEN}{name} uses {skill['name']}, increasing armor by {scaled_dmg}% for {duration} turns!{RESET}")
                                elif effect == "dodge_bonus":
                                    monster_skill_effects[skill["name"]] = duration
                                    monster_dodge_bonus = scaled_dmg
                                    print(f"{GREEN}{name} uses {skill['name']}, increasing dodge chance by {scaled_dmg}% for {duration} turns!{RESET}")
                                elif effect == "curse":
                                    player_status["curse"] = duration
                                    print(f"{RED}{name} uses {skill['name']}, cursing you and blocking skills for {duration} turns!{RESET}")
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
                                print(f"{BLUE}You dodge {name}'s attack!{RESET}")
                            else:
                                armor_reduction = (player.get_total_armor_value() + player_armor_bonus) / 100
                                reduced_damage = damage * (1 - armor_reduction)
                                player.hp -= reduced_damage
                                print(f"{RED}{name} deals {round(reduced_damage, 1)} damage to you (reduced from {round(damage, 1)} by armor)!{RESET}")
                    except Exception as e:
                        print(f"{RED}ERROR: Monster skill processing failed: {e}{RESET}")
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
                        print(f"{BLUE}You dodge {name}'s attack!{RESET}")
                    else:
                        armor_reduction = (player.get_total_armor_value() + player_armor_bonus) / 100
                        reduced_damage = damage * (1 - armor_reduction)
                        player.hp -= reduced_damage
                        print(f"{RED}{name} deals {round(reduced_damage, 1)} damage to you (reduced from {round(damage, 1)} by armor)!{RESET}")

            # Apply DOT/HOT effects on monster's turn (affects player)
            for skill_name, turns in list(monster_skill_effects.items()):
                if turns > 0:
                    for skill in skills:
                        if skill["name"] == skill_name and skill["effect"] == "damage_over_time":
                            base_dmg = skill["base_dmg"]
                            stat = skill["stat"]
                            dot_dmg = base_dmg + (int(monster_stats["stats"][stat] * 0.2) if stat != "none" else 0)
                            player.hp -= dot_dmg
                            print(f"{RED}{name}'s {skill_name} deals {dot_dmg} damage to you!{RESET}")
                            monster_skill_effects[skill_name] -= 1
                            if monster_skill_effects[skill_name] <= 0:
                                del monster_skill_effects[skill_name]
                            break

            # Decrement monster status effects
            for status in list(monster_status.keys()):
                if monster_status[status] > 0:
                    monster_status[status] -= 1
                    if monster_status[status] <= 0:
                        del monster_status[status]

            turn = "player"  # Switch to player turn after monster acts
            player_mp_regenerated = False

        # Player Turn
        elif turn == "player":
            # Regenerate MP only once per turn
            if not player_mp_regenerated and player.mp < player.max_mp:
                mp_regen = player.stats["W"] * 0.3
                player.mp = min(player.mp + mp_regen, player.max_mp)
                print(f"\n{CYAN}You regenerate {round(mp_regen, 1)} MP{RESET}")
                player_mp_regenerated = True
            elif not player_mp_regenerated:
                player_mp_regenerated = True

            # Combat UI
            bonus_display = ""  # Define bonus_display as an empty string or assign its appropriate value
            player_status_display = f" Status: {', '.join([f'{k} ({v})' for k, v in player_status.items() if v > 0])}" if any(v > 0 for v in player_status.values()) else ""
            monster_status_display = f" Status: {', '.join([f'{k} ({v})' for k, v in monster_status.items() if v > 0])}" if any(v > 0 for v in monster_status.values()) else ""
            print(f"\n| {monster_stats['name']}: {round(monster_hp, 1)} HP{monster_status_display} | {player.name}: {round(player.hp, 1)}/{player.max_hp} HP, {round(player.mp, 1)}/{player.max_mp} MP{player_status_display} |")
            print(f"{BLUE}1. Attack | 2. Item | 3. Skills | 4. Flee{RESET}")
            choice = input("Selection: ")

            action_taken = False

            if choice == "1":  # Attack
                min_dmg, max_dmg = get_weapon_damage_range(player)
                dodge_chance = (monster_stats["stats"]["A"] * 0.02) + (monster_dodge_bonus / 100)
                crit_chance = player.stats["A"] * 0.02
                damage = random.uniform(min_dmg, max_dmg)
                if random.random() < dodge_chance:
                    print(f"{GREEN}{name} dodges your attack!{RESET}")
                else:
                    if random.random() < crit_chance:
                        damage *= 1.5
                        print(f"{YELLOW}Critical hit!{RESET}")
                    armor_reduction = (monster_stats["armor_value"] + monster_armor_bonus) / 100
                    reduced_damage = damage * (1 - armor_reduction)
                    monster_hp -= reduced_damage
                    if damage != reduced_damage:
                        print(f"{BLUE}You deal {round(reduced_damage, 1)} damage to {name} (reduced from {round(damage, 1)} by armor)!{RESET}")
                    else:
                        print(f"{BLUE}You deal {round(reduced_damage, 1)} damage to {name}!{RESET}")
                action_taken = True

            elif choice == "2":  # Item
                if not player.inventory:
                    print(f"{RED}No items available!{RESET}")
                    continue
                print(f"\n{BLUE}Inventory:{RESET}", ", ".join(player.inventory))
                item = input("Select item (or 'back'): ")
                if item == "back":
                    continue
                if item in player.inventory:
                    if not use_item(player, item, monster_stats):
                        print(f"{RED}{item} cannot be used here!{RESET}")
                        continue
                    if "effects" in monster_stats and monster_stats["effects"]:
                        for effect, turns in list(monster_stats["effects"].items()):
                            if turns > 0:
                                monster_hp -= 5
                                monster_stats["effects"][effect] -= 1
                                if monster_stats["effects"][effect] <= 0:
                                    del monster_stats["effects"][effect]
                    print(f"{CYAN}Used {item}!{RESET}")
                    action_taken = True
                else:
                    print(f"{RED}Item not found!{RESET}")
                    continue

            elif choice == "3":  # Skills
                if not player.skills or player_status.get("curse", 0) > 0:
                    print(f"{RED}No skills available!{RESET}" if not player.skills else f"{RED}You are cursed and cannot use skills!{RESET}")
                else:
                    print(f"\n{BLUE}Available Skills:{RESET}")
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
                                print(f"{RED}Not enough MP!{RESET}" if skill else f"{RED}Skill '{skill_name}' not found!{RESET}")
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
                                    player_skill_effects[skill_name] = duration
                                    print(f"{CYAN}{skill_name} activated! +{scaled_dmg} damage for {duration} turns.{RESET}")
                                elif effect_type == "direct_damage":
                                    monster_hp -= scaled_dmg
                                    print(f"{BLUE}{skill_name} deals {scaled_dmg} damage to {name}!{RESET}")
                                elif effect_type == "damage_over_time":
                                    player_skill_effects[skill_name] = duration
                                    monster_status["poison"] = duration
                                    print(f"{BLUE}{skill_name} applies {scaled_dmg} damage per turn for {duration} turns!{RESET}")
                                elif effect_type == "heal":
                                    player.hp = min(player.hp + scaled_dmg, player.max_hp)
                                    print(f"{CYAN}{skill_name} heals you for {scaled_dmg} HP!{RESET}")
                                elif effect_type == "heal_over_time":
                                    player_skill_effects[skill_name] = duration
                                    print(f"{CYAN}{skill_name} will heal you for {scaled_dmg} HP per turn for {duration} turns!{RESET}")
                                elif effect_type == "armor_bonus":
                                    player_skill_effects[skill_name] = duration
                                    player_armor_bonus = scaled_dmg
                                    print(f"{CYAN}{skill_name} increases your armor by {scaled_dmg}% for {duration} turns!{RESET}")
                                elif effect_type == "dodge_bonus":
                                    player_skill_effects[skill_name] = duration
                                    player_dodge_bonus = scaled_dmg
                                    print(f"{CYAN}{skill_name} increases your dodge chance by {scaled_dmg}% for {duration} turns!{RESET}")
                                elif effect_type == "sleep":
                                    monster_status["sleep"] = duration
                                    print(f"{CYAN}{skill_name} puts {name} to sleep for {duration} turns!{RESET}")
                                elif effect_type == "curse":
                                    monster_status["curse"] = duration
                                    print(f"{CYAN}{skill_name} curses {name}, blocking skills for {duration} turns!{RESET}")
                            action_taken = True
                    except ValueError:
                        print(f"{RED}Please enter a valid number!{RESET}")
                continue

            elif choice == "4":  # Flee
                flee_chance = 0.5 + (player.stats["A"] - monster_stats["stats"]["A"]) * 0.05
                if random.random() < flee_chance:
                    print(f"{BLUE}You flee successfully, ending your adventure!{RESET}")
                    return "FleeAdventure"
                else:
                    print(f"{RED}You fail to flee!{RESET}")
                    action_taken = True

            # Apply DOT/HOT effects on player's turn (affects monster)
            for skill_name, turns in list(player_skill_effects.items()):
                if turns > 0:
                    skill = next((s for s in skills if s["name"] == skill_name), None)
                    if skill:
                        # Handle both old and new skill formats
                        if "effects" in skill:
                            for effect in skill["effects"]:
                                if effect["type"] == "damage_over_time":
                                    scaled_dmg = effect["base_dmg"] + (player.stats[effect["stat"]] * 0.2 if effect["stat"] != "none" else 0)
                                    armor_reduction = (monster_stats["armor_value"] + monster_armor_bonus) / 100
                                    reduced_damage = scaled_dmg * (1 - armor_reduction)
                                    monster_hp -= reduced_damage
                                    print(f"{BLUE}{skill_name} deals {round(reduced_damage, 1)} damage to {name}!{RESET}")
                                elif effect["type"] == "heal_over_time":
                                    scaled_dmg = effect["base_dmg"] + (player.stats[effect["stat"]] * 0.5 if effect["stat"] != "none" else 0)
                                    player.hp = min(player.hp + scaled_dmg, player.max_hp)
                                    print(f"{CYAN}{skill_name} heals you for {round(scaled_dmg, 1)} HP!{RESET}")
                        else:
                            # Handle old skill format
                            if skill["effect"] == "damage_over_time":
                                scaled_dmg = skill["base_dmg"] + (player.stats[skill["stat"]] * 0.2 if skill["stat"] != "none" else 0)
                                armor_reduction = (monster_stats["armor_value"] + monster_armor_bonus) / 100
                                reduced_damage = scaled_dmg * (1 - armor_reduction)
                                monster_hp -= reduced_damage
                                print(f"{BLUE}{skill_name} deals {round(reduced_damage, 1)} damage to {name}!{RESET}")
                            elif skill["effect"] == "heal_over_time":
                                scaled_dmg = skill["base_dmg"] + (player.stats[skill["stat"]] * 0.5 if skill["stat"] != "none" else 0)
                                player.hp = min(player.hp + scaled_dmg, player.max_hp)
                                print(f"{CYAN}{skill_name} heals you for {round(scaled_dmg, 1)} HP!{RESET}")
                        player_skill_effects[skill_name] -= 1
                        if player_skill_effects[skill_name] <= 0:
                            del player_skill_effects[skill_name]

            if action_taken:
                turn = "monster"  # Switch to monster turn only after a real action

    # Combat resolution
    if player.hp <= 0:
        return "Defeat"
    elif monster_hp <= 0:
        xp = level * 2 * (1.5 if monster_stats["rare"] or boss_fight else 1)
        gold = random.randint(level * 2, level * 5) * (2 if monster_stats["rare"] or boss_fight else 1)
        player.gold += gold
        # Apply XP immediately
        player.exp += xp
        # Handle any level-ups
        while player.exp >= player.max_exp and player.level < 25:
            player.level_up()
        # Save the game silently
        save_game(player)
        return f"{GREEN}Victory against {monster_stats['name']}{RESET} {YELLOW}{xp} XP{RESET} {YELLOW}{gold} gold{RESET}"

def trigger_npc_event(player, npc_name):
    """Trigger special NPC appearance based on event, quest, or item."""
    if not hasattr(player, "tavern_npcs"):
        player.tavern_npcs = []
    if npc_name and npc_name not in [n["name"] for n in player.tavern_npcs]:
        player.tavern_npcs.append({"name": npc_name, "room": False})
        print(f"{npc_name} has appeared at the tavern!")