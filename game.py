import os
import sys
import time
import random
import json
import importlib
from player import Player, save_game, load_game
from combat import combat
from shop import shop_menu, parse_shop_item, calculate_price
from tavern import tavern_menu
from events import random_event
from utils import load_json, load_file, load_art_file, parse_stats, get_resource_path

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []


def parse_gear_drop_info(gear_line):
    parts = gear_line.split()
    if not parts or not parts[-1].startswith("[") or not parts[-1].endswith("]"):
        return (1, 1), 0.0, False
    
    name = " ".join(parts[:-1])
    bracket_str = parts[-1][1:-1]
    bracket = bracket_str.split()
    
    is_rare = False
    if bracket and bracket[-1] == "[R]":
        bracket.pop()
        is_rare = True
    
    if len(bracket) != 9:  # Expect 9 elements: L:1-10, slot, scaling_stat, stats, damage, AV:value, drop_rate, gold
        print(f"Warning: Invalid gear format: {gear_line}")
        return (1, 1), 0.0, False
    
    try:
        level_part, slot, scaling_stat, stats, damage, armor_part, drop_rate, gold, _ = bracket
        min_level, max_level = map(int, level_part[2:].split("-"))
        
        if not armor_part.startswith("AV:"):
            raise ValueError("Invalid armor value format")
        armor_value = int(armor_part[3:])
        
        if not drop_rate.endswith("%"):
            raise ValueError("Invalid drop rate format")
        drop_chance = float(drop_rate[:-1]) / 100
        
        if scaling_stat not in ["S", "A", "I", "W", "L"]:
            raise ValueError("Invalid scaling stat format")
        
        return (min_level, max_level), drop_chance, is_rare
    except (ValueError, IndexError) as e:
        print(f"Error parsing gear '{gear_line}': {e}. Using defaults.")
        return (1, 1), 0.0, False


def display_inventory(player):
    gear = load_json("gear.json")
    standard_items = [item for item in player.inventory if not any(item == g["name"] for g in gear)]
    print("\nStandard Items:", ", ".join(standard_items) if standard_items else "No standard items in inventory!")
    
    print("Equipment:")
    for slot, item in player.equipment.items():
        if item:
            item_name, stats, scaling_stat, armor_value = item
            stat_display = ", ".join([f"+{val} {stat[:3].capitalize()}" for stat, val in stats.items() if val > 0])
            damage = next((g["damage"] for g in gear if g["name"] == item_name), "none")
            parts = [stat_display] if stat_display else []
            parts.append(f"AV:{armor_value}")
            if damage != "none":
                parts.append(f"Dmg:{damage}")
            display_str = f"{item_name} ({', '.join(parts)})"
            print(f"{slot.capitalize()}: {display_str}")
        else:
            print(f"{slot.capitalize()}: None")


