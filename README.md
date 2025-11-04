# Zagreus' Descent - A Dark Dungeon Crawler

A brutal, story-driven text adventure game inspired by Fear and Hunger with unforgiving mechanics, branching narratives, and **AI-powered strict combat**.

## Story

You are Zagreus, betrayed by a former companion and thrown into a flooded dungeon hole to drown. You survived the initial fall, wounded and trapped in darkness. Now you must escape a massive, deadly dungeon where most choices lead to death. Only the wisest (or luckiest) will survive.

## ⭐ Latest Updates (Major)

**Version 2.0 - AI Combat & Checkpoint System:**
- **🤖 REAL AI Combat Integration** - OpenAI-powered combat evaluation that is BRUTALLY strict
- **💾 Checkpoint System** - Save at key moments, no more starting over from the beginning
- **⏰ Time Pressure Mechanics** - Taking too long = death (drowning, burning, etc.)
- **🔮 Enhanced Foreshadowing** - Environmental hints (smells, sounds, warmth) warn of danger
- **🎯 Strict AI Logic** - AI finds excuses to kill you unless solution is nearly perfect
- **Auto-Save Points** - Game automatically checkpoints at major story milestones

## Features

### Core Gameplay
- **Massive Decision Tree**: 287+ unique story nodes with hundreds of paths
- **Brutal Difficulty**: Most choices lead to death - only 2-3 routes from the start survive
- **AI-Powered Combat** (Optional): Real AI evaluates your actions and punishes bad decisions
  - No arms? Try to attack? **INSTANT DEATH**
  - Generic attack? **FAILURE AND DAMAGE**  
  - Creative + logical solution? **Survival possible**
- **Checkpoint System**: Save and load at key moments
- **Time-Sensitive Scenarios**: Take too long searching/talking = death

### Combat & Survival
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
  - **Time pressure in critical situations**
- **Advanced Body Damage**: Can lose limbs, eyes with realistic consequences
- **Foreshadowing**: Environmental clues (sulfur smell = fire ahead, wet dragging = Harvester)

### Story
- **100 Different Endings**: 10 good, 90 bad based on your path
- **Hundreds of Unique Deaths**: Die in brutal, unexpected ways
- **Rich Atmosphere**: Dark environmental storytelling with hints
- **15-20 Minute Playtime**: First act in the dungeon
- **Pure Terminal Experience**: No UI needed

## Requirements

### Basic (Works Without AI)
- Python 3.6 or higher
- Works on Linux and Windows

### Enhanced (AI Combat - Recommended)
```bash
pip install -r requirements.txt
```
- OpenAI API key (for AI combat)
- Costs: ~$0.50-2.00 per full playthrough with GPT-4
- Or ~$0.05-0.20 with GPT-3.5-turbo

## How to Play

### Quick Start - Basic (No AI)

**Linux/Mac:**
```bash
./play.sh
```

**Windows:**
```bash
play.bat
```

### Enhanced Start - With AI Combat (Recommended)

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Set environment variables:**

Linux/Mac:
```bash
export USE_AI_COMBAT=true
export OPENAI_API_KEY="your-api-key-here"
export AI_MODEL="gpt-4"  # or gpt-3.5-turbo
./play.sh
```

Windows (PowerShell):
```powershell
$env:USE_AI_COMBAT="true"
$env:OPENAI_API_KEY="your-api-key-here"
$env:AI_MODEL="gpt-4"
.\play.bat
```

**See [AI_SETUP.md](AI_SETUP.md) for detailed AI configuration.**

## Gameplay

### Basic Controls
- Read situation descriptions carefully
- Type the number of your choice (1-6)
- Type the checkpoint number to save manually
- On death, choose to restart or load checkpoint

### NEW: Checkpoint System

**Auto-Checkpoints** happen at:
- Escaping the flooded cell
- After first combat victory
- Key story milestones

**Manual Checkpoints**:
- Select `[Save Checkpoint]` at any decision point
- Name your save or use auto-name
- Load on death or restart

**Time Pressure Warning:**
Some scenarios are timed:
- ⏰ Icon appears when time-sensitive
- ⚠️ Warning at halfway point
- Taking too long = instant death

