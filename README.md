# Zagreus' Descent - A Dark Dungeon Crawler

A complex, story-driven text adventure game inspired by Fear and Hunger with deep mechanics and branching narratives.

## Story

You are Zagreus, betrayed and thrown into a flooded dungeon cell to drown. But you survived the water, the darkness, and the cold. Now you must navigate a massive, deadly dungeon filled with horrors, tough choices, and countless ways to die.

## Features

- **Massive Decision Tree**: 287+ unique story nodes with hundreds of unique paths and choices
- **AI Dungeon Master**: Custom actions evaluated intelligently based on full context
- **Enhanced Combat System**: 
  - Tactical targeting (eyes, head, legs, throat, etc.)
  - Status effects (bleeding, poisoned, burning, stunned, etc.)
  - Critical hits and counterattacks
  - Equipment bonuses and durability
  - Environmental factors and positioning
- **Deep Survival Mechanics**: 
  - Hunger, temperature, wounds, sanity, fear
  - Equipment degradation over time
  - Status effects that persist across encounters
  - Lighting affects combat and exploration
- **Advanced Body Damage System**: Can lose limbs, eyes, and other body parts with realistic consequences
- **Multiple Endings**: 100 different endings (10 good, 90 bad) based on your choices
- **Thousands of Deaths**: Die in ridiculous, brutal, and unexpected ways
- **Rich Environmental Storytelling**: Ancient symbols, hidden lore, and atmospheric details
- **NPC Interactions**: Guards, prisoners, and other characters with their own motivations
- **15-20 Minute Playtime**: First act takes place entirely in the dungeon
- **No UI Needed**: Pure console/terminal experience

## Requirements

- Python 3.6 or higher
- Works on Linux and Windows

## How to Play

### Quick Start

**Linux/Mac:**
```bash
./play.sh
```
or
```bash
python3 zagreus_dungeon.py
```

**Windows:**
```bash
play.bat
```
or
```bash
python zagreus_dungeon.py
```

## Gameplay

The game presents you with situations and choices. You can:
1. **Select numbered options** - Type the number and press Enter
2. **Use custom actions** - Choose "Custom action" and describe what you want to do
   - The AI Dungeon Master will evaluate your action based on:
     - Your stats (strength, agility, mind)
     - Your equipment (weapons, light source, armor, offhand)
     - Your condition (wounds, hunger, temperature, status effects)
     - Environmental factors (darkness, water, etc.)
     - The situation context

### Enhanced Combat System

Combat is challenging and deeply tactical:
- **Targeting matters**: Hitting weak points (eyes, throat, joints) is more effective
- **Status effects**: Bleeding, poison, burning, stunning enemies and yourself
- **Equipment matters**: Weapons, light sources, and armor significantly impact outcomes
- **Stats matter**: Strength, agility, and mind affect success rates and damage
- **Conditions matter**: Fighting in darkness, with injuries, or without limbs is much harder
- **Critical hits**: Chance-based critical strikes for devastating damage
- **Counterattacks**: Enemies can strike back if you're not careful
- **Death is permanent**: Each playthrough ends when you die or escape

### Survival Mechanics

Monitor your status carefully:
- **Health**: Damage from combat, falls, and environmental hazards
- **Stamina**: Energy for actions, recovers when resting
- **Hunger**: Increases over time (every 5 turns), find food or face starvation
- **Wetness**: Affects temperature and health, dries slowly over time
- **Temperature**: Too cold (hypothermia) or too hot causes ongoing damage
- **Sanity**: Witnessing horrors and making dark choices affects your mind
- **Fear**: High fear attracts the Harvester
- **Light**: Darkness hides details, options, and dangers
- **Status Effects**: Bleeding, poisoned, burning, infected, stunned, etc.
- **Equipment Durability**: Gear degrades and can break (every 8 turns)

### Death

Death is common and often brutal:
- Drowning in flooded cells
- Eaten by dungeon creatures (ghouls, etc.)
- Poisoning from bad food or traps
- Bleeding out from wounds
- Starvation when hunger reaches 100
- Hypothermia from cold and wet conditions
- Madness from low sanity
- The Harvester (a special horror)
- Infection from untreated wounds
- Combat wounds and accumulated damage
- And hundreds more ways...

## Tips

1. **Light is crucial** - Finding a torch or tinderbox early opens many paths and improves combat
2. **Not all food is safe** - Inspect before eating, poison kills quickly
3. **Combat is risky** - Sometimes running or talking is smarter than fighting
4. **Equipment matters** - A weapon, armor, and light can save your life
5. **Manage resources** - Don't waste healing items, food, or water
6. **Read carefully** - Details in descriptions often hint at dangers
7. **Experiment** - Custom actions can find creative solutions
8. **Death teaches** - Each death reveals something about the dungeon
9. **Status effects matter** - Treat bleeding and infection quickly
10. **Equipment degrades** - Don't rely on gear lasting forever

## Game Structure

The decision tree works as follows:
- **Branching paths**: Choices lead to different scenarios
- **Converging paths**: Different routes can merge back together
- **State persistence**: Items, wounds, and status effects persist across nodes
- **Item dependency**: Some choices only available with specific items
- **Multiple endpoints**: Many ways to die, several ways to escape
- **Dynamic combat**: AI evaluates custom combat actions contextually
- **Environmental effects**: Light, temperature, and location affect outcomes

## New Features

### Status Effects System
- Bleeding: Causes damage over time
- Poisoned: Damages health and stamina
- Burning: Intense damage over time
- Infected: Reduces max health over time
- Stunned: Cannot act effectively
- And more...

### Equipment System
- **Weapon slot**: Increases damage and unlocks combat options
- **Armor slot**: Reduces damage taken
- **Light slot**: Reveals details, improves accuracy
- **Accessory slot**: Special effects
- **Offhand slot**: Shield or secondary weapon
- **Durability**: All equipment degrades with use

### Enhanced AI
- Evaluates stealth attempts based on wetness, armor, light
- Swimming checks consider armor weight and limb status
- Climbing considers wetness, stamina, and equipment
- Persuasion affected by sanity level
- Puzzle-solving requires light and sanity
- Trap detection uses agility and tools

## Warnings

⚠️ This game contains:
- Dark themes and horror elements
- Graphic descriptions of violence and death
- Difficult moral choices
- High difficulty and frequent death
- Psychological horror

Not recommended for players sensitive to dark content.

## Development

Created as a complex narrative game with:
- Dynamic AI-driven responses with deep context awareness
- Extensive branching story structure (287+ nodes)
- Sophisticated state management with status effects
- Realistic consequence system with equipment degradation
- Rich environmental storytelling

The game is designed to be replayed, with each playthrough revealing new paths and secrets.

---

**Can you escape the dungeon? Or will you become another forgotten corpse in the darkness?**
