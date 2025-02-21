import random
import os
import time
from items import use_item
from utils import load_file, parse_stats

def get_weapon_damage_range(player):
    weapon = player.equipment.get("main_hand")
    damage_bonus = 4 if player.rage_turns > 0 else 0  # Rage bonus
    if weapon:
        for g in load_file("gear.txt"):
            parts = g.split()
            if parts[0] == weapon[0] and len(parts) > 3:
                min_dmg, max_dmg = map(float, parts[-3].split("-"))
                if "Sword" in weapon[0]:
                    stat_bonus = player.stats["S"] * 0.5
                elif "Dagger" in weapon[0]:
                    stat_bonus = player.stats["A"] * 0.5
                elif "Staff" in weapon[0]:
                    stat_bonus = player.stats["I"] * 0.5
                    # Mage-specific I modifier (0.8% per I point)
                    if player.class_type == "2":
                        i_modifier = 1 + (player.stats["I"] * 0.008)
                        min_dmg *= i_modifier
                        max_dmg *= i_modifier
                else:
                    stat_bonus = 0
                return (min_dmg + stat_bonus + damage_bonus, max_dmg + stat_bonus + damage_bonus)
    return (1 + damage_bonus, 2 + damage_bonus)

def calculate_dodge_chance(attacker_a, defender_a):
    base_dodge = min(5 + defender_a * 0.5, 20)
    if defender_a > attacker_a:
        bonus = (defender_a - attacker_a) * 0.25
        total_dodge = min(base_dodge + bonus, 20)
    else:
        total_dodge = base_dodge
    return total_dodge / 100

def calculate_flee_chance(player_luck, monster_luck):
    base_chance = 0.5
    luck_diff = player_luck - monster_luck
    modifier = luck_diff * 0.05
    flee_chance = base_chance + modifier
    return max(0.1, min(flee_chance, 0.9))

