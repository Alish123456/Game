# AI Combat Configuration Guide

## Overview

Zagreus' Descent now supports **AI-powered combat** for the most immersive and brutal experience. The AI acts as a strict dungeon master, evaluating your creative combat actions and finding logical reasons to kill you unless your solution is nearly perfect.

## Setup

### 1. Install Dependencies (Optional)

```bash
pip install -r requirements.txt
```

**Note:** The game works without AI, using a rule-based fallback system. But AI combat is MUCH better.

### 2. Configure AI (Recommended)

Set environment variables:

```bash
# Linux/Mac
export USE_AI_COMBAT=true
export OPENAI_API_KEY="your-api-key-here"
export AI_MODEL="gpt-4"  # or gpt-3.5-turbo for cheaper option

# Windows (Command Prompt)
set USE_AI_COMBAT=true
set OPENAI_API_KEY=your-api-key-here
set AI_MODEL=gpt-4

# Windows (PowerShell)
$env:USE_AI_COMBAT="true"
$env:OPENAI_API_KEY="your-api-key-here"
$env:AI_MODEL="gpt-4"
```

### 3. Get an API Key

- OpenAI: https://platform.openai.com/api-keys
- Costs: ~$0.01-0.03 per combat encounter with GPT-4
- Alternative: Use GPT-3.5-turbo for ~$0.001 per encounter

## How AI Combat Works

### The AI is STRICT

The AI evaluates your combat actions based on:
- Your current stats (strength, agility, mind)
- Your equipment (weapons, armor, light source)
- Your injuries (missing limbs, wounds, status effects)
- Enemy type and weaknesses
- Logic and creativity of your action

### Rules the AI Follows

