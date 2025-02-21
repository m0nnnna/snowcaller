import os
import time
import random
from player import Player, save_game, load_game
from combat import combat
from shop import shop_menu, parse_shop_item, calculate_price
from tavern import tavern_menu
from utils import load_file, parse_stats

def parse_gear_drop_info(gear_line):
    parts = gear_line.split()
    bracket = parts[-1] if parts[-1].startswith("[") else None
    if not bracket:
        return None, None, False
    bracket_parts = bracket[1:-1].split()
    level_part = bracket_parts[0]
    chance_part = bracket_parts[1]
    is_rare = "R" in bracket_parts
    min_level, max_level = map(int, level_part[2:].split("-"))
    drop_chance = float(chance_part[:-1]) / 100
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
        gold = random.randint(5, 15)
        player.inventory.extend(items)
        player.gold += gold
        print(f"You open the chest and find: {', '.join(items)} and {gold} gold!")
        time.sleep(0.5)

    elif chest_type == "locked":
        if "Lockpick" in player.inventory:
            print("Use a Lockpick to open the chest? (1. Yes | 2. No)")
            time.sleep(0.5)
            choice = input("Selection: ")
            if choice == "1":
                player.inventory.remove("Lockpick")
                items = random.sample(treasures, random.randint(2, 3))
                gold = random.randint(15, 30)
                player.inventory.extend(items)
                player.gold += gold
                print(f"You use a Lockpick and open the chest, finding: {', '.join(items)} and {gold} gold!")
                time.sleep(0.5)
            else:
                print("You leave the locked chest behind.")
                time.sleep(0.5)
        else:
            print("The chest is locked! You need a Lockpick to open it.")
            time.sleep(0.5)

    elif chest_type == "magical":
        if "Magical Removal Scroll" in player.inventory:
            print("Use a Magical Removal Scroll to open the chest? (1. Yes | 2. No)")
            time.sleep(0.5)
            choice = input("Selection: ")
            if choice == "1":
                player.inventory.remove("Magical Removal Scroll")
                items = random.sample(treasures, random.randint(3, 4))
                gold = random.randint(30, 50)
                player.inventory.extend(items)
                player.gold += gold
                print(f"You use a Magical Removal Scroll and open the chest, finding: {', '.join(items)} and {gold} gold!")
                time.sleep(0.5)
            else:
                print("You leave the magically locked chest behind.")
                time.sleep(0.5)
        else:
            print("The chest is magically locked! You need a Magical Removal Scroll to open it.")
            time.sleep(0.5)

