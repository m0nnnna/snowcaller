import random
import time
from utils import load_file

def random_event(player, encounter_count, max_encounters):
    print(f"\nDistance traveled: {encounter_count}/{max_encounters}")
    time.sleep(0.5)

    # Define base options and weights
    all_options = ["treasure", "merchant", "trap", "friendly", "curse", "lost"]
    base_weights = [20, 15, 15, 15, 10, 10]  # CHANGED: "lost" from 25 to 10

    # Filter out events on cooldown
    available_options = []
    available_weights = []
    for opt, weight in zip(all_options, base_weights):
        if player.event_cooldowns[opt] == 0:
            available_options.append(opt)
            available_weights.append(weight)

    # If no events are available, reset cooldowns and use all options
    if not available_options:
        for opt in all_options:
            player.event_cooldowns[opt] = 0
        available_options = all_options
        available_weights = base_weights

    # Pick event from available pool
    event = random.choices(available_options, weights=available_weights, k=1)[0]

    # Set cooldowns (longer for "lost")
    cooldown_duration = 3 if event == "lost" else 1
    player.event_cooldowns[event] = cooldown_duration

    # Decrement all cooldowns
    for opt in player.event_cooldowns:
        if player.event_cooldowns[opt] > 0:
            player.event_cooldowns[opt] -= 1

    # Event logic
    if event == "treasure":
        treasures = load_file("treasures.txt")
        items = random.sample(treasures, random.randint(1, 3))
        gold = random.randint(10, 20)
        player.inventory.extend(items)
        player.gold += gold
        print("You spot a glint beneath some roots—a forgotten stash!")
        print(f"You find: {', '.join(items)} and {gold} gold!")
        time.sleep(0.5)

    elif event == "merchant":
        gear = load_file("gear.txt") + load_file("consumables.txt")
        item = random.choice([g for g in gear if not any(i in g for i in ["main_hand", "off_hand"])])
        name = item.split()[0]
        base_price = int(item.split()[-1].split()[2]) if "L:" in item else 10
        price_mod = random.choice([0.8, 1.5])  # 20% discount or 50% markup
        price = int(base_price * price_mod)
        print(f"A cloaked figure emerges from the mist, offering {name} for {price} gold.")
        print("1. Buy | 2. Pass")
        time.sleep(0.5)
        choice = input("Selection: ")
        if choice == "1" and player.gold >= price:
            player.gold -= price
            player.inventory.append(name)
            print(f"You purchase {name} for {price} gold!")
            time.sleep(0.5)
        elif choice == "1":
            print("Not enough gold!")
            time.sleep(0.5)
        else:
            print("You pass by the merchant.")
            time.sleep(0.5)

    elif event == "trap":
        damage = player.max_hp * 0.1
        if player.stats["A"] > 5 and random.random() < 0.5:
            print("A twig snaps—a trap springs to life, but you dodge it!")
            time.sleep(0.5)
        else:
            player.hp -= damage
            print(f"A trap catches you off guard, dealing {round(damage, 1)} damage!")
            time.sleep(0.5)

    elif event == "friendly":
        if random.random() < 0.5:
            heal = player.max_hp * 0.2
            player.hp = min(player.hp + heal, player.max_hp)
            print(f"A kind stranger shares a tale and heals you for {round(heal, 1)} HP!")
        else:
            consumables = load_file("consumables.txt")
            item = random.choice(consumables).split()[0]
            player.inventory.append(item)
            print(f"A kind stranger shares a tale and gives you a {item}!")
        time.sleep(0.5)

    elif event == "curse":
        print("An eerie shrine whispers promises of power...")
        print("1. Accept | 2. Decline")
        time.sleep(0.5)
        choice = input("Selection: ")
        if choice == "1":
            if random.random() < 0.5:
                stat = random.choice(["S", "A", "I", "W", "L"])
                player.stats[stat] += 2
                print(f"The shrine blesses you with +2 {stat[:3].capitalize()}!")
            else:
                damage = player.max_hp * 0.1
                player.hp -= damage
                print(f"The shrine curses you, dealing {round(damage, 1)} damage!")
            time.sleep(0.5)
        else:
            print("You leave the shrine untouched.")
            time.sleep(0.5)

    elif event == "lost":
        max_encounters = min(max_encounters + 1, 10)
        print("The trail twists—where are you now? One more encounter ahead!")
        time.sleep(0.5)

    return max_encounters  # Return updated max_encounters