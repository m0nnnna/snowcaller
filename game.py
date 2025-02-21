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
        return None, None, False
    name = " ".join(parts[:-1])
    bracket = parts[-1][1:-1].split()
    is_rare = False
    if bracket[-1] == "[R]":
        bracket.pop()
        is_rare = True
    if len(bracket) != 6:
        print(f"Warning: Invalid gear format: {gear_line}")
        return None
    level_part, slot, stats, damage, drop_rate, gold = bracket
    min_level, max_level = map(int, level_part[2:].split("-"))
    drop_chance = float(drop_rate[:-1]) / 100
    return (min_level, max_level), drop_chance, is_rare

def display_inventory(player):
    gear = load_file("gear.txt")
    print("\nStandard Items:", ", ".join([item for item in player.inventory if not any(item == g.split()[0] for g in gear)]) if any(item not in [g.split()[0] for g in gear] for item in player.inventory) else "No standard items in inventory!")
    print("Equipment:")
    for slot, item in player.equipment.items():
        if item:
            stats = item[1]
            stat_display = ", ".join([f"+{val} {stat[:3].capitalize()}" for stat, val in stats.items() if val > 0])
            print(f"{slot.capitalize()}: {item[0]} ({stat_display})")
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
                    compatible_items = [item for item in player.inventory if any(g.split()[0] == item and g.split()[2] == selected_slot for g in gear)]
                    if not compatible_items and not player.equipment[selected_slot]:
                        print("No compatible gear for this slot!")
                        time.sleep(0.5)
                        continue
                    print(f"\nAvailable gear for {selected_slot.capitalize()}:")
                    for idx, item in enumerate(compatible_items, 1):
                        for g in gear:
                            if g.split()[0] == item:
                                stats = parse_stats(g.split()[1], is_consumable=False)
                                stat_display = ", ".join([f"+{val} {stat[:3].capitalize()}" for stat, val in stats.items() if val > 0])
                                print(f"{idx}. {item} ({stat_display})")
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
                                if g.split()[0] == new_item:
                                    stats = parse_stats(g.split()[1], is_consumable=False)
                                    player.equipment[selected_slot] = (new_item, stats)
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
        time.sleep(0.5)

    while True:
        print(f"\n{'-' * 20} {player.name}: Level {player.level} {'-' * 20}")
        print(f"HP: {round(player.hp, 1)}/{player.max_hp} | MP: {player.mp}/{player.max_mp} | Gold: {player.gold}")
        print("1. Adventure | 2. Inventory | 3. Stats | 4. Shop | 5. Tavern | 6. Save | 7. Quit")
        time.sleep(0.5)
        choice = input("Selection: ")

        if choice == "1":
            locations = load_file("locations.txt")
            location = random.choice(locations)
            print(f"\nYou set out for {location}!")
            time.sleep(0.5)
            max_encounters = random.randint(2, 10)
            boss_fight = False
            encounter_count = 0
            completed_encounters = 0
            treasure_inventory = []
            adventure = True
            event_chance = 25

            while adventure:
                if encounter_count >= max_encounters:
                    adventure = False
                    break

                encounter_count += 1
                Encounters = []

                if encounter_count >= 8 and not boss_fight and random.random() < 0.25:
                    print(f"\nA powerful foe blocks your path! Fight the boss?")
                    print("1. Yes | 2. No")
                    time.sleep(0.5)
                    boss_choice = input("Selection: ")
                    if boss_choice == "1":
                        boss_fight = True
                        result = combat(player, True)
                        Encounters.append(result)
                    else:
                        print("You avoid the boss and continue cautiously.")
                        time.sleep(0.5)
                else:
                    if random.randint(1, 100) <= event_chance:
                        max_encounters = random_event(player, encounter_count, max_encounters)
                    else:
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

                    # Gear drops
                    for g in gear:
                        level_range, drop_chance, is_rare = parse_gear_drop_info(g)
                        if level_range and player.level >= level_range[0] and player.level <= level_range[1] and (not is_rare or boss_fight):
                            valid_drops.append((g.split()[0], drop_chance))

                    # Consumable drops
                    from items import parse_consumable
                    for c in consumables:
                        consumable = parse_consumable(c)
                        if consumable and player.level >= consumable["level_range"][0] and player.level <= consumable["level_range"][1]:
                            if not consumable["is_rare"] or boss_fight:  # Rare only for bosses
                                valid_drops.append((consumable["name"], consumable["drop_rate"]))

                    # Drop chance check
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

                elif Encounters and "Fled" in Encounters[-1]:
                    print("You fled, forfeiting potential rewards.")
                    time.sleep(0.5)

            print(f"\nAdventure complete! Returning to town with {len(treasure_inventory)} treasure items from {completed_encounters} victories.")
            time.sleep(0.5)
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