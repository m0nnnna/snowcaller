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
        self.rage_turns = 0
        self.event_cooldowns = {"treasure": 0, "merchant": 0, "trap": 0, "friendly": 0, "curse": 0, "lost": 0}
        self.skills = []
        self.skill_effects = {}

        if class_type == "1":  # Warrior
            self.stats = {"S": 3, "A": 1, "I": 1, "W": 2, "L": 1}
        elif class_type == "2":  # Mage
            self.stats = {"S": 1, "A": 1, "I": 3, "W": 2, "L": 1}
        elif class_type == "3":  # Rogue
            self.stats = {"S": 2, "A": 3, "I": 1, "W": 1, "L": 2}
        
        gear = load_file("gear.txt")
        starting_gear = {
            "1": ["Warrior Cap", "Warrior Vest", "Warrior Blade"],
            "2": ["Mage Cap", "Mage Gown", "Mage Wand"],
            "3": ["Rogue Pants", "Rogue Gloves", "Rogue Boots", "Rogue Shirt", "Rogue Knife"]
        }
        for item in starting_gear[class_type]:
            for g in gear:
                name_part, bracket_part = g.split('[', 1)
                gear_name = name_part.strip()
                if gear_name == item:
                    bracket = bracket_part.strip("]").split()
                    slot = bracket[1]
                    scaling_stat = bracket[2]
                    stats_str = bracket[3]
                    armor_value = int(bracket[5].split(":")[1])
                    stats = parse_stats(stats_str, is_consumable=False)
                    self.equipment[slot] = (item, stats, scaling_stat, armor_value)
                    for stat, val in stats.items():
                        self.stats[stat] += val
                    break
            else:
                print(f"Warning: Starting gear '{item}' not found in gear.txt!")
        
        self.max_hp = 10 + 2 * self.stats["S"]
        self.hp = self.max_hp
        self.max_mp = 3 * self.stats["W"] if class_type == "2" else 2 * self.stats["W"]
        self.mp = self.max_mp

    def get_total_armor_value(self):
        total_av = 0
        for slot, item in self.equipment.items():
            if item:
                _, _, scaling_stat, base_av = item
                scaling_bonus = self.stats[scaling_stat] * 0.5
                total_av += base_av + scaling_bonus
        return min(total_av, 100)

    def apply_xp(self):
        self.exp += self.pending_xp
        self.pending_xp = 0
        while self.exp >= self.max_exp:
            self.level += 1
            self.exp -= self.max_exp
            self.max_exp = int(10 * (self.level ** 1.5))
            self.stat_points += 1
            print(f"{self.name} leveled up to {self.level}! You have {self.stat_points} stat points to allocate.")
            skills = load_file("skills.txt")
            for skill_line in skills:
                parts = skill_line[1:-1].split()
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
        f.write(",".join(player.inventory) if player.inventory else "\n")
        equipment_str = ",".join([f"{k}:{v[0]}:{''.join([f'{stat}{val}' for stat, val in v[1].items()])}:{v[2]}:{v[3]}" for k, v in player.equipment.items() if v]) or ""
        f.write(f"{equipment_str}\n")
        f.write(f"{player.active_enemy_effect[0]}:{player.active_enemy_effect[1]}" if player.active_enemy_effect else "None\n")
        f.write(f"{player.class_type}\n")
        f.write(f"{player.pending_xp}\n")
        f.write(f"{player.stat_points}\n")
        f.write(f"{player.gold}\n")
        f.write(",".join([f"{k}:{v}" for k, v in player.shop_stock.items()]) if player.shop_stock else "\n")
        f.write(f"{player.tavern_buff['stat']}:{player.tavern_buff['value']}" if player.tavern_buff else "None\n")
        f.write(f"{player.rage_turns}\n")
        f.write(",".join(player.skills) if player.skills else "\n")
        f.write(",".join([f"{k}:{v}" for k, v in player.skill_effects.items()]) if player.skill_effects else "\n")

def load_game():
    try:
        with open("save.txt", "r") as f:
            lines = [line.strip() for line in f.readlines()]  # No filtering blanks yet
            if len(lines) != 21:
                raise ValueError(f"Expected 21 lines, got {len(lines)}")

            player = Player(lines[0], lines[12])  # name, class_type
            player.level = int(lines[1])
            player.exp = int(lines[2])
            player.max_exp = int(lines[3])
            player.stats = parse_stats(lines[4], is_consumable=False)
            player.hp = float(lines[5])
            player.max_hp = float(lines[6])
            player.mp = float(lines[7])
            player.max_mp = float(lines[8])
            player.inventory = lines[9].split(",") if lines[9] else []
            equipment = lines[10].split(",") if lines[10] else []
            for slot_item in equipment:
                if slot_item:
                    slot, item_name, stats_str, scaling_stat, av = slot_item.split(":")
                    stats = parse_stats(stats_str, is_consumable=False)
                    player.equipment[slot] = (item_name, stats, scaling_stat, int(av))
            player.active_enemy_effect = lines[11].split(":") if lines[11] != "None" else None
            # player.class_type already set in constructor
            player.pending_xp = int(lines[13])
            player.stat_points = int(lines[14])
            player.gold = int(lines[15])
            player.shop_stock = dict(item.split(":") for item in lines[16].split(",") if item) if lines[16] else {}
            buff = lines[17]
            player.tavern_buff = {buff.split(":")[0]: int(buff.split(":")[1])} if buff != "None" and ":" in buff else None
            if player.tavern_buff:
                stat, value = list(player.tavern_buff.items())[0]
                player.stats[stat] += value
            player.rage_turns = int(lines[18])
            player.skills = lines[19].split(",") if lines[19] else []
            player.skill_effects = dict(item.split(":") for item in lines[20].split(",") if item) if lines[20] else {}
            return player
    except (IndexError, ValueError, FileNotFoundError) as e:
        print(f"Save file corrupted or missing: {e}. Starting new game.")
        raise