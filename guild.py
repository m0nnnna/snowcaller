import json
from typing import Dict, List, Optional, Union
from utils import load_json, save_json

class Guild:
    def __init__(self, player):
        self.player = player
        self.exchange_data = self._load_exchange_data()
        self.key_items = self._load_key_items()
        self.quests_data = load_json("quest.json")
        self.lore_data = load_json("lore.json")

    def _load_exchange_data(self) -> Dict:
        try:
            with open('guild_exchange.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"exchange_options": {"adventure_points": {"rates": []}, "crafted_items": {"recipes": []}}}

    def _load_key_items(self) -> Dict:
        try:
            with open('keyitems.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"key_items": []}

    def guild_menu(self, player):
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
                    return
            elif choice == "2":
                return
            else:
                print("Invalid choice!")
                return
        
        # If player is already in the guild
        quests = self.quests_data.get("quests", [])
        lore = self.lore_data.get("lore", [])
        
        active_quests = player.active_quests
        completed_quests = player.completed_quests if hasattr(player, "completed_quests") else []
        
        print(f"Current Rank: {player.get_rank_name()} Adventurer")
        print(f"Adventurer Points: {player.adventurer_points}/{player.max_adventurer_points}")
        if player.adventurer_rank < 6:
            next_rank_points = player.get_next_rank_points()
            print(f"Points needed for next rank: {next_rank_points}")
        print("\n1. Accept Quest | 2. Turn In Quest | 3. Exchange Items | 0. Return")
        choice = input("Selection: ")

        if choice == "1":
            self._handle_quest_acceptance(player, quests, lore, active_quests, completed_quests)
        elif choice == "2":
            self.turn_in_quest(player)
        elif choice == "3":
            self.exchange_menu(player)

    def _handle_quest_acceptance(self, player, quests, lore, active_quests, completed_quests):
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

    def turn_in_quest(self, player):
        if not player.active_quests:
            print("You have no active quests to turn in.")
            return

        print("\nActive Quests:")
        for i, quest in enumerate(player.active_quests, 1):
            quest_data = next((q for q in self.quests_data["quests"] if q["quest_name"] == quest["quest_name"]), None)
            if quest_data:
                print(f"{i}. {quest['quest_name']}")
                print(f"   {quest_data['quest_description']}")
                print(f"   Reward: {quest_data['quest_reward']} | Points: {quest_data['adventure_points']}")

        quest_choice = input("\nSelect a quest to turn in (or 0 to return): ")
        if quest_choice == "0":
            return

        try:
            quest_index = int(quest_choice) - 1
            if 0 <= quest_index < len(player.active_quests):
                selected_quest = player.active_quests[quest_index]
                quest_data = next((q for q in self.quests_data["quests"] if q["quest_name"] == selected_quest["quest_name"]), None)
                
                if quest_data:
                    # Check if quest is completed
                    if self._check_quest_completion(player, selected_quest, quest_data):
                        # Award rewards
                        self._award_quest_rewards(player, quest_data)
                        # Remove quest from active quests
                        player.active_quests.pop(quest_index)
                        # Add to completed quests
                        if not hasattr(player, "completed_quests"):
                            player.completed_quests = []
                        player.completed_quests.append(quest_data["quest_name"])
                        print(f"Quest completed: {quest_data['quest_name']}")
                    else:
                        print("You haven't completed this quest yet.")
            else:
                print(f"Invalid selection. Choose between 1 and {len(player.active_quests)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def _check_quest_completion(self, player, quest, quest_data):
        for stage in quest_data["stages"]:
            if stage["type"] == "kill":
                if "target_monster" in stage:
                    if player.kill_counts.get(stage["target_monster"], 0) < stage["kill_count_required"]:
                        return False
                elif "target_item" in stage:
                    if player.kill_counts.get(stage["target_item"], 0) < stage["item_count_required"]:
                        return False
            elif stage["type"] == "collect":
                if player.inventory.get(stage["target_item"], 0) < stage["item_count_required"]:
                    return False
            elif stage["type"] == "dialogue":
                if not hasattr(player, "dialogue_flags") or stage["target_npc"] not in player.dialogue_flags:
                    return False
        return True

    def _award_quest_rewards(self, player, quest_data):
        # Award adventure points
        player.adventurer_points += quest_data["adventure_points"]
        if player.adventurer_points >= player.max_adventurer_points:
            player.adventurer_points = player.max_adventurer_points

        # Award gold
        gold_reward = int(quest_data["quest_reward"].split()[0])
        player.gold += gold_reward

        # Award gear if specified
        if " " in quest_data["quest_reward"]:
            gear_name = quest_data["quest_reward"].split(" ", 1)[1]
            if gear_name not in player.inventory:
                player.inventory[gear_name] = 1
            else:
                player.inventory[gear_name] += 1

    def exchange_menu(self, player):
        print("\n=== Guild Exchange ===")
        print("1. Exchange for Adventure Points")
        print("2. Craft Special Items")
        print("0. Return")
        choice = input("Selection: ")

        if choice == "1":
            self._handle_points_exchange(player)
        elif choice == "2":
            self._handle_crafting(player)
        elif choice == "0":
            return
        else:
            print("Invalid choice!")

    def _handle_points_exchange(self, player):
        print("\nAvailable Items for Exchange:")
        rates = self.exchange_data["exchange_options"]["adventure_points"]["rates"]
        for i, rate in enumerate(rates, 1):
            print(f"{i}. {rate['item']} - {rate['points']} points")
            print(f"   You have: {player.inventory.get(rate['item'], 0)}")
        
        item_choice = input("\nSelect an item to exchange (or 0 to return): ")
        if item_choice == "0":
            return

        try:
            item_index = int(item_choice) - 1
            if 0 <= item_index < len(rates):
                selected_rate = rates[item_index]
                item_name = selected_rate["item"]
                quantity = int(input(f"How many {item_name} would you like to exchange? "))
                
                if quantity <= 0:
                    print("Invalid quantity!")
                    return
                
                if player.inventory.get(item_name, 0) < quantity:
                    print("You don't have enough items!")
                    return
                
                points = selected_rate["points"] * quantity
                player.inventory[item_name] -= quantity
                player.adventurer_points += points
                
                if player.adventurer_points > player.max_adventurer_points:
                    player.adventurer_points = player.max_adventurer_points
                
                print(f"Exchanged {quantity} {item_name} for {points} adventure points!")
            else:
                print(f"Invalid selection. Choose between 1 and {len(rates)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def _handle_crafting(self, player):
        print("\nAvailable Recipes:")
        recipes = self.exchange_data["exchange_options"]["crafted_items"]["recipes"]
        for i, recipe in enumerate(recipes, 1):
            print(f"{i}. {recipe['name']}")
            print(f"   {recipe['description']}")
            print("   Requirements:")
            for req in recipe["requirements"]:
                print(f"   - {req['quantity']}x {req['item']} (You have: {player.inventory.get(req['item'], 0)})")
        
        recipe_choice = input("\nSelect a recipe to craft (or 0 to return): ")
        if recipe_choice == "0":
            return

        try:
            recipe_index = int(recipe_choice) - 1
            if 0 <= recipe_index < len(recipes):
                selected_recipe = recipes[recipe_index]
                if self.can_craft_item(selected_recipe["name"], player.inventory):
                    result = self.craft_item(selected_recipe["name"], player.inventory)
                    if result:
                        player.inventory = result["inventory"]
                        crafted_item = result["result"]
                        if crafted_item["name"] not in player.inventory:
                            player.inventory[crafted_item["name"]] = crafted_item["quantity"]
                        else:
                            player.inventory[crafted_item["name"]] += crafted_item["quantity"]
                        print(f"Successfully crafted {crafted_item['name']}!")
                else:
                    print("You don't have enough materials!")
            else:
                print(f"Invalid selection. Choose between 1 and {len(recipes)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def get_exchange_options(self) -> Dict:
        """Returns all available exchange options."""
        return self.exchange_data["exchange_options"]

    def get_adventure_point_rates(self) -> List[Dict]:
        """Returns the list of items that can be exchanged for adventure points."""
        return self.exchange_data["exchange_options"]["adventure_points"]["rates"]

    def get_crafted_item_recipes(self) -> List[Dict]:
        """Returns the list of recipes for crafted items."""
        return self.exchange_data["exchange_options"]["crafted_items"]["recipes"]

    def exchange_for_points(self, item_name: str, quantity: int = 1) -> Optional[int]:
        """Exchange key items for adventure points."""
        for rate in self.get_adventure_point_rates():
            if rate["item"] == item_name:
                return rate["points"] * quantity
        return None

    def can_craft_item(self, recipe_name: str, inventory: Dict[str, int]) -> bool:
        """Check if the player has enough items to craft a specific recipe."""
        recipe = next((r for r in self.get_crafted_item_recipes() if r["name"] == recipe_name), None)
        if not recipe:
            return False

        for req in recipe["requirements"]:
            if inventory.get(req["item"], 0) < req["quantity"]:
                return False
        return True

    def craft_item(self, recipe_name: str, inventory: Dict[str, int]) -> Optional[Dict]:
        """Craft an item if the player has the required materials."""
        if not self.can_craft_item(recipe_name, inventory):
            return None

        recipe = next((r for r in self.get_crafted_item_recipes() if r["name"] == recipe_name), None)
        if not recipe:
            return None

        # Create a copy of the inventory to modify
        new_inventory = inventory.copy()

        # Remove required items
        for req in recipe["requirements"]:
            new_inventory[req["item"]] -= req["quantity"]

        return {
            "inventory": new_inventory,
            "result": recipe["result"]
        }

    def get_item_drop_info(self, item_name: str) -> Optional[Dict]:
        """Get information about where an item can be dropped from."""
        for item in self.key_items["key_items"]:
            if item["name"] == item_name:
                return {
                    "drop_from": item["drop_from"],
                    "drop_chance": item["drop_chance"],
                    "quest": item["quest"]
                }
        return None 