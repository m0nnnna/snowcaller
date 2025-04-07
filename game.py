import os
import sys
import time
import builtins
import random
import json
import importlib
import shutil
import textwrap
import re
from colorama import init, Fore, Back, Style
from player import Player, save_game, load_game
from combat import combat
from shop import shop_menu, calculate_price
from tavern import tavern_menu, Tavern
from guild import Guild
from events import random_event
from utils import load_json, load_file, load_art_file, parse_stats, get_resource_path, save_json
from commands import handle_command

# Initialize colorama
init()

# Global sleep delay (in seconds)
MENU_DELAY = 0.0005  # Very fast for menus
TEXT_DELAY = 0.001   # Fast for normal text
ANIMATION_DELAY = 0.005  # Normal for special animations

# Store the original print function
_original_print = builtins.print

def progress_bar(progress, total, length=50, fill='█', empty='░'):
    """Display a progress bar animation."""
    percent = progress / total
    filled_length = int(length * percent)
    bar = fill * filled_length + empty * (length - filled_length)
    _original_print(f'\r[{bar}] {int(percent * 100)}%', end='', flush=True)

def spinning_cursor():
    """Display a spinning cursor animation."""
    while True:
        for cursor in '|/-\\':
            yield cursor

def fade_text(text, steps=10, delay=0.05):
    """Create a fade-in effect for text."""
    for i in range(steps):
        alpha = i / steps
        faded_text = f"\033[38;2;255;255;255;{int(alpha * 255)}m{text}\033[0m"
        _original_print(faded_text, end='\r', flush=True)
        time.sleep(delay)
    _original_print(text)

def pulse_text(text, cycles=3, delay=0.1):
    """Create a pulsing effect for text."""
    for _ in range(cycles):
        for i in range(10):
            brightness = int(255 * (i / 10))
            _original_print(f"\033[38;2;{brightness};{brightness};{brightness}m{text}\033[0m", end='\r', flush=True)
            time.sleep(delay)
        for i in range(10, 0, -1):
            brightness = int(255 * (i / 10))
            _original_print(f"\033[38;2;{brightness};{brightness};{brightness}m{text}\033[0m", end='\r', flush=True)
            time.sleep(delay)
    _original_print(text)

def scroll_text(text, width=80, delay=0.05):
    """Create a scrolling text effect."""
    if len(text) <= width:
        return text
    
    for i in range(len(text) - width + 1):
        _original_print(f"\r{text[i:i+width]}", end='', flush=True)
        time.sleep(delay)
    return text[-width:]

def format_text(text, color=Fore.WHITE, style=Style.NORMAL, width=80):
    """Format text with color, style, and proper wrapping."""
    # Wrap text to specified width
    wrapped_text = textwrap.fill(text, width=width)
    # Apply color and style
    return f"{style}{color}{wrapped_text}{Style.RESET_ALL}"

def print_section(title, color=Fore.CYAN):
    """Print a section header with a border."""
    border = "=" * 80
    _original_print(format_text(border, color))
    _original_print(format_text(title.center(80), color))
    _original_print(format_text(border, color))

def print_important(text, color=Fore.YELLOW):
    """Print important information with emphasis."""
    _original_print(format_text(f"! {text} !", color, Style.BRIGHT))

def print_menu_item(number, text, color=Fore.GREEN):
    """Print a menu item with consistent formatting."""
    _original_print(format_text(f"{number}. {text}", color))

# Override print to include a typing animation and formatting
def print(*args, **kwargs):
    # Get the text to print
    text = " ".join(str(arg) for arg in args)
    
    # Determine color, style, and animation from kwargs
    color = kwargs.pop('color', Fore.WHITE)
    style = kwargs.pop('style', Style.NORMAL)
    animation = kwargs.pop('animation', 'type')  # Default to typing animation
    is_menu = kwargs.pop('is_menu', False)  # New parameter for menu text
    
    # Format the text
    formatted_text = format_text(text, color, style)
    
    # Choose appropriate delay based on context
    delay = MENU_DELAY if is_menu else TEXT_DELAY
    
    if animation == 'type':
        # Print character by character with appropriate delay
        for char in formatted_text:
            _original_print(char, end='', flush=True)
            time.sleep(delay)
    elif animation == 'fade':
        fade_text(formatted_text)
    elif animation == 'pulse':
        pulse_text(formatted_text)
    elif animation == 'scroll':
        scroll_text(formatted_text)
    
    # Print newline if needed
    if not kwargs.get('end', ''):
        _original_print()
    
    # Add a small delay after each line
    time.sleep(delay * 2)

# Replace the built-in print with our version
builtins.print = print

# Import the update checker
try:
    # Get the directory containing the game files
    if getattr(sys, 'frozen', False):
        # If running as a compiled executable
        base_path = os.path.dirname(sys.executable)
    else:
        # If running as a script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Add the base path to Python's path
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
    
    from update import check_for_updates
