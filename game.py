import os
import time
import random
from player import Player, save_game, load_game
from combat import combat
from shop import shop_menu, parse_shop_item, calculate_price
from tavern import tavern_menu
from events import random_event
from utils import load_file, parse_stats

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
    
    if len(bracket) != 7:  # Now 7 elements with ScalingStat
        print(f"Warning: Invalid gear format: {gear_line}")
        return (1, 1), 0.0, False
    
    try:
        level_part, slot, scaling_stat, stats, damage, drop_rate, gold = bracket
        min_level, max_level = map(int, level_part[2:].split("-"))
        drop_chance = float(drop_rate[:-1]) / 100
        if not (level_part.startswith("L:") and drop_rate.endswith("%") and scaling_stat in ["S", "A", "I", "W", "L"]):
            raise ValueError("Invalid level, drop rate, or scaling stat format")
        return (min_level, max_level), drop_chance, is_rare
    except (ValueError, IndexError) as e:
        print(f"Error parsing gear '{gear_line}': {e}. Using defaults.")
        return (1, 1), 0.0, False

def display_inventory(player):
    gear = load_file("gear.txt")
    print("\nStandard Items:", ", ".join([item for item in player.inventory if not any(item == g.split()[0] for g in gear)]) if any(item not in [g.split()[0] for g in gear] for item in player.inventory) else "No standard items in inventory!")
    print("Equipment:")
    for slot, item in player.equipment.items():
        if item:
            item_name, stats, scaling_stat, armor_value = item  # Unpack the tuple
            stat_display = ", ".join([f"+{val} {stat[:3].capitalize()}" for stat, val in stats.items() if val > 0])
            
            # Look up damage from gear.txt
            damage = "none"
            for g in gear:
                gear_name = g.split('[')[0].strip()  # Get name before bracket
                if gear_name == item_name:
                    bracket = g.split('[')[1].strip("]").split()
                    damage = bracket[4]  # Damage field (e.g., "1-3" or "none")
                    break
            
            # Build display string
            parts = []
            if stat_display:
                parts.append(stat_display)
            parts.append(f"AV:{armor_value}")
            if damage != "none":
                parts.append(f"Dmg:{damage}")
            display_str = f"{item_name} ({', '.join(parts)})"
            print(f"{slot.capitalize()}: {display_str}")
        else:
            print(f"{slot.capitalize()}: None")

def inventory_menu(player):
    gear = load_file("gear.txt")
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
                    compatible_items = [item for item in player.inventory if any(" ".join(g.split()[:-1]) == item and g.split()[-1].strip("[]").split()[1] == selected_slot for g in gear)]
                    if not compatible_items and not player.equipment[selected_slot]:
                        print("No compatible gear for this slot!")
                        time.sleep(0.5)
                        continue
                    print(f"\nAvailable gear for {selected_slot.capitalize()}:")
                    for idx, item in enumerate(compatible_items, 1):
                        for g in gear:
                            gear_name = g.split('[')[0].strip()
                            if gear_name == item:
                                bracket = g.split('[')[1].strip("]").split()
                                stats = parse_stats(bracket[3], is_consumable=False)
                                stat_display = ", ".join([f"+{val} {stat[:3].capitalize()}" for stat, val in stats.items() if val > 0])
                                armor_value = int(bracket[5].split(":")[1])
                                damage = bracket[4]
                                parts = [stat_display] if stat_display else []
                                parts.append(f"AV:{armor_value}")
                                if damage != "none":
                                    parts.append(f"Dmg:{damage}")
                                display_str = f"{item} ({', '.join(parts)})"
                                print(f"{idx}. {display_str}")
                                break
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
                            if player.equipment[selected_slot]:
                                old_item = player.equipment[selected_slot][0]
                                player.inventory.append(old_item)
                                for stat, val in player.equipment[selected_slot][1].items():
                                    player.stats[stat] -= val
                            for g in gear:
                                parts = g.split()
                                if " ".join(parts[:-1]) == new_item:
                                    bracket = parts[-1].strip("[]").split()
                                    stats = parse_stats(bracket[3], is_consumable=False)
                                    scaling_stat = bracket[2]
                                    armor_value = int(bracket[5].split(":")[1])
                                    player.equipment[selected_slot] = (new_item, stats, scaling_stat, armor_value)
                                    for stat, val in stats.items():
                                        player.stats[stat] += val
                                    break
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
    treasures = load_file("treasures.txt")
    chest_type = random.choices(["unlocked", "locked", "magical"], weights=[70, 20, 10], k=1)[0]
    print(f"\nYou find a {chest_type} treasure chest!")
    time.sleep(0.5)

    if chest_type == "unlocked":
        items = random.sample(treasures, random.randint(1, 2))
        gold = random.randint(10, 25)
        player.inventory.extend(items)
        player.gold += gold
        print(f"You open it and find: {', '.join(items)} and {gold} gold!")
        time.sleep(0.5)

    elif chest_type == "locked":
        if random.random() < player.stats["A"] * 0.05:
            items = random.sample(treasures, random.randint(1, 3))
            gold = random.randint(15, 30)
            player.inventory.extend(items)
            player.gold += gold
            print(f"You pick the lock and find: {', '.join(items)} and {gold} gold!")
            time.sleep(0.5)
        else:
            print("The lock holds firm—you leave empty-handed.")
            time.sleep(0.5)

    elif chest_type == "magical":
        if random.random() < player.stats["I"] * 0.05:
            items = random.sample(treasures, random.randint(2, 4))
            gold = random.randint(20, 40)
            player.inventory.extend(items)
            player.gold += gold
            print(f"You dispel the ward and find: {', '.join(items)} and {gold} gold!")
            time.sleep(0.5)
        else:
            damage = player.max_hp * 0.1
            player.hp -= damage
            print(f"The ward backfires, dealing {round(damage, 1)} damage!")
            time.sleep(0.5)

