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

## Running the Game

The easiest way to play Snowcaller is through the [Frosted Launcher](https://github.com/m0nnnna/Frosted_Launcher). The launcher will automatically:
- Download and set up the latest version of Snowcaller
- Handle all dependencies
- Provide a simple way to launch the game

### Running from Source

If you prefer to run from source:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/m0nnnna/snowcaller.git
   cd snowcaller-main
   ```
2. **Install python 3.x**
3. **Install Requests package**
   ```bash
   # For Windows
   python -m pip install requests
   
   # For Linux/macOS
   pip install requests
   ```
4. **Launch the Game**
   ```bash
   python game.py
   ```

**Controls**
- Main Menu: Use 1-8 for:
  1. Adventure
  2. Inventory
  3. Stats
  4. Shop
  5. Tavern
  6. Guild
  7. Save
  8. Quit

- Combat
  1. Attack
  2. Item
  3. Skills
  4. Flee

**Files**
1. game.py: the main game loop and link to all other files 
2. combat.py: controls the combat and encounters 
3. player.py: controls all information about the player.
4. items.py: controls how items get used
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

### Adding a New Event
File: event.json
Steps:
1. Open event.json
2. Create events by defining:
   - name
   - spawn_chance
   - cooldown
   - optional level_range
   - one_time/triggered
   - description
   - optional choice_prompt
   - outcomes

Outcome Types:
- item: Drops 1+ items from a JSON file (e.g., "treasures.json")
- gold: Gives a random gold amount (e.g., 10-20)
- merchant: Offers an item for purchase from sources (e.g., "gear.json")
- quest: Provides a quest from "quest.json" if under max limit
- extend_encounters: Adds encounters to the adventure (e.g., +1, max 10)
- heal: Restores % of max HP (e.g., 10-20%)
- damage: Deals % of max HP damage (e.g., 5-15%)
- lore: Displays a text message (e.g., "The wind howls...")
- combat: Starts a fight with monsters (e.g., 2 Bandits)

### Creating New Items

Items in Snowcaller are managed through several JSON files depending on their type:

1. **Gear Items** (gear.json):
```json
{
  "name": "Item Name",
  "slot": "head/chest/pants/boots/gloves/main_hand/off_hand/neck/ring",
  "stats": {
    "S": 0,  // Strength
    "A": 0,  // Agility
    "I": 0,  // Intelligence
    "W": 0,  // Willpower
    "L": 0   // Luck
  },
  "modifier": "S/A/I/W/L",  // Stat that scales the item
  "armor_value": 0,  // For armor pieces
  "damage": 0,  // For weapons
  "gold": 0  // Base gold value
}
```

2. **Consumable Items** (consumables.json):
```json
{
  "name": "Item Name",
  "type": "HP/MP/Buff/Offense",
  "value": 0,  // Amount of effect
  "duration": 0,  // Duration in turns (0 for instant)
  "stat": "S/A/I/W/L",  // For buffs
  "gold": 0  // Base gold value
}
```

3. **Treasure Items** (treasures.json):
```json
{
  "name": "Item Name",
  "gold": 0,  // Base gold value
  "description": "Item description"
}
```

Key Points:
- All items must have a unique name
- Gear items must specify a valid slot
- Consumables must have a valid type
- All items should have a gold value
- Stats and modifiers should be balanced with the game's progression
- Armor values and damage should scale appropriately with item level

Remember to:
1. Keep item names consistent across all files
2. Balance stats and values with existing items
3. Test new items in-game to ensure they work as intended
4. Update shop.json if you want the item to be purchasable

## Expanded Lore for Snowcaller

**The Shattering Frost**

In the annals of the old world, before the ice claimed all, the realm of Snowcaller was a tapestry of vibrant kingdoms, rolling fields, and towering forests. Magic pulsed through the land, wielded by sorcerers and guarded by hero's in the large empires. Goblins skulked in the shadows, a petty nuisance to the might of human empires. It was a world of balance—until the Shattering Frost descended.
No one knows its true origin. Some whisper of a betrayed god unleashing vengeance; others claim a cabal of reckless mages tore the veil between worlds, letting winter's heart bleed through. Whatever the cause, the skies darkened, the sun grew pale, and a relentless blizzard swept across the land. Rivers froze solid, crops withered beneath snowdrifts, and entire cities vanished under glacial tombs. The never-ending winter gripped Snowcaller, transforming it into an icy hell where survival became a daily defiance of nature's wrath.

**The Rise of the Beasts**

As humanity faltered, the creatures of the wild adapted and thrived. The Shattering Frost birthed a new breed of monsters—ice-wrought horrors that revel in the cold. Goblins, once mere scavengers, grew bolder and more numerous, their tribes uniting under cunning warlords who saw opportunity in mankind's ruin. Dragons, long dormant, awoke from their mountain lairs, their scales gleaming with frost as they soared through blizzards, hunting weakened settlements. New abominations emerged from the ice: wraiths of frozen mist, hulking frost-trolls with hides like glaciers, and spectral wolves whose howls chill the soul itself.
Magic, too, twisted under the winter's influence. Once a tool of creation, it now often manifests as jagged, uncontrollable power—spells that freeze blood in veins or summon shards of ice from thin air. Those who wield it risk madness or worse, their bodies slowly crystallizing as the cold claims them from within.

**Humanity on the Brink**

The survivors of Snowcaller cling to life in scattered enclaves, their once-proud civilizations reduced to crumbling ruins or buried relics. Towns like Brighthaven stand as rare beacons, fortified against the ice and the monsters that roam beyond their walls. Built atop geothermal springs or ancient magical wards, these settlements offer fleeting warmth in a frozen wasteland, drawing adventurers, outcasts, and desperate souls seeking to carve out a name—or merely to live another day.
Farther afield, villages like Eldwood teeter on the edge of extinction. Once prosperous, they now huddle around dying hearths, their fields barren beneath the frost. Raids by goblin warbands or the sudden wrath of a dragon can snuff out such places in a night, leaving only whispers carried on the wind.
Humanity's numbers dwindle, pushed to the brink by starvation, cold, and ceaseless attacks. The old orders—knights, kings, and guilds—have fractured, replaced by ragtag bands of warriors, opportunistic warlords, and the enigmatic Guild, a loose alliance of heroes and mercenaries who answer calls for aid in exchange for coin, shelter, or secrets of the lost world.

**The Echoes of the Past**

Beneath the ice lie the bones of a grander age. Ruined citadels, frozen battlefields, and forgotten temples hold relics of power: enchanted blades, dragon-hoarded gold, and tomes of magic that might yet turn back the frost—or doom the world further. Legends speak of the Snowcaller, a mythic figure or force tied to the winter's origin. Some say it's a slumbering titan beneath the glaciers, others a cursed artifact buried in the deepest ice. Whatever it is, its name has become a rallying cry for those who dream of ending the eternal cold—and a curse for those who fear its awakening.

**The Struggle**
In Snowcaller, hope is a fragile thing, snuffed out as easily as a candle in a storm. The land is a merciless crucible where survival demands sacrifice, and heroism often ends in unmarked graves. Goblins gnaw at the edges of civilization, dragons rule the skies with indifferent cruelty, and the ice itself seems alive, creeping ever closer to swallow what remains. Yet amid the despair, sparks of defiance flicker—whether in the blade of a lone warrior facing a frost-troll or the muttered prayers of a village elder like Thane, clinging to the past.
What will you become in this frozen hell? A savior seeking to unravel the Shattering Frost's mystery? A scavenger profiting from the chaos? Or just another corpse lost to the snow?