def inventory_menu(player):
    gear = load_json("gear.json")
    while True:
        display_inventory(player)
        print("\n1. Change Gear | 2. Back")
        time.sleep(0.5)
        choice = input("Selection: ")
        
        if choice == "1":
            print("\nSelect slot to change:")
            slots = list(player.equipment.keys())
            for idx, slot in enumerate(slots, 1):
                print(f"{idx}. {slot.capitalize()}")
            time.sleep(0.5)
            slot_choice = input("Selection (or 0 to back): ")
            
            if slot_choice == "0":
                continue
            try:
                slot_idx = int(slot_choice) - 1
                if 0 <= slot_idx < len(slots):
                    selected_slot = slots[slot_idx]
                    compatible_items = [item for item in player.inventory if any(g["name"] == item and g["slot"] == selected_slot for g in gear)]
                    if not compatible_items and not player.equipment[selected_slot]:
                        print("No compatible gear for this slot!")
                        time.sleep(0.5)
                        continue
                    
                    print(f"\nAvailable gear for {selected_slot.capitalize()}:")
                    for idx, item in enumerate(compatible_items, 1):
                        g = next(g for g in gear if g["name"] == item)
                        stats = g["stats"]
                        stat_display = ", ".join([f"+{val} {stat[:3].capitalize()}" for stat, val in stats.items() if val > 0])
                        armor_value = g["armor_value"]
                        damage = g["damage"]
                        parts = [stat_display] if stat_display else []
                        parts.append(f"AV:{armor_value}")
                        if damage:
                            parts.append(f"Dmg:{damage}")
                        display_str = f"{item} ({', '.join(parts)})"
                        print(f"{idx}. {display_str}")
                    print(f"{len(compatible_items) + 1}. Remove")
                    print(f"{len(compatible_items) + 2}. Back")
                    time.sleep(0.5)
                    gear_choice = input("Selection: ")
                    
                    try:
                        gear_idx = int(gear_choice) - 1
                        if gear_idx == len(compatible_items):  # Remove
                            if player.equipment[selected_slot]:
                                old_item = player.equipment[selected_slot][0]
                                player.inventory.append(old_item)
                                for stat, val in player.equipment[selected_slot][1].items():
                                    player.stats[stat] -= val
                                player.equipment[selected_slot] = None
                                print(f"Removed {old_item} from {selected_slot}.")
                                time.sleep(0.5)
                            else:
                                print("Nothing equipped in this slot!")
                                time.sleep(0.5)
                        elif gear_idx == len(compatible_items) + 1:  # Back
                            continue
                        elif 0 <= gear_idx < len(compatible_items):
                            new_item = compatible_items[gear_idx]
                            g = next(g for g in gear if g["name"] == new_item)
                            if player.equipment[selected_slot]:
                                old_item = player.equipment[selected_slot][0]
                                player.inventory.append(old_item)
                                for stat, val in player.equipment[selected_slot][1].items():
                                    player.stats[stat] -= val
                            player.equipment[selected_slot] = (new_item, g["stats"], g["modifier"], g["armor_value"])
                            for stat, val in g["stats"].items():
                                player.stats[stat] += val
                            player.inventory.remove(new_item)
                            print(f"Equipped {new_item} to {selected_slot}.")
                            time.sleep(0.5)
                        else:
                            print("Invalid selection!")
                            time.sleep(0.5)
                    except ValueError:
                        print("Invalid input!")
                        time.sleep(0.5)
                else:
                    print("Invalid slot!")
                    time.sleep(0.5)
            except ValueError:
                print("Invalid input!")
                time.sleep(0.5)
        elif choice == "2":
            break
        else:
            print("Invalid choice!")
            time.sleep(0.5)


def award_treasure_chest(player):
    treasures = load_json("treasures.json")
    chest_type = random.choices(["unlocked", "locked", "magical"], weights=[70, 20, 10], k=1)[0]
    print(f"\nYou find a {chest_type} treasure chest!")
    time.sleep(0.5)

    if chest_type == "unlocked":
        valid_treasures = [(t["name"], t["drop_rate"]) for t in treasures if t["drop_rate"] > 0]
        if valid_treasures:
            items = random.choices([t[0] for t in valid_treasures], weights=[t[1] for t in valid_treasures], k=random.randint(1, 2))
            gold = random.randint(10, 25)
            player.inventory.extend(items)
            player.gold += gold
            print(f"You open it and find: {', '.join(items)} and {gold} gold!")
        else:
            print("The chest is empty!")
        time.sleep(0.5)
    elif chest_type == "locked":
        if random.random() < player.stats["A"] * 0.05:
            valid_treasures = [(t["name"], t["drop_rate"]) for t in treasures if t["drop_rate"] > 0]
            if valid_treasures:
                items = random.choices([t[0] for t in valid_treasures], weights=[t[1] for t in valid_treasures], k=random.randint(1, 3))
                gold = random.randint(15, 30)
                player.inventory.extend(items)
                player.gold += gold
                print(f"You pick the lock and find: {', '.join(items)} and {gold} gold!")
            else:
                print("You pick the lock, but the chest is empty!")
        else:
            print("The lock holds firm—you leave empty-handed.")
        time.sleep(0.5)
    elif chest_type == "magical":
        if random.random() < player.stats["I"] * 0.05:
            valid_treasures = [(t["name"], t["drop_rate"]) for t in treasures if t["drop_rate"] > 0]
            if valid_treasures:
                items = random.choices([t[0] for t in valid_treasures], weights=[t[1] for t in valid_treasures], k=random.randint(2, 4))
                gold = random.randint(20, 40)
                player.inventory.extend(items)
                player.gold += gold
                print(f"You dispel the ward and find: {', '.join(items)} and {gold} gold!")
            else:
                print("You dispel the ward, but the chest is empty!")
        else:
            damage = player.max_hp * 0.1
            player.hp -= damage
            print(f"The ward backfires, dealing {round(damage, 1)} damage!")
        time.sleep(0.5)

