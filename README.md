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
   ```
2. **Install python 3.x**
3. **Install Requests package**
This game has an automatic update feature you would need to ensure both python and git are installed on your system.
For Windows 
```bash
python -m pip install requests
```
For Linux/macOS
```bash
pip install requests
```
This will allow the game to prompt you to update if a new commit is made.

4. **Launch the Game**
   ```bash
   python game.py
   ```
5. Begin Your Journey
select "New Game" for an intro lore and character creation, or "Load Game" to pick up where you left off. Make sure to full screen your terminal! 

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
16. skills.json: controls available skills
17. locations.txt: controls available locations 

Love Snowcaller? Fork it, tweak it, or add your own flair! Submit pull requests with new features, or expand the world by editing the JSON files—no coding needed for new monsters, skills, items, gear, quests, or lore.

## Creating Things

1. Adding a New Event
File: event.json
Steps:
Open event.json.

Create events by defining a name, spawn_chance, cooldown, optional level_range, one_time/triggered, description, optional choice_prompt, and outcomes

Outcome Types
item: Drops 1+ items from a JSON file (e.g., "treasures.json").

gold: Gives a random gold amount (e.g., 10-20).

merchant: Offers an item for purchase from sources (e.g., "gear.json").

quest: Provides a quest from "quest.json" if under max limit.

extend_encounters: Adds encounters to the adventure (e.g., +1, max 10).

heal: Restores % of max HP (e.g., 10-20%).

damage: Deals % of max HP damage (e.g., 5-15%).

lore: Displays a text message (e.g., "The wind howls...").

combat: Starts a fight with monsters (e.g., 2 Bandits).

```json
    {
        "name": "bandit_ambush",
        "spawn_chance": 15,
        "cooldown": 3,
        "level_range": {"min": 3, "max": 999},
        "one_time": false,
        "triggered": false,
        "description": "Bandits leap from the shadows!",
        "outcomes": [
            {
                "type": "combat",
                "monster": "Bandit",
                "count": 2,
                "weight": 100
            }
        ]
    },
```

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
  {
    "name": "Gold Coin",
    "drop_rate": 0.1,
    "gold": 5,
    "boss_only": false
  },
```

Consumables (consumables.json):
```json
  {
    "name": "Minor Health Potion",
    "level_range": {"min": 1, "max": 10},
    "type": "HP",
    "value": 20,
    "stat": null,
    "duration": 0,
    "drop_rate": 0.05,
    "gold": 10,
    "boss_only": false
  },
```
Notes:
Use in events (e.g., "source": "gear.json") or quest rewards.

"drop_rate": Chance of dropping (used as weight in events).

5. Skills

Skills are of a given type and have many options.

Here are the type of effects you can use:
damage_bonus, direct_damage, heal, damage_over_time,

Here is how a skill looks 
```json
    {
      "class_type": "2",
      "level_req": 1,
      "name": "Fireball",
      "base_dmg": 5,
      "effect": "direct_damage",
      "mp_cost": 5,
      "duration": 0,
      "stat": "I"
    },
```
Class type 1 is warrior, 2 mage, 3 rogue.

**XP Give**

Inside of combat.py there is a line
```python
xp = level * 1 * (1.5 if monster_stats["rare"] or boss_fight else 1)
```
This will control the base XP and rate per level.

A value of 10 is 10 base and increased by 10 per level a level 3 will be 30 XP.

## Expanded Lore for Snowcaller

**The Shattering Frost**

In the annals of the old world, before the ice claimed all, the realm of Snowcaller was a tapestry of vibrant kingdoms, rolling fields, and towering forests. Magic pulsed through the land, wielded by sorcerers and guarded by hero's in the large empires. Goblins skulked in the shadows, a petty nuisance to the might of human empires. It was a world of balance—until the Shattering Frost descended.
No one knows its true origin. Some whisper of a betrayed god unleashing vengeance; others claim a cabal of reckless mages tore the veil between worlds, letting winter’s heart bleed through. Whatever the cause, the skies darkened, the sun grew pale, and a relentless blizzard swept across the land. Rivers froze solid, crops withered beneath snowdrifts, and entire cities vanished under glacial tombs. The never-ending winter gripped Snowcaller, transforming it into an icy hell where survival became a daily defiance of nature’s wrath.

**The Rise of the Beasts**

As humanity faltered, the creatures of the wild adapted and thrived. The Shattering Frost birthed a new breed of monsters—ice-wrought horrors that revel in the cold. Goblins, once mere scavengers, grew bolder and more numerous, their tribes uniting under cunning warlords who saw opportunity in mankind’s ruin. Dragons, long dormant, awoke from their mountain lairs, their scales gleaming with frost as they soared through blizzards, hunting weakened settlements. New abominations emerged from the ice: wraiths of frozen mist, hulking frost-trolls with hides like glaciers, and spectral wolves whose howls chill the soul itself.
Magic, too, twisted under the winter’s influence. Once a tool of creation, it now often manifests as jagged, uncontrollable power—spells that freeze blood in veins or summon shards of ice from thin air. Those who wield it risk madness or worse, their bodies slowly crystallizing as the cold claims them from within.

**Humanity on the Brink**

The survivors of Snowcaller cling to life in scattered enclaves, their once-proud civilizations reduced to crumbling ruins or buried relics. Towns like Brighthaven stand as rare beacons, fortified against the ice and the monsters that roam beyond their walls. Built atop geothermal springs or ancient magical wards, these settlements offer fleeting warmth in a frozen wasteland, drawing adventurers, outcasts, and desperate souls seeking to carve out a name—or merely to live another day.
Farther afield, villages like Eldwood teeter on the edge of extinction. Once prosperous, they now huddle around dying hearths, their fields barren beneath the frost. Raids by goblin warbands or the sudden wrath of a dragon can snuff out such places in a night, leaving only whispers carried on the wind.
Humanity’s numbers dwindle, pushed to the brink by starvation, cold, and ceaseless attacks. The old orders—knights, kings, and guilds—have fractured, replaced by ragtag bands of warriors, opportunistic warlords, and the enigmatic Guild, a loose alliance of heroes and mercenaries who answer calls for aid in exchange for coin, shelter, or secrets of the lost world.

**The Echoes of the Past**

Beneath the ice lie the bones of a grander age. Ruined citadels, frozen battlefields, and forgotten temples hold relics of power: enchanted blades, dragon-hoarded gold, and tomes of magic that might yet turn back the frost—or doom the world further. Legends speak of the Snowcaller, a mythic figure or force tied to the winter’s origin. Some say it’s a slumbering titan beneath the glaciers, others a cursed artifact buried in the deepest ice. Whatever it is, its name has become a rallying cry for those who dream of ending the eternal cold—and a curse for those who fear its awakening.

**The Struggle**
In Snowcaller, hope is a fragile thing, snuffed out as easily as a candle in a storm. The land is a merciless crucible where survival demands sacrifice, and heroism often ends in unmarked graves. Goblins gnaw at the edges of civilization, dragons rule the skies with indifferent cruelty, and the ice itself seems alive, creeping ever closer to swallow what remains. Yet amid the despair, sparks of defiance flicker—whether in the blade of a lone warrior facing a frost-troll or the muttered prayers of a village elder like Thane, clinging to the past.
What will you become in this frozen hell? A savior seeking to unravel the Shattering Frost’s mystery? A scavenger profiting from the chaos? Or just another corpse lost to the snow?


