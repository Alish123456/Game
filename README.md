# Zagreus' Descent - A Dark Dungeon Crawler

A complex, story-driven text adventure game inspired by Fear and Hunger.

## Story

You are Zagreus, betrayed and thrown into a flooded dungeon cell to drown. But you survived the water, the darkness, and the cold. Now you must navigate a massive, deadly dungeon filled with horrors, tough choices, and countless ways to die.

## Features

- **Massive Decision Tree**: Hundreds of unique paths and choices
- **AI Dungeon Master**: Custom actions evaluated intelligently in context
- **Complex Combat System**: Stats, weapons, environmental factors matter
- **Survival Mechanics**: Hunger, temperature, wounds, sanity, lighting
- **Body Damage System**: Can lose limbs, eyes, and other body parts
- **Multiple Endings**: 100 different endings (10 good, 90 bad)
- **Thousands of Deaths**: Die in ridiculous, brutal, and unexpected ways
- **15-20 Minute Playtime**: First act takes place entirely in the dungeon
- **No UI Needed**: Pure console/terminal experience

## Requirements

- Python 3.6 or higher
- Works on Linux and Windows

## How to Play

### Linux/Mac:
```bash
python3 zagreus_dungeon.py
```

### Windows:
```bash
python zagreus_dungeon.py
```

## Gameplay

The game presents you with situations and choices. You can:
1. **Select numbered options** - Type the number and press Enter
2. **Use custom actions** - Choose "Custom action" and describe what you want to do
   - The AI Dungeon Master will evaluate your action based on:
     - Your stats (strength, agility, mind)
     - Your equipment (weapons, light source, armor)
     - Your condition (wounds, hunger, temperature)
     - Environmental factors (darkness, water, etc.)
     - The situation context

### Combat System

Combat is challenging and tactical:
- **Targeting matters**: Hitting weak points (eyes, joints) is more effective
- **Equipment matters**: Having a weapon, light source, or armor changes outcomes
- **Stats matter**: Strength, agility, and mind affect success rates
- **Conditions matter**: Fighting in darkness, with injuries, or without limbs is harder
- **Death is permanent**: Each playthrough ends when you die or escape

### Survival Mechanics

Monitor your status carefully:
- **Health**: Damage from combat, falls, and environmental hazards
- **Hunger**: Increases over time, find food or face starvation
- **Wetness**: Affects temperature and health
- **Temperature**: Too cold or too hot causes problems
- **Sanity**: Witnessing horrors and making dark choices affects your mind
- **Light**: Darkness hides details, options, and dangers

### Death

Death is common and often brutal:
- Drowning in flooded cells
- Eaten by dungeon creatures
- Poisoning from bad food
- Bleeding out from wounds
- Starvation
- Madness
- The Harvester (a special horror)
- And hundreds more ways...

## Tips

1. **Light is crucial** - Finding a torch or tinderbox early opens many paths
2. **Not all food is safe** - Inspect before eating
3. **Combat is risky** - Sometimes running or talking is smarter
4. **Equipment matters** - A weapon can save your life
5. **Read carefully** - Details in descriptions often hint at dangers
6. **Experiment** - Custom actions can find creative solutions
7. **Death teaches** - Each death reveals something about the dungeon

## Game Structure

The decision tree works as follows:
- **Branching paths**: Choices lead to different scenarios
- **Converging paths**: Different routes can merge back together
- **State persistence**: Items gained in one path persist if paths merge
- **Item dependency**: Some choices only available with specific items
- **Multiple endpoints**: Many ways to die, several ways to escape

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
- Dynamic AI-driven responses
- Extensive branching story structure
- Sophisticated state management
- Realistic consequence system

The game is designed to be replayed, with each playthrough revealing new paths and secrets.

---

**Can you escape the dungeon? Or will you become another forgotten corpse in the darkness?**
