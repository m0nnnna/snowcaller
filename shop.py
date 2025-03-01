import time
from utils import load_file
from items import parse_consumable

def parse_shop_item(shop_line):
    start = shop_line.find("[")
    end = shop_line.rfind("]") + 1
    if start == -1 or end == 0:
        return None
    name = shop_line[:start].strip()
    bracket_str = shop_line[start:end]
    bracket = bracket_str[1:-1].split()
    
    if not bracket or not bracket[0].startswith("L:"):
        return None
    
    level_part = bracket[0]
    try:
        min_level, max_level = map(int, level_part[2:].split("-"))
        if len(bracket) >= 7:  # Consumables: [L:min-max HP/MP value none stock drop% price]
            stock = int(bracket[4])
            price = int(bracket[6])
            category = "Consumables" if "HP" in bracket or "MP" in bracket else "Gear"
        elif len(bracket) == 3:  # Items: [L:min-max stock price]
            stock = int(bracket[1])
            price = int(bracket[2])
            category = "Items" if name in ["Lockpick", "Magical Removal Scroll"] else "Gear"
        else:
            return None
        
        return {
            "name": name,
            "level_range": (min_level, max_level),
            "category": category,
            "stock": stock,
            "price": price
        }
    except (ValueError, IndexError):
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
        is_rare = True
    if len(bracket) != 7:
        return None
    level_part, slot, scaling_stat, stats, damage, drop_rate, gold = bracket
    try:
        min_level, max_level = map(int, level_part[2:].split("-"))
        drop_rate = float(drop_rate[:-1]) / 100
        gold = int(gold)
        armor_value = int(bracket[5].split(":")[1])
        return {
            "name": name,
            "level_range": (min_level, max_level),
            "slot": slot,
            "stats": stats,
            "damage": damage,
            "armor_value": armor_value,
            "drop_rate": drop_rate,
            "gold": gold,
            "is_rare": is_rare
        }
    except (ValueError, IndexError):
        return None

def calculate_price(base_price, drop_chance):
    return int(base_price * (1 / drop_chance)) if drop_chance > 0 else base_price

