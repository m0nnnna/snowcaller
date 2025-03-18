import random
import time
import json
import os
from utils import load_json
from combat import combat

def execute_outcome(player, outcome, max_encounters):
    if outcome["type"] == "item":
        source = outcome["source"]
        items = load_json(source)
        valid_items = [i for i in items if i.get("drop_rate", 0) > 0]
        count = random.randint(outcome["count"]["min"], outcome["count"]["max"])
        selected_items = random.choices(valid_items, weights=[i["drop_rate"] for i in valid_items], k=min(count, len(valid_items)))
        item_names = [i["name"] for i in selected_items]
        player.inventory.extend(item_names)
        return f"Found: {', '.join(item_names)}"
    elif outcome["type"] == "quest":
       quests = load_json("quest.json")["quests"]
       quest_name = outcome.get("quest", {}).get("quest_name")
       if not quest_name:
           print("Error: No quest_name specified in event outcome!")
           return
       quest = next((q for q in quests if q["quest_name"] == quest_name), None)
       if not quest:
           print(f"Quest '{quest_name}' not found!")
           return
       conditions = outcome.get("conditions", {})
       max_active = conditions.get("max_active_quests", 5)
       if len(player.active_quests) >= max_active:
           print("You have too many active quests!")
           return
       print(f"\nNew Quest Available: {quest['quest_name']}")
       print(quest["quest_description"])
       if outcome.get("requires_choice", False):
           print("1. Accept | 2. Decline")
           choice = input("Selection: ")
           if choice == "1":
               # Quest is accepted in tavern, not here; event just triggers NPC
               if "on_accept" in outcome:
                   on_accept = outcome["on_accept"]
                   if on_accept["type"] == "custom" and on_accept["action"] == "add_tavern_npc":
                       npc = on_accept["npc"]
                       if not hasattr(player, "tavern_npcs"):
                           player.tavern_npcs = []
                       if npc["name"] not in [n["name"] for n in player.tavern_npcs]:
                           player.tavern_npcs.append(npc)
                           print(f"{npc['name']} has appeared at the tavern!")
           else:
               print("You decline the opportunity.")
       else:
           print("Event triggered without choice; see tavern for details.")

    elif outcome["type"] == "gold":
        amount = random.randint(outcome["amount"]["min"], outcome["amount"]["max"])
        player.gold += amount
        return f"Gained {amount} gold"

    elif outcome["type"] == "merchant":
        sources = outcome["source"]
        exclude_slots = outcome.get("exclude_slots", [])
        all_items = []
        for src in sources:
            items = load_json(src)
            all_items.extend([i for i in items if not any(slot in i.get("slot", "") for slot in exclude_slots)])
        if not all_items:
            return "Merchant has nothing to sell!"
        item = random.choice(all_items)
        name = item["name"]
        price_field = outcome.get("price_field", "drop_rate")
        try:
            base_price = int(item.get(price_field, 10))
        except (ValueError, TypeError):
            base_price = 10
        price = int(base_price * random.choice(outcome["price_modifiers"]))
        if not outcome.get("requires_choice", False):
            return f"Merchant offers {name} for {price} gold (logic error: choice required)"
        print("1 for Yes | 2 for No")
        time.sleep(0.5)
        choice = input("Selection: ")
        if choice == "1" and player.gold >= price:
            player.gold -= price
            player.inventory.append(name)
            return f"Purchased {name} for {price} gold"
        elif choice == "1":
            return "Not enough gold!"
        return "You pass by the merchant"

    elif outcome["type"] == "extend_encounters":
        max_encounters = min(max_encounters + outcome["amount"], outcome["max_limit"])
        return f"Encounters extended to {max_encounters}"

    elif outcome["type"] == "heal":
        heal = player.max_hp * random.uniform(outcome["amount"]["min"], outcome["amount"]["max"])
        player.hp = min(player.hp + heal, player.max_hp)
        return f"Healed for {round(heal, 1)} HP"

    elif outcome["type"] == "damage":
        damage = player.max_hp * random.uniform(outcome["amount"]["min"], outcome["amount"]["max"])
        player.hp -= damage
        return f"Took {round(damage, 1)} damage"

    elif outcome["type"] == "lore":
        if outcome.get("requires_choice", False):
            print("1 for Yes | 2 for No")
            time.sleep(0.5)
            choice = input("Selection: ")
            if choice == "1":
                return outcome["text"]
            return "You ignore the message."
        return outcome["text"]

    elif outcome["type"] == "combat":
        monsters = load_json("monster.json")["monsters"]
        monster = next((m for m in monsters if m["name"] == outcome["monster"]), None)
        if not monster:
            return f"Monster {outcome['monster']} not found!"
        count = outcome.get("count", 1)
        for _ in range(count):
            result = combat(player, monster["rare"], monster["name"])
            if player.hp <= 0:
                return "You died in combat!"
            if "Victory" not in result:
                return "You fled or failed the fight."
        return f"Defeated {count} {outcome['monster']}(s)!"

    elif outcome["type"] == "dialogue":
        if outcome.get("requires_choice", False):
            print("Will you help? 1 for Yes | 2 for No")
            time.sleep(0.5)
            choice = input("Selection: ")
            if choice == "1":
                if "on_reply" in outcome and outcome["on_reply"].get("reply_index") == 0:
                    on_reply = outcome["on_reply"]
                    if on_reply["action"] == "add_tavern_npc":
                        npc = on_reply["npc"]
                        if "quest" in outcome:
                            npc["quest"] = outcome["quest"]
                        if not hasattr(player, "tavern_npcs"):
                            player.tavern_npcs = []
                        if npc["name"] not in [n["name"] for n in player.tavern_npcs]:
                            player.tavern_npcs.append(npc)
                            print(f"{npc['name']} has joined the tavern!")
                            from player import save_game
                            save_game(player)  # Save after adding NPC
                return "You agree to help."
            return "You decline to help."
        return "Dialogue triggered without choice."