def update_kill_count(player, monster_name):
    quests = load_json("quest.json")["quests"]
    
    for quest in player.active_quests:
        quest_info = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
        if quest_info and quest_info["target_monster"] == monster_name:
            quest["kill_count"] = quest.get("kill_count", 0) + 1
            print(f"Progress on '{quest['quest_name']}': {quest['kill_count']}/{quest_info['kill_count_required']} {monster_name}s killed.")
    # No need to save here; game.py will save via save_game(player) after adventure

def main():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    save_path = get_resource_path("save.json")

    if os.path.exists(save_path):
        print("1. New Game | 2. Load Game")
        time.sleep(0.5)
        choice = input("Selection: ")
        if choice == "2":
            try:
                player = load_game()
                print(f"Welcome back, {player.name}!")
                time.sleep(0.5)
            except Exception as e:
                print(f"Failed to load save: {e}. Starting new game.")
                time.sleep(0.5)
                choice = "1"
        else:
            choice = "1"
    else:
        choice = "1"

    if choice == "1":
        lore_data = load_json("lore.json")
        if not isinstance(lore_data, dict) or "lore" not in lore_data:
            print("Error: Could not load lore.json or 'lore' key missing. Skipping intro.")
            intro_lore = None
        else:
            intro_lore = next((l for l in lore_data["lore"] if l["quest_name"] == "intro"), None)
            if intro_lore:
                print("\n=== Welcome to Snowcaller ===")
                print(intro_lore["lore_text"])
                time.sleep(2)

        name = input("\nEnter your name: ")
        print("Select your class:")
        print("1. Warrior (High Strength) | 2. Mage (High Intelligence) | 3. Rogue (High Agility)")
        time.sleep(0.5)
        class_type = input("Selection: ")
        while class_type not in ["1", "2", "3"]:
            print("Invalid class! Choose 1, 2, or 3.")
            class_type = input("Selection: ")

        # Define class-specific data
        class_data = {
            "1": {
                "name": "Warrior",
                "art_file": os.path.join(base_path, "art", "warrior.txt"),
                "lore": "Forged in the crucible of battle, Warriors are the unyielding shield of Snowcaller. With strength as their blade and courage as their armor, they stand against the tides of chaos that threaten the realm."
            },
            "2": {
                "name": "Mage",
                "art_file": os.path.join(base_path, "art", "mage.txt"),
                "lore": "Masters of the arcane, Mages wield the primal forces of ice and fire. In Snowcaller’s frozen wastes, their intellect unravels mysteries older than the mountains, bending the elements to their will."
            },
            "3": {
                "name": "Rogue",
                "art_file": os.path.join(base_path, "art", "rogue.txt"),
                "lore": "Shadows of the frostbitten wilds, Rogues dance between life and death. With agility unmatched and cunning sharp as a dagger, they thrive in the unseen corners of Snowcaller, striking when least expected."
            }
        }

        # Display ASCII art and lore for the selected class
        selected_class = class_data[class_type]
        print(f"\n=== You have chosen the {selected_class['name']} ===")
        
        # Load and display ASCII art
        try:
            art_lines = load_art_file(selected_class["art_file"])
            print("\nClass Art:")
            for line in art_lines:
                print(line)  # Default print, adds its own newline
        except Exception as e:
             print(f"Error loading {selected_class['name']} art: {e}")
             print(f"(Imagine a grand {selected_class['name']} here!)")
        
        # Display class lore
        print(f"\n{selected_class['lore']}")
        time.sleep(2)  # Pause to let the player read

        # Proceed with player creation
        player = Player(name, class_type)
        print(f"Welcome, {player.name} the {selected_class['name']}!")
        if player.skills:
            print(f"Skills unlocked: {', '.join(player.skills)}")
        time.sleep(0.5)

    save_game(player)
    print("Game autosaved!")
    time.sleep(0.5)

    while True:
        print(f"\n{'-' * 20} {player.name}: Level {player.level} {'-' * 20}")
        print(f"HP: {round(player.hp, 1)}/{player.max_hp} | MP: {player.mp}/{player.max_mp} | Gold: {player.gold}")
        print("1. Adventure | 2. Inventory | 3. Stats | 4. Shop | 5. Tavern | 6. Guild | 7. Save | 8. Quit")
        time.sleep(0.5)
        choice = input("Selection: ")

        if choice == "1":
            lines = load_file("locations.txt")
            main_areas = []
            sub_areas = []
            current_section = None
            for line in lines:
                if line == "# Main Areas":
                    current_section = main_areas
                elif line == "# Sub Areas":
                    current_section = sub_areas
                elif current_section is not None:
                    current_section.append(line)
            
            if not main_areas:
                main_areas = ["Forest", "Desert", "Mountain"]
                print("Warning: No main areas loaded from locations.txt, using defaults.")
            if not sub_areas:
                sub_areas = ["Castle", "Cave", "Village"]
                print("Warning: No sub areas loaded from locations.txt, using defaults.")

            active_quests = player.active_quests

            if active_quests:
                print("1. Random Adventure | 2. Quest Adventure")
                adventure_type = input("Selection: ")
            else:
                adventure_type = "1"

            if adventure_type == "1":
                main_area = random.choice(main_areas)
                sub_area = random.choice(sub_areas)
                location = f"{main_area} {sub_area}"
                print(f"\nYou set out for the {location}!")
                monsters = load_json("monster.json")["monsters"]  # Access the "monsters" list
                encounter_pool = []
                for m in monsters:
                    if not m["rare"]:  # Exclude bosses
                        min_monster_level = m["level_range"]["min"]
                        max_monster_level = m["level_range"]["max"]
                        if (min_monster_level <= player.level + 2 and max_monster_level >= player.level - 2):
                            encounter_pool.extend([m] * m["spawn_chance"])
                if not encounter_pool:
                    print("Warning: No suitable monsters found for your level. Using fallback.")
                    encounter_pool = [m for m in monsters if not m["rare"]][:1]  # Fallback to first non-rare

                time.sleep(0.5)
                max_encounters = random.randint(2, 10)
                boss_fight = False
                encounter_count = 0
                combat_count = 0
                completed_encounters = 0
                treasure_inventory = []
                adventure = True
                event_chance = 25

                while adventure:
                    if encounter_count >= max_encounters:
                        if encounter_count >= 8 and not boss_fight and random.random() < 0.25:
                            print(f"\nA powerful foe blocks your path! Fight the boss?")
                            print("1. Yes | 2. No")
                            time.sleep(0.5)
                            boss_choice = input("Selection: ")
                            if boss_choice == "1":
                                boss_fight = True
                                boss_monsters = [m for m in monsters if m["rare"] and m["spawn_chance"] > 0]  # Exclude quest bosses
                                boss = random.choice(boss_monsters) if boss_monsters else random.choice([m for m in monsters if not m["rare"]])  # Fallback to non-rare if no valid bosses
                                result = combat(player, True, boss["name"])
                                Encounters.append(result)
                                if player.hp <= 0:
                                    print("\nYou have died!")
                                    if os.path.exists("save.txt"):
                                        os.remove("save.txt")
                                    print("Game Over.")
                                    time.sleep(1)
                                    return
                                if "Victory" in result:
                                    completed_encounters += 1
                                    update_kill_count(player, result.split("against ")[1])
                            else:
                                print("You avoid the boss and head back to town.")
                                time.sleep(0.5)
                            adventure = False
                            break
                        adventure = False
                        break

                    encounter_count += 1
                    Encounters = []

                    if random.randint(1, 100) <= event_chance:
                        max_encounters = random_event(player, encounter_count, max_encounters)
                    else:
                        combat_count += 1
                        monster = random.choice(encounter_pool)
                        result = combat(player, False, monster["name"])
                        Encounters.append(result)

                        if player.hp <= 0:
                            print("\nYou have died!")
                            if os.path.exists("save.txt"):
                                os.remove("save.txt")
                            print("Game Over.")
                            time.sleep(1)
                            return

                        if Encounters and "Victory" in Encounters[-1]:
                            completed_encounters += 1
                            update_kill_count(player, monster["name"])
                            drop_item = None
                            gear = load_json("gear.json")
                            consumables = load_json("consumables.json")
                            valid_drops = []

                            for item in gear:
                                if (player.level >= item["level_range"]["min"] and 
                                    player.level <= item["level_range"]["max"] and 
                                    item.get("drop_rate", 0) > 0 and
                                    (not item.get("boss_only", False) or boss_fight)):
                                    valid_drops.append((item["name"], item["drop_rate"]))

                            for item in consumables:
                                if (player.level >= item["level_range"]["min"] and 
                                    player.level <= item["level_range"]["max"] and 
                                    item.get("drop_rate", 0) > 0 and  
                                    (not item["boss_only"] or boss_fight)):
                                    valid_drops.append((item["name"], item["drop_rate"]))

 #                           print(f"Player Level: {player.level}")
 #                           print(f"Valid Drops: {valid_drops}")

                            if valid_drops and random.random() < 0.25:
                                items = [item[0] for item in valid_drops]
                                weights = [item[1] for item in valid_drops]
                                drop_item = random.choices(items, weights=weights, k=1)[0]
                                player.inventory.append(drop_item)
                                print(f"\nYou found a {drop_item}!")
                                time.sleep(0.5)
                            else:
                                print("\nNo item dropped this time.")
                                time.sleep(0.5)

                            if random.random() < 0.15 or (boss_fight and random.random() < 0.5):
                                treasure_inventory.append("Treasure Chest")

                        elif Encounters and "FleeAdventure" in Encounters[-1]:
                            print(f"\nYou escaped the {location}, ending your adventure with {completed_encounters} victories.")
                            time.sleep(0.5)
                            adventure = False
                            break

                    if combat_count > 0 and player.hp < player.max_hp / 2 and adventure:
                        print(f"\nYou've fought {combat_count} battles in the {location}. HP: {round(player.hp, 1)}/{player.max_hp}")
                        print("Continue adventure? 1 for Yes | 2 for No")
                        time.sleep(0.5)
                        choice = input("Selection: ")
                        if choice == "2":
                            print(f"You decide to return to town with {completed_encounters} victories.")
                            adventure = False
                            break
                        elif choice != "1":
                            print("Invalid choice, continuing adventure.")
                            time.sleep(0.5)

                if adventure is False and "FleeAdventure" not in Encounters:
                    print(f"\nAdventure complete! Returning to town with {len(treasure_inventory)} treasure items from {completed_encounters} victories.")
                    time.sleep(0.5)
                    if choice != "2":
                        for _ in range(len(treasure_inventory)):
                            award_treasure_chest(player)
                    save_game(player)

            elif adventure_type == "2":
                quests = load_json("quest.json")["quests"]
                monsters = load_json("monster.json")["monsters"]
                
                print("\nActive Quests:")
                for i, quest in enumerate(active_quests, 1):
                    q = next(q for q in quests if q["quest_name"] == quest["quest_name"])
                    print(f"{i}. {quest['quest_name']} (Kills: {quest['kill_count']}/{q['kill_count_required']})")
                quest_choice = int(input("Select a quest: ")) - 1
                selected_quest = active_quests[quest_choice]
                quest_info = next(q for q in quests if q["quest_name"] == selected_quest["quest_name"])
                target_monster = next(m for m in monsters if m["name"] == quest_info["target_monster"])
                remaining_kills = quest_info["kill_count_required"] - selected_quest["kill_count"]

                print(f"\nPursuing quest: {quest_info['quest_name']} at the {location}!")
                time.sleep(0.5)
                for _ in range(remaining_kills):
                    result = combat(player, target_monster["rare"], target_monster["name"])
                    if player.hp <= 0:
                        print("\nYou have died!")
                        if os.path.exists("save.txt"):
                            os.remove("save.txt")
                        print("Game Over.")
                        time.sleep(1)
                        return
                    if "Victory" in result:
                        update_kill_count(player, target_monster["name"])
                    else:
                        print("You fled or failed the encounter. Quest progress unchanged.")
                        break

                if selected_quest["kill_count"] >= quest_info["kill_count_required"]:
                    print(f"\nQuest '{quest_info['quest_name']}' ready to turn in! Visit the Guild.")
                else:
                    print(f"\nReturning to town with {selected_quest['kill_count']} kills toward {quest_info['quest_name']}.")

            player.buff = []
            player.event_cooldowns = {k: 0 for k in player.event_cooldowns}
            player.rage_turns = 0

            if player.stat_points > 0:
                player.allocate_stat()
            player.apply_xp()

        elif choice == "2":
            inventory_menu(player)

        elif choice == "3":
            print(f"\nStats: S:{player.stats['S']} A:{player.stats['A']} I:{player.stats['I']} W:{player.stats['W']} L:{player.stats['L']}")
            print(f"Level: {player.level} | XP: {player.exp}/{player.max_exp}")
            from combat import get_weapon_damage_range
            min_dmg, max_dmg = get_weapon_damage_range(player)
            attack_dps = (min_dmg + max_dmg) / 2
            print(f"Attack DPS: {round(attack_dps, 1)} (avg weapon damage per turn)")
            skills = load_file("skills.txt")
            total_skill_dps = 0
            skill_count = 0
            for skill in skills:
                skill_data = skill.split('#')[0].strip()
                if not skill_data.startswith('[') or not skill_data.endswith(']'):
                    continue
                parts = skill_data[1:-1].strip().split()
                if len(parts) != 8:
                    continue
                class_type, level_req, name, base_dmg, effect, mp_cost, duration, stat = parts
                if name in player.skills:
                    base_dmg = int(base_dmg)
                    mp_cost = int(mp_cost)
                    duration = int(duration)
                    scaled_dmg = base_dmg
                    if stat != "none":
                        if effect == "damage_bonus":
                            scaled_dmg = base_dmg + int(player.stats[stat] * 0.5)
                        elif effect == "direct_damage":
                            scaled_dmg = base_dmg + int(player.stats[stat] * 1.0)
                        elif effect == "damage_over_time":
                            scaled_dmg = base_dmg + int(player.stats[stat] * 0.2)
                    if effect == "direct_damage" and duration == 0:
                        dps = scaled_dmg
                    elif effect in ["damage_bonus", "damage_over_time"]:
                        total_turns = max(1, mp_cost) + duration
                        dps = (scaled_dmg * duration) / total_turns if duration > 0 else 0
                    else:
                        dps = 0
                    total_skill_dps += dps
                    skill_count += 1
            skill_dps = total_skill_dps / skill_count if skill_count > 0 else 0
            print(f"Skill DPS: {round(skill_dps, 1)} (avg skill damage per turn)")
            print(f"Armor Value: {round(player.get_total_armor_value(), 1)}% (damage reduction)")
            if player.stat_points > 0:
                player.allocate_stat()
            time.sleep(0.5)

        elif choice == "4":
            shop_menu(player)

        elif choice == "5":
            tavern_menu(player)

        elif choice == "6":
            guild_menu(player)

        elif choice == "7":
            save_game(player)
            print("Game saved!")
            time.sleep(0.5)

        elif choice == "8":
            print("Goodbye!")
            time.sleep(0.5)
            break

        else:
            print("Invalid choice!")
            time.sleep(0.5)

