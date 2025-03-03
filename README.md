Snowcaller
Snowcaller is a text-based RPG built in Python, immersing players in a frozen world of adventure, danger, and lore. Step into the boots of a hero in a realm shaped by ancient wars, where the Guild offers quests to slay monsters, uncover treasures, and forge your legend.
Features
Dynamic Combat: Engage in turn-based battles with a variety of monsters, using weapons, skills, and items. Dodge, crit, and strategize to survive!

Quest System: Accept up to 5 quests from the Adventurers' Guild, track progress, and turn them in for rewards. Complete quests to unlock new challenges.

Rich Lore: Dive into the world with an intro story and optional quest lore, stored in JSON for easy expansion.

Character Progression: Choose from Warrior, Mage, or Rogue classes, level up, and allocate stats to customize your playstyle.

Exploration: Venture into randomized locations (e.g., Forest Cave, Mountain Village) with variable encounters and rare boss fights.

JSON-Driven Data: Monsters, gear, quests, and lore are managed via JSON files for modularity and ease of editing.

Getting Started
Clone the Repository:

$git clone https://github.com/m0nnnna/snowcaller.git
$cd snowcaller

$# Snowcaller

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
   cd snowcallerpython game.py
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
game.py
combat.py
player.py
items.py
shop.py
tavern.py
events.py
utils.py
gear.json
consumables.json
monsters.json
lore.json
quest.json
treasures.json
shop.txt
skills.txt
locations.txt
