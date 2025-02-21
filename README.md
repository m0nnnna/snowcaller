Overview
Title: [Snow Caller]
[Snow Caller] is a Python-based, text-driven role-playing game where players embark on adventures, battle monsters, and gather loot in a fantasy world. Choose from three classes—Warrior, Mage, or Rogue—and explore procedurally generated adventures with random encounters, events, and boss fights. Manage your inventory, upgrade gear, use skills, and visit the shop or tavern to prepare for the next challenge. The game features a persistent save system (stored in save.txt) and a modular design with items, skills, and mechanics defined in text files for easy customization.
How It Works

    Game Loop: From a central hub, players select options: Adventure, Inventory, Stats, Shop, Tavern, Save, or Quit.
    Adventures: Travel to random locations, facing 2-10 encounters (combat or events). Defeat enemies to earn XP, gold, and loot; survive to claim a treasure chest (if victorious).
    Combat: Turn-based battles with options to attack, use items, flee, or cast skills (unlocked at level 5+). Damage scales with stats and gear, with dodge/crit mechanics.
    Progression: Gain XP to level up, allocating stat points (Strength, Agility, Intelligence, Will, Luck) and unlocking class-specific skills from skills.txt.
    Economy: Gold from combat and events funds purchases at the shop (shop.txt) or tavern buffs. Sell gear and consumables for half their Gold value.
    Loot: Gear (gear.txt) and consumables (consumables.txt) drop from monsters, with rare items ([R]) exclusive to bosses.

Core Mechanics

    Classes: Warrior (Strength-focused), Mage (Intelligence-focused), Rogue (Agility-focused), each with unique starting gear and skills.
    Stats: S (Strength: HP/damage), A (Agility: dodge/crit), I (Intelligence: magic), W (Will: MP), L (Luck: flee/events).
    Skills: Defined in skills.txt, scale with stats (e.g., Rage boosts damage, Fireball deals direct damage).
    Items: Gear enhances stats; consumables restore HP/MP, buff stats, or harm enemies, with level-scaled effects.
    Events: Random encounters (treasure, traps, etc.) add variety, with cooldowns to prevent repetition.
    Persistence: Death deletes the save; manual saves preserve progress

Quick Reference Sheet for Players
Game Basics

    Start: Choose a name and class (1: Warrior, 2: Mage, 3: Rogue).
    Hub Options:
        1. Adventure: Fight monsters, find loot (2-10 encounters).
        2. Inventory: Equip gear or use items.
        3. Stats: View stats, allocate points (if available).
        4. Shop: Buy/sell items (level-gated).
        5. Tavern: Rest (HP/MP) or feast (stat buff).
        6. Save: Save progress.
        7. Quit: Exit game.
    Death: Save file (save.txt) is deleted; start anew.

Combat

    Options:
        1. Attack: Deals weapon damage (scaled by S/A/I).
        2. Item: Use consumables or equip gear.
        3. Flee: Escape chance based on Luck/Agility.
        4. Skill (Level 5+): Use class skills (MP cost).
    Mechanics:
        Dodge: Chance based on Agility (A * 0.02).
        Crit: Chance based on Agility (A * 0.02, 1.5x damage).
        Bosses: Appear after 8+ encounters (25% chance), tougher stats.

Stats Cheat Sheet

    S (Strength): +2 HP per point, boosts sword damage.
    A (Agility): Improves dodge/crit, dagger damage.
    I (Intelligence): Boosts staff damage, mage skill power.
    W (Will): +2 MP (3 for Mage), regen on equip.
    L (Luck): Improves flee chance, event outcomes.

Items

    Gear: Equipped in slots (e.g., head, main_hand), boosts stats.
        Example: Short Sword [L:1-10 main_hand S2A0I0W0L0 2-4 3% 25]
        Sell: Half Gold value (e.g., 25 → 12 gold).
    Consumables: HP/MP restore, stat buffs, or monster effects.
        Example: Minor Health Potion [L:1-10 HP 20 none 0 5% 10]
        Sell: Half Gold value (e.g., 10 → 5 gold).
        Scaling: Effect doubles per 10 levels (e.g., 20 HP → 40 HP at 11-20).

Skills

    Defined in skills.txt (e.g., [1 5 Rage 2 damage_bonus 5 3 S]).
    Unlocked at level milestones (e.g., 5).
    Effects: Damage bonus, direct damage, heal, etc., scaled by stat (S/A/I).

Tips

    Fleeing/Declining Boss: No chest rewards.
    Shop: Items level-gated (1-10, 11-20, etc.).
    Tavern: Rest (10g) or feast (5g, +2 stat).
    Loot: Rare items ([R]) from bosses only.
Shop Items

    Lockpick: 25 gold, unlocks physical locked chests.
    Magical Removal Scroll: 45 gold, unlocks magically locked chests.
