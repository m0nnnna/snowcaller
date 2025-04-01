# Quest System Guide

This guide explains how to create and manage quests in the game.

## Overview

Quests are managed through two main files:
- `quest.json`: Contains quest definitions and requirements
- `lore.json`: Contains additional story and background information for quests

## Creating a New Quest

### 1. Add the Quest to quest.json

Add your new quest to `quest.json`:

```json
{
  "quests": [
    {
      "quest_name": "Your Quest Name",
      "quest_level": 5,  // Minimum level required
      "quest_description": "Description of what the player needs to do",
      "quest_reward": "50 gold",  // Can include items: "50 gold Item Name"
      "source": "guild",  // or "npc"
      "adventure_points": 5,  // Points awarded for completion
      "required_rank": 0,  // Minimum guild rank required
      "location": {
        "main": "Location Name",
        "sub": "Sub-Location Name"
      },
      "stages": [
        {
          "type": "kill",  // or "collect" or "dialogue"
          "target_monster": "Monster Name",  // for kill type
          "kill_count_required": 5
        },
        {
          "type": "collect",
          "target_item": "Item Name",
          "item_count_required": 1
        },
        {
          "type": "dialogue",
          "target_npc": "NPC Name",
          "stage": "quest_start"
        }
      ],
      "next_quest": "Next Quest Name",  // or null for final quest
      "npc_trigger": "NPC Name"  // NPC that gives the quest
    }
  ]
}
```

### 2. Add Lore (Optional)

Add quest lore to `lore.json`:

```json
{
  "lore": [
    {
      "quest_name": "Your Quest Name",
      "lore_text": "Detailed story and background information about the quest..."
    }
  ]
}
```

## Quest Types

### 1. Kill Quests
```json
{
  "type": "kill",
  "target_monster": "Monster Name",
  "kill_count_required": 5
}
```

### 2. Collection Quests
```json
{
  "type": "collect",
  "target_item": "Item Name",
  "item_count_required": 1
}
```

### 3. Dialogue Quests
```json
{
  "type": "dialogue",
  "target_npc": "NPC Name",
  "stage": "quest_start"
}
```

## Best Practices

1. **Quest Progression**:
   - Start with simple kill/collect quests
   - Gradually introduce more complex quest types
   - Chain quests logically with `next_quest`

2. **Rewards**:
   - Match rewards to quest difficulty
   - Include both gold and adventure points
   - Consider adding unique items for special quests

3. **Requirements**:
   - Set appropriate level requirements
   - Consider guild rank requirements
   - Balance kill/collect counts

## Example

Here's a complete example of a quest chain:

```json
// In quest.json
{
  "quests": [
    {
      "quest_name": "Goblin Cleanup",
      "quest_level": 3,
      "quest_description": "Clear out the goblins from the village of Eldwood.",
      "quest_reward": "30 gold",
      "source": "guild",
      "adventure_points": 5,
      "required_rank": 0,
      "location": {
        "main": "Village",
        "sub": "Eldwood"
      },
      "stages": [
        {
          "type": "kill",
          "target_monster": "Goblin",
          "kill_count_required": 5
        }
      ],
      "next_quest": "Kobold Trouble",
      "npc_trigger": "Guild Master"
    },
    {
      "quest_name": "Kobold Trouble",
      "quest_level": 3,
      "quest_description": "Head to the caves of Blackrock and kill all the kobolds.",
      "quest_reward": "30 gold",
      "source": "guild",
      "adventure_points": 5,
      "required_rank": 0,
      "location": {
        "main": "Blackrock",
        "sub": "Caves"
      },
      "stages": [
        {
          "type": "kill",
          "target_monster": "Kobold",
          "kill_count_required": 5
        }
      ],
      "next_quest": "Orc Invasion",
      "npc_trigger": "Guild Master"
    }
  ]
}

// In lore.json
{
  "lore": [
    {
      "quest_name": "Goblin Cleanup",
      "lore_text": "The peaceful village of Eldwood has been overrun by goblins. The villagers are too weak to defend themselves and need your help to drive out the invaders. The goblins have been stealing food and causing chaos in the village."
    },
    {
      "quest_name": "Kobold Trouble",
      "lore_text": "With the goblins dealt with, a new threat has emerged. Kobolds have been spotted in the Blackrock Caves, and they seem to be gathering strength. The Guild Master believes they might be planning something bigger."
    }
  ]
}
```

## Testing Your Quests

1. Add the quest to `quest.json`
2. Add any lore to `lore.json`
3. Test the quest in-game:
   - Verify level and rank requirements
   - Check quest progression
   - Test all quest stages
   - Verify rewards are given correctly
   - Ensure next quest is properly triggered 