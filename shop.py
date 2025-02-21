import time
from utils import load_file

def parse_shop_item(shop_line):
    parts = shop_line.split()
    if not parts or parts[-1] == "":
        return None
    bracket = parts[-1]
    if not bracket.startswith("[") or not bracket.endswith("]"):
        return None
    bracket_parts = bracket[1:-1].split()
    if len(bracket_parts) != 3:
        print(f"Warning: Invalid shop item format: {shop_line}")
        return None
    level_part = bracket_parts[0]
    try:
        stock = int(bracket_parts[1])
        price = int(bracket_parts[2])
        min_level, max_level = map(int, level_part[2:].split("-"))
        return {"name": " ".join(parts[:-1]), "level_range": (min_level, max_level), "stock": stock, "price": price}
    except (ValueError, IndexError):
        print(f"Warning: Could not parse shop item: {shop_line}")
        return None

def calculate_price(base_price, drop_chance):
    return int(base_price * (1 / drop_chance)) if drop_chance > 0 else base_price

def shop_menu(player, gear, consumables):
    shop_items = load_file("shop.txt")
    print(f"\nWelcome to the Shop! Gold: {player.gold}")
    print("1. Buy | 2. Sell | 3. Exit")
    time.sleep(0.5)
    shop_choice = input("Selection: ")
    
    if shop_choice == "1":
        level_block = (player.level // 10) * 10 + 1
        available_items = [item for item in shop_items if parse_shop_item(item) and parse_shop_item(item)["level_range"][0] <= level_block <= parse_shop_item(item)["level_range"][1]]
        if not available_items:
            print("No items available for your level!")
            time.sleep(0.5)
            return
        print("\nItems for sale:")
        for idx, item in enumerate(available_items):
            shop_data = parse_shop_item(item)
            stock = player.shop_stock.get(shop_data["name"], shop_data["stock"])
            print(f"{idx + 1}. {shop_data['name']} - Price: {shop_data['price']} Gold (Stock: {stock})")
        time.sleep(0.5)
        buy_choice = input("Select item to buy (or 0 to exit): ")
        if buy_choice == "0":
            return
        try:
            item_idx = int(buy_choice) - 1
            if 0 <= item_idx < len(available_items):
                shop_data = parse_shop_item(available_items[item_idx])
                stock = player.shop_stock.get(shop_data["name"], shop_data["stock"])
                if stock > 0 and player.gold >= shop_data["price"]:
                    player.gold -= shop_data["price"]
                    player.inventory.append(shop_data["name"])
                    player.shop_stock[shop_data["name"]] = stock - 1
                    print(f"Purchased {shop_data['name']} for {shop_data['price']} gold!")
                    time.sleep(0.5)
                elif stock <= 0:
                    print("Out of stock!")
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
        if not player.inventory:
            print("Nothing to sell!")
            time.sleep(0.5)
            return
        print("\nYour inventory:")
        for idx, item in enumerate(player.inventory):
            base_price = next((parse_shop_item(s)["price"] for s in shop_items + gear if s.split()[0] == item.split()[0]), 10)
            drop_chance = next((parse_gear_drop_info(g)[1] for g in gear + consumables if g.split()[0] == item), 0.1)
            sell_price = calculate_price(base_price, drop_chance) // 2
            print(f"{idx + 1}. {item} - Sell Price: {sell_price} Gold")
        time.sleep(0.5)
        sell_choice = input("Select item to sell (or 0 to exit): ")
        if sell_choice == "0":
            return
        try:
            item_idx = int(sell_choice) - 1
            if 0 <= item_idx < len(player.inventory):
                item = player.inventory[item_idx]
                base_price = next((parse_shop_item(s)["price"] for s in shop_items + gear if s.split()[0] == item.split()[0]), 10)
                drop_chance = next((parse_gear_drop_info(g)[1] for g in gear + consumables if g.split()[0] == item), 0.1)
                sell_price = calculate_price(base_price, drop_chance) // 2
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
