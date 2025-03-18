import random
import time
import json
import os
from utils import load_json
from player import save_game  # Import to save after room purchase

class Tavern:
    def __init__(self, player):
        self.player = player
        self.room_cost = 100
        self.standard_npcs = ["Barkeep"]
        if not hasattr(player, "tavern_npcs"):
            self.player.tavern_npcs = []
        # Load special NPCs from NPC folder
        self.npc_data = {}
        npc_folder = "NPC"
        if os.path.exists(npc_folder):
            for filename in os.listdir(npc_folder):
                if filename.endswith(".json"):
                    with open(os.path.join(npc_folder, filename), "r") as f:
                        npc = json.load(f)
        self.npc_spawn_data = load_json("npcs.json")
        
    def roll_tavern_npcs(self):  # New line: Define method to roll NPCs from npc.json
        """Roll for NPCs from npc.json, preserving existing special NPCs not in npc.json."""
        player_level = self.player.level if hasattr(self.player, "level") else 1  # New line
        npc_json_names = {npc["name"] for npc in self.npc_spawn_data}  # New line: Names from npc.json

        # Remove only NPCs from npc.json, keep others (e.g., from NPC folder)
        self.player.tavern_npcs = [npc for npc in self.player.tavern_npcs if npc["name"] not in npc_json_names]  # New line

        # Roll for NPCs from npc.json
        for npc in self.npc_spawn_data:  # New line
            level_range = npc["level_range"]  # New line
            if level_range["min"] <= player_level <= level_range["max"]:  # New line
                if random.randint(1, 100) <= npc["spawn_chance"]:  # New line
                    # Check if this NPC is already in tavern_npcs (unlikely but possible)
                    if not any(n["name"] == npc["name"] for n in self.player.tavern_npcs):  # New line
                        self.player.tavern_npcs.append({  # New line
                            "name": npc["name"],  # New line
                            "quest": npc.get("quest"),  # New line
                            "bond": 0  # New line: Reset bond for npc.json NPCs
                        })  # New line

    def visit_tavern(self):
        while True:
            print("\nWelcome to the Tavern!")
            print(f"Gold: {self.player.gold}")
            print("1. Visit the Bar | 2. Rest | 3. Buy a Room | 4. Interact with Special NPC | 5. Leave")
            choice = input("Selection: ")

            if choice == "1":
                self.visit_bar()
            elif choice == "2":
                self.rest()
            elif choice == "3":
                self.buy_room()
            elif choice == "4":
                self.interact_special_npc()
            elif choice == "5":
                print("You leave the tavern.")
                break
            else:
                print("Invalid choice!")

    def visit_bar(self):
        print("\nYou approach the bar, buzzing with chatter.")
        available_npcs = self.standard_npcs + [npc["name"] for npc in self.player.tavern_npcs]
        
        if not available_npcs:
            print("No one is here to talk to!")
            return
        
        print("Who would you like to talk to?")
        for i, npc in enumerate(available_npcs[:9], 1):
            print(f"{i}. {npc}")
        print("0. Back")
        
        choice = input("Selection: ")
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            elif 1 <= choice_num <= len(available_npcs[:9]):
                npc = available_npcs[choice_num - 1]
                if npc in self.standard_npcs:
                    self.handle_standard_npc(npc)
                else:
                    self.handle_special_npc(npc)
            else:
                print(f"Invalid selection! Choose a number between 0 and {len(available_npcs[:9])}")
        except ValueError:
            print("Invalid input! Please enter a number between 0 and", len(available_npcs[:9]))

    def handle_standard_npc(self, npc):
        quests = load_json("quest.json")["quests"]
        dialogue = {
            "Barkeep": "Need a drink or a job?",
            "Old Storyteller": "Heard rumors of a beast beneath the ice...",
            "Drunk Mercenary": "Lost my blade to some wolves!"
        }
        print(f"{npc}: {dialogue.get(npc, 'Hey there!')}")
        if npc == "Old Storyteller" and "Beast Rumors" in [q["quest_name"] for q in quests]:
            self.offer_quest("Beast Rumors")
        elif npc == "Drunk Mercenary" and "Wolf Blade" in [q["quest_name"] for q in quests]:
            self.offer_quest("Wolf Blade")

    def offer_quest(self, quest_name):
        quest = next(q for q in load_json("quest.json")["quests"] if q["quest_name"] == quest_name)
        print(f"\nQuest: {quest['quest_name']} - {quest['quest_description']}")
        if input("Accept? (y/n): ").lower() == "y":
            self.player.active_quests.append({
                "quest_name": quest["quest_name"],
                "stages": [{"type": s["type"], "target_monster": s.get("target_monster"), "kill_count": 0} 
                           if s["type"] in ["kill", "boss"] else {"type": s["type"], "target_item": s["target_item"], "item_count": 0} 
                           for s in quest["stages"]]
            })
            print("Quest accepted!")

    def handle_special_npc(self, npc):
        npc_name = npc["name"]
        bond = npc.get("bond", 0)
        
        # Load NPC dialogue from NPC folder
        npc_file = os.path.join("NPC", f"{npc_name}.json")
        dialogue_options = []
        if os.path.exists(npc_file):
            with open(npc_file, 'r') as f:
                npc_data = json.load(f)
            dialogue_options = npc_data.get("dialogue", [])
        else:
            # Fallback: Try a known filename mapping
            name_to_file = {
                "Elara, the Fox": "elarathefox.json"
            }
            fallback_file = os.path.join("NPC", name_to_file.get(npc_name, f"{npc_name}.json"))
            if os.path.exists(fallback_file):
                with open(fallback_file, 'r') as f:
                    npc_data = json.load(f)
                dialogue_options = npc_data.get("dialogue", [])
            else:
                print(f"Warning: No dialogue file found for {npc_name} at {npc_file}")
                npc_data = {}  # Define npc_data to avoid UnboundLocalError

        # Determine quest stage
        current_quest = npc.get("quest")
        completed_quests = [q["quest_name"] for q in self.player.completed_quests]
        active_quests = [q["quest_name"] for q in self.player.active_quests]
        quest_section = next((d for d in dialogue_options if "quest" in d and d["quest"] == current_quest), None)
        stage = "quest_start"  # Default for new NPCs
        if quest_section:
            stages = quest_section["stages"]
            if current_quest in completed_quests:
                stage = "quest_complete"
            elif current_quest in active_quests:
                stage = "pending"
            elif npc.get("quest_accepted", False):
                stage = "quest_accepted"
            elif npc.get("quest_denied", False):
                stage = "quest_denied"
            dialogue = next((s for s in stages if s["stage"] == stage), None)
        else:
            dialogue = None

        # Check conditions
        room_condition = npc_data.get("room_condition", {})
        room_dialogue = next((d for d in dialogue_options if "room" in d), None)
        show_room_option = (room_dialogue and bond >= room_condition.get("bond_required", float('inf')) and 
                            room_condition.get("quest_completed") in completed_quests and not npc.get("room", False))
        invitation_dialogue = next((d for d in dialogue_options if "invitation" in d), None)
        show_invitation = (invitation_dialogue and hasattr(self.player, "room") and self.player.room and 
                           bond >= room_condition.get("bond_required", 8) and not npc.get("living_with_player", False))
        show_romance = npc.get("living_with_player", False)

        # Get dialogue
        if show_room_option:
            dialogue = room_dialogue["room"]
        elif show_invitation:
            dialogue = invitation_dialogue["invitation"]

        if not dialogue:
            print(f"{npc_name}: I have nothing to say right now.")
            return

        print(f"{npc_name}: {dialogue['text']}")

        # Menu options
        options = ["1. Ask about Quest", "2. Turn in Quest", "3. Talk"]
        if show_room_option:
            options = ["1. Discuss Room", "2. Talk"]
        elif show_invitation:
            options = ["1. Invite to Stay", "2. Talk"]
        elif show_romance:
            options = ["1. Ask about Quest", "2. Turn in Quest", "3. Talk", "4. Romance"]

        print(" | ".join(options))
        choice = input("Selection: ")

        if choice == "1":
            if show_room_option:
                replies = dialogue["replies"]
                for i, reply in enumerate(replies, 1):
                    print(f"{i}. {reply['text']}")
                reply_choice = int(input("Select reply: ")) - 1
                if 0 <= reply_choice < len(replies):
                    selected_reply = replies[reply_choice]
                    print(f"{npc_name}: {selected_reply['response']}")
                    npc["bond"] = bond + selected_reply["bond_change"]
                    if reply_choice == 0:  # Accept room
                        npc["room"] = True
                    print(f"Bond with {npc_name} is now {npc['bond']}")
            elif show_invitation:
                replies = dialogue["replies"]
                for i, reply in enumerate(replies, 1):
                    print(f"{i}. {reply['text']}")
                reply_choice = int(input("Select reply: ")) - 1
                if 0 <= reply_choice < len(replies):
                    selected_reply = replies[reply_choice]
                    print(f"{npc_name}: {selected_reply['response']}")
                    npc["bond"] = bond + selected_reply["bond_change"]
                    if reply_choice == 0:  # Accept invitation
                        npc["living_with_player"] = True
                    print(f"Bond with {npc_name} is now {npc['bond']}")
            elif current_quest and current_quest not in completed_quests and current_quest not in active_quests:
                if stage == "quest_start" and "replies" in dialogue:
                    while True:  # Loop until accept or deny
                        replies = dialogue["replies"]
                        flavor_options = dialogue.get("flavor", [])
                        npc["flavor_count"] = npc.get("flavor_count", 0)  # Track flavor progress
                        available_flavor = []
                        
                        # Check for next flavor option
                        if flavor_options and npc["flavor_count"] < len(flavor_options):
                            next_flavor = next((f for f in flavor_options if f["option"] == f"3-{npc['flavor_count'] + 1}"), None)
                            if next_flavor:
                                available_flavor.append(next_flavor)
                        
                        # Display options: 1. Accept, 2. Deny, 3. Flavor (if available)
                        for i, reply in enumerate(replies, 1):
                            print(f"{i}. {reply['text']}")
                        if available_flavor:
                            print(f"3. {available_flavor[0]['text']}")
                        
                        reply_choice = int(input("Select reply: ")) - 1
                        if reply_choice == 0:  # Accept quest
                            selected_reply = replies[0]
                            print(f"{npc_name}: {selected_reply['response']}")
                            npc["bond"] = bond + selected_reply["bond_change"]
                            quests = load_json("quest.json")["quests"]
                            quest_data = next((q for q in quests if q["quest_name"] == current_quest), None)
                            if quest_data:
                                new_quest = {"quest_name": current_quest, "stages": [{"type": s["type"], "target_monster": s.get("target_monster"), "kill_count_required": s.get("kill_count_required", 0), "kill_count": 0, "target_item": s.get("target_item"), "item_count_required": s.get("item_count_required", 0), "item_count": 0} for s in quest_data["stages"]]}
                                self.player.active_quests.append(new_quest)
                                npc["quest_accepted"] = True
                                dialogue = next((s for s in stages if s["stage"] == "quest_accepted"), None)
                                if dialogue:
                                    print(f"{npc_name}: {dialogue['text']}")
                                save_game(self.player)
                            break
                        elif reply_choice == 1:  # Deny quest
                            selected_reply = replies[1]
                            print(f"{npc_name}: {selected_reply['response']}")
                            npc["bond"] = bond + selected_reply["bond_change"]
                            npc["quest_denied"] = True
                            dialogue = next((s for s in stages if s["stage"] == "quest_denied"), None)
                            if dialogue:
                                print(f"{npc_name}: {dialogue['text']}")
                            save_game(self.player)
                            break
                        elif reply_choice == 2 and available_flavor:  # Flavor option
                            selected_flavor = available_flavor[0]
                            print(f"{npc_name}: {selected_flavor['response']}")
                            npc["bond"] = bond + selected_flavor["bond_change"]
                            npc["flavor_count"] = npc["flavor_count"] + 1
                            save_game(self.player)
                            if npc["flavor_count"] < len(flavor_options):
                                print("\nChoose again:")
                            else:
                                print("\nNo more questions to ask. Please decide:")
                        else:
                            print("Invalid choice, try again.")
                else:
                    print(f"{npc_name}: No new quests available right now.")
            else:
                print(f"{npc_name}: No new quests available right now.")
        elif choice == "2":
            if current_quest and current_quest in active_quests:
                self.turn_in_quest(current_quest)
                # Update completed_quests and re-evaluate stage
                completed_quests = [q["quest_name"] for q in self.player.completed_quests]
                if quest_section:  # Re-check stages after turn-in
                    stages = quest_section["stages"]
                    if current_quest in completed_quests:
                        stage = "quest_complete"
                    dialogue = next((s for s in stages if s["stage"] == stage), None)
                    if dialogue:
                        print(f"{npc_name}: {dialogue['text']}")
                # Handle next quest
                quests = load_json("quest.json")["quests"]
                quest_data = next((q for q in quests if q["quest_name"] == current_quest), None)
                if quest_data and quest_data.get("next_quest"):
                    npc["quest"] = quest_data["next_quest"]
                    npc["quest_accepted"] = False
                    npc["quest_denied"] = False
                save_game(self.player)
            else:
                print(f"{npc_name}: No active quest to turn in.")
                talk_section = next((d for d in dialogue_options if "talk" in d), None)
                if talk_section:
                    talk_options = talk_section["talk"]
                    available_options = []
                    for i in range(1, 10):
                        base_opt = str(i)
                        highest_replace = None
                        for opt in talk_options:
                            if opt["option"].startswith(base_opt):
                                bond_check = opt.get("bond_check", -1)
                                if bond >= bond_check and (highest_replace is None or bond_check > highest_replace.get("bond_check", -1)):
                                    highest_replace = opt
                        if highest_replace:
                            available_options.append(highest_replace)
                        elif any(opt["option"] == base_opt for opt in talk_options):
                            available_options.append(next(opt for opt in talk_options if opt["option"] == base_opt))
                    print("Talk Options (0 to back):")
                    for i, opt in enumerate(available_options, 1):
                        print(f"{i}. {opt['text']}")
                        for flavor in opt.get("flavor_text", []):
                            print(f"   - {flavor}")
                    print("0. Back")
                    reply_choice = int(input("Select option: ")) - 1
                    if 0 <= reply_choice < len(available_options):
                        selected_opt = available_options[reply_choice]
                        print(f"{npc_name}: {selected_opt['response']}")
                        npc["bond"] = bond + selected_opt["bond_change"]
                        print(f"Bond with {npc_name} is now {npc['bond']}")

        elif choice == "3":
            talk_section = next((d for d in dialogue_options if "talk" in d), None)
            if talk_section:
                talk_options = talk_section["talk"]
                available_options = []
                for i in range(1, 10):
                    base_opt = str(i)
                    highest_replace = None
                    for opt in talk_options:
                        if opt["option"].startswith(base_opt):
                            bond_check = opt.get("bond_check", -1)
                            if bond >= bond_check and (highest_replace is None or bond_check > highest_replace.get("bond_check", -1)):
                                highest_replace = opt
                    if highest_replace:
                        available_options.append(highest_replace)
                    elif any(opt["option"] == base_opt for opt in talk_options):
                        available_options.append(next(opt for opt in talk_options if opt["option"] == base_opt))
                print("Talk Options (0 to back):")
                for i, opt in enumerate(available_options, 1):
                    print(f"{i}. {opt['text']}")
                    for flavor in opt.get("flavor_text", []):
                        print(f"   - {flavor}")
                print("0. Back")
                reply_choice = int(input("Select option: ")) - 1
                if 0 <= reply_choice < len(available_options):
                    selected_opt = available_options[reply_choice]
                    print(f"{npc_name}: {selected_opt['response']}")
                    npc["bond"] = bond + selected_opt["bond_change"]
                    print(f"Bond with {npc_name} is now {npc['bond']}")

        elif choice == "4" and show_romance:
            romance_section = next((d for d in dialogue_options if "romance" in d), None)
            if romance_section:
                romance_options = romance_section["romance"]
                available_options = []
                for opt in romance_options:
                    base_opt = opt["option"].split("-")[0]
                    bond_check = opt.get("bond_check", -1)
                    if bond >= bond_check:
                        # Only add if no higher replacement exists
                        if not any(o["option"].startswith(base_opt + "-") and o.get("bond_check", -1) > bond_check and bond >= o.get("bond_check", -1) for o in romance_options):
                            available_options.append(opt)
                print("Romance Options (0 to back):")
                for i, opt in enumerate(available_options, 1):
                    print(f"{i}. {opt['text']}")
                    for flavor in opt.get("flavor_text", []):
                        print(f"   - {flavor}")
                print("0. Back")
                reply_choice = int(input("Select option: ")) - 1
                if 0 <= reply_choice < len(available_options):
                    selected_opt = available_options[reply_choice]
                    print(f"{npc_name}: {selected_opt['response']}")
                    npc["bond"] = bond + selected_opt["bond_change"]
                    print(f"Bond with {npc_name} is now {npc['bond']}")
            elif current_quest and current_quest not in completed_quests and current_quest not in active_quests:
                quests = load_json("quest.json")["quests"]
                quest_data = next((q for q in quests if q["quest_name"] == current_quest), None)
                if quest_data:
                    print(f"{npc_name}: {quest_data['quest_description']}")
                    accept = input("Accept quest? (y/n): ").lower()
                    if accept == "y":
                        new_quest = {"quest_name": current_quest, "stages": [{"type": s["type"], "target_monster": s.get("target_monster"), "kill_count_required": s.get("kill_count_required", 0), "kill_count": 0, "target_item": s.get("target_item"), "item_count_required": s.get("item_count_required", 0), "item_count": 0} for s in quest_data["stages"]]}
                        self.player.active_quests.append(new_quest)
                        npc["quest_accepted"] = True
                        dialogue = next((s for s in stages if s["stage"] == "quest_accepted"), None)
                        if dialogue:
                            print(f"{npc_name}: {dialogue['text']}")
                    else:
                        npc["quest_denied"] = True
                        dialogue = next((s for s in stages if s["stage"] == "quest_denied"), None)
                        if dialogue:
                            print(f"{npc_name}: {dialogue['text']}")
            else:
                print(f"{npc_name}: No new quests available right now.")

        elif choice == "2":
            if current_quest and current_quest in active_quests:
                self.turn_in_quest(current_quest)
                if quest_data.get("next_quest"):
                    npc["quest"] = quest_data["next_quest"]
                    npc["quest_accepted"] = False
                    npc["quest_denied"] = False
            else:
                # Handle "Talk" when room or invitation is active
                talk_section = next((d for d in dialogue_options if "talk" in d), None)
                if talk_section:
                    talk_options = talk_section["talk"]
                    available_options = []
                    for i in range(1, 10):
                        base_opt = str(i)
                        highest_replace = None
                        for opt in talk_options:
                            if opt["option"].startswith(base_opt):
                                bond_check = opt.get("bond_check", -1)
                                if bond >= bond_check and (highest_replace is None or bond_check > highest_replace.get("bond_check", -1)):
                                    highest_replace = opt
                        if highest_replace:
                            available_options.append(highest_replace)
                        elif any(opt["option"] == base_opt for opt in talk_options):
                            available_options.append(next(opt for opt in talk_options if opt["option"] == base_opt))
                    print("Talk Options (0 to back):")
                    for i, opt in enumerate(available_options, 1):
                        print(f"{i}. {opt['text']}")
                        for flavor in opt.get("flavor_text", []):
                            print(f"   - {flavor}")
                    print("0. Back")
                    reply_choice = int(input("Select option: ")) - 1
                    if 0 <= reply_choice < len(available_options):
                        selected_opt = available_options[reply_choice]
                        print(f"{npc_name}: {selected_opt['response']}")
                        npc["bond"] = bond + selected_opt["bond_change"]
                        print(f"Bond with {npc_name} is now {npc['bond']}")

        elif choice == "3":
            talk_section = next((d for d in dialogue_options if "talk" in d), None)
            if talk_section:
                talk_options = talk_section["talk"]
                available_options = []
                for i in range(1, 10):
                    base_opt = str(i)
                    highest_replace = None
                    for opt in talk_options:
                        if opt["option"].startswith(base_opt):
                            bond_check = opt.get("bond_check", -1)
                            if bond >= bond_check and (highest_replace is None or bond_check > highest_replace.get("bond_check", -1)):
                                highest_replace = opt
                    if highest_replace:
                        available_options.append(highest_replace)
                    elif any(opt["option"] == base_opt for opt in talk_options):
                        available_options.append(next(opt for opt in talk_options if opt["option"] == base_opt))
                print("Talk Options (0 to back):")
                for i, opt in enumerate(available_options, 1):
                    print(f"{i}. {opt['text']}")
                    for flavor in opt.get("flavor_text", []):
                        print(f"   - {flavor}")
                print("0. Back")
                reply_choice = int(input("Select option: ")) - 1
                if 0 <= reply_choice < len(available_options):
                    selected_opt = available_options[reply_choice]
                    print(f"{npc_name}: {selected_opt['response']}")
                    npc["bond"] = bond + selected_opt["bond_change"]
                    print(f"Bond with {npc_name} is now {npc['bond']}")

        elif choice == "4" and show_romance:
            romance_section = next((d for d in dialogue_options if "romance" in d), None)
            if romance_section:
                romance_options = romance_section["romance"]
                available_options = []
                for opt in romance_options:
                    base_opt = opt["option"].split("-")[0]
                    bond_check = opt.get("bond_check", -1)
                    if bond >= bond_check:
                        # Only add if no higher replacement exists
                        if not any(o["option"].startswith(base_opt + "-") and o.get("bond_check", -1) > bond_check and bond >= o.get("bond_check", -1) for o in romance_options):
                            available_options.append(opt)
                print("Romance Options (0 to back):")
                for i, opt in enumerate(available_options, 1):
                    print(f"{i}. {opt['text']}")
                    for flavor in opt.get("flavor_text", []):
                        print(f"   - {flavor}")
                print("0. Back")
                reply_choice = int(input("Select option: ")) - 1
                if 0 <= reply_choice < len(available_options):
                    selected_opt = available_options[reply_choice]
                    print(f"{npc_name}: {selected_opt['response']}")
                    npc["bond"] = bond + selected_opt["bond_change"]
                    print(f"Bond with {npc_name} is now {npc['bond']}")

    def offer_quest(self, quest_name):
        quests = load_json("quest.json")["quests"]
        quest = next((q for q in quests if q["quest_name"] == quest_name), None)
        if not quest:
            print(f"Quest '{quest_name}' not found in quest.json!")
            return
        if quest["quest_name"] in [q["quest_name"] for q in self.player.active_quests]:
            print("You already have this quest!")
            return
        if quest["quest_name"] in [q["quest_name"] if isinstance(q, dict) else q for q in self.player.completed_quests]:
            print("You’ve already completed this quest!")
            return
        print(f"\nQuest: {quest['quest_name']} - {quest['quest_description']}")
        if input("Accept? (y/n): ").lower() == "y":
            self.player.active_quests.append({
                "quest_name": quest["quest_name"],
                "stages": [
                   {
                        "type": s["type"],
                        "target_monster": s.get("target_monster"),
                        "kill_count": 0,
                        "kill_count_required": s.get("kill_count_required", 0)
                    } if s["type"] in ["kill", "boss"] else {
                        "type": s["type"],
                        "target_item": s["target_item"],
                        "item_count": 0,
                        "item_count_required": s.get("item_count_required", 0)
                    } for s in quest["stages"]
                ]
            })
            print("Quest accepted!")
            save_game(self.player)

    def turn_in_quest(self, quest_name):
        if not quest_name:
            print("No quest to turn in!")
            return
        quests = load_json("quest.json")["quests"]
        for quest in self.player.active_quests[:]:
            if quest["quest_name"] == quest_name:
                quest_data = next((q for q in quests if q["quest_name"] == quest_name), None)
                if not quest_data:
                    print(f"Quest '{quest_name}' not found in quest.json!")
                    return
                all_stages_complete = True
                for i, stage in enumerate(quest["stages"]):
                    if stage["type"] in ["kill", "boss"]:
                        if stage["kill_count"] < quest_data["stages"][i]["kill_count_required"]:
                            all_stages_complete = False
                            break
                    elif stage["type"] == "collect":
                        item_count = self.player.inventory.count(quest_data["stages"][i]["target_item"])
                        if "item_count" not in stage or stage["item_count"] < quest_data["stages"][i]["item_count_required"]:
                            stage["item_count"] = item_count
                            if item_count < quest_data["stages"][i]["item_count_required"]:
                                all_stages_complete = False
                                break
                if all_stages_complete:
                    reward = quest_data["quest_reward"].split(", ")
                    gold_amount = int(reward[0].split()[0])
                    self.player.gold += gold_amount
                    if len(reward) > 1:
                        self.player.inventory.append(reward[1])
                    print(f"Quest '{quest_name}' completed! Reward: {quest_data['quest_reward']}")
                    self.player.completed_quests.append({"quest_name": quest_name})  # Consistent dict format
                    self.player.active_quests.remove(quest)
                    save_game(self.player)  # Persist state
                    # Update NPC quest chain
                    for npc_name, npc in self.npc_data.items():
                        if npc.get("quest") == quest_name or npc.get("next_quest") == quest_name:
                            if quest_data.get("next_quest"):
                                npc["quest"] = None
                                npc["next_quest"] = quest_data["next_quest"]
                                print(f"{npc_name} has a new task for you: {npc['next_quest']}")
                            else:
                                npc["next_quest"] = None
                                print(f"{npc_name} has no further quests for now.")
                else:
                    print("Quest not yet complete!")
                    print("Progress:")
                    for i, stage in enumerate(quest["stages"]):
                        if stage["type"] in ["kill", "boss"]:
                            print(f" - {stage['target_monster']}: {stage['kill_count']}/{quest_data['stages'][i]['kill_count_required']}")
                        elif stage["type"] == "collect":
                            print(f" - {stage['target_item']}: {stage.get('item_count', 0)}/{quest_data['stages'][i]['item_count_required']}")
                break

    def talk_personally(self, npc_name, npc_data, replies):
        print(f"\n{npc_name} awaits your reply:")
        for i, reply in enumerate(replies, 1):
            print(f"{i}. {reply['text']}")
        choice = input("Selection: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(replies):
                reply = replies[idx]
                print(f"{npc_name}: {reply['response']}")
                npc_data["bond"] = npc_data.get("bond", 0) + reply["bond_change"]
                print(f"(Bond with {npc_name}: {npc_data['bond']})")
            else:
                print("Invalid choice!")
        except ValueError:
            print("Invalid input!")

    def invite_to_room(self, npc_data, room_condition):
        if "bond" not in npc_data:
            npc_data["bond"] = 0
        bond_met = npc_data["bond"] >= room_condition["bond_required"]
        quest_met = room_condition["quest_completed"] in [q["quest_name"] for q in self.player.completed_quests]
        
        if bond_met and quest_met and not npc_data["room"]:
            npc_data["room"] = True
            print(f"{npc_data['name']} agrees happily. 'I’d love to stay with you!'")
        elif npc_data["room"]:
            print(f"{npc_data['name']} is already living in your room!")
        elif not bond_met:
            print(f"{npc_data['name']} hesitates. 'I don’t feel close enough to you yet.'")
        elif not quest_met:
            print(f"{npc_data['name']} says, 'How nice it would be to stay the night with you once our work is done.'")

    def turn_in_quest(self, quest_name):
        if not quest_name:
            print("No quest to turn in!")
            return
        quests = load_json("quest.json")["quests"]
        for quest in self.player.active_quests[:]:
            if quest["quest_name"] == quest_name:
                quest_data = next((q for q in quests if q["quest_name"] == quest_name), None)
                if quest_data:
                    all_stages_complete = True
                    for i, stage in enumerate(quest["stages"]):
                        if stage["type"] in ["kill", "boss"]:
                            if stage["kill_count"] < quest_data["stages"][i]["kill_count_required"]:
                                all_stages_complete = False
                                break
                        elif stage["type"] == "collect":
                            item_count = self.player.inventory.count(quest_data["stages"][i]["target_item"])
                            stage["item_count"] = item_count
                            if item_count < quest_data["stages"][i]["item_count_required"]:
                                all_stages_complete = False
                                break
                    if all_stages_complete:
                        reward = quest_data["quest_reward"].split(", ")
                        gold_amount = int(reward[0].split()[0])
                        self.player.gold += gold_amount
                        if len(reward) > 1:
                            self.player.inventory.append(reward[1])
                        print(f"Quest '{quest_name}' completed! Reward: {quest_data['quest_reward']}")
                        self.player.completed_quests.append({"quest_name": quest_name})
                        self.player.active_quests.remove(quest)
                        # Update NPC quest chain
                        for npc_name, npc in self.npc_data.items():
                            if npc.get("quest") == quest_name and quest_data.get("next_quest"):
                                npc["quest"] = quest_data["next_quest"]
                                print(f"{npc_name} has a new task for you: {npc['quest']}")

    def rest(self):
        elara_in_room = any(npc["name"] == "Elara, the Lost Scholar" and npc["room"] for npc in self.player.tavern_npcs)
        if self.player.has_room:  # Use player.has_room
            if elara_in_room:
                print("You and Elara sleep together in your room, sharing stories of Snowcaller.")
                self.player.hp = self.player.max_hp * 1.1
                self.player.mp = self.player.max_mp * 1.1
                self.player.hp = min(self.player.hp, self.player.max_hp * 1.1)
                self.player.mp = min(self.player.mp, self.player.max_mp * 1.1)
            else:
                print("You rest in your own room for free.")
                self.player.hp = self.player.max_hp
                self.player.mp = self.player.max_mp
        else:
            print("Resting costs 5 gold.")
            if self.player.gold >= 5:
                if input("Pay to rest? (y/n): ").lower() == "y":
                    self.player.gold -= 5
                    self.player.hp = self.player.max_hp
                    self.player.mp = self.player.max_mp
                    print("You rest and recover.")
            else:
                print("Not enough gold!")

    def buy_room(self):
        if not self.player.has_room and self.player.gold >= self.room_cost:  # Use player.has_room
            self.player.gold -= self.room_cost
            self.player.has_room = True
            print(f"You’ve bought a permanent room for {self.room_cost} gold!")
            save_game(self.player)  # Save state after purchase
        elif self.player.has_room:
            print("You already own a room!")
        else:
            print(f"Not enough gold! A room costs {self.room_cost} gold.")

    def interact_special_npc(self):
        if not self.player.tavern_npcs:
            print("No special NPCs are here yet!")
            return
        
        special_npcs = self.player.tavern_npcs
        print("\nSpecial NPCs present:")
        for i, npc in enumerate(special_npcs[:9], 1):
            print(f"{i}. {npc['name']}")
        print("0. Back")
        
        choice = input("Selection: ")
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            elif 1 <= choice_num <= len(special_npcs[:9]):
                self.handle_special_npc(special_npcs[choice_num - 1])
            else:
                print(f"Invalid selection! Choose a number between 0 and {len(special_npcs[:9])}")
        except ValueError:
            print("Invalid input! Please enter a number between 0 and", len(special_npcs[:9]))

def tavern_menu(player):
    """Wrapper function to provide compatibility with game.py."""
    tavern = Tavern(player)
    tavern.visit_tavern()