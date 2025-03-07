import random
import time
import json
from utils import load_json  # Assuming this exists in utils.py

def execute_outcome(player, outcome, max_encounters):
    """Handle a single outcome based on its type."""
    outcome_type = outcome["type"]

    if outcome_type == "item":
        source = outcome["source"]
        items = load_json(source)
        valid_items = [i for i in items if i.get("drop_rate", 0) > 0]
        if not valid_items:
            return "No items available!"
        count = random.randint(outcome["count"]["min"], outcome["count"]["max"])
        selected_items = random.choices(
            valid_items,
            weights=[i["drop_rate"] for i in valid_items],
            k=min(count, len(valid_items))
        )
        item_names = [i["name"] for i in selected_items]
        player.inventory.extend(item_names)
        return f"Found: {', '.join(item_names)}"

    elif outcome_type == "gold":
        amount = random.randint(outcome["amount"]["min"], outcome["amount"]["max"])
        player.gold += amount
        return f"Gained {amount} gold"

    elif outcome_type == "merchant":
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
            base_price = int(item.get(price_field, 10))  # Default to 10 if missing
        except (ValueError, TypeError):
            base_price = 10
        price = int(base_price * random.choice(outcome["price_modifiers"]))
        if not outcome.get("requires_choice", False):
            return f"Merchant offers {name} for {price} gold (logic error: choice required)"
        choice = input("Selection: ")
        if choice == "1" and player.gold >= price:
            player.gold -= price
            player.inventory.append(name)
            return f"Purchased {name} for {price} gold"
        elif choice == "1":
            return "Not enough gold!"
        return "You pass by the merchant"

    elif outcome_type == "quest":
        quests = load_json(outcome["source"])["quests"]  # Access "quests" list
        active_quests = player.active_quests  # Use player.active_quests directly
        completed_quests = player.completed_quests if hasattr(player, "completed_quests") else []  # Fallback
        if len(active_quests) >= outcome["conditions"]["max_active_quests"]:
            return "Too many active quests!"
        available_quests = [
            q for q in quests
            if q["quest_name"] not in [aq["quest_name"] for aq in active_quests]
            and q["quest_name"] not in completed_quests
            and player.level >= q["quest_level"]
        ]
        if not available_quests:
            return "No suitable quests available."
        quest = random.choice(available_quests)
        if not outcome.get("requires_choice", False):
            return f"Quest {quest['quest_name']} offered (logic error: choice required)"
        choice = input("Selection: ")
        if choice == "1":
            active_quests.append({"quest_name": quest["quest_name"], "kill_count": 0})
            player.active_quests = active_quests  # Update player object
            return f"Accepted quest: {quest['quest_name']}"
        return "You decline the quest"

    elif outcome_type == "extend_encounters":
        max_encounters = min(max_encounters + outcome["amount"], outcome["max_limit"])
        return f"Encounters extended to {max_encounters}"

    elif outcome_type == "heal":
        heal = player.max_hp * random.uniform(outcome["amount"]["min"], outcome["amount"]["max"])
        player.hp = min(player.hp + heal, player.max_hp)
        return f"Healed for {round(heal, 1)} HP"

    elif outcome_type == "damage":
        damage = player.max_hp * random.uniform(outcome["amount"]["min"], outcome["amount"]["max"])
        player.hp -= damage
        return f"Took {round(damage, 1)} damage"

    return "Outcome not implemented!"

def random_event(player, encounter_count, max_encounters):
    """Trigger a random event from event.json."""
    print(f"\nDistance traveled: {encounter_count}/{max_encounters}")
    time.sleep(0.5)

    # Load events
    events = load_json("event.json")

    # Filter out events on cooldown
    available_events = [
        e for e in events if player.event_cooldowns.get(e["name"], 0) == 0
    ]
    if not available_events:
        for e in events:
            player.event_cooldowns[e["name"]] = 0
        available_events = events

    # Pick an event
    event = random.choices(
        available_events,
        weights=[e["spawn_chance"] for e in available_events],
        k=1
    )[0]

    # Set cooldown (customizable per event)
    cooldown_duration = event.get("cooldown", 1)  # Default to 1 if not specified
    player.event_cooldowns[event["name"]] = cooldown_duration

    # Decrement all cooldowns
    for opt in player.event_cooldowns:
        if player.event_cooldowns[opt] > 0:
            player.event_cooldowns[opt] -= 1

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