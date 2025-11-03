# Chronicles of Destiny - A Complex Story RPG

⚔️ An immersive text-based RPG adventure with deep gameplay systems ⚔️

## Description

Chronicles of Destiny is a complex, story-driven RPG game featuring:
- **Branching narrative** with multiple chapters and locations
- **Dynamic combat system** with strategic elements
- **Character progression** with leveling, stats, and experience
- **Rich inventory system** with weapons, armor, and consumables
- **Quest tracking** with objectives and rewards
- **Save/Load functionality** to preserve your progress
- **Multiple enemy types** with unique stats and loot
- **Exploration** across diverse locations from villages to dark dungeons

## Features

### 🎮 Core Gameplay Systems

1. **Character System**
   - Health, Attack, Defense stats
   - Level progression with stat increases
   - Experience points from combat
   - Equipment slots (Weapon & Armor)
   - Gold currency

2. **Combat System**
   - Turn-based combat mechanics
   - Attack, Use Item, or Flee options
   - Defense calculation reduces damage
   - Random damage variance for unpredictability
   - Victory rewards: Experience, Gold, and Loot

3. **Inventory Management**
   - Multiple item types: Weapons, Armor, Consumables, Key Items
   - Equipment system with stat bonuses
   - Usable items (healing potions)
   - Quest items and collectibles

4. **Quest System**
   - Multiple active quests
   - Objective tracking with progress indicators
   - Quest rewards (Gold, Experience, Items)
   - Story integration

5. **World Exploration**
   - 10+ unique locations to discover
   - Connected world map with directional movement
   - Random encounters in dangerous areas
   - First-visit location events

### 🗺️ Game World

**Locations include:**
- Willowbrook Village (Starting point)
- The Rusty Tankard Tavern
- Dark Forest and Deep Forest
- Witch's Hut
- Mountain Path and Peak
- Ancient Temple
- Ancient Ruins
- Catacombs
- Forgotten Throne Room (Final Boss)

### ⚔️ Enemies

Battle various foes of increasing difficulty:
- **Goblin** - Weak forest dweller
- **Dire Wolf** - Aggressive beast
- **Bandit** - Armed robber
- **Dark Knight** - Powerful warrior
- **Shadow Beast** - Magical creature
- **Shadow King** - Final boss (200 HP, 35 ATK)

### 🎒 Items & Equipment

**Weapons:**
- Rusty Sword (ATK +3)
- Iron Sword (ATK +7)
- Steel Sword (ATK +12)
- Legendary Blade of Light (ATK +25)

**Armor:**
- Leather Armor (DEF +3)
- Chainmail Armor (DEF +8)
- Plate Armor (DEF +15)

**Consumables:**
- Health Potion (Restores 30 HP)
- Greater Health Potion (Restores 60 HP)

**Key Items:**
- Ancient Key
- Royal Seal
- Crystal Shard

## Installation

### Requirements
- Python 3.7 or higher

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Alish123456/Game.git
cd Game
```

2. Run the game:
```bash
python story_game.py
```

Or make it executable:
```bash
chmod +x story_game.py
./story_game.py
```

## How to Play

### Starting the Game

1. Run `python story_game.py`
2. Choose "New Game" from the main menu
3. Enter your character's name
4. Begin your adventure!

### Controls

**Main Game Commands:**
- `m` or `move` - Travel to another location
- `i` or `inventory` - View and manage items
- `q` or `quests` - Check active quests
- `s` or `stats` - View detailed character stats
- `r` or `rest` - Restore health for 20 gold
- `save` - Save your current progress
- `load` - Load a saved game
- `help` - Display help information
- `quit` - Exit the game

**Combat Commands:**
- `a` or `attack` - Attack the enemy
- `i` or `item` - Use a healing potion
- `r` or `run` - Attempt to flee (50% success rate)

### Gameplay Tips

1. **Save Often** - Use the save command regularly to preserve progress
2. **Explore Everything** - Visit all locations to find items and encounters
3. **Manage Resources** - Don't waste healing potions; rest when safe
4. **Upgrade Equipment** - Equip better gear as you find it
5. **Level Up** - Fight enemies to gain experience and grow stronger
6. **Complete Quests** - Quests provide valuable rewards
7. **Prepare for Bosses** - Stock up on potions before dangerous areas

### Progression Path

Recommended route for new players:
1. Start in Willowbrook Village
2. Visit the Tavern to gather information
3. Explore the Dark Forest (easier enemies)
4. Progress to Mountain Path and Peak
5. Investigate the Ancient Ruins
6. Descend into the Catacombs
7. Face the Shadow King in the Throne Room

## Game Mechanics

### Leveling System
- Gain experience by defeating enemies
- Required XP = Level × 100
- Each level grants:
  - +10 Max Health
  - +2 Attack
  - +1 Defense
  - Full health restoration

### Combat Calculation
- **Damage Dealt** = Attack × (0.8 to 1.2 random) - Enemy Defense (min 1)
- **Damage Taken** = Enemy Attack - Your Defense (min 1)
- Equipment bonuses added to base stats

### Save System
- Game state saved to `savegame.json`
- Preserves:
  - Character stats and inventory
  - Current location
  - Story progress flags
  - Visited locations
  - Chapter number

## Story Synopsis

In the peaceful village of Willowbrook, darkness is spreading across the land. Strange creatures emerge from the Dark Forest, and travelers speak of an ancient evil awakening. The village elder believes you have the potential to become the hero the realm desperately needs.

Your journey will take you through haunted forests, treacherous mountains, and forgotten ruins as you uncover the mystery of the Shadow King and his plans to plunge the world into eternal darkness.

Will you rise to become the Champion of Light, or will the realm fall to shadow?

## Technical Details

### Architecture
- **Object-Oriented Design** - Clean class structure
- **Dataclasses** - Modern Python for data structures
- **Enum Types** - Type-safe state management
- **JSON Serialization** - Save/load functionality

### Code Structure
- `GameState` - Enum for game states
- `ItemType` - Enum for item categories
- `Item` - Item dataclass with stats
- `Character` - Player character with stats and inventory
- `Quest` - Quest system with objectives
- `Enemy` - Enemy class with combat stats
- `Location` - World location with connections
- `StoryGame` - Main game controller

## Future Enhancements

Potential additions:
- Multiple story endings based on choices
- Magic/spell system
- Crafting system
- Merchant NPCs
- Side quests and optional content
- Character classes (Warrior, Mage, Rogue)
- Difficulty settings
- Achievement system
- More items and equipment
- Expanded world with more locations

## License

This project is open source and available for educational purposes.

## Credits

Created as a complex story-based RPG demonstration.

---

**Enjoy your adventure in Chronicles of Destiny!** ⚔️🛡️✨