def main():
    if os.path.exists("save.txt"):
        print("1. New Game | 2. Load Game")
        time.sleep(0.5)
        choice = input("Selection: ")
        if choice == "2":
            try:
                player = load_game()
                print(f"Welcome back, {player.name}!")
                time.sleep(0.5)
            except:
                print("Save file corrupted! Starting new game.")
                time.sleep(0.5)
                choice = "1"
        else:
            choice = "1"
    else:
        choice = "1"

    if choice == "1":
        name = input("Enter your name: ")
        print("Select your class:")
        print("1. Warrior (High Strength) | 2. Mage (High Intelligence) | 3. Rogue (High Agility)")
        time.sleep(0.5)
        class_type = input("Selection: ")
        while class_type not in ["1", "2", "3"]:
            print("Invalid class! Choose 1, 2, or 3.")
            class_type = input("Selection: ")
        player = Player(name, class_type)
        print(f"Welcome, {player.name} the {'Warrior' if class_type == '1' else 'Mage' if class_type == '2' else 'Rogue'}!")
        if player.skills:  # Only print if skills were assigned in __init__
            print(f"Skills unlocked: {', '.join(player.skills)}")
        time.sleep(0.5)
        
    # Autosave after player setup (new or loaded)
    save_game(player)
    print("Game autosaved!")
    time.sleep(0.5)

    while True:
        print(f"\n{'-' * 20} {player.name}: Level {player.level} {'-' * 20}")
        print(f"HP: {round(player.hp, 1)}/{player.max_hp} | MP: {player.mp}/{player.max_mp} | Gold: {player.gold}")
        print("1. Adventure | 2. Inventory | 3. Stats | 4. Shop | 5. Tavern | 6. Save | 7. Quit")
        time.sleep(0.5)
        choice = input("Selection: ")

        if choice == "1":
            with open("locations.txt", "r") as f:
                lines = [line.strip() for line in f if line.strip()]
            
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
            
            main_area = random.choice(main_areas)
            sub_area = random.choice(sub_areas)
            location = f"{main_area} {sub_area}"
            print(f"\nYou set out for the {location}!")
            time.sleep(0.5)
            max_encounters = random.randint(2, 10)
            boss_fight = False
            encounter_count = 0  # Total attempts (combat + events)
            combat_count = 0     # Only combat encounters
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
                            result = combat(player, True)
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
                        else:
                            print("You avoid the boss and head back to town.")
                            time.sleep(0.5)
                    adventure = False
                    break

                encounter_count += 1
                Encounters = []

                # Random event or combat
                if random.randint(1, 100) <= event_chance:
                    max_encounters = random_event(player, encounter_count, max_encounters)
                else:
                    combat_count += 1
                    result = combat(player, False)
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
                        drop_item = None
                        gear = load_file("gear.txt")
                        consumables = load_file("consumables.txt")
                        valid_drops = []

                        for g in gear:
                            level_range, drop_chance, is_rare = parse_gear_drop_info(g)
                            if level_range and player.level >= level_range[0] and player.level <= level_range[1] and (not is_rare or boss_fight):
                                valid_drops.append((g.split()[0], drop_chance))

                        from items import parse_consumable
                        for c in consumables:
                            consumable = parse_consumable(c)
                            if consumable and player.level >= consumable["level_range"][0] and player.level <= consumable["level_range"][1]:
                                if not consumable["is_rare"] or boss_fight:
                                    valid_drops.append((consumable["name"], consumable["drop_rate"]))

                        if valid_drops and random.random() < 0.25:
                            drop_item = random.choices(
                                [item[0] for item in valid_drops],
                                weights=[item[1] for item in valid_drops],
                                k=1
                            )[0]
                            player.inventory.append(drop_item)
                            print(f"\nYou found a {drop_item}!")
                            time.sleep(0.5)

                        if random.random() < 0.15 or (boss_fight and random.random() < 0.5):
                            treasure_inventory.append("Treasure Chest")

                    elif Encounters and "FleeAdventure" in Encounters[-1]:
                        print(f"\nYou escaped the {location}, ending your adventure with {completed_encounters} victories.")
                        time.sleep(0.5)
                        adventure = False
                        break

                # Prompt only if HP < 50% of max after combat
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
                if choice != "2":  # Only award chests if not manually ending early
                    for _ in range(len(treasure_inventory)):
                        award_treasure_chest(player)
            
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
            
            # Calculate Attack DPS
            from combat import get_weapon_damage_range
            min_dmg, max_dmg = get_weapon_damage_range(player)
            attack_dps = (min_dmg + max_dmg) / 2
            print(f"Attack DPS: {round(attack_dps, 1)} (avg weapon damage per turn)")
            
            # Calculate Skill DPS
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
                if name in player.skills:  # Only count unlocked skills
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
                        # "heal" excluded from DPS
                    
                    if effect == "direct_damage" and duration == 0:
                        dps = scaled_dmg  # One-time damage
                    elif effect in ["damage_bonus", "damage_over_time"]:
                        # Spread damage over duration + MP recovery turns
                        total_turns = max(1, mp_cost) + duration  # Approximate MP recharge
                        dps = (scaled_dmg * duration) / total_turns if duration > 0 else 0
                    else:
                        dps = 0  # Heal or invalid effect
                    
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
            save_game(player)
            print("Game saved!")
            time.sleep(0.5)

        elif choice == "7":
            print("Goodbye!")
            time.sleep(0.5)
            break

        else:
            print("Invalid choice!")
            time.sleep(0.5)

if __name__ == "__main__":
    main()