1. **No arms = instant death** if you try to attack
2. **Weak/generic actions = failure** (just saying "attack" won't work)
3. **Huge monsters = death** unless you use perfect strategy
4. **Targeting weaknesses = higher success chance**
5. **Creative + logical = survival possible**
6. **Running/dodging = valid IF you have the ability**

### Example Outcomes

**Bad action (dies):**
```
You: "I attack the huge water monster"
AI: "You have no weapon and no arms. You flail uselessly. The monster 
     crushes you instantly. [INSTANT DEATH]"
```

**Good action (survives):**
```
You: "I notice the ghoul's dry skin fears fire. I thrust my torch into 
     its eyes while dodging left using my agility."
AI: "The ghoul's weakness exploited! Your torch sears its sensitive eyes.
     It reels back, blinded. You strike again! [25 damage dealt, ghoul dies]"
```

**Creative but flawed (takes damage):**
```
You: "I throw sand in its eyes then stab its throat"
AI: "Creative! But you have no sand in a stone dungeon. You improvise with 
     dirt and rubble. Partially works - creature is briefly distracted. You 
     stab but miss the throat, hitting shoulder instead. [15 damage dealt, 
     10 damage taken]"
```

## Checkpoint System

### Auto-Checkpoints

The game automatically saves at key story points:
- Escaping the flooded cell (drainage_tunnel)
- After first major combat (equip_dagger_continue)
- Past the ghoul (past_ghoul_quick)
- Finding the guardroom (guardroom_escape)
- Trophy room entrance

### Manual Checkpoints

At any decision point, select `[Save Checkpoint]` to manually save.

### Loading Checkpoints

On game start or death, you can:
1. Start from beginning
2. Load a checkpoint

Checkpoints are saved in `saves/` directory as `checkpoint_N.pkl` files.

## Time Pressure System

### Timed Scenarios

Some situations have time limits:
- **Drowning cell**: 5 actions to escape
- **Chases**: varies
- **Fires**: varies

### Warnings

- Halfway through: "⚠️ TIME PRESSURE: You're running out of time!"
- Too slow: Instant death appropriate to situation

### Tips

- Don't overthink in timed scenarios
- Talking too much = death
- Searching too long = death
- Act decisively

## Foreshadowing System

### Environmental Hints

The game now includes subtle hints about upcoming dangers:

**Smell hints:**
- Sulfur = fire/chemical hazard ahead
- Decay = undead/ghoul nearby
- Chemical = experiments/overseer territory

**Sound hints:**
- Wet dragging = The Harvester
- Chewing = feeding creature
- Scraping = claws on stone
- Screaming = danger ahead

**Visual hints (with light):**
- Fresh blood = recent kill
- Claw marks = predator territory
- Warmth = fire/lava ahead
- Symbols = warnings or secrets

**Temperature hints:**
- Warm walls = fire ahead
- Cold draft = deep pit/chasm
- Humid = water/flooding

### Reading Hints

Pay attention to:
1. **Sensory details** in descriptions
2. **Physical clues** (scratches, blood, bodies)
3. **Environmental changes** (temperature, smell, sound)
4. **NPC hints** (journals, notes, dying words)

## Best Practices

### For AI Combat

1. **Be specific**: "I dodge left and strike its right eye with my dagger"
2. **Use environment**: "I push the shelf to crush it"
3. **Target weaknesses**: Read enemy descriptions carefully
4. **Consider your state**: Don't try heroics with missing limbs
5. **Know when to run**: Survival > heroism

### For Survival

1. **Read carefully**: Hints are ALWAYS there
2. **Save often**: Manual checkpoints are your friend
3. **Act fast in timed scenarios**: Don't deliberate
4. **Light is life**: Always try to have a light source
5. **Status effects kill**: Treat wounds immediately

### For Story

1. **Foreshadowing is real**: Sulfur smell = fire coming
2. **Bodies tell stories**: Check what killed previous victims
3. **NPCs lie**: Trust no one completely
4. **Choices matter**: Most lead to death
5. **Learn from failure**: Each death teaches something

## Troubleshooting

### AI Not Working

```
[AI Error: ... Falling back to rule-based system]
```

**Solutions:**
- Check API key is correct
- Verify `USE_AI_COMBAT=true` is set
- Check internet connection
- Verify OpenAI account has credits
- Game works fine with rule-based fallback

### Checkpoint Not Loading

**Solutions:**
- Check `saves/` directory exists
- Verify checkpoint file isn't corrupted
- Try different checkpoint number
- Worst case: Start new game

### Too Difficult

**Tips:**
- Use AI combat for better outcomes
- Read descriptions carefully for hints
- Save before risky choices
- Learn enemy patterns
- Use creative tactics

### Too Easy

**Tips:**
- Don't use checkpoints
- Don't use AI (rule-based is more random)
- Try permadeath challenge
- Speed run challenges

## Configuration Examples

### Maximum Difficulty (Permadeath, No AI)
```bash
# Don't set USE_AI_COMBAT
# Don't use checkpoints manually
# Delete saves/ folder after each death
```

### Recommended Experience (AI + Checkpoints)
```bash
export USE_AI_COMBAT=true
export OPENAI_API_KEY="sk-..."
export AI_MODEL="gpt-4"
# Use manual checkpoints at your discretion
```

### Story Mode (Frequent Checkpoints)
```bash
export USE_AI_COMBAT=true
export OPENAI_API_KEY="sk-..."
# Save before every major decision
# Reload after every death to learn
```

## Cost Estimation

### With GPT-4
- Typical combat: ~300 tokens (~$0.01-0.03)
- Full playthrough: ~$0.50-2.00
- Multiple deaths: ~$2.00-5.00

### With GPT-3.5-Turbo
- Typical combat: ~300 tokens (~$0.001)
- Full playthrough: ~$0.05-0.20
- Much cheaper, slightly less creative

## Privacy Note

When using AI combat:
- Your actions are sent to OpenAI
- Game state is included in prompts
- No personal information sent
- Standard OpenAI privacy policy applies
- Game works offline without AI

## Support

Issues? Check:
1. README.md for basic setup
2. GAMEPLAY_GUIDE.md for mechanics
3. This file for AI/checkpoint info
4. Error messages in game

---

**Remember: The AI is designed to kill you. Be creative, be logical, or be dead.**
