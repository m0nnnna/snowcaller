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
   cd snowcallerpython
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