### Starting Paths (SPOILERS - TIME SENSITIVE!)

From the flooded cell, you have **~5 actions** before drowning:

**Survival routes:**
1. **Search corpse thoroughly** → Take tinderbox → Find drainage grate → Escape
2. **Feel walls** → Continue feeling → Find hidden bundle → Escape  
3. **Scream for help** → Betrayer taunts you → Find hidden crack → Escape

**Death routes (wasting time):**
- **Stand and conserve energy** → Hypothermia + drowning
- **Take chain** → Waste time pulling, drown
- **Attempt to climb** → Fall and drown
- **Talk too much** → Drown while talking
- **Search too long** → Drown while searching
- And many more...

### Combat System (With AI)

**The AI is EXTREMELY STRICT:**
- No weapon + no arms + "attack" = **INSTANT DEATH**
- Generic actions = **FAILURE**
- Huge monster + melee = **DEATH**
- Targeting weakness + good tactic = **Survival possible**

**Example:**
```
❌ BAD: "I attack it"
   → AI: "With what? You have no weapon. It kills you. [DEATH]"

✅ GOOD: "The ghoul's dry skin fears fire. I thrust my torch into its 
         eyes while dodging left, using my agility."
   → AI: "Perfect! Fire weakness exploited. Agility dodge succeeds.
         Ghoul takes 35 damage and dies. You survive with minor scratches."
```

### Combat System (Without AI - Fallback)

Combat resolved by rule-based system using:
- Your stats (strength, agility, mind)
- Your equipment (weapon, light, armor)
- Your condition (wounds, stamina, status effects)
- Enemy type and weaknesses
- Environmental factors

### Foreshadowing & Hints (NEW)

**Pay attention to environmental clues:**

**Smells:**
- Sulfur = Fire/lava/chemical hazard ahead
- Decay = Undead/ghouls nearby
- Chemical = Overseer's experiments
- Blood = Recent kill

**Sounds:**
- Wet dragging = **THE HARVESTER** (run!)
- Chewing = Feeding creature
- Scraping = Claws on stone
- Screams = Danger or victim ahead

**Touch/Temperature:**
- Warm walls = Fire ahead
- Cold draft = Pit/chasm/deep drop
- Humid air = Water/flooding
- Sticky = Blood or chemicals

**Visual (with light):**
- Fresh blood = Very recent danger
- Claw marks = Predator territory
- Burn marks = Fire trap/monster
- Bodies = Learn from their mistakes

### Survival Mechanics

Monitor carefully:
- **Health**: Damage from all sources
- **Stamina**: Energy for actions
- **Hunger**: Death at 100 (increases over time)
- **Wetness**: Affects temperature
- **Temperature**: Hypothermia kills
- **Sanity**: Low sanity causes problems
- **Fear**: Attracts the Harvester
- **Status Effects**: Bleeding, poison, etc.
- **Equipment Durability**: Gear breaks
- **⏰ TIME**: In some scenarios, every second counts

### Death

Death is permanent and common:
- Drowning variations (most common early)
- Starvation
- Hypothermia
- Poisoning
- Combat
- Blood loss
- Infection
- Falls
- **Time pressure** (talking/searching too long)
- And 100+ more unique scenarios

**NEW: On Death Options:**
1. Restart from beginning
2. Load last checkpoint
3. Load specific checkpoint

## Tips

### Critical Tips (NEW)
1. **⏰ Time Pressure = ACT FAST** - Don't deliberate in timed scenarios
2. **🔮 Read environmental hints** - Sulfur smell means fire coming
3. **💾 Save before risky choices** - Manual checkpoints are lifesavers
4. **🤖 Use AI combat if possible** - Much better outcomes with creativity
5. **🎯 Target weaknesses** - Hints are always in enemy descriptions

### General Tips
6. **Light is crucial** - Darkness hides dangers and limits options
7. **Not all paths are equal** - Some choices are obvious traps
8. **Equipment matters** - Find weapons and armor early
9. **Manage resources** - Don't waste healing items
10. **Most choices kill you** - Expect to die and learn
11. **Status effects are deadly** - Treat wounds immediately
12. **The betrayer won't help** - Don't trust rope tricks
13. **Search thoroughly** - But not when drowning!
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
