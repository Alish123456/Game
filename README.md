# Zagreus' Descent - A Dark Dungeon Crawler

A brutal, story-driven text adventure game inspired by Fear and Hunger with unforgiving mechanics and branching narratives.

## Story

You are Zagreus, betrayed by a former companion and thrown into a flooded dungeon hole to drown. You survived the initial fall, wounded and trapped in darkness. Now you must escape a massive, deadly dungeon where most choices lead to death. Only the wisest (or luckiest) will survive.

## Key Changes

**Recent Updates:**
- **Removed "Custom Action" menu option** - AI combat system remains for resolving fights, but player choices are now limited to specific options for a more focused experience
- **Betrayer character replaces guard** - The sadistic figure mocking you from above is your former companion who betrayed you, not a guard
- **Escape from the hole is nearly impossible** - Rope tricks don't work, climbing fails, most paths lead to death
- **Hidden crack is the primary escape route** - Only 2-3 specific starting paths lead to finding the secret passage
- **Vastly increased early-game lethality** - Most starting choices now lead to unique death scenarios
- **More diverse outcomes** - Different bad choices lead to different gruesome deaths

## Features

- **Massive Decision Tree**: 287+ unique story nodes with hundreds of paths
- **Brutal Difficulty**: Most choices lead to death - only 2-3 routes from the start survive
- **AI-Powered Combat**: Combat outcomes determined by AI based on stats, equipment, and tactics
- **Enhanced Combat System**: 
  - Tactical targeting (eyes, head, legs, throat, etc.)
  - Status effects (bleeding, poisoned, burning, stunned, etc.)
  - Critical hits and counterattacks
  - Equipment bonuses and durability
- **Deep Survival Mechanics**: 
  - Hunger, temperature, wounds, sanity, fear
  - Equipment degradation
  - Status effects that persist
  - Light/darkness affects everything
- **Advanced Body Damage**: Can lose limbs, eyes with realistic consequences
- **100 Different Endings**: 10 good, 90 bad based on your path
- **Hundreds of Unique Deaths**: Die in brutal, unexpected ways
- **Rich Atmosphere**: Dark environmental storytelling
- **15-20 Minute Playtime**: First act in the dungeon
- **Pure Terminal Experience**: No UI needed

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

The game presents situations and numbered choices. Select by typing the number.

### Starting Paths (SPOILERS)

From the flooded cell, only these paths typically survive:
1. **Search corpse thoroughly** → Take tinderbox → Find drainage grate → Escape
2. **Feel walls** → Continue feeling → Find hidden bundle → Escape
3. **Scream for help** → Betrayer taunts you → Find hidden crack → Escape

All other initial choices lead to unique death scenarios:
- **Stand and conserve energy** → Die from hypothermia
- **Take chain without searching** → Waste time, drown
- **Attempt to climb** → Fall and die
- **Panic or recoil** → Head injury, drown
- And many more...

### Combat System

Combat is resolved by the AI based on:
- Your stats (strength, agility, mind)
- Your equipment (weapon, light, armor)
- Your condition (wounds, stamina, status effects)
- Enemy type and weaknesses
- Environmental factors

### Survival Mechanics

Monitor carefully:
- **Health**: Damage from all sources
- **Stamina**: Energy for actions
- **Hunger**: Death at 100
- **Wetness**: Affects temperature
- **Temperature**: Hypothermia kills
- **Sanity**: Low sanity causes problems
- **Fear**: Attracts the Harvester
- **Status Effects**: Bleeding, poison, etc.
- **Equipment Durability**: Gear breaks

### Death

Death is permanent and common:
- Drowning variations
- Starvation
- Hypothermia
- Poisoning
- Combat
- Blood loss
- Infection
- Falls
- And 100+ more unique scenarios

## Tips

1. **Read carefully** - Most hints are in the descriptions
2. **Light is crucial** - Darkness hides dangers and limits options
3. **Not all paths are equal** - Some choices are traps
4. **Equipment matters** - Find weapons and armor early
5. **Manage resources** - Don't waste healing items
6. **Most choices kill you** - Expect to die and restart
7. **Learn from deaths** - Each death teaches you something
8. **Status effects are deadly** - Treat wounds immediately
9. **The betrayer won't help** - Don't trust rope tricks
10. **Search thoroughly** - Hidden items save lives

## Warnings

⚠️ This game contains:
- Dark themes and horror
- Graphic violence and death
- Difficult moral choices
- Extreme difficulty
- Psychological horror
- Frequent player death

Not for players sensitive to dark content.

## Development

A complex narrative game featuring:
- AI-driven combat resolution
- Extensive branching paths (287+ nodes)
- Sophisticated survival systems
- Realistic consequences
- Rich environmental storytelling
- Betrayal-focused narrative

Designed for multiple playthroughs to discover all paths and endings.

---

**Can you escape the dungeon? Or will you become another forgotten corpse in the darkness?**