def combat(player, monster, monster_stats):
    monster_hp = monster_stats.get("hp_boost", 10 + 2 * monster_stats["S"])
    monster_max_hp = monster_hp
    monster_mp = 2 * monster_stats["W"]
    base_min_dmg, base_max_dmg = map(float, monster_stats["damage_range"].split("-"))
    level_scale = 1 + (monster_stats["level"] - 1) * 0.05
    monster_min_dmg = base_min_dmg * level_scale + monster_stats["S"] * 0.5
    monster_max_dmg = base_max_dmg * level_scale + monster_stats["S"] * 0.5
    
    print(f"A {monster} (Level {monster_stats['level']}) appears! HP: {monster_hp}, MP: {monster_mp}")
    time.sleep(1)
    original_monster_stats = monster_stats.copy()
    while monster_hp > 0 and player.hp > 0:
        crit_chance = 0.2 * player.stats["A"]
        print(f"\n{player.name}: HP {round(player.hp, 1)}/{player.max_hp}, MP {player.mp}/{player.max_mp} | {monster}: HP {round(monster_hp, 1)}/{monster_max_hp}, MP {monster_mp}")
        if player.active_enemy_effect:
            print(f"Active effect: {player.active_enemy_effect[0]} ({player.active_enemy_effect[1]} turns left)")
        if player.rage_turns > 0:
            print(f"Rage active ({player.rage_turns} turns left)")
        time.sleep(0.5)
        if player.level >= 5:
            skill = {"1": "Rage", "2": "Fireball", "3": "Backstab"}[player.class_type]
            print(f"1. Attack | 2. Use Item | 3. Flee | 4. {skill}")
        else:
            print("1. Attack | 2. Use Item | 3. Flee")
        choice = input("Selection: ")
        
        player_turn_used = True
        if choice == "1":
            min_dmg, max_dmg = get_weapon_damage_range(player)
            damage = random.uniform(min_dmg, max_dmg)
            if random.random() < crit_chance / 100:
                damage *= 2
                print("Critical hit!")
                time.sleep(1)
            damage = round(damage, 1)
            dodge_chance = calculate_dodge_chance(player.stats["A"], monster_stats["A"])
            if random.random() < dodge_chance:
                print(f"{monster} dodges your attack!")
                time.sleep(1)
            else:
                monster_hp -= damage
                print(f"You deal {damage} damage!")
                time.sleep(1)
            if monster_hp <= 0:
                print(f"You defeated the {monster}!")
                time.sleep(1)
                xp_gain = max(1, monster_stats["level"] * 5 - (player.level - monster_stats["level"]) * 2)
                player.pending_xp += xp_gain
                print(f"Earned {xp_gain} XP (to be applied after adventure)!")
                time.sleep(1)
                return True
        elif choice == "2" and player.rage_turns == 0:
            if not player.inventory:
                print("No items in inventory!")
                time.sleep(1)
                player_turn_used = False
            else:
                print("Inventory:", ", ".join(player.inventory))
                time.sleep(0.5)
                item = input("Choose item: ")
                if item in player.inventory:
                    player_turn_used = use_item(player, item, monster_stats)
                    if not player_turn_used:
                        monster_hp = min(monster_hp, 10 + 2 * monster_stats["S"])
                        monster_mp = 2 * monster_stats["W"]
                else:
                    print("Item not found!")
                    time.sleep(1)
                    player_turn_used = False
        elif choice == "3" and player.rage_turns == 0:
            flee_chance = calculate_flee_chance(player.stats["L"], monster_stats["L"])
            if random.random() < flee_chance:
                print("You fled successfully!")
                time.sleep(1)
                return False
            else:
                print("Failed to flee!")
                time.sleep(1)
        elif choice == "4" and player.level >= 5:
            if player.class_type == "1":  # Warrior - Rage
                if player.mp >= 5:
                    player.mp -= 5
                    player.rage_turns = 3
                    print("You enter a Rage, increasing damage by 4 for 3 turns!")
                    time.sleep(1)
                else:
                    print("Not enough MP for Rage (5 MP required)!")
                    time.sleep(1)
                    player_turn_used = False
            elif player.class_type == "3":  # Rogue - Backstab
                if player.mp >= 5:
                    player.mp -= 5
                    min_dmg, max_dmg = get_weapon_damage_range(player)
                    base_damage = random.uniform(min_dmg, max_dmg)
                    damage = base_damage + 2 * player.stats["A"]
                    hit_chance = 0.7 - calculate_dodge_chance(player.stats["A"], monster_stats["A"])
                    if random.random() < hit_chance:
                        monster_hp -= damage
                        print(f"You Backstab, dealing {round(damage, 1)} damage!")
                        time.sleep(1)
                    else:
                        print(f"{monster} dodges your Backstab!")
                        time.sleep(1)
                    if monster_hp <= 0:
                        print(f"You defeated the {monster}!")
                        time.sleep(1)
                        xp_gain = max(1, monster_stats["level"] * 5 - (player.level - monster_stats["level"]) * 2)
                        player.pending_xp += xp_gain
                        print(f"Earned {xp_gain} XP (to be applied after adventure)!")
                        time.sleep(1)
                        return True
                else:
                    print("Not enough MP for Backstab (5 MP required)!")
                    time.sleep(1)
                    player_turn_used = False
            elif player.class_type == "2":  # Mage - Fireball
                if player.mp >= 10:
                    player.mp -= 10
                    base_damage = 15
                    i_bonus = 1 + (player.stats["I"] * 0.005)
                    damage = base_damage * i_bonus
                    monster_hp -= damage
                    print(f"You cast Fireball, dealing {round(damage, 1)} damage!")
                    time.sleep(1)
                    if monster_hp <= 0:
                        print(f"You defeated the {monster}!")
                        time.sleep(1)
                        xp_gain = max(1, monster_stats["level"] * 5 - (player.level - monster_stats["level"]) * 2)
                        player.pending_xp += xp_gain
                        print(f"Earned {xp_gain} XP (to be applied after adventure)!")
                        time.sleep(1)
                        return True
                else:
                    print("Not enough MP for Fireball (10 MP required)!")
                    time.sleep(1)
                    player_turn_used = False
        
        if player_turn_used:
            damage = random.uniform(monster_min_dmg, monster_max_dmg)
            if random.random() < 0.2 * monster_stats["A"] / 100:
                damage *= 2
                print(f"{monster} lands a critical hit!")
                time.sleep(1)
            damage = round(damage, 1)
            dodge_chance = calculate_dodge_chance(monster_stats["A"], player.stats["A"])
            if random.random() < dodge_chance:
                print("You dodge the monster's attack!")
                time.sleep(1)
            else:
                player.hp -= damage
                print(f"{monster} deals {damage} damage!")
                time.sleep(1)
            
            if player.active_enemy_effect:
                player.active_enemy_effect[1] = int(player.active_enemy_effect[1]) - 1
                if player.active_enemy_effect[1] <= 0:
                    print(f"{player.active_enemy_effect[0]} effect wears off!")
                    time.sleep(1)
                    for stat in monster_stats:
                        if stat not in ["level", "damage_range", "hp_boost"]:
                            monster_stats[stat] = original_monster_stats[stat]
                    player.active_enemy_effect = None
        
        if player.rage_turns > 0:
            player.rage_turns -= 1
            if player.rage_turns == 0:
                print("Your Rage subsides.")
                time.sleep(1)
        
        if player.hp <= 0:
            print("You died!")
            time.sleep(1)
            try:
                os.remove("save.txt")
            except PermissionError:
                print("Could not delete save file due to a permission issue. Please close any programs using 'save.txt' and delete it manually.")
                time.sleep(1)
            return False
    return False
