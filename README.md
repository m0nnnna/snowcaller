# Snowcaller

**Snowcaller** is a text-based RPG crafted in Python, set in a frozen realm of epic quests and ancient mysteries. Become a hero guided by the Guild, battling monsters, collecting loot, and unraveling the lore of a world shaped by ice and fire.

---

## ✨ Features

- **Dynamic Combat**: Face off in turn-based battles with diverse foes. Use weapons, skills, and items—dodge attacks, land critical hits, and outwit your enemies!
- **Quest System**: Take on up to 5 quests at a time from the Adventurers' Guild. Track your progress and return to claim rewards, unlocking new adventures as you go.
- **Rich Lore**: Immerse yourself with an opening tale and optional quest-specific lore, all stored in JSON for easy expansion.
- **Character Growth**: Pick from Warrior, Mage, or Rogue classes, level up, and customize your stats to suit your playstyle.
- **Exploration**: Roam randomized locations like Forest Caves or Mountain Villages, encountering foes and rare bosses with every step.
- **JSON-Driven**: Monsters, gear, quests, and lore are managed in JSON files, making it simple to tweak or expand the game.

---

## 🚀 Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/m0nnnna/snowcaller.git
   cd snowcaller-main
2. **Launch the Game**"
   ```bash
   python game.py
3. **Install python 3.x**
4. Begin Your Journey
select "New Game" for an intro lore and character creation, or "Load Game" to pick up where you left off.

**Controls**
Main Menu: Use 1-8 for:
1. Adventure
2. Inventory
3. Stats
4. Shop
5. Tavern
6. Guild
7. Save
8. Quit
Combat
1. Attack
2. Item
3. Skills
4. Flee
Guild
1. Accept Quests
2. Turn them in
0. Go back

**Files**
1. game.py: the main game loop and link to all other files 
2. combat.py: controls the combat and encounters 
3. player.py: controls all information about the player.
4.items.py: controls how items get used
5. shop.py: allows the player to purchase and sell items
6. tavern.py: controls players getting buffs and healing
7. events.py: controls the random events that happen during adventures
8. utils.py: controls the basic parse features
9. gear.json: controls what gear is available to the player including starting items
10. consumables.json: controls what usable items do 
11. monsters.json: controls what mobs are available
12. lore.json: controls flavor text
13. quest.json: controls what quests are available
14. treasures.json: control random loot
15. shop.txt: allows the listing of items - Note due to the change to .json this might need work
16. skills.txt: controls available skills
17. locations.txt: controls available locations 

Love Snowcaller? Fork it, tweak it, or add your own flair! Submit pull requests with new features, or expand the world by editing the JSON files—no coding needed for new monsters, skills, items, gear, quests, or lore.

**Creating Things**

1. Adding a New Event
File: event.json
Steps:
Open event.json.

Add a new entry with name, spawn_chance, description, and outcomes.

Define outcomes (e.g., "item", "quest", "heal") with appropriate fields.

Example: "Hidden Cache" event giving gear or gold:
```json
{
    "name": "hidden_cache",
    "spawn_chance": 15,
    "description": "You stumble upon a concealed cache in the underbrush.",
    "outcomes": [
        {
            "type": "item",
            "source": "gear.json",
            "count": {"min": 1, "max": 1},
            "weight": 70
        },
        {
            "type": "gold",
            "amount": {"min": 15, "max": 25},
            "weight": 30
        }
    ]
}
```

Notes:
"spawn_chance": Adjusts likelihood (total weights don’t need to sum to 100).

"weight": Relative chance among outcomes if multiple are listed.

Add "choice_prompt" and "requires_choice": true for player decisions (e.g., "1. Open | 2. Leave").

2. Adding a New Quest

File: quest.json
Steps:
Open quest.json.

Add a new quest with required fields: quest_name, quest_level, quest_description, target_monster, kill_count_required, quest_reward.

Link it to a monster in monster.json.

Example: "Slay the Shadow Beast" quest:
```json
{
    "quest_name": "Slay the Shadow Beast",
    "quest_level": 10,
    "quest_description": "A dark creature terrorizes the woods. End its reign.",
    "target_monster": "Shadow Beast",
    "kill_count_required": 1,
    "quest_reward": "50 gold, Shadow Cloak"
}
```
Notes:
"target_monster": Must match a "name" in monster.json.

"quest_reward": Format as "X gold, Item Name".

Trigger via an event (e.g., "quest_giver") or guild menu.

3. Adding a New Monster

File: monster.json
Steps:
Open monster.json.

Add a new monster with fields: name, stats, level_range, damage_range, spawn_chance, gold_chance, armor_value, hp_range, rare.

Set spawn_chance to 0 for quest bosses.

Example: "Shadow Beast" (quest boss):
```json
{
    "name": "Shadow Beast",
    "stats": {"S": 6, "A": 4, "I": 3, "W": 4, "L": 2},
    "level_range": {"min": 12, "max": 15},
    "damage_range": {"min": 7, "max": 13},
    "spawn_chance": 0,
    "gold_chance": 80,
    "armor_value": 30,
    "hp_range": {"min": 35, "max": 50},
    "rare": true,
    "notes": "Quest boss for Slay the Shadow Beast."
}
```

Example: "Goblin Scout" (regular monster):
```json
{
    "name": "Goblin Scout",
    "stats": {"S": 2, "A": 3, "I": 1, "W": 1, "L": 2},
    "level_range": {"min": 1, "max": 5},
    "damage_range": {"min": 2, "max": 4},
    "spawn_chance": 20,
    "gold_chance": 50,
    "armor_value": 10,
    "hp_range": {"min": 10, "max": 15},
    "rare": false
}
```

Notes:
"spawn_chance": 0 = quest boss, full level_range.

"rare": true = boss (random if spawn_chance > 0).

Stats (S, A, I, W, L) affect combat behavior.

4. Adding New Gear, Treasures, or Consumables

Gear (gear.json):
```json
{
    "name": "Shadow Cloak",
    "slot": "chest",
    "stats": {"A": 2, "L": 1},
    "modifier": "A",
    "armor_value": 15,
    "damage": null,
    "level_range": {"min": 10, "max": 15},
    "drop_rate": 5,
    "boss_only": true
}
```

Treasures (treasures.json):
```json
{"name": "Silver Ring", "drop_rate": 40}
```

Consumables (consumables.json):
```json
{"name": "Mana Elixir", "level_range": {"min": 5, "max": 15}, "drop_rate": 15, "boss_only": false}
```
Notes:
Use in events (e.g., "source": "gear.json") or quest rewards.

"drop_rate": Chance of dropping (used as weight in events).