except (ImportError, ModuleNotFoundError) as e:
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
        print("Warning: No quests found in quest.json!", color=Fore.RED, animation='pulse')
        return
    
    for quest in player.active_quests:
        quest_info = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
        if quest_info is None:
            print(f"Warning: Quest '{quest['quest_name']}' in active_quests not found in quest.json!", 
                  color=Fore.RED, animation='pulse')
            continue
        if "target_monster" not in quest_info:
            print(f"Warning: Quest '{quest['quest_name']}' in quest.json missing 'target_monster' key!", 
                  color=Fore.RED, animation='pulse')
            continue
        if quest_info["target_monster"] == monster_name:
            quest["kill_count"] = quest.get("kill_count", 0) + 1
            progress_text = f"Progress on '{quest['quest_name']}': {quest['kill_count']}/{quest_info['kill_count_required']} {monster_name}s killed."
            print(progress_text, color=Fore.YELLOW, animation='fade')

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
        
        # Display class lore
        print(f"\n{selected_class['lore']}")

        print(f"Welcome, {player.name} the {selected_class['name']}!")
        if player.skills:
            print(f"Skills unlocked: {', '.join(player.skills)}")

    save_game(player)
    print("Game autosaved!")

    # Initialize Tavern and Guild instances
    tavern = Tavern(player)
    guild = Guild(player)

    while True:
        print(f"\n{'-' * 20} {player.name}: Level {player.level} {'-' * 20}")
        print(f"HP: {round(player.hp, 1)}/{player.max_hp} | MP: {player.mp}/{player.max_mp} | Gold: {player.gold}")
        print("1. Adventure | 2. Inventory | 3. Stats | 4. Shop | 5. Tavern | 6. Guild | 7. Save | 8. Quit", is_menu=True)
        choice = input("Selection: ").strip().lower()
        if handle_command(choice, player, commands_enabled):
            continue

        if choice == "1":
            print("\nChoose your adventure type:")
            print("1. Short Trip (2-3 encounters)", is_menu=True)
            print("2. Adventure (3-6 encounters)", is_menu=True)
            print("3. Dungeon (6-10 encounters)", is_menu=True)
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

            # Initialize adventure variables
            boss_fight = False
            encounter_count = 0
            combat_count = 0
            completed_encounters = 0
            gear_drops = []
            treasure_count = 0
            total_xp = 0
            total_gold = 0
            initial_gold = player.gold  # Track initial gold to calculate gain correctly
            adventure = True
            
            print(f"\nYou set out for the {location}! (Planning for {max_encounters} encounters)")

            while adventure:
                # Boss encounter check
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
                                total_gold += gold_gained
                        adventure = False  # End after boss fight regardless of choice
                        continue

                # Regular encounter
                if random.randint(1, 100) <= event_chance:
                    encounter_count += 1
                    completed_encounters += 1
                    new_max = random_event(player, encounter_count, max_encounters)
                    if new_max > max_encounters:
                        print(f"\nAdventure extended! New maximum encounters: {new_max}", color=Fore.YELLOW)
                        max_encounters = new_max
                    if "Treasure Chest" in player.inventory:
                        treasure_count += player.inventory.count("Treasure Chest")
                        while "Treasure Chest" in player.inventory:
                            player.inventory.remove("Treasure Chest")
                            award_treasure_chest(player)
                else:
                    encounter_count += 1
                    combat_count += 1
                    monster = random.choice(encounter_pool)
                    result = combat(player, False, monster["name"])

                    if player.hp <= 0:
                        print("\nYou have died!")
                        if os.path.exists("save.json"):
                            os.remove("save.json")
                        print("Game Over.")
                        return

                    if "Victory" in result:
                        completed_encounters += 1
                        # Remove ANSI color codes before parsing
                        clean_result = re.sub(r'\x1b\[[0-9;]*m', '', result)
                        parts = clean_result.split(" ")
                        monster_name = parts[2]
                        
                        # Find gold and XP values
                        gold_gained = 0
                        xp_gained = 0
                        for i, part in enumerate(parts):
                            if part == "gold" and i > 0 and parts[i-1].isdigit():
                                gold_gained = int(parts[i-1])
                            elif part == "XP" and i > 0 and parts[i-1].isdigit():
                                xp_gained = int(parts[i-1])
                        
                        # Update totals before displaying victory message
                        total_xp += xp_gained
                        total_gold += gold_gained
                        
                        # Combine victory messages into a single print
                        victory_text = f"\nVictory! Gained {xp_gained} XP and {gold_gained} gold! (Total: {total_xp} XP, {total_gold} gold)"
                        print(victory_text, color=Fore.GREEN, animation='type', is_menu=True)
                        update_kill_count(player, monster_name)
                        
                        # Handle drops
                        drop_item = None
                        gear = load_json("gear.json")
                        consumables = load_json("consumables.json")
                        valid_drops = []

                        for item in gear:
                            if (player.level >= item["level_range"]["min"] and
                                player.level <= item["level_range"]["max"] and
                                item.get("drop_rate", 0) > 0 and
                                (not item.get("boss_only", False) or boss_fight)):
                                modified_drop_rate = item["drop_rate"] * (1 + drop_rate_modifier)
                                valid_drops.append((item["name"], modified_drop_rate))

                        for item in consumables:
                            if (player.level >= item["level_range"]["min"] and
                                player.level <= item["level_range"]["max"] and
                                item.get("drop_rate", 0) > 0 and
                                (not item["boss_only"] or boss_fight)):
                                modified_drop_rate = item["drop_rate"] * (1 + drop_rate_modifier)
                                valid_drops.append((item["name"], modified_drop_rate))

                        if valid_drops and random.random() < 0.25:
                            items = [item[0] for item in valid_drops]
                            weights = [item[1] for item in valid_drops]
                            drop_item = random.choices(items, weights=weights, k=1)[0]
                            gear_drops.append(drop_item)
                            player.inventory.append(drop_item)
                            print(f"\nYou found a {drop_item}!")

                        if random.random() < (0.15 * (1 + drop_rate_modifier)) or (boss_fight and random.random() < 0.5):
                            treasure_count += 1

                        save_game(player)
                    elif "FleeAdventure" in result:
                        print(f"\nYou escaped the {location}, ending your adventure with {completed_encounters} victories.")
                        adventure = False
                        break

                    # Check if player wants to continue
                    if combat_count > 0 and player.hp < player.max_hp / 2 and adventure:
                        status_text = f"\nYou've fought {combat_count} battles in the {location}. HP: {round(player.hp, 1)}/{player.max_hp}"
                        print(status_text, color=Fore.YELLOW, animation='fade')
                        print("Continue adventure? 1 for Yes | 2 for No", color=Fore.CYAN)
                        choice = input("Selection: ")
                        if choice == "2":
                            print(f"You decide to return to town with {completed_encounters} victories.",
                                  color=Fore.YELLOW, animation='fade')
                            adventure = False
                            break
                        elif choice != "1":
                            print("Invalid choice, continuing adventure.", color=Fore.RED, animation='pulse')
                            
                # Check if we should end the adventure
                if encounter_count >= max_encounters and not (encounter_count >= 8 and not boss_fight):
                    print(f"\nReached maximum encounters ({max_encounters}). Returning to town.", color=Fore.YELLOW)
                    adventure = False
                    break

            # End adventure and show summary
            end_adventure(player, location, completed_encounters, gear_drops, treasure_count, total_xp, total_gold, tavern)

        elif choice == "2":
            inventory_menu(player)

        elif choice == "3":
            # Show player stats
            print(f"\n=== {player.name}'s Stats ===")
            print(f"Level: {player.level}")
            print(f"XP: {player.exp}/{player.max_exp}")
            print(f"HP: {round(player.hp, 1)}/{player.max_hp}")
            print(f"MP: {player.mp}/{player.max_mp}")
            print(f"Gold: {player.gold}")
            print("\nAttributes:")
            for stat, value in player.stats.items():
                print(f"{stat}: {value}")
            input("\nPress Enter to continue...")

        elif choice == "4":
            shop_menu(player)

        elif choice == "5":
            tavern.visit_tavern()

        elif choice == "6":
            guild.guild_menu(player)

        elif choice == "7":
            save_game(player)
            print("Game saved!")

        elif choice == "8":
            print("Goodbye!")
            break

        else:
            print("Invalid choice!")

