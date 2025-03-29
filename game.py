import os
import sys
import time
import builtins
import random
import json
import importlib
import shutil
from player import Player, save_game, load_game
from combat import combat
from shop import shop_menu, calculate_price
from tavern import tavern_menu, Tavern
from events import random_event
from utils import load_json, load_file, load_art_file, parse_stats, get_resource_path, save_json
from commands import handle_command

# Global sleep delay (in seconds)
SLEEP_DELAY = 0.3

# Store the original print function
_original_print = builtins.print

# Override print to include a delay
def print(*args, **kwargs):
    _original_print(*args, **kwargs)
    time.sleep(SLEEP_DELAY)

# Replace the built-in print with our version
builtins.print = print

# Import the update checker
try:
    from update import check_for_updates
except ImportError:
    def check_for_updates():
        pass  # Dummy function if update.py is missing
    print("Warning: update.py not found. Skipping update checks.")

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def check_repo_status():
    if not shutil.which("git"):
        print("Warning: Git not installed. Update checking skipped.")
        return False
    if not os.path.exists(".git"):
        print("Warning: Not a git repository. Update checking skipped.")
        return False


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
        choice = input("Selection: ")
        
        if choice == "1":
            print("\nSelect slot to change:")
            slots = list(player.equipment.keys())
            for idx, slot in enumerate(slots, 1):
                print(f"{idx}. {slot.capitalize()}")
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
                            else:
                                print("Nothing equipped in this slot!")
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
                        else:
                            print("Invalid selection!")
                    except ValueError:
                        print("Invalid input!")
                else:
                    print("Invalid slot!")
            except ValueError:
                print("Invalid input!")
        elif choice == "2":
            break
        else:
            print("Invalid choice!")


def award_treasure_chest(player):
    treasures = load_json("treasures.json")
    chest_type = random.choices(["unlocked", "locked", "magical"], weights=[70, 20, 10], k=1)[0]
    print(f"\nYou find a {chest_type} treasure chest!")

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


def update_kill_count(player, monster_name):
    quests_data = load_json("quest.json")
    quests = quests_data.get("quests", [])
    
    if not quests:
        print("Warning: No quests found in quest.json!")
        return
    
    for quest in player.active_quests:
        quest_info = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
        if quest_info is None:
            print(f"Warning: Quest '{quest['quest_name']}' in active_quests not found in quest.json!")
            continue
        if "target_monster" not in quest_info:
            print(f"Warning: Quest '{quest['quest_name']}' in quest.json missing 'target_monster' key!")
            continue
        if quest_info["target_monster"] == monster_name:
            quest["kill_count"] = quest.get("kill_count", 0) + 1
            print(f"Progress on '{quest['quest_name']}': {quest['kill_count']}/{quest_info['kill_count_required']} {monster_name}s killed.")

