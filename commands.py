import os
import json
from events import random_event, trigger_specific_event

def handle_command(input_str, player, commands_enabled):
    """
    Process command input. Returns True if a command was handled, False otherwise.
    """
    if not input_str or player is None:
        if commands_enabled and input_str:
            print("No player loaded. Please start or load a game first.")
        return False

    parts = input_str.split()
    command = parts[0].lower() if parts else ""

    try:
        if command == "set.hp" and len(parts) == 2:
            value = float(parts[1])
            player.hp = min(value, player.max_hp)
            if commands_enabled:
                print(f"HP set to {player.hp}/{player.max_hp}")
            return True

        elif command == "set.mp" and len(parts) == 2:
            value = float(parts[1])
            player.mp = min(value, player.max_mp)
            if commands_enabled:
                print(f"MP set to {player.mp}/{player.max_mp}")
            return True

        elif command == "set.gold" and len(parts) == 2:
            value = int(parts[1])
            player.gold = max(0, value)
            if commands_enabled:
                print(f"Gold set to {player.gold}")
            return True

        elif command == "set.rank" and len(parts) == 2:
            try:
                rank = int(parts[1])
                if 1 <= rank <= 6:
                    player.adventurer_rank = rank
                    rank_names = ["Silver", "Gold", "Crystal", "Sapphire", "Ruby", "Emerald"]
                    if commands_enabled:
                        print(f"Adventurer rank set to {rank_names[rank-1]} (Rank {rank})")
                    return True
                else:
                    if commands_enabled:
                        print("Rank must be between 1 and 6")
                    return False
            except ValueError:
                if commands_enabled:
                    print("Please enter a valid number between 1 and 6")
                return False

        elif command == "level.up" and len(parts) == 1:
            level_up(player, commands_enabled)
            return True

        elif command == "start.event" and len(parts) == 2:
            event_name = parts[1].lower()
            start_event(player, event_name, commands_enabled)
            return True

    except (ValueError, AttributeError) as e:
        if commands_enabled:
            print(f"Command error: {e}")
        return False

    return False

def level_up(player, commands_enabled):
    """Trigger a full level-up process via Player class."""
    player.trigger_level_up()  # Call Player method
    from player import save_game
    save_game(player)  # Save the updated state
    if commands_enabled:
        print(f"{player.name} leveled up to {player.level}! HP: {player.hp}/{player.max_hp}, MP: {player.mp}/{player.max_mp}")

def start_event(player, event_name, commands_enabled):
    """
    Trigger a specific event by name.
    """
    events = load_json("event.json", commands_enabled)
    event = next((e for e in events if e["name"].lower() == event_name), None)
    
    if event:
        encounter_count = 1
        max_encounters = 6
        print(f"\nTriggering event: {event['name']}")
        trigger_specific_event(player, event, encounter_count, max_encounters)
        from player import save_game
        save_game(player)
        if commands_enabled:
            print(f"Event '{event_name}' triggered successfully.")
    else:
        print(f"Event '{event_name}' not found in event.json! Available events: {[e['name'] for e in events]}")

def load_json(filename, commands_enabled):
    """Utility to load JSON files relative to script directory."""
    from utils import get_resource_path  # Import consistent path resolver
    file_path = get_resource_path(filename)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if commands_enabled:
                print(f"Loaded {filename} from {file_path}")
            return data
    except Exception as e:
        print(f"Error loading {filename} at {file_path}: {e}")  # Always print errors for debugging
        return []