def random_event(player, encounter_count, max_encounters):
    events = load_json("event.json")
    available_events = [
        e for e in events 
        if e["level_range"]["min"] <= player.level <= e["level_range"]["max"] 
        and player.event_cooldowns.get(e["name"], 0) == 0 
        and (not e.get("one_time", False) or not e.get("triggered", False))
    ]
    if not available_events:
        for event_name in player.event_timers:
            player.event_timers[event_name] = max(0, player.event_timers[event_name] - 1)
        return max_encounters
    
    event = random.choices(available_events, weights=[e["spawn_chance"] for e in available_events], k=1)[0]
    player.event_timers[event["name"]] = event.get("event_timer", 1)
    if event.get("one_time", False) and not event.get("triggered", False):
        event["triggered"] = True
        with open(os.path.join(os.path.dirname(__file__), "event.json"), "w") as f:
            json.dump(events, f, indent=4)
    print(f"Distance traveled: {encounter_count}/{max_encounters}")  # Example use of encounter_count
    print(event["description"])
    outcome = random.choices(event["outcomes"], weights=[o["weight"] for o in event["outcomes"]], k=1)[0]
    result = execute_outcome(player, outcome, max_encounters)
    print(result)
    
    for event_name in player.event_timers:
        player.event_timers[event_name] = max(0, player.event_timers[event_name] - 1)
    
    return max_encounters

    # Mark one-time event as triggered
    if event.get("one_time", False) and not event.get("triggered", False):
        event["triggered"] = True
        base_path = os.path.dirname(__file__)
        event_path = os.path.join(base_path, "event.json")
        with open(event_path, "w") as f:
            json.dump(events, f, indent=4)

    # Decrement event timers
    for opt in player.event_timers:
        if player.event_timers[opt] > 0:
            player.event_timers[opt] -= 1

    # Execute event
    print(event["description"])
    if "choice_prompt" in event:
        print(event["choice_prompt"])
        time.sleep(0.5)

    outcomes = event["outcomes"]
    if len(outcomes) > 1:
        outcome = random.choices(outcomes, weights=[o["weight"] for o in outcomes], k=1)[0]
    else:
        outcome = outcomes[0]

    result = execute_outcome(player, outcome, max_encounters)
    print(result)
    time.sleep(0.5)

    return max_encounters

def trigger_specific_event(player, event, encounter_count, max_encounters):
    """Trigger a specific event directly, bypassing random selection."""
    print(f"\nDistance traveled: {encounter_count}/{max_encounters}")
    time.sleep(0.5)

    # Set cooldown
    cooldown_duration = event.get("cooldown", 1)
    player.event_cooldowns[event["name"]] = cooldown_duration

    # Mark one-time event as triggered
    if event.get("one_time", False) and not event.get("triggered", False):
        event["triggered"] = True
        base_path = os.path.dirname(__file__)
        event_path = os.path.join(base_path, "event.json")
        events = load_json("event.json")
        with open(event_path, "w") as f:
            json.dump(events, f, indent=4)

    # Decrement cooldowns for other events
    for opt in player.event_cooldowns:
        if player.event_cooldowns[opt] > 0:
            player.event_cooldowns[opt] -= 1

    # Execute the specific event
    print(event["description"])
    if "choice_prompt" in event:
        print(event["choice_prompt"])
        time.sleep(0.5)

    outcomes = event["outcomes"]
    if len(outcomes) > 1:
        outcome = random.choices(outcomes, weights=[o["weight"] for o in outcomes], k=1)[0]
    else:
        outcome = outcomes[0]

    result = execute_outcome(player, outcome, max_encounters)
    print(result)
    time.sleep(0.5)

    return max_encounters