def main():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    save_path = os.path.join(base_path, "save.json")

    from commands import handle_command  # Import command handler
    commands_enabled = os.path.exists(os.path.join(base_path, "commands_enabled.txt"))

    if os.path.exists(save_path):
        print("1. New Game | 2. Load Game")
        choice = input("Selection: ").strip().lower()
        if handle_command(choice, None, commands_enabled):
            return
        if choice == "2":
            try:
                player = load_game()
                print(f"Welcome back, {player.name}!")
            except Exception as e:
                print(f"Failed to load save: {e}. Starting new game.")
                choice = "1"
        else:
            choice = "1"
    else:
        print("No save file detected, forcing new game.")
        choice = "1"

    check_for_updates()

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

        name = input("\nEnter your name: ")
        print("Select your class:")
        print("1. Warrior (High Strength) | 2. Mage (High Intelligence) | 3. Rogue (High Agility)")
        class_type = input("Selection: ")
        while class_type not in ["1", "2", "3"]:
            print("Invalid class! Choose 1, 2, or 3.")
            class_type = input("Selection: ")

        player = Player(name, class_type)
        print("Calling load_starting_data...")
        player.load_starting_data()
        save_game(player)

        # Define class-specific data
        class_data = {
            "1": {
                "name": "Warrior",
                "art_file": "warrior.txt",
                "lore": "Warriors are the backbone of the realm. They are the defenders of the weak, the protectors of the innocent, and the champions of the just. They are the sword and shield of those lost to the snow"
            },
            "2": {
                "name": "Mage",
                "art_file": "mage.txt",
                "lore": "Mages are a powerful force. Once understanding a wide range of magic, they have chosen to specialize in the cold arts. They are the architects of the arcane, the masters of the frost, and the keepers of the flame."
            },
            "3": {
                "name": "Rogue",
                "art_file": "rogue.txt",
                "lore": "Rogue's in this world are feared for their ability to hide in the snow. The frozen wastes may be harsh, but they are harsher. They are the shadows that move in the night."
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
                print(line)
        except Exception as e:
            print(f"Error loading {selected_class['name']} art: {e}")
            print(f"(Imagine a grand {selected_class['name']} here!)")
        
        # Display class lore
        print(f"\n{selected_class['lore']}")

        print(f"Welcome, {player.name} the {selected_class['name']}!")
        if player.skills:
            print(f"Skills unlocked: {', '.join(player.skills)}")

    save_game(player)
    print("Game autosaved!")

    while True:
        print(f"\n{'-' * 20} {player.name}: Level {player.level} {'-' * 20}")
        print(f"HP: {round(player.hp, 1)}/{player.max_hp} | MP: {player.mp}/{player.max_mp} | Gold: {player.gold}")
        print("1. Adventure | 2. Inventory | 3. Stats | 4. Shop | 5. Tavern | 6. Guild | 7. Save | 8. Quit")
        choice = input("Selection: ").strip().lower()
        if handle_command(choice, player, commands_enabled):
            continue

        if choice == "1":
            print("\nChoose your adventure type:")
            print("1. Short Trip (2-3 encounters)")
            print("2. Adventure (3-6 encounters)")
            print("3. Dungeon (6-10 encounters)")
            adventure_length = input("Selection: ").strip()
            
            while adventure_length not in ["1", "2", "3"]:
                print("Invalid choice! Choose 1, 2, or 3.")
                adventure_length = input("Selection: ").strip()

            # Set encounter range and modifiers based on adventure type
            if adventure_length == "1":
                max_encounters = random.randint(2, 3)
                event_chance = 5
                drop_rate_modifier = 0
                adventure_section = "short"
            elif adventure_length == "2":
                max_encounters = random.randint(3, 6)
                event_chance = 8
                drop_rate_modifier = 0.03
                adventure_section = "adventure"
            else:  # Dungeon
                max_encounters = random.randint(6, 10)
                event_chance = 11
                drop_rate_modifier = 0.06
                adventure_section = "dungeon"

            # Load appropriate areas based on adventure type
            lines = load_file("locations.txt")
            main_areas = []
            sub_areas = []
            current_section = None
            
            for line in lines:
                if line == f"# {adventure_section.capitalize()} Trip Areas":
                    current_section = None
                elif line == "# Main Areas":
                    current_section = "main"
                elif line == "# Sub Areas":
                    current_section = "sub"
                elif current_section is not None and line.strip() and not line.startswith("#"):
                    if current_section == "main":
                        main_areas.append(line)
                    elif current_section == "sub":
                        sub_areas.append(line)

            if not main_areas or not sub_areas:
                print("Warning: No areas loaded for this adventure type. Using defaults.")
                main_areas = ["Forest", "Desert", "Mountain"]
                sub_areas = ["Castle", "Cave", "Village"]

            main_area = random.choice(main_areas)
            sub_area = random.choice(sub_areas)
            location = f"{main_area} {sub_area}"
            print(f"\nYou set out for the {location}!")

            monsters = load_json("monster.json")["monsters"]
            encounter_pool = []
            for m in monsters:
                if not m["rare"]:
                    min_monster_level = m["level_range"]["min"]
                    max_monster_level = m["level_range"]["max"]
                    if min_monster_level <= player.level + 2 and max_monster_level >= player.level - 2:
                        encounter_pool.extend([m] * m["spawn_chance"])
            if not encounter_pool:
                print("Warning: No suitable monsters found for your level. Using fallback.")
                encounter_pool = [m for m in monsters if not m["rare"]][:1]

            boss_fight = False
            encounter_count = 0
            combat_count = 0
            completed_encounters = 0
            gear_drops = []
            treasure_count = 0
            total_xp = 0
            total_gold = player.gold
            adventure = True

            while adventure:
                if encounter_count >= max_encounters:
                    if encounter_count >= 8 and not boss_fight and random.random() < 0.25:
                        print(f"\nA powerful foe blocks your path! Fight the boss?")
                        print("1. Yes | 2. No")
                        boss_choice = input("Selection: ")
                        if boss_choice == "1":
                            boss_fight = True
                            boss_monsters = [m for m in monsters if m["rare"] and m["spawn_chance"] > 0]
                            boss = random.choice(boss_monsters) if boss_monsters else random.choice([m for m in monsters if not m["rare"]])
                            result = combat(player, True, boss["name"])
                            if player.hp <= 0:
                                print("\nYou have died!")
                                if os.path.exists("save.json"):
                                    os.remove("save.json")
                                print("Game Over.")
                                return
                            if "Victory" in result:
                                completed_encounters += 1
                                update_kill_count(player, result.split("against ")[1])
                                total_xp += player.pending_xp
                            adventure = False  # End after boss decision
                        else:
                            adventure = False  # Full completion

                if adventure:
                    encounter_count += 1
                    Encounters = []

                    if random.randint(1, 100) <= event_chance:
                        max_encounters = random_event(player, encounter_count, max_encounters)
                        if "Treasure Chest" in player.inventory:
                            treasure_count += player.inventory.count("Treasure Chest")
                            while "Treasure Chest" in player.inventory:
                                player.inventory.remove("Treasure Chest")
                                award_treasure_chest(player)
                    else:
                        combat_count += 1
                        monster = random.choice(encounter_pool)
                        result = combat(player, False, monster["name"])
                        Encounters.append(result)

                        if player.hp <= 0:
                            print("\nYou have died!")
                            if os.path.exists("save.json"):
                                os.remove("save.json")
                            print("Game Over.")
                            return

                        if "Victory" in result:
                            completed_encounters += 1
                            parts = result.split(" ")
                            monster_name = parts[2]
                            xp_gained = int(parts[3])
                            gold_gained = int(parts[4])
                            print(f"\nVictory! Gained {xp_gained} XP and {gold_gained} gold!")
                            update_kill_count(player, monster_name)
                            total_gold += gold_gained
                        else:
                            print("You avoid the boss and head back to town.")
                            adventure = False
                        break

                    encounter_count += 1
                    Encounters = []  # Changed: Moved inside loop to reset per encounter

                    if random.randint(1, 100) <= event_chance:
                        max_encounters = random_event(player, encounter_count, max_encounters)
                        if "Treasure Chest" in player.inventory:
                            treasure_count += player.inventory.count("Treasure Chest")
                            while "Treasure Chest" in player.inventory:
                                player.inventory.remove("Treasure Chest")
                                award_treasure_chest(player)
                    else:
                        combat_count += 1
                        monster = random.choice(encounter_pool)
                        result = combat(player, False, monster["name"])
                        Encounters.append(result)

                        if player.hp <= 0:
                            print("\nYou have died!")
                            if os.path.exists("save.json"):  # Changed: Updated to save.json from save.txt
                                os.remove("save.json")
                            print("Game Over.")
                            return

                        if "Victory" in result:
                            completed_encounters += 1
                            parts = result.split(" ")
                            monster_name = parts[2]
                            xp_gained = int(parts[3])
                            gold_gained = int(parts[4])
                            print(f"\nVictory! Gained {xp_gained} XP and {gold_gained} gold!")
                            update_kill_count(player, monster_name)
                            total_gold += gold_gained
                            drop_item = None
                            gear = load_json("gear.json")
                            consumables = load_json("consumables.json")
                            valid_drops = []

                            for item in gear:
                                if (player.level >= item["level_range"]["min"] and 
                                    player.level <= item["level_range"]["max"] and 
                                    item.get("drop_rate", 0) > 0 and
                                    (not item.get("boss_only", False) or boss_fight)):
                                    # Add the drop rate modifier to the item's base drop rate
                                    modified_drop_rate = item["drop_rate"] * (1 + drop_rate_modifier)
                                    valid_drops.append((item["name"], modified_drop_rate))

                            for item in consumables:
                                if (player.level >= item["level_range"]["min"] and 
                                    player.level <= item["level_range"]["max"] and 
                                    item.get("drop_rate", 0) > 0 and 
                                    (not item["boss_only"] or boss_fight)):
                                    # Add the drop rate modifier to the item's base drop rate
                                    modified_drop_rate = item["drop_rate"] * (1 + drop_rate_modifier)
                                    valid_drops.append((item["name"], modified_drop_rate))

                            if valid_drops and random.random() < 0.25:  # Keep the base 25% chance to get a drop
                                items = [item[0] for item in valid_drops]
                                weights = [item[1] for item in valid_drops]
                                drop_item = random.choices(items, weights=weights, k=1)[0]
                                gear_drops.append(drop_item)
                                player.inventory.append(drop_item)
                                print(f"\nYou found a {drop_item}!")

                            # Apply the same modifier to treasure chest chance
                            if random.random() < (0.15 * (1 + drop_rate_modifier)) or (boss_fight and random.random() < 0.5):
                                treasure_count += 1

                            total_xp += player.pending_xp
                            total_gold += player.gold - total_gold

                        elif "FleeAdventure" in result:
                            print(f"\nYou escaped the {location}, ending your adventure with {completed_encounters} victories.")
                            adventure = False

                        if combat_count > 0 and player.hp < player.max_hp / 2 and adventure:
                            print(f"\nYou've fought {combat_count} battles in the {location}. HP: {round(player.hp, 1)}/{player.max_hp}")
                            print("Continue adventure? 1 for Yes | 2 for No")
                            choice = input("Selection: ")
                            if choice == "2":
                                print(f"You decide to return to town with {completed_encounters} victories.")
                                adventure = False
                            elif choice != "1":
                                print("Invalid choice, continuing adventure.")

                # End adventure here
                end_adventure(player, location, completed_encounters, gear_drops, treasure_count, total_xp, total_gold)

        elif choice == "2":
            inventory_menu(player)

        elif choice == "3":
            print(f"\nStats: S:{player.stats['S']} A:{player.stats['A']} I:{player.stats['I']} W:{player.stats['W']} L:{player.stats['L']}")
            print(f"Level: {player.level} | XP: {player.exp}/{player.max_exp}")
            from combat import get_weapon_damage_range
            min_dmg, max_dmg = get_weapon_damage_range(player)
            attack_dps = (min_dmg + max_dmg) / 2 if min_dmg and max_dmg else 0
            print(f"Attack DPS: {round(attack_dps, 1)} (avg weapon damage per turn)")
            
            skills = load_json("skills.json")["skills"]
            total_skill_dps = 0
            skill_count = 0
            for skill in skills:
                if skill["name"] in player.skills:
                    # Handle both old and new skill formats like combat.py
                    effects = skill.get("effects", [{"type": skill.get("effect", "direct_damage"), 
                                                    "base_dmg": skill.get("base_dmg", 0), 
                                                    "duration": skill.get("duration", 0), 
                                                    "stat": skill.get("stat", "none")}]),
                    mp_cost = skill.get("mp_cost", 1)

                    # Aggregate base damage and determine key properties from effects
                    base_dmg = 0
                    duration = 0
                    stat = "none"
                    effect_types = []
                    for effect in effects[0]:  # Unpack the tuple returned by get()
                        if effect["type"] in ["direct_damage", "damage_bonus", "damage_over_time"]:
                            base_dmg += effect.get("base_dmg", 0)
                        duration = max(duration, effect.get("duration", 0))
                        if effect.get("stat", "none") != "none":
                            stat = effect["stat"]
                        effect_types.append(effect["type"])

                    scaled_dmg = base_dmg
                    if stat != "none":
                        if "damage_bonus" in effect_types:
                            scaled_dmg = base_dmg + (player.stats[stat] * 0.5)
                        elif "direct_damage" in effect_types:
                            scaled_dmg = base_dmg + (player.stats[stat] * 1.0)
                        elif "damage_over_time" in effect_types:
                            scaled_dmg = base_dmg + (player.stats[stat] * 0.2)
                        elif "heal" in effect_types or "heal_over_time" in effect_types:
                            scaled_dmg = base_dmg + (player.stats[stat] * 0.5)
                        elif effect_types in [["armor_bonus"], ["dodge_bonus"]]:
                            scaled_dmg = base_dmg + (player.stats[stat] * 0.5)

                    # Calculate DPS based on effect type
                    if "direct_damage" in effect_types and duration == 0:
                        dps = scaled_dmg
                    elif any(e in ["damage_bonus", "damage_over_time"] for e in effect_types):
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

        elif choice == "4":
            shop_menu(player)

        elif choice == "5":
            tavern_menu(player)

        elif choice == "6":
            guild_menu(player)

        elif choice == "7":
            save_game(player)
            print("Game saved!")

        elif choice == "8":
            print("Goodbye!")
            break

        else:
            print("Invalid choice!")

def guild_menu(player):
    print("\n=== Adventurers' Guild ===")
    
    # If player is not in the guild yet
    if not hasattr(player, "guild_member") or not player.guild_member:
        print("Hello there adventurer. How may I help you?")
        print("1. Join | 2. Leave")
        choice = input("Selection: ")
        
        if choice == "1":
            if player.level < 3:
                print("I'm sorry but you seem to be lacking. We do not have work for you.")
                return
            else:
                player.guild_member = True
                player.adventurer_rank = 0
                player.adventurer_points = 0
                player.max_adventurer_points = 10
                print("Welcome to the Adventurers' Guild! You start at the lowest rank with 0 points.")
                save_game(player)
                return
        elif choice == "2":
            return
        else:
            print("Invalid choice!")
            return
    
    # If player is already in the guild
    quests_data = load_json("quest.json")
    lore_data = load_json("lore.json")
    quests = quests_data.get("quests", [])
    lore = lore_data.get("lore", [])
    
    active_quests = player.active_quests
    completed_quests = player.completed_quests if hasattr(player, "completed_quests") else []
    
    print(f"Current Rank: {player.get_rank_name()} Adventurer")
    print(f"Adventurer Points: {player.adventurer_points}/{player.max_adventurer_points}")
    if player.adventurer_rank < 6:
        next_rank_points = player.get_next_rank_points()
        print(f"Points needed for next rank: {next_rank_points}")
    print("\n1. Accept Quest | 2. Turn In Quest | 0. Return")
    choice = input("Selection: ")

    if choice == "1":
        if len(active_quests) >= 5:
            print("You've reached the maximum of 5 active quests.")
            return
        
        available_quests = [
            q for q in quests 
            if player.level >= q["quest_level"] 
            and player.adventurer_rank >= q["required_rank"]
            and q["quest_name"] not in [aq["quest_name"] for aq in active_quests] 
            and q["quest_name"] not in completed_quests
        ]
        if not available_quests:
            print("No new quests available at your current rank.")
        else:
            print("\nAvailable Quests:")
            for i, quest in enumerate(available_quests, 1):
                print(f"{i}. {quest['quest_name']} (Level {quest['quest_level']})")
                print(f"   {quest['quest_description']}")
                print(f"   Reward: {quest['quest_reward']} | Points: {quest['adventure_points']}")
            quest_choice = input("Select a quest to accept (or 0 to return): ")
            if quest_choice == "0":
                return
            try:
                quest_index = int(quest_choice) - 1
                if 0 <= quest_index < len(available_quests):
                    selected_quest = available_quests[quest_index]
                    active_quests.append({"quest_name": selected_quest["quest_name"], "kill_count": 0})
                    player.active_quests = active_quests
                    print(f"Accepted quest: {selected_quest['quest_name']}")
                    
                    lore_entry = next((l for l in lore if l["quest_name"] == selected_quest["quest_name"]), None)
                    if lore_entry:
                        lore_choice = input("Would you like to read the lore? (y/n): ").lower()
                        if lore_choice == "y":
                            print(f"\nLore for '{selected_quest['quest_name']}':")
                            print(lore_entry["lore_text"])
                else:
                    print(f"Invalid selection. Choose between 1 and {len(available_quests)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    elif choice == "2":
        turn_in_quest(player)

def turn_in_quest(player):
    if not player.active_quests:
        print("\nYou have no active quests to turn in.")
        return

    print("\nActive Quests:")
    for i, quest in enumerate(player.active_quests, 1):
        print(f"{i}. {quest['quest_name']} - {quest['quest_description']}")

    while True:
        try:
            choice = int(input("\nEnter the number of the quest to turn in (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(player.active_quests):
                break
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    quest = player.active_quests[choice - 1]
    player.active_quests.remove(quest)
    player.completed_quests.append(quest)

    # Handle quest rewards
    rewards = quest['quest_reward'].split(", ")
    for reward in rewards:
        if "gold" in reward.lower():
            amount = int(reward.split()[0])
            player.gold += amount
            print(f"\nYou received {amount} gold!")
        else:
            # Handle item rewards
            item_name = reward
            item = find_item_by_name(item_name)
            if item:
                player.inventory.append(item)
                print(f"\nYou received {item_name}!")

    # Handle adventurer points
    if 'adventure_points' in quest and quest['adventure_points'] is not None:
        points = quest['adventure_points']
        current_points = player.apply_adventurer_points(points)
        print(f"\nYou received {points} Adventurer Points! Current points: {current_points}/{player.max_adventurer_points}")
        print(f"Current Rank: {player.get_rank_name()}")

    print("\nQuest completed successfully!")

def end_adventure(player, location, completed_encounters, gear_drops, treasure_count, total_xp, total_gold):
    gear_summary = f"{len(gear_drops)} piece{'s' if len(gear_drops) != 1 else ''} of gear" if gear_drops else "no gear"
    treasure_summary = f"{treasure_count} piece{'s' if treasure_count != 1 else ''} of treasure" if treasure_count else "no treasure"
    gold_gained = player.gold - total_gold
    print(f"\nAdventure complete! Returning to town with {gear_summary}, {treasure_summary} from {completed_encounters} victories.")
    if gear_drops:
        gear_counts = {}
        for item in gear_drops:
            gear_counts[item] = gear_counts.get(item, 0) + 1
        for item, count in gear_counts.items():
            suffix = f" x{count}" if count > 1 else ""
            print(f"- Found {item}{suffix}")
    if treasure_count > 0:
        print(f"- Found {treasure_count} Treasure Chest{'s' if treasure_count > 1 else ''}")
        for _ in range(treasure_count):
            award_treasure_chest(player)
    print(f"Total gold gained: {gold_gained}")
    print(f"Current XP: {player.exp}/{player.max_exp}")
    tavern = Tavern(player)
    tavern.roll_tavern_npcs()

if __name__ == "__main__":
    main()