# 🎮 Quick Start Guide - Zagreus' Descent v2.0

## 30-Second Start (Basic Mode)

```bash
python3 zagreus_dungeon.py
```

That's it! The game works without any setup.

---

## 2-Minute Start (AI Combat - Recommended)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get API Key
- Go to https://platform.openai.com/api-keys
- Create a new API key
- Copy it

### Step 3: Set Environment Variables

**Linux/Mac:**
```bash
export USE_AI_COMBAT=true
export OPENAI_API_KEY="your-key-here"
export AI_MODEL="gpt-4"
```

**Windows (PowerShell):**
```powershell
$env:USE_AI_COMBAT="true"
$env:OPENAI_API_KEY="your-key-here"
$env:AI_MODEL="gpt-4"
```

**Windows (Command Prompt):**
```cmd
set USE_AI_COMBAT=true
set OPENAI_API_KEY=your-key-here
set AI_MODEL=gpt-4
```

### Step 4: Play!
```bash
python3 zagreus_dungeon.py
```

---

## First-Time Player Tips

### 🎯 Core Concepts

1. **You will die. A LOT.** - That's the game. Learn from each death.
2. **Read carefully** - Hints are ALWAYS there (smells, sounds, warmth).
3. **Time pressure is real** - Don't overthink when drowning/burning.
4. **Save often** - Use manual checkpoints before risky choices.
5. **Be creative in combat** - Generic attacks fail. Target weaknesses.

### ⏰ Starting Scenario (IMPORTANT!)

You start **drowning** in a flooded cell with ~5 actions to escape:

✅ **FAST actions that work:**
- Search corpse thoroughly
- Feel walls for hidden crack
- Scream for help (reveals crack)

❌ **SLOW actions that kill:**
- Standing still (hypothermia)
- Talking too long
- Searching too carefully
- Trying to climb

### 🎮 How to Play

1. **Read the description** - Contains vital hints
2. **Choose a number** - Type 1-6 based on options
3. **Save if risky** - Select `[Save Checkpoint]` option
4. **On death** - Choose to restart or load checkpoint

### 🔮 Reading Hints

**Smells tell you what's ahead:**
- Sulfur → Fire/lava/chemicals
- Decay → Undead/ghouls
- Chemical → Experiments

**Sounds warn you:**
- Wet dragging → THE HARVESTER (run!)
- Chewing → Feeding creature
- Screaming → Danger

**Temperature matters:**
- Warm walls → Fire ahead
- Cold draft → Deep pit
- Humid → Water/flooding

### 💾 Checkpoints

**Auto-saves happen at:**
- Escaping the cell
- After first combat
- Key story moments

**Manual saves:**
- Select `[Save Checkpoint]` option
- Name it or press Enter
- Load on death or restart

### 🤖 AI Combat (If Enabled)

**The AI is BRUTAL. It will:**
- Kill you instantly for stupid actions
- Find logical reasons you should die
- Only let you survive if creative + logical

**Examples:**

❌ **BAD:** "I attack the huge monster"
```
AI: "You have no weapon. You're in water. The monster is HUGE. 
     You try to punch it. It crushes you instantly. [DEATH]"
```

✅ **GOOD:** "I notice it has dry skin and fears fire. I thrust my 
              torch into its eyes while dodging left."
```
AI: "Perfect! Fire weakness exploited. Torch burns its eyes. 
     It recoils. You dodge its claws. [40 damage dealt, 5 taken]"
```

### 📊 Cost (AI Combat Only)

- **GPT-4:** ~$0.50-2.00 per full playthrough
- **GPT-3.5-turbo:** ~$0.05-0.20 per playthrough
- **No AI:** FREE (uses rule-based system)

---

## Troubleshooting

### "AI Error: ... Falling back to rule-based system"
- Check API key is correct
- Verify internet connection
- Check OpenAI account has credits
- Game still works with rule-based combat

### "Node not found" error
- This is a bug - please report it
- Try loading a recent checkpoint
- Worst case: restart

### Game too hard?
- Use AI combat (better outcomes for creative players)
- Save before every risky choice
- Read descriptions very carefully
- Learn enemy patterns

### Game too easy?
- Don't use checkpoints (permadeath mode)
- Don't use AI (more random)
- Speed run challenges

---

## File Overview

- **zagreus_dungeon.py** - Main game (run this)
- **README.md** - Full documentation
- **AI_SETUP.md** - Detailed AI configuration
- **IMPROVEMENTS_v2.md** - What's new in v2.0
- **CHANGELOG.md** - Version history
- **GAMEPLAY_GUIDE.md** - Mechanics explained
- **requirements.txt** - Dependencies

---

## Support

### Need Help?
1. Check **AI_SETUP.md** for AI configuration
2. Check **README.md** for gameplay tips
3. Check **GAMEPLAY_GUIDE.md** for mechanics
4. Check error messages in game

### Found a Bug?
- Note what you did before the bug
- Check which node you were on
- Try loading a checkpoint
- Report with details

---

## Quick Reference Card

```
🎮 CONTROLS
- Type number (1-6) to choose action
- Type checkpoint number to save manually
- On death: restart or load checkpoint

⏰ TIME PRESSURE
- ⏰ icon = time-sensitive scenario
- ⚠️ warning = halfway to death
- Don't overthink in timed scenarios

🔮 HINTS
- Smells: sulfur=fire, decay=undead
- Sounds: dragging=Harvester, chewing=creature
- Temperature: warm=fire, cold=pit
- Visual: blood=danger, marks=predator

💾 CHECKPOINTS
- Auto-saves at major milestones
- Manual save anytime with [Save Checkpoint]
- Load on death or from main menu

🤖 AI COMBAT
- Be specific and creative
- Target weaknesses
- Use environment
- Know when to run
```

---

**Ready to die? Let's play!** 🎲💀

```bash
python3 zagreus_dungeon.py
```