def main():
    if os.path.exists("save.txt"):
        player = load_game()
        print(f"Welcome back, {player.name}!")
    else:
        name = input("Enter your name: ")
        print("Choose class: 1. Warrior | 2. Mage | 3. Rogue")
        class_type = input("Selection: ")
        player = Player(name, class_type)
        print(f"Starting gear equipped!")
        player.gold = 0
        player.shop_stock = {}
        save_game(player)
        print("New save file created with your character!")
        time.sleep(0.5)

    locations = load_file("locations.txt")
    monsters = load_file("monsters.txt")
    gear = load_file("gear.txt")
    consumables = load_file("consumables.txt")
    shop_items = load_file("shop.txt")
    
    regular_monsters = [m for m in monsters if not m.startswith("# Boss Monsters")]
    boss_monsters = [m for m in monsters if not m.startswith("# Regular Monsters") and not m.startswith("#")]

    while True:
        print(f"\n{player.name} | Level: {player.level} | HP: {player.hp}/{player.max_hp} | MP: {player.mp}/{player.max_mp} | XP: {player.exp}/{player.max_exp} | Gold: {player.gold}")
        print("Stats: S:{0} A:{1} I:{2} W:{3} L:{4}".format(
            player.stats["S"], player.stats["A"], player.stats["I"], player.stats["W"], player.stats["L"]))
        if player.stat_points > 0:
            print(f"Stat points to allocate: {player.stat_points}")
        print("1. Adventure | 2. Inventory | 3. Allocate Stat Point | 4. Shop | 5. Tavern | 6. Save | 7. Quit")
        time.sleep(0.5)
        choice = input("Selection: ")

        if choice == "1":
            location = random.choice(locations).split()
            print(f"You travel to the {location[0]} {location[1]}...")
            time.sleep(0.5)
            num_encounters = random.randint(2, 10)
            boss_triggered = False
            
            for i in range(num_encounters):
                if player.hp <= 0:
                    break
                
                if i > 0 and survived:
                    print("\nA new encounter approaches!")
                    time.sleep(0.5)
                
                if i == num_encounters - 1 and num_encounters >= 8:
                    if num_encounters == 10 and random.random() < 0.25:
                        monster_line = random.choice(boss_monsters)
                        boss_type = "rare boss"
                        is_rare_monster = True
                    else:
                        monster_line = random.choice(boss_monsters)
                        boss_type = "boss"
                        is_rare_monster = False
                    
                    print(f"\nWARNING: A powerful {boss_type} lies ahead!")
                    print("1. Fight the Boss | 2. Return to Town")
                    time.sleep(0.5)
                    boss_choice = input("Selection: ")
                    
                    if boss_choice == "2":
                        print("You return to town, ending the adventure.")
                        time.sleep(0.5)
                        boss_triggered = True
                        break
                    elif boss_choice != "1":
                        print("Invalid choice, proceeding to fight the boss!")
                        time.sleep(0.5)
                    print(f"A powerful {boss_type} appears!")
                    time.sleep(0.5)
                else:
                    eligible_monsters = []
                    for m in regular_monsters:
                        parts = m.split()
                        level_idx = next(i for i, part in enumerate(parts) if part.startswith("L:"))
                        level_range = parts[level_idx][2:]
                        min_level, max_level = map(int, level_range.split("-"))
                        rare_idx = next((i for i, part in enumerate(parts) if part.endswith("%") and not part.startswith("G:")), -1)
                        if rare_idx != -1 and rare_idx > level_idx:
                            if random.random() < float(parts[rare_idx][:-1]) / 100:
                                eligible_monsters.append(m)
                        else:
                            for lvl in range(min_level, max_level + 1):
                                if abs(player.level - lvl) <= 3:
                                    eligible_monsters.append(m)
                                    break
                    if not eligible_monsters:
                        print("No suitable monsters found for this encounter!")
                        time.sleep(0.5)
                        continue
                    monster_line = random.choice(eligible_monsters)
                    is_rare_monster = False
                
                monster_name = monster_line.split('[')[1].split(']')[0]
                monster_parts = monster_line.split()
                level_idx = next(i for i, part in enumerate(monster_parts) if part.startswith("L:"))
                monster_stats = parse_stats(monster_parts[level_idx - 1], is_consumable=False)
                min_level, max_level = map(int, monster_parts[level_idx][2:].split("-"))
                monster_stats["level"] = random.randint(
                    max(min_level, player.level - 3), 
                    min(max_level, player.level + 3)
                )
                monster_stats["damage_range"] = monster_parts[level_idx + 1][2:]
                
                gold_idx = next((i for i, part in enumerate(monster_parts) if part.startswith("G:")), -1)
                if gold_idx != -1:
                    gold_chance = float(monster_parts[gold_idx][2:-1]) / 100
                    if random.random() < gold_chance:
                        max_gold = monster_stats["level"] * 2
                        gold_drop = int(random.triangular(0, max_gold, 0))
                        player.gold += gold_drop
                        if gold_drop > 0:
                            print(f"You found {gold_drop} gold!")
                            time.sleep(0.5)
                
                if is_rare_monster:
                    for stat in ["S", "A", "I", "W", "L"]:
                        monster_stats[stat] = int(monster_stats[stat] * 1.2)
                    monster_hp_boost = int((10 + 2 * monster_stats["S"]) * 1.2)
                    monster_stats["hp_boost"] = monster_hp_boost
                
                survived = combat(player, monster_name, monster_stats)
                if not survived:
                    print("Adventure ended prematurely!")
                    time.sleep(0.5)
                    break
                
                if i == num_encounters - 1 and survived:
                    monster_level_block = (monster_stats["level"] // 10) * 10 + 1
                    if num_encounters >= 8:
                        eligible_gear = []
                        eligible_consumables = []
                        for g in gear + consumables:
                            level_range, drop_chance, _ = parse_gear_drop_info(g)
                            if level_range and monster_level_block <= level_range[1] and monster_level_block >= level_range[0]:
                                boosted_chance = min(drop_chance + (0.08 if is_rare_monster else 0.05), 1.0)
                                if random.random() < boosted_chance:
                                    (eligible_gear if g in gear else eligible_consumables).append(g)
                        eligible_items = eligible_gear + eligible_consumables
                        if eligible_items:
                            reward = random.choice(eligible_items).split()[0]
                            player.inventory.append(reward)
                            print(f"{'Rare monster' if is_rare_monster else 'Boss'} dropped: {reward}!")
                            time.sleep(0.5)
                        else:
                            reward = random.choice(gear + consumables).split()[0]
                            player.inventory.append(reward)
                            print(f"You found: {reward}")
                            time.sleep(0.5)
                    else:
                        rare_drop_chance = (num_encounters - 1) * 0.1
                        if random.random() < rare_drop_chance:
                            rare_items = [g for g in gear if " R]" in g]
                            if rare_items:
                                reward = random.choice(rare_items).split()[0]
                                player.inventory.append(reward)
                                print(f"Rare drop! You found: {reward}")
                                time.sleep(0.5)
                            else:
                                reward = random.choice(gear + consumables).split()[0]
                                player.inventory.append(reward)
                                print(f"You found: {reward}")
                                time.sleep(0.5)
                        else:
                            reward = random.choice(gear + consumables).split()[0]
                            player.inventory.append(reward)
                            print(f"You found: {reward}")
                            time.sleep(0.5)
            
            # Reset tavern buff and award chest after adventure
            if hasattr(player, "tavern_buff") and player.tavern_buff:
                stat, value = list(player.tavern_buff.items())[0]
                player.stats[stat] -= value
                player.tavern_buff = None
                print("Your tavern feast buff has worn off.")
                time.sleep(0.5)
            
            if player.hp > 0:
                print("\nAdventure completed!")
                time.sleep(0.5)
                player.apply_xp()
                award_treasure_chest(player)  # Award chest here
                save_game(player)
                print("Game autosaved!")
                time.sleep(0.5)
            else:
                player.apply_xp()
        
        elif choice == "2":
            inventory_menu(player)
        
        elif choice == "3":
            if player.stat_points > 0:
                player.allocate_stat()
            else:
                print("No stat points available!")
                time.sleep(0.5)
        
        elif choice == "4":
            shop_menu(player, gear, consumables)
        
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

if __name__ == "__main__":
    main()
