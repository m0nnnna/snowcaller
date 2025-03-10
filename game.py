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

# Add the current directory to sys.path to find update.py
sys.path.append(os.path.dirname(__file__))

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

def main():
    # Check for updates before anything else
    check_for_updates()

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
                print(line)
        except Exception as e:
            print(f"Error loading {selected_class['name']} art: {e}")
            print(f"(Imagine a grand {selected_class['name']} here!)")
        
        # Display class lore
        print(f"\n{selected_class['lore']}")
        time.sleep(2)

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
                monsters = load_json("monster.json")["monsters"]
                encounter_pool = []
                for m in monsters:
                    if not m["rare"]:
                        min_monster_level = m["level_range"]["min"]
                        max_monster_level = m["level_range"]["max"]
                        if (min_monster_level <= player.level + 2 and max_monster_level >= player.level - 2):
                            encounter_pool.extend([m] * m["spawn_chance"])
                if not encounter_pool:
                    print("Warning: No suitable monsters found for your level. Using fallback.")
                    encounter_pool = [m for m in monsters if not m["rare"]][:1]

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
                                boss_monsters = [m for m in monsters if m["rare"] and m["spawn_chance"] > 0]
                                boss = random.choice(boss_monsters) if boss_monsters else random.choice([m for m in monsters if not m["rare"]])
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

if __name__ == "__main__":
    main()