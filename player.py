import json
import sys
import os
from utils import load_json, save_json, get_base_path
class Player:
    def __init__(self, name, class_type):
#        print("Initializing Player...")
        self.name = name
        self.level = 1
        self.exp = 0
        self.max_exp = 25  # Changed from 100 to 25 to match our new XP scaling
        self.inventory = []
        self.equipment = {
            "head": None, "chest": None, "pants": None, "boots": None,
            "gloves": None, "main_hand": None, "off_hand": None, "neck": None, "ring": None
        }
        self.active_enemy_effect = None
        self.class_type = class_type
        self.pending_xp = 0
        self.stat_points = 0
        self.gold = 0
        self.shop_stock = {}
        self.tavern_buff = None
        self.rage_turns = 0
        self.event_cooldowns = {}
        self.event_timers = {}
        self.skills = []
        self.skill_effects = {}
        self.active_quests = []
        self.completed_quests = []
        self.tavern_npcs = []
        self.has_room = False
        
        # Guild membership and rank system
        self.guild_member = False  # New players are not guild members
        self.adventurer_rank = 0  # Start at 0 until they join
        self.adventurer_points = 0  # Start with 0 points
        self.max_adventurer_points = 10  # Initial max points
        self.rank_thresholds = [0, 20, 60, 140, 200, 300]  # Points needed for each rank

        if class_type == "1":  # Warrior
            self.stats = {"S": 5, "A": 1, "I": 1, "W": 1, "L": 1}
        elif class_type == "2":  # Mage
            self.stats = {"S": 1, "A": 1, "I": 5, "W": 3, "L": 2}
        elif class_type == "3":  # Rogue
            self.stats = {"S": 1, "A": 5, "I": 1, "W": 2, "L": 3}

        self.max_hp = 10 + 2 * self.stats["S"]
        self.hp = self.max_hp
        self.max_mp = 3 * self.stats["W"] if class_type == "2" else 2 * self.stats["W"]
        self.mp = self.max_mp
#        print(f"Base stats: {self.stats}, HP: {self.hp}, MP: {self.mp}")

    def load_starting_data(self):
        # print("Entering load_starting_data...")
        gear = load_json("gear.json")
        # print(f"Loaded gear.json: {len(gear)} items")
        starting_gear = {
            "1": ["Worn Armor", "Aged Sword", "Patch Pants", "Rugged Boots"],
            "2": ["Tattered Robe", "Walking Stick", "Woolen Pants", "Sandals"],
            "3": ["Hide Shirt", "Chipped Knife", "Worn Pants", "Footwraps"]
        }
        for item_name in starting_gear.get(self.class_type, []):
            # print(f"Looking for {item_name}...")
            item = next((g for g in gear if g["name"] == item_name), None)
            if item:
                slot = item["slot"]
                stats = item.get("stats", {})
                scaling_stat = item.get("modifier", "")
                armor_value = item.get("armor_value", 0)
                self.equipment[slot] = (item_name, stats, scaling_stat, armor_value)
                for stat, val in stats.items():
                    self.stats[stat] += val
                # print(f"Equipped {item_name} to {slot}, Stats now: {self.stats}")
            # Removed empty else block; uncomment below if you want to keep it
            # else:
            #     print(f"Warning: Starting gear '{item_name}' not found in gear.json!")

        self.max_hp = 10 + 2 * self.stats["S"]
        self.hp = self.max_hp
        self.max_mp = 3 * self.stats["W"] if self.class_type == "2" else 2 * self.stats["W"]
        self.mp = self.max_mp
