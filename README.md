Snow Caller is a text based video game that plays entirely within terminal.

To run git clone the repo and then launch game.py.

See below the custom math and random chances.

Combat Mechanics

    Critical Hit Chance:
        Base Rate: 20% per point of Agility (A).
        Formula: Chance = 0.2 * A / 100.
        Effect: Doubles damage on a successful basic attack or Backstab.
        Example: A=5 → 1% chance to crit.
    Dodge Chance:
        Base Rate: 5% + 0.5% per defender’s Agility (A), capped at 20%.
        Bonus: If defender’s A > attacker’s A, +0.25% per difference, still capped at 20%.
        Formula: Base = min(5 + 0.5 * Defender_A, 20); Total = min(Base + (Defender_A - Attacker_A) * 0.25, 20) / 100.
        Example: Defender A=10, Attacker A=5 → min(5 + 5, 20) + (10 - 5) * 0.25 = 11.25%.
    Flee Chance:
        Base Rate: 50%.
        Modifier: ±5% per point of difference between player’s Luck (L) and monster’s L.
        Formula: Chance = 0.5 + (Player_L - Monster_L) * 0.05, capped between 10% and 90%.
        Example: Player L=3, Monster L=1 → 0.5 + (3 - 1) * 0.05 = 60%.
    Rogue - Backstab Hit Chance:
        Base Rate: 70%.
        Adjusted: Reduced by monster’s dodge chance.
        Formula: Hit_Chance = 0.7 - Monster_Dodge_Chance.
        Example: Monster Dodge=10% → 0.7 - 0.1 = 60%.
    Monster Critical Hit Chance:
        Base Rate: 20% per point of monster’s Agility (A).
        Formula: Chance = 0.2 * Monster_A / 100.
        Example: Monster A=5 → 1% chance to crit.

Damage Modifiers

    Warrior - Rage:
        Damage Increase: +4 to basic attack damage.
        Duration: 3 turns.
        Cost: 5 MP.
    Rogue - Backstab:
        Damage: Weapon damage + 2 * A.
        Cost: 5 MP.
        Example: Dagger (2-3), A=3 → 8-9 damage.
    Mage - Fireball:
        Base Damage: 15.
        I Modifier: +0.5% per Intelligence (I) point.
        Formula: Damage = 15 * (1 + 0.005 * I).
        Cost: 10 MP.
        Example: I=3 → 15 * 1.015 = 15.225.
    Mage - Basic Attack (Staff):
        I Modifier: +0.8% per I point to weapon base damage.
        Formula: Min_Dmg * (1 + 0.008 * I), Max_Dmg * (1 + 0.008 * I) + stat bonus.
        Example: Staff (1-2), I=3 → 1.024-2.048 + 1.5 = 2.524-3.548.

Treasure Chests (End of Adventure)

    Chest Type Probabilities:
        Unlocked: 70% (1-2 treasures, 5-15 gold).
        Locked (Physical): 20% (2-3 treasures, 15-30 gold, requires Lockpick).
        Magically Locked: 10% (3-4 treasures, 30-50 gold, requires Magical Removal Scroll).

Adventure Rewards

    Rare Drop Chance (Non-Boss):
        Base Rate: 10% per encounter defeated (e.g., 5 encounters = 40%).
        Effect: Grants a rare gear item if successful.
    Boss/Rare Monster Drop Boost:
        Base Drop Chance Increase: +5% (boss), +8% (rare boss).
        Formula: Boosted_Chance = min(Base_Chance + Boost, 1.0).
    Gold Drop Chance:
        Base Rate: Defined in monsters.txt (G:X%), e.g., G:50%.
        Amount: Triangular distribution from 0 to 2 * Monster_Level.

Stat Effects

    Strength (S): +2 HP per point, +0.5 damage per point for Swords.
    Agility (A): +0.2% crit chance per point, +0.5 damage per point for Daggers, +2 damage per point for Backstab.
    Intelligence (I): +0.5 damage per point for Staffs, +0.8% basic attack damage per point (Mage), +0.5% Fireball damage per point.
    Will (W): +2 MP per point (Warrior/Rogue), +3 MP per point (Mage).
    Luck (L): +5% flee chance per point.

Shop Items

    Lockpick: 25 gold, unlocks physical locked chests.
    Magical Removal Scroll: 45 gold, unlocks magically locked chests.