def shop_menu(player):
    shop_items = load_file("shop.txt")
    gear_items = load_file("gear.txt")
    consumable_items = load_file("consumables.txt")
    print(f"\nWelcome to the Shop! Gold: {player.gold}")
    print("1. Buy | 2. Sell | 3. Exit")
    time.sleep(0.5)
    shop_choice = input("Selection: ")

    level_block = ((player.level - 1) // 10) * 10 + 1
    level_max = level_block + 9

    if shop_choice == "1":
        available_items = []
        always_available = ["Lockpick", "Magical Removal Scroll"]

        for line in shop_items:
            if line.startswith("#"):
                continue
            shop_item = parse_shop_item(line)
            if not shop_item:
                continue
            
            if shop_item["name"] in always_available:
                item_details = {"name": shop_item["name"], "price": shop_item["price"], "stock": float('inf'), "type": "Item"}
                available_items.append(item_details)
            elif shop_item["level_range"][0] <= player.level <= shop_item["level_range"][1] and shop_item["stock"] > 0:
                if shop_item["category"] == "Gear":
                    gear_detail = next((parse_gear_item(g) for g in gear_items if parse_gear_item(g) and parse_gear_item(g)["name"] == shop_item["name"]), None)
                    if gear_detail:
                        available_items.append({
                            "name": shop_item["name"],
                            "price": shop_item["price"],
                            "stock": shop_item["stock"],
                            "type": "Gear",
                            "damage": gear_detail["damage"],
                            "armor_value": gear_detail["armor_value"],
                            "stats": gear_detail["stats"]
                        })
                elif shop_item["category"] == "Consumables":
                    try:
                        cons_detail = next((parse_consumable(c) for c in consumable_items if parse_consumable(c) and parse_consumable(c)["name"] == shop_item["name"]), None)
                        if cons_detail:
                            available_items.append({
                                "name": shop_item["name"],
                                "price": shop_item["price"],
                                "stock": shop_item["stock"],
                                "type": cons_detail["type"],
                                "value": cons_detail["value"],
                                "turns": cons_detail["duration"],
                                "buff": cons_detail["stat"] if cons_detail["type"] in ["Buff", "Offense"] else None
                            })
                        else:
                            bracket = line.split("[")[1].split("]")[0].split()
                            effect_type = "HP" if "HP" in bracket else "MP" if "MP" in bracket else "Unknown"
                            value = int(bracket[2]) if len(bracket) > 2 else 0
                            available_items.append({
                                "name": shop_item["name"],
                                "price": shop_item["price"],
                                "stock": shop_item["stock"],
                                "type": effect_type,
                                "value": value,
                                "turns": 0,
                                "buff": None
                            })
                    except NameError:
                        bracket = line.split("[")[1].split("]")[0].split()
                        effect_type = "HP" if "HP" in bracket else "MP" if "MP" in bracket else "Unknown"
                        value = int(bracket[2]) if len(bracket) > 2 else 0
                        available_items.append({
                            "name": shop_item["name"],
                            "price": shop_item["price"],
                            "stock": shop_item["stock"],
                            "type": effect_type,
                            "value": value,
                            "turns": 0,
                            "buff": None
                        })
                elif shop_item["category"] == "Items":
                    available_items.append({
                        "name": shop_item["name"],
                        "price": shop_item["price"],
                        "stock": shop_item["stock"],
                        "type": "Item"
                    })

        if not available_items:
            print("No items available for your level!")
            time.sleep(0.5)
            return
        
        print("\nAvailable items:")
        for idx, item in enumerate(available_items, 1):
            if item["type"] == "Gear":
                stats_str = item["stats"] if item["stats"] else ""
                print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != float('inf') else '∞'}, Dmg: {item['damage']}, AV: {item['armor_value']}, Stats: {stats_str})")
            elif item["type"] in ["HP", "MP"]:
                print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != float('inf') else '∞'}, Restores: {item['value']} {item['type']})")
            elif item["type"] == "Buff":
                print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != float('inf') else '∞'}, +{item['value']} {item['buff']} for {item['turns']} turns)")
            elif item["type"] == "Offense":
                effect = f"{item['value']} damage/turn for {item['turns']} turns" if item["buff"] == "Poison" else f"{item['value']} damage"
                print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != float('inf') else '∞'}, {effect})")
            else:
                print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != float('inf') else '∞'})")
        time.sleep(0.5)
        
        buy_choice = input("Select item to buy (or 0 to exit): ")
        if buy_choice == "0":
            return
        
        try:
            item_idx = int(buy_choice) - 1
            if 0 <= item_idx < len(available_items):
                item = available_items[item_idx]
                if player.gold >= item["price"]:
                    player.gold -= item["price"]
                    player.inventory.append(item["name"])
                    # Only decrement stock for non-infinite items
                    if item["stock"] != float('inf'):
                        item["stock"] -= 1
                        with open("shop.txt", "w") as f:
                            for line in shop_items:
                                if line.startswith(item["name"]):
                                    parts = line.split()
                                    bracket = parts[-1][1:-1].split()
                                    bracket[2] = str(item["stock"])
                                    new_line = f"{item['name']} [{' '.join(bracket)}]"
                                    f.write(new_line + "\n")
                                else:
                                    f.write(line + "\n")
                    print(f"Bought {item['name']} for {item['price']} gold!")
                    time.sleep(0.5)
                else:
                    print("Not enough gold!")
                    time.sleep(0.5)
            else:
                print("Invalid selection!")
                time.sleep(0.5)
        except ValueError:
            print("Invalid input!")
            time.sleep(0.5)

    elif shop_choice == "2":
        # [Sell logic unchanged]
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