#        print(f"Updated HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}")

        skills_data = load_json("skills.json")
        skills = skills_data.get("skills", [])
       # print(f"Loaded skills.json: {len(skills)} skills")
        for skill in skills:
            if (skill.get("class_type") == self.class_type and 
                skill.get("level_req") == 1 and 
                skill.get("name") not in self.skills and 
                len(self.skills) < 15):
                self.skills.append(skill["name"])
               # print(f"Starting skill unlocked: {skill['name']}")
       # print(f"Final equipment: {self.equipment}")
       # print(f"Final skills: {self.skills}")
       # print(f"XP after load: exp={self.exp}, pending_xp={self.pending_xp}")

    def update_kill_count(self, monster_name):
        quests = load_json("quest.json").get("quests", [])
        for quest in self.active_quests:
            quest_data = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
            if quest_data:
                for i, stage in enumerate(quest["stages"]):
                    if (stage["type"] in ["kill", "boss"] and 
                        stage["target_monster"] == monster_name):
                        stage["kill_count"] = stage.get("kill_count", 0) + 1
                        required = quest_data["stages"][i]["kill_count_required"]
                        print(f"Progress: {quest['quest_name']} - {monster_name} {stage['kill_count']}/{required}")

    def update_quest_items(self, item_name):
        quests = load_json("quest.json").get("quests", [])
        for quest in self.active_quests:
            quest_data = next((q for q in quests if q["quest_name"] == quest["quest_name"]), None)
            if quest_data:
                for i, stage in enumerate(quest["stages"]):
                    if stage["type"] == "collect" and stage["target_item"] == item_name:
                        stage["item_count"] = min(
                            self.inventory.count(item_name),
                            quest_data["stages"][i]["item_count_required"]
                        )
                        required = quest_data["stages"][i]["item_count_required"]
                        print(f"Progress: {quest['quest_name']} - {item_name} {stage['item_count']}/{required}")
                        break

    def get_total_armor_value(self):
        total_av = 0
        for slot, item in self.equipment.items():
            if item:
                _, _, scaling_stat, base_av = item
                scaling_bonus = self.stats[scaling_stat] * 0.1
                total_av += base_av + scaling_bonus
        return min(total_av, 100)

    def apply_xp(self):
        # Add pending XP to current XP regardless of level
        self.exp += self.pending_xp
            
        # Only try to level up if we're not at max level
        while self.exp >= self.max_exp and self.level < 25:
            self.level_up()
            
        # Clear pending XP after applying it
        self.pending_xp = 0
        
        # Save the game after applying XP to ensure it's persisted
        save_game(self)

    def apply_adventurer_points(self, points):
        if self.adventurer_points >= self.max_adventurer_points:
            print("\nYou have reached the maximum adventurer rank!")
            return self.adventurer_points
            
        self.adventurer_points = min(self.adventurer_points + points, self.max_adventurer_points)
        
        # Check for rank up
        while self.adventurer_rank < 6 and self.adventurer_points >= self.rank_thresholds[self.adventurer_rank]:
            self.rank_up()
            
        return self.adventurer_points

    def rank_up(self):
        if self.adventurer_rank < 6:  # Max rank is 6 (Emerald)
            self.adventurer_rank += 1
            rank_names = ["Silver", "Gold", "Crystal", "Sapphire", "Ruby", "Emerald"]
            print(f"\nCongratulations! You have achieved the rank of {rank_names[self.adventurer_rank-1]} Adventurer!")
            return True
        return False

    def get_rank_name(self):
        rank_names = ["Silver", "Gold", "Crystal", "Sapphire", "Ruby", "Emerald"]
        return rank_names[self.adventurer_rank - 1]

    def get_next_rank_points(self):
        if self.adventurer_rank < 6:
            return self.rank_thresholds[self.adventurer_rank] - self.adventurer_points
        return 0

    def level_up(self):
        """Handle a single level-up with scaled HP/MP increases."""
        old_max_hp = self.max_hp
        old_max_mp = self.max_mp

        self.level += 1
        self.exp -= self.max_exp  # Only subtract XP if leveling via apply_xp
        self.max_exp = int(25 * (2.5 ** (self.level - 1)))  # Start at 25 XP, scale by 2.5x per level
        self.stat_points += 1
        print(f"{self.name} leveled up to {self.level}! You have {self.stat_points} stat points to allocate.")

        # Check for new skills
        skills_data = load_json("skills.json").get("skills", [])
        for skill in skills_data:
            if (skill["class_type"] == self.class_type and 
                skill["level_req"] <= self.level and 
                skill["name"] not in self.skills and 
                len(self.skills) < 15):
                self.skills.append(skill["name"])
                print(f"You've unlocked the {skill['name']} skill!")

        # Allocate stat points
        if self.stat_points > 0:
            self.allocate_stat()

        # Apply scaled HP/MP increases AFTER stat allocation
        self.max_hp += 2 + (2 * self.stats["S"])  # Base 2 + 2 per Strength
        self.max_mp += 1 + (2 * self.stats["W"])  # Base 1 + 2 per Wisdom
        self.hp = self.max_hp
        self.mp = self.max_mp

        # Show increase
        hp_increase = self.max_hp - old_max_hp
        mp_increase = self.max_mp - old_max_mp
        print(f"HP increased by {hp_increase} to {self.hp}/{self.max_hp}")
        print(f"MP increased by {mp_increase} to {self.mp}/{self.max_mp}")

    def allocate_stat(self):
        while self.stat_points > 0:
            print(f"\nStat Points Available: {self.stat_points}")
            print(f"Current Stats: S:{self.stats['S']} A:{self.stats['A']} I:{self.stats['I']} W:{self.stats['W']} L:{self.stats['L']}")
            print("1. Strength (S) | 2. Agility (A) | 3. Intelligence (I) | 4. Willpower (W) | 5. Luck (L) | 6. Done")
            choice = input("Select stat to increase: ")
            stat_map = {"1": "S", "2": "A", "3": "I", "4": "W", "5": "L"}
            if choice in stat_map:
                self.stats[stat_map[choice]] += 1
                self.stat_points -= 1
                print(f"{stat_map[choice]} increased to {self.stats[stat_map[choice]]}!")
            elif choice == "6":
                break
            else:
                print("Invalid choice!")

