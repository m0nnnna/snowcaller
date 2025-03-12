import time
from utils import load_json, save_json

def calculate_price(base_price, drop_chance):
    return int(base_price * (1 / drop_chance)) if drop_chance > 0 else base_price

def shop_menu(player):
    shop_data = load_json("shop.json")
    shop_items = shop_data.get("items", []) if shop_data else []
    gear_items = load_json("gear.json")
    consumable_items = load_json("consumables.json")
    treasures = load_json("treasures.json")
    
    while True:  # Main shop loop
        print(f"\nWelcome to the Shop! Gold: {player.gold}")
        print("1. Buy | 2. Sell | 3. Exit")
        shop_choice = input("Selection: ")

        if shop_choice == "1":
            while True:
                available_items = []
                for shop_item in shop_items:
                    min_level, max_level = shop_item["level_range"]
                    if shop_item["stock"] == -1 or shop_item["stock"] > 0:
                        if min_level <= player.level <= max_level:
                            if shop_item["category"] == "Gear":
                                gear_detail = next((g for g in gear_items if g["name"] == shop_item["name"]), None)
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
                                cons_detail = next((c for c in consumable_items if c["name"] == shop_item["name"]), None)
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
                            elif shop_item["category"] == "Item":
                                available_items.append({
                                    "name": shop_item["name"],
                                    "price": shop_item["price"],
                                    "stock": shop_item["stock"],
                                    "type": "Item"
                                })

                if not available_items:
                    print("No items available for your level!")
                    break

                print("\nAvailable items:")
                for idx, item in enumerate(available_items, 1):
                    if item["type"] == "Gear":
                        stats_str = item["stats"] if item["stats"] else ""
                        print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != -1 else '∞'}, Dmg: {item['damage']}, AV: {item['armor_value']}, Stats: {stats_str})")
                    elif item["type"] in ["HP", "MP"]:
                        print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != -1 else '∞'}, Restores: {item['value']} {item['type']})")
                    elif item["type"] == "Buff":
                        print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != -1 else '∞'}, +{item['value']} {item['buff']} for {item['turns']} turns)")
                    elif item["type"] == "Offense":
                        effect = f"{item['value']} damage/turn for {item['turns']} turns" if item["buff"] == "Poison" else f"{item['value']} damage"
                        print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != -1 else '∞'}, {effect})")
                    else:
                        print(f"{idx}. {item['name']} - Price: {item['price']} Gold (Stock: {item['stock'] if item['stock'] != -1 else '∞'})")

                buy_choice = input("Select item to buy (or 0 to back): ")
                if buy_choice == "0":
                    break

                try:
                    item_idx = int(buy_choice) - 1
                    if 0 <= item_idx < len(available_items):
                        item = available_items[item_idx]
                        if player.gold >= item["price"]:
                            player.gold -= item["price"]
                            player.inventory.append(item["name"])
                            if item["stock"] != -1:
                                shop_item = next(s for s in shop_items if s["name"] == item["name"])
                                shop_item["stock"] -= 1
                                save_json("shop.json", shop_data)
                            print(f"Bought {item['name']} for {item['price']} gold!")
                        else:
                            print("Not enough gold!")
                    else:
                        print("Invalid selection!")
                except ValueError:
                    print("Invalid input!")

        elif shop_choice == "2":
            while True:
                if not player.inventory:
                    print("Nothing to sell!")
                    break
                gear = load_json("gear.json")
                consumables = load_json("consumables.json")
                treasures = load_json("treasures.json")
                print("\nYour inventory:")
                for idx, item in enumerate(player.inventory, 1):
                    gear_item = next((g for g in gear if g["name"] == item), None)
                    if gear_item:
                        sell_price = gear_item["gold"] // 2
                    else:
                        cons_item = next((c for c in consumables if c["name"] == item), None)
                        if cons_item:
                            sell_price = cons_item["gold"] // 2
                        else:
                            treasure_item = next((t for t in treasures if t["name"] == item), None)
                            sell_price = treasure_item["gold"] // 2 if treasure_item else 5
                    print(f"{idx}. {item} - Sell Price: {sell_price} Gold")
                sell_choice = input("Select item to sell (or 0 to back): ")
                if sell_choice == "0":
                    break
                try:
                    item_idx = int(sell_choice) - 1
                    if 0 <= item_idx < len(player.inventory):
                        item = player.inventory[item_idx]
                        gear_item = next((g for g in gear if g["name"] == item), None)
                        if gear_item:
                            sell_price = gear_item["gold"] // 2
                        else:
                            cons_item = next((c for c in consumables if c["name"] == item), None)
                            if cons_item:
                                sell_price = cons_item["gold"] // 2
                            else:
                                treasure_item = next((t for t in treasures if t["name"] == item), None)
                                sell_price = treasure_item["gold"] // 2 if treasure_item else 5
                        player.gold += sell_price
                        player.inventory.pop(item_idx)
                        print(f"Sold {item} for {sell_price} gold!")
                    else:
                        print("Invalid selection!")
                except ValueError:
                    print("Invalid input!")

        elif shop_choice == "3":
            return
        else:
            print("Invalid choice!")