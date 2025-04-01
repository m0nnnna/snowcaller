# Exchange Items Guide

This guide explains how to create and manage exchange items in the game's guild system.

## Overview

The exchange system allows players to:
1. Exchange key items for adventure points
2. Craft special items using multiple key items
3. View available exchange options and requirements

## Creating a New Exchange Item

### 1. Add the Item to keyitems.json

First, add your new item to `keyitems.json`:

```json
{
  "key_items": [
    {
      "name": "Your New Item",
      "description": "A description of your new item",
      "drop_from": "Monster Name",
      "drop_chance": 50,  // Percentage chance to drop (0-100)
      "quest": null,      // Set to null for non-quest items
      "npc_trigger": null // Set to null for non-quest items
    }
  ]
}
```

### 2. Add Exchange Rate to guild_exchange.json

Add your item to the adventure points exchange rates in `guild_exchange.json`:

```json
{
  "exchange_options": {
    "adventure_points": {
      "rates": [
        {
          "item": "Your New Item",
          "points": 3  // Number of adventure points per item
        }
      ]
    }
  }
}
```

### 3. Create a Crafted Item Recipe (Optional)

If you want to create a recipe that uses your item, add it to the crafted items section:

```json
{
  "exchange_options": {
    "crafted_items": {
      "recipes": [
        {
          "name": "Your Crafted Item",
          "description": "Description of the crafted item",
          "requirements": [
            {
              "item": "Your New Item",
              "quantity": 2
            },
            {
              "item": "Another Required Item",
              "quantity": 1
            }
          ],
          "result": {
            "type": "gear",  // or "consumable"
            "name": "Your Crafted Item",
            "quantity": 1
          }
        }
      ]
    }
  }
}
```

## Best Practices

1. **Drop Rates**:
   - Common items: 50-80% drop chance
   - Rare items: 20-40% drop chance
   - Very rare items: 5-15% drop chance

2. **Adventure Points**:
   - Common items: 1-2 points
   - Rare items: 3-5 points
   - Very rare items: 6-10 points

3. **Recipe Requirements**:
   - Keep requirements reasonable (2-4 items)
   - Mix common and rare items for balance
   - Ensure crafted items are worth the materials

## Example

Here's a complete example of adding a new exchange item:

```json
// In keyitems.json
{
  "key_items": [
    {
      "name": "Phoenix Feather",
      "description": "A feather from the legendary phoenix.",
      "drop_from": "Phoenix",
      "drop_chance": 30,
      "quest": null,
      "npc_trigger": null
    }
  ]
}

// In guild_exchange.json
{
  "exchange_options": {
    "adventure_points": {
      "rates": [
        {
          "item": "Phoenix Feather",
          "points": 5
        }
      ]
    },
    "crafted_items": {
      "recipes": [
        {
          "name": "Phoenix Wing Cape",
          "description": "A magnificent cape crafted from phoenix feathers",
          "requirements": [
            {
              "item": "Phoenix Feather",
              "quantity": 3
            },
            {
              "item": "Shadow Cloak",
              "quantity": 1
            }
          ],
          "result": {
            "type": "gear",
            "name": "Phoenix Wing Cape",
            "quantity": 1
          }
        }
      ]
    }
  }
}
```

## Testing Your Changes

1. Add the new item to `keyitems.json`
2. Add exchange rates to `guild_exchange.json`
3. Add any recipes to `guild_exchange.json`
4. Test the item in-game:
   - Verify it drops from the specified monster
   - Check the exchange rates in the guild menu
   - Test any crafting recipes
   - Ensure adventure points are awarded correctly 