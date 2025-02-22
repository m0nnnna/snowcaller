import time
from utils import load_file

def parse_shop_item(shop_line):
    parts = shop_line.split()
    if not parts or not parts[-1].startswith("[") or not parts[-1].endswith("]"):
        return None
    name = " ".join(parts[:-1])
    bracket = parts[-1][1:-1].split()
    if len(bracket) != 4:
        print(f"Warning: Invalid shop item format: {shop_line}")
        return None
    level_part, category, stock, price = bracket
    if not level_part.startswith("L:"):
        print(f"Warning: Invalid level range: {shop_line}")
        return None
    try:
        min_level, max_level = map(int, level_part[2:].split("-"))
        stock = int(stock)
        price = int(price)
        if category not in ["Gear", "Consumables", "Items"]:
            print(f"Warning: Invalid category {category} in {shop_line}")
            return None
        return {
            "name": name,
            "level_range": (min_level, max_level),
            "category": category,
            "stock": stock,
            "price": price
        }
    except (ValueError, IndexError):
        print(f"Warning: Could not parse shop item: {shop_line}")
        return None

def parse_gear_item(gear_line):
    parts = gear_line.split()
    if not parts or not parts[-1].startswith("[") or not parts[-1].endswith("]"):
        return None
    name = " ".join(parts[:-1])
    bracket = parts[-1][1:-1].split()
    is_rare = False
    if bracket[-1] == "[R]":
        bracket.pop()
    if len(bracket) != 6:
        print(f"Warning: Invalid gear format: {gear_line}")
        return None
    level_part, slot, stats, damage, drop_rate, gold = bracket
    try:
        min_level, max_level = map(int, level_part[2:].split("-"))
        drop_rate = float(drop_rate[:-1]) / 100
        gold = int(gold)
        return {
            "name": name,
            "level_range": (min_level, max_level),
            "slot": slot,
            "stats": stats,
            "damage": damage,
            "drop_rate": drop_rate,
            "gold": gold,
            "is_rare": is_rare
        }
    except (ValueError, IndexError):
        print(f"Warning: Could not parse gear: {gear_line}")
        return None

def calculate_price(base_price, drop_chance):
    return int(base_price * (1 / drop_chance)) if drop_chance > 0 else base_price

def shop_menu(player):
    shop_items = load_file("shop.txt")
    print(f"\nWelcome to the Shop! Gold: {player.gold}")
    print("1. Buy | 2. Sell | 3. Exit")
    time.sleep(0.5)
    shop_choice = input("Selection: ")

    level_block = ((player.level - 1) // 10) * 10 + 1
    level_max = level_block + 9

    if shop_choice == "1":
        pass  # Placeholder - add your buy logic here
        # You might want to add code like:
        # print("Buy menu coming soon!")
        # time.sleep(0.5)
    elif shop_choice == "2":
        if not player.inventory:
            print("Nothing to sell!")
            time.sleep(0.5)
            return
        gear = load_file("gear.txt")
        consumables = load_file("consumables.txt")
        from items import parse_consumable
        print("\nYour inventory:")
        for idx, item in enumerate(player.inventory, 1):
            gear_item = next((parse_gear_item(g) for g in gear if parse_gear_item(g) and parse_gear_item(g)["name"] == item), None)
            if gear_item:
                sell_price = gear_item["gold"] // 2
            else:
                cons_item = next((parse_consumable(c) for c in consumables if parse_consumable(c) and parse_consumable(c)["name"] == item), None)
                sell_price = cons_item["gold"] // 2 if cons_item else 5
            print(f"{idx}. {item} - Sell Price: {sell_price} Gold")
        time.sleep(0.5)
        sell_choice = input("Select item to sell (or 0 to exit): ")
        if sell_choice == "0":
            return
        try:
            item_idx = int(sell_choice) - 1
            if 0 <= item_idx < len(player.inventory):
                item = player.inventory[item_idx]
                gear_item = next((parse_gear_item(g) for g in gear if parse_gear_item(g) and parse_gear_item(g)["name"] == item), None)
                if gear_item:
                    sell_price = gear_item["gold"] // 2
                else:
                    cons_item = next((parse_consumable(c) for c in consumables if parse_consumable(c) and parse_consumable(c)["name"] == item), None)
                    sell_price = cons_item["gold"] // 2 if cons_item else 5
                player.gold += sell_price
                player.inventory.pop(item_idx)
                print(f"Sold {item} for {sell_price} gold!")
                time.sleep(0.5)
            else:
                print("Invalid selection!")
                time.sleep(0.5)
        except ValueError:
            print("Invalid input!")
            time.sleep(0.5)
    elif shop_choice == "3":
        return
    else:
        print("Invalid choice!")
        time.sleep(0.5)