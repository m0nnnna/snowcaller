import time

def tavern_menu(player):
    print("\nWelcome to the Tavern!")
    print("1. Rest (10 Gold) | 2. Feast (5 Gold) | 3. Exit")
    time.sleep(0.5)  # Half-second delay before input
    choice = input("Selection: ")

    if choice == "1":
        if player.gold >= 10:
            player.gold -= 10
            player.hp = player.max_hp
            player.mp = player.max_mp
            print("You rest at the tavern, fully restoring your HP and MP!")
            time.sleep(0.5)
        else:
            print("Not enough gold to rest!")
            time.sleep(0.5)

    elif choice == "2":
        if player.gold >= 5:
            print("\nChoose a feast buff (overwrites existing buff):")
            print("1. Strength (+2 S) | 2. Agility (+2 A) | 3. Intelligence (+2 I) | 4. Will (+2 W) | 5. Luck (+2 L)")
            time.sleep(0.5)
            buff_choice = input("Selection: ")
            buff_options = {
                "1": ("S", 2),
                "2": ("A", 2),
                "3": ("I", 2),
                "4": ("W", 2),
                "5": ("L", 2)
            }
            if buff_choice in buff_options:
                # Remove old buff if it exists
                if hasattr(player, "tavern_buff") and player.tavern_buff:
                    old_stat, old_val = list(player.tavern_buff.items())[0]
                    player.stats[old_stat] -= old_val
                # Apply new buff
                stat, value = buff_options[buff_choice]
                player.stats[stat] += value
                player.tavern_buff = {stat: value}
                player.gold -= 5
                print(f"You feast and gain +{value} {stat[:3].capitalize()}!")
                time.sleep(0.5)
            else:
                print("Invalid choice, no buff applied!")
                time.sleep(0.5)
        else:
            print("Not enough gold to feast!")
            time.sleep(0.5)

    elif choice == "3":
        return
    else:
        print("Invalid choice!")
        time.sleep(0.5)