def end_adventure(player, location, completed_encounters, gear_drops, treasure_count, total_xp, total_gold, tavern):
    print("\n" + "="*50)
    print("Adventure Summary".center(50))
    print("="*50)
    
    # Display encounter summary
    print(f"Location: {location}")
    print(f"Total Victories: {completed_encounters}")
    
    # Display gear summary
    gear_summary = f"{len(gear_drops)} piece{'s' if len(gear_drops) != 1 else ''} of gear" if gear_drops else "no gear"
    if gear_drops:
        print("\nGear found:")
        gear_counts = {}
        for item in gear_drops:
            gear_counts[item] = gear_counts.get(item, 0) + 1
        for item, count in gear_counts.items():
            suffix = f" x{count}" if count > 1 else ""
            print(f"- {item}{suffix}")
    
    # Display treasure summary
    if treasure_count > 0:
        print(f"\nTreasure Chests found: {treasure_count}")
        for _ in range(treasure_count):
            award_treasure_chest(player)
    
    # Display rewards summary
    print("\nRewards Summary:")
    print(f"Total gold gained: {total_gold}")
    print(f"Total XP gained: {total_xp}")
    print(f"Current XP progress: {player.exp}/{player.max_exp}")
    print("="*50)
    
    tavern.roll_tavern_npcs()
    # Save at the end of adventure
    save_game(player)

if __name__ == "__main__":
    main()