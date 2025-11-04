# Changelog

## Version 2.0.0 - Major Feature Release (2024-01-15)

### 🎉 Major New Features

#### 🤖 AI Combat System
- **Real AI Integration**: OpenAI GPT-powered combat evaluation
- **Strict Logic Enforcement**: AI finds excuses to kill unless solution is nearly perfect
- **Context-Aware**: AI considers stats, equipment, injuries, enemy weaknesses
- **Fallback System**: Works without AI using rule-based combat
- **Configurable**: Environment variables for easy setup
- **Cost-Effective**: ~$0.50-2 per playthrough with GPT-4, ~$0.05-0.20 with GPT-3.5

#### 💾 Checkpoint System
- **Auto-Checkpoints**: Automatic saves at 5 major story milestones
- **Manual Saves**: Save at any decision point with custom names
- **Load on Death**: Choose to restart or load checkpoint after dying
- **Full State Preservation**: All stats, inventory, flags preserved
- **Multiple Saves**: Keep multiple checkpoints for different runs

#### ⏰ Time Pressure Mechanics
- **Timed Scenarios**: Drowning (5 actions), fires, chases
- **Action Tracking**: Game counts your actions in timed situations
- **Death by Delay**: Talking too much or searching too long = death
- **Visual Warnings**: ⏰ icon when time-sensitive, ⚠️ at halfway point
- **Contextual Deaths**: Drowning, burning, or generic time pressure death

#### 🔮 Enhanced Foreshadowing
- **Smell Hints**: Sulfur (fire), decay (undead), chemical (experiments)
- **Sound Hints**: Wet dragging (Harvester), chewing (creatures), screams
- **Temperature Hints**: Warm walls (fire), cold drafts (pits), humidity (water)
- **Visual Hints**: Fresh blood, claw marks, burn marks, body positions
- **Environmental Storytelling**: Rich atmospheric details in descriptions

### 📝 Story & Content Updates

#### Enhanced Story Nodes
- **drainage_tunnel**: Added sulfur smell and temperature hints
- **torch_corridor**: Added claw mark details and fresh blood indicators
- **take_torch**: Added shadow movement and smell intensification
- **blood_trail**: Added victim detail and ghoul weakness hint (dry skin/fire)

#### New Death Scenarios
- **death_time_pressure**: Generic death from taking too long
- **death_burning**: Death from fire-related scenarios
- Multiple variations based on context

### 🛠️ Technical Improvements

#### Code Quality
- Modular AI system with clean fallback
- Pickle-based save system
- Environment variable configuration
- Comprehensive error handling
- Type hints maintained

#### New Constants
```python
USE_AI_COMBAT = bool  # Enable/disable AI
AI_API_KEY = str      # OpenAI API key
AI_MODEL = str        # Model selection (gpt-4, gpt-3.5-turbo)
AUTO_CHECKPOINT_NODES = list  # Auto-save locations
```

#### New Methods
- `create_checkpoint()` - Save game state
- `load_checkpoint()` - Restore game state
- `list_checkpoints()` - Show all saves
- `check_time_pressure()` - Validate action timer
- `start_time_pressure()` - Begin timed scenario
- `_evaluate_combat_ai()` - AI combat evaluation

### 📚 Documentation

#### New Files
- **AI_SETUP.md**: Comprehensive AI configuration guide (7.5KB)
- **requirements.txt**: Dependency management
- **IMPROVEMENTS_v2.md**: Detailed changelog and examples (11.6KB)
- **CHANGELOG.md**: This file

#### Updated Files
- **README.md**: Major overhaul with new features, examples, tips
- **zagreus_dungeon.py**: +500 lines of new functionality

### 🐛 Bug Fixes
- Fixed node_history tracking for better state management
- Improved error messages for missing nodes
- Enhanced input validation
- Better handling of edge cases in combat

### ⚡ Performance
- No performance impact when AI disabled
- Checkpoint saves < 1MB per file
- Fast save/load operations
- Minimal memory footprint

### 🔧 Configuration

#### Required (Basic Play)
- Python 3.6+

#### Optional (Enhanced Experience)
- openai >= 1.0.0
- OpenAI API key
- Internet connection (for AI only)

### 📊 Statistics
- **Lines of Code Added**: ~500
- **New Features**: 4 major systems
- **New Death Scenarios**: 2+
- **Enhanced Nodes**: 4+
- **Auto-Checkpoint Nodes**: 5
- **Documentation**: +19KB

### 🎮 Gameplay Changes

#### Balance
- Time pressure makes early game more challenging
- Checkpoints prevent frustration on long runs
- AI combat rewards creativity and logic
- Foreshadowing gives skilled players advantage

#### Player Experience
- More forgiving with checkpoints
- More brutal with AI combat
- More atmospheric with foreshadowing
- More urgent with time pressure

### 🚀 Migration Guide

#### For Existing Players
1. Old save files won't work (new save system)
2. Game behavior unchanged if AI not enabled
3. Checkpoints completely optional
4. Can continue playing without any setup

#### For New Players
1. Follow AI_SETUP.md for best experience
2. Or play without AI for free experience
3. Checkpoints auto-save at key moments
4. Manual saves recommended before risky choices

### 🔮 Future Roadmap

Potential future additions:
- More AI integration (NPCs, descriptions)
- Adaptive difficulty
- Achievement system
- Multiplayer shared dungeons
- Mod support
- Voice acting with TTS

### 🙏 Acknowledgments

Implemented based on user requirements for:
- Strict AI combat logic
- Long-route checkpoint preservation
- Time-pressure death mechanics
- Environmental foreshadowing

---

## Version 1.0.0 - Initial Release

### Features
- 287+ story nodes
- Brutal difficulty
- Rule-based combat
- Survival mechanics
- Body damage system
- Status effects
- Multiple endings
- Dark atmosphere

---

**For detailed setup instructions, see AI_SETUP.md**
**For complete improvement details, see IMPROVEMENTS_v2.md**
