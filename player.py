import json
import sys
import os
import math
from utils import load_json, load_file, parse_stats, save_json  # Added save_json

class Player:
    def __init__(self, name, class_type):
        self.name = name
        self.level = 1
        self.exp = 0
        self.max_exp = 10
        self.inventory = []
        self.equipment = {"head": None, "chest": None, "pants": None, "boots": None,
                         "gloves": None, "main_hand": None, "off_hand": None, "neck": None, "ring": None}
        self.active_enemy_effect = None
        self.class_type = class_type
        self.pending_xp = 0
        self.stat_points = 0
        self.gold = 100
        self.shop_stock = {}
        self.tavern_buff = None
        self.rage_turns = 0
        self.event_cooldowns = {"treasure": 0, "merchant": 0, "trap": 0, "friendly": 0, "curse": 0, "lost": 0}
        self.skills = []
        self.skill_effects = {}
        self.active_quests = []
        self.completed_quests = []

        if class_type == "1":  # Warrior
            self.stats = {"S": 3, "A": 1, "I": 1, "W": 2, "L": 1}
        elif class_type == "2":  # Mage
            self.stats = {"S": 1, "A": 1, "I": 3, "W": 2, "L": 1}
        elif class_type == "3":  # Rogue
            self.stats = {"S": 2, "A": 3, "I": 1, "W": 1, "L": 2}

        self.max_hp = 10 + 2 * self.stats["S"]
        self.hp = self.max_hp
        self.max_mp = 3 * self.stats["W"] if class_type == "2" else 2 * self.stats["W"]
        self.mp = self.max_mp

    def load_starting_data(self):
        # Your existing implementation
        gear = load_json("gear.json")
        starting_gear = {
            "1": ["Warrior Cap", "Warrior Vest", "Warrior Blade"],
            "2": ["Mage Cap", "Mage Gown", "Mage Wand"],
            "3": ["Rogue Pants", "Rogue Gloves", "Rogue Boots", "Rogue Shirt", "Rogue Knife"]
        }
        for item_name in starting_gear[self.class_type]:
            for g in gear:
                if g["name"] == item_name:
                    slot = g["slot"]
                    scaling_stat = g["modifier"]
                    stats = g["stats"]
                    armor_value = g["armor_value"]
                    self.equipment[slot] = (item_name, stats, scaling_stat, armor_value)
                    for stat, val in stats.items():
                        self.stats[stat] += val
                    break
            else:
                print(f"Warning: Starting gear '{item_name}' not found in gear.json!")

        skills_data = load_json("skills.json").get("skills", [])
        for skill in skills_data:
            if (skill["class_type"] == self.class_type and 
                skill["level_req"] == 1 and 
                skill["name"] not in self.skills and 
                len(self.skills) < 15):
                self.skills.append(skill["name"])
                print(f"Starting skill unlocked: {skill['name']}")

    def get_total_armor_value(self):
        # Your existing implementation
        pass

    def apply_xp(self):
        # Your existing implementation
        pass

    def allocate_stat(self):
        # Your existing implementation
        pass

def save_game(player):
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
        "completed_quests": player.completed_quests
    }
    if save_json("save.json", save_data):
        print("Game saved successfully as save.json.")
    else:
        print("Failed to save game.")
        raise Exception("Save failed")

def load_game():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    save_path = os.path.join(base_path, "save.json")
    print(f"Loading from: {save_path}")  # Debug
    try:
        with open(save_path, "r") as f:
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
        
        player.max_hp = 10 + 2 * player.stats["S"]
        player.hp = min(player.hp, player.max_hp)
        player.max_mp = 3 * player.stats["W"] if player.class_type == "2" else 2 * player.stats["W"]
        player.mp = min(player.mp, player.max_mp)
        
        print("Game loaded successfully from save.json.")
        return player
    except KeyError as e:
        print(f"Error loading save file: Missing key {e}")
        raise