def save_game(player):
    base_path = get_base_path()  # Use utils.get_base_path()
    save_path = os.path.join(base_path, "save.json")
    save_data = {
        "name": player.name,
        "level": player.level,
        "exp": player.exp,
        "max_exp": player.max_exp,
        "stats": player.stats,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "mp": player.mp,
        "max_mp": player.max_mp,
        "inventory": player.inventory,
        "equipment": {
            slot: (item[0], item[1], item[2], item[3]) if item else None
            for slot, item in player.equipment.items()
        },
        "active_enemy_effect": player.active_enemy_effect,
        "class_type": player.class_type,
        "pending_xp": player.pending_xp,
        "stat_points": player.stat_points,
        "gold": player.gold,
        "shop_stock": player.shop_stock,
        "tavern_buff": player.tavern_buff,
        "rage_turns": player.rage_turns,
        "skills": player.skills,
        "skill_effects": player.skill_effects,
        "active_quests": player.active_quests,
        "completed_quests": player.completed_quests,
        "tavern_npcs": player.tavern_npcs,
        "event_cooldowns": player.event_cooldowns,
        "has_room": player.has_room,
        "adventurer_rank": player.adventurer_rank,
        "adventurer_points": player.adventurer_points,
        "max_adventurer_points": player.max_adventurer_points,
        "guild_member": getattr(player, "guild_member", False)  # Add guild membership status
    }
    try:
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=4)
#        print("Game saved successfully as save.json.")
    except Exception as e:
        print(f"Failed to save game: {e}")

def load_game():
    base_path = get_base_path()  # Use utils.get_base_path()
    save_path = os.path.join(base_path, "save.json")
    if not os.path.exists(save_path):
        return None
    try:
        with open(save_path, 'r') as f:
            save_data = json.load(f)
        player = Player(save_data["name"], save_data["class_type"])
        player.level = save_data["level"]
        player.exp = save_data["exp"]
        player.max_exp = save_data["max_exp"]
        player.stats = save_data["stats"]
        player.hp = save_data["hp"]
        player.max_hp = save_data["max_hp"]
        player.mp = save_data["mp"]
        player.max_mp = save_data["max_mp"]
        player.inventory = save_data["inventory"]
        player.equipment = {
            slot: (data[0], data[1], data[2], data[3]) if data else None
            for slot, data in save_data["equipment"].items()
        }
        player.active_enemy_effect = save_data["active_enemy_effect"]
        player.pending_xp = save_data["pending_xp"]
        player.stat_points = save_data["stat_points"]
        player.gold = save_data["gold"]
        player.shop_stock = save_data["shop_stock"]
        player.tavern_buff = save_data["tavern_buff"]
        player.rage_turns = save_data["rage_turns"]
        player.skills = save_data["skills"]
        player.skill_effects = save_data["skill_effects"]
        player.active_quests = save_data.get("active_quests", [])
        player.completed_quests = save_data.get("completed_quests", [])
        player.tavern_npcs = save_data.get("tavern_npcs", [])
        player.event_cooldowns = save_data.get("event_cooldowns", {})
        player.has_room = save_data.get("has_room", False)
        player.adventurer_rank = save_data["adventurer_rank"]
        player.adventurer_points = save_data["adventurer_points"]
        player.max_adventurer_points = save_data["max_adventurer_points"]
        player.guild_member = save_data.get("guild_member", False)  # Load guild membership status
        return player
    except Exception as e:
        print(f"Error loading save: {e}")
        return None