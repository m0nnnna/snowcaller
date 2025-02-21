import os
import math
from utils import load_file, parse_stats

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
        self.gold = 0
        self.shop_stock = {}
        self.tavern_buff = None
        self.rage_turns = 0  # Legacy, keeping for compatibility
        self.event_cooldowns = {"treasure": 0, "merchant": 0, "trap": 0, "friendly": 0, "curse": 0, "lost": 0}
        self.skills = []  # NEW: List of unlocked skill names
        self.skill_effects = {}  # NEW: Dict of active effects (e.g., {"Rage": 3 turns})

        if class_type == "1":  # Warrior
            self.stats = {"S": 3, "A": 1, "I": 1, "W": 2, "L": 1}
        elif class_type == "2":  # Mage
            self.stats = {"S": 1, "A": 1, "I": 3, "W": 2, "L": 1}
        elif class_type == "3":  # Rogue
            self.stats = {"S": 2, "A": 3, "I": 1, "W": 1, "L": 2}
        
        gear = load_file("gear.txt")
        starting_gear = {
            "1": ["Leather Helm", "Leather Chest", "Leather Pants", "Old Boots",
                  "Worn Gloves", "Short Sword", "Wooden Shield", "Tin Necklace", "Copper Ring"],
            "2": ["Cloth Hood", "Robe", "Cloth Pants", "Sandals",
                  "Cloth Gloves", "Staff", "Tome", "Beaded Necklace", "Silver Ring"],
            "3": ["Hood", "Tunic", "Trousers", "Soft Boots",
                  "Leather Gloves", "Dagger", "Buckler", "Chain Necklace", "Brass Ring"]
        }
        for item in starting_gear[class_type]:
            for g in gear:
                if g.split()[0] == item:
                    slot = g.split()[2]
                    stats = parse_stats(g.split()[1], is_consumable=False)
                    self.equipment[slot] = (item, stats)
                    for stat, val in stats.items():
                        self.stats[stat] += val
        
        self.max_hp = 10 + 2 * self.stats["S"]
        self.hp = self.max_hp
        self.max_mp = 3 * self.stats["W"] if class_type == "2" else 2 * self.stats["W"]
        self.mp = self.max_mp

    def apply_xp(self):
        self.exp += self.pending_xp
        self.pending_xp = 0
        while self.exp >= self.max_exp:
            self.level += 1
            self.exp -= self.max_exp
            self.max_exp = int(10 * (self.level ** 1.5))
            self.stat_points += 1
            print(f"{self.name} leveled up to {self.level}! You have {self.stat_points} stat points to allocate.")
            # Check for new skills
            skills = load_file("skills.txt")
            for skill_line in skills:
                parts = skill_line[1:-1].split()  # Remove brackets
                class_type, level, name = parts[0], int(parts[1]), parts[2]
                if class_type == self.class_type and level == self.level and name not in self.skills:
                    self.skills.append(name)
                    print(f"You’ve unlocked the {name} skill!")

    def allocate_stat(self):
        if self.stat_points > 0:
            print(f"\nStats: S:{self.stats['S']} A:{self.stats['A']} I:{self.stats['I']} W:{self.stats['W']} L:{self.stats['L']}")
            print("Allocate stat point: 1. Strength (S) | 2. Agility (A) | 3. Intelligence (I) | 4. Will (W) | 5. Luck (L)")
            choice = input("Selection: ")
            if choice == "1":
                self.stats["S"] += 1
                self.max_hp += 2
                self.hp = self.max_hp
            elif choice == "2":
                self.stats["A"] += 1
            elif choice == "3":
                self.stats["I"] += 1
            elif choice == "4":
                self.stats["W"] += 1
                self.max_mp += 3 if self.class_type == "2" else 2
                self.mp = self.max_mp
            elif choice == "5":
                self.stats["L"] += 1
            else:
                print("Invalid choice, point not allocated.")
                return
            self.stat_points -= 1
            print(f"Stat allocated! Remaining points: {self.stat_points}")

def save_game(player):
    with open("save.txt", "w") as f:
        f.write(f"{player.name}\n")
        f.write(f"{player.level}\n")
        f.write(f"{player.exp}\n")
        f.write(f"{player.max_exp}\n")
        f.write("".join([f"{k}{v}" for k, v in player.stats.items()]) + "\n")
        f.write(f"{player.hp}\n")
        f.write(f"{player.max_hp}\n")
        f.write(f"{player.mp}\n")
        f.write(f"{player.max_mp}\n")
        f.write(",".join(player.inventory) + "\n")
        f.write(",".join([f"{k}:{v[0]}" for k, v in player.equipment.items() if v]) + "\n")
        f.write(f"{player.active_enemy_effect[0]}:{player.active_enemy_effect[1]}" if player.active_enemy_effect else "None\n")
        f.write(f"{player.class_type}\n")
        f.write(f"{player.pending_xp}\n")
        f.write(f"{player.stat_points}\n")
        f.write(f"{player.gold}\n")
        f.write(",".join([f"{k}:{v}" for k, v in player.shop_stock.items()]) + "\n")
        f.write(f"{player.tavern_buff['stat']}:{player.tavern_buff['value']}\n" if player.tavern_buff else "None\n")
        f.write(f"{player.rage_turns}\n")
        f.write(",".join(player.skills) + "\n")  # NEW: Save skills
        f.write(",".join([f"{k}:{v}" for k, v in player.skill_effects.items()]) + "\n")  # NEW: Save active effects

def load_game():
    with open("save.txt", "r") as f:
        lines = f.readlines()
        player = Player(lines[0].strip(), lines[12].strip())
        player.level = int(lines[1])
        player.exp = int(lines[2])
        player.max_exp = int(lines[3])
        player.stats = parse_stats(lines[4].strip(), is_consumable=False)
        player.hp = float(lines[5])
        player.max_hp = float(lines[6])
        player.mp = float(lines[7])
        player.max_mp = float(lines[8])
        player.inventory = lines[9].strip().split(",") if lines[9].strip() else []
        equipment = lines[10].strip().split(",")
        gear = load_file("gear.txt")
        for slot_item in equipment:
            if slot_item:
                slot, item = slot_item.split(":")
                for g in gear:
                    if g.split()[0] == item:
                        player.equipment[slot] = (item, parse_stats(g.split()[1], is_consumable=False))
        effect = lines[11].strip()
        player.active_enemy_effect = effect.split(":") if effect != "None" else None
        player.pending_xp = int(lines[13])
        player.stat_points = int(lines[14])
        player.gold = int(lines[15]) if len(lines) > 15 else 0
        player.shop_stock = dict(item.split(":") for item in lines[16].strip().split(",") if item) if len(lines) > 16 and lines[16].strip() else {}
        buff = lines[17].strip() if len(lines) > 17 else "None"
        player.tavern_buff = {buff.split(":")[0]: int(buff.split(":")[1])} if buff != "None" and ":" in buff else None
        if player.tavern_buff:
            stat, value = list(player.tavern_buff.items())[0]
            player.stats[stat] += value
        player.rage_turns = int(lines[18]) if len(lines) > 18 else 0
        player.skills = lines[19].strip().split(",") if len(lines) > 19 and lines[19].strip() else []  # NEW: Load skills
        player.skill_effects = dict(item.split(":") for item in lines[20].strip().split(",") if item) if len(lines) > 20 and lines[20].strip() else {}  # NEW: Load effects
        return player