def guild_menu(player):
    quests = load_json("quest.json")["quests"]
    lore_data = load_json("lore.json")["lore"]
    
    active_quests = player.active_quests  # Use player attribute
    completed_quests = player.completed_quests if hasattr(player, "completed_quests") else []  # Fallback until player.py is updated
    
    print("\n=== Adventurers' Guild ===")
    print("1. Accept Quest | 2. Turn In Quest | 0. Return")
    choice = input("Selection: ")

    if choice == "1":
        if len(active_quests) >= 5:
            print("You’ve reached the maximum of 5 active quests.")
            return
        
        available_quests = [
            q for q in quests 
            if player.level >= q["quest_level"] 
            and q["quest_name"] not in [aq["quest_name"] for aq in active_quests] 
            and q["quest_name"] not in completed_quests
        ]
        if not available_quests:
            print("No new quests available.")
        else:
            print("\nAvailable Quests:")
            for i, quest in enumerate(available_quests, 1):
                print(f"{i}. {quest['quest_name']} (Level {quest['quest_level']})")
                print(f"   {quest['quest_description']}")
            quest_choice = input("Select a quest to accept (or 0 to return): ")
            if quest_choice == "0":
                return
            if 1 <= int(quest_choice) <= len(available_quests):
                selected_quest = available_quests[int(quest_choice) - 1]
                active_quests.append({"quest_name": selected_quest["quest_name"], "kill_count": 0})
                player.active_quests = active_quests  # Update player object
                print(f"Accepted quest: {selected_quest['quest_name']}")
                time.sleep(0.5)
                
                lore_entry = next((l for l in lore_data if l["quest_name"] == selected_quest["quest_name"]), None)
                if lore_entry:
                    lore_choice = input("Would you like to read the lore? (y/n): ").lower()
                    if lore_choice == "y":
                        print(f"\nLore for '{selected_quest['quest_name']}':")
                        print(lore_entry["lore_text"])
                        time.sleep(1)

    elif choice == "2":
        if not active_quests:
            print("No active quests to turn in.")
            return
        
        print("\nActive Quests:")
        for i, quest in enumerate(active_quests, 1):
            q = next(q for q in quests if q["quest_name"] == quest["quest_name"])
            print(f"{i}. {quest['quest_name']} (Kills: {quest['kill_count']}/{q['kill_count_required']})")
        turn_in_choice = input("Select a quest to turn in (or 0 to return): ")
        if turn_in_choice == "0":
            return
        if 1 <= int(turn_in_choice) <= len(active_quests):
            selected_quest = active_quests[int(turn_in_choice) - 1]
            quest_info = next(q for q in quests if q["quest_name"] == selected_quest["quest_name"])
            if selected_quest["kill_count"] >= quest_info["kill_count_required"]:
                reward_parts = quest_info["quest_reward"].split(", ")
                gold_amount = int(reward_parts[0])
                item_reward = reward_parts[1] if len(reward_parts) > 1 else None
                player.gold += gold_amount
                if item_reward:
                    player.inventory.append(item_reward)
                print(f"Quest '{quest_info['quest_name']}' completed! Reward: {quest_info['quest_reward']}")
                active_quests.remove(selected_quest)
                if not hasattr(player, "completed_quests"):
                    player.completed_quests = []  # Initialize if not present
                player.completed_quests.append(quest_info["quest_name"])
                player.active_quests = active_quests  # Update player object
                time.sleep(0.5)
            else:
                print(f"Quest '{quest_info['quest_name']}' not complete yet. Kills: {selected_quest['kill_count']}/{quest_info['kill_count_required']}")
                time.sleep(0.5)

if __name__ == "__main__":
    main()