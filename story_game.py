#!/usr/bin/env python3
"""
Complex Story-Based RPG Game
A deep, branching narrative adventure with combat, inventory, quests, and character progression
"""

import json
import os
import random
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class GameState(Enum):
    """Possible states the game can be in"""
    MENU = "menu"
    PLAYING = "playing"
    COMBAT = "combat"
    DIALOGUE = "dialogue"
    INVENTORY = "inventory"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class ItemType(Enum):
    """Types of items in the game"""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    KEY_ITEM = "key_item"
    QUEST_ITEM = "quest_item"


@dataclass
class Item:
    """Represents an item in the game"""
    name: str
    item_type: ItemType
    description: str
    value: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    health_restore: int = 0
    usable: bool = False
    
    def use(self, character) -> str:
        """Use the item on a character"""
        if not self.usable:
            return f"You can't use {self.name}."
        
        if self.health_restore > 0:
            old_health = character.health
            character.health = min(character.max_health, character.health + self.health_restore)
            healed = character.health - old_health
            return f"You used {self.name} and restored {healed} health!"
        
        return f"You used {self.name}."


@dataclass
class Character:
    """Base character class for player and NPCs"""
    name: str
    health: int
    max_health: int
    attack: int
    defense: int
    level: int = 1
    experience: int = 0
    inventory: List[Item] = field(default_factory=list)
    equipped_weapon: Optional[Item] = None
    equipped_armor: Optional[Item] = None
    gold: int = 0
    
    def get_total_attack(self) -> int:
        """Calculate total attack including equipment"""
        total = self.attack
        if self.equipped_weapon:
            total += self.equipped_weapon.attack_bonus
        return total
    
    def get_total_defense(self) -> int:
        """Calculate total defense including equipment"""
        total = self.defense
        if self.equipped_armor:
            total += self.equipped_armor.defense_bonus
        return total
    
    def take_damage(self, damage: int) -> int:
        """Apply damage to character, accounting for defense"""
        actual_damage = max(1, damage - self.get_total_defense())
        self.health = max(0, self.health - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """Check if character is still alive"""
        return self.health > 0
    
    def gain_experience(self, exp: int):
        """Gain experience and level up if threshold met"""
        self.experience += exp
        exp_needed = self.level * 100
        
        if self.experience >= exp_needed:
            self.level_up()
    
    def level_up(self):
        """Level up the character"""
        self.level += 1
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        self.defense += 1
        self.experience = 0
    
    def add_item(self, item: Item):
        """Add item to inventory"""
        self.inventory.append(item)
    
    def remove_item(self, item: Item):
        """Remove item from inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
    
    def equip_weapon(self, weapon: Item) -> str:
        """Equip a weapon"""
        if weapon.item_type != ItemType.WEAPON:
            return f"{weapon.name} is not a weapon!"
        
        if self.equipped_weapon:
            old_weapon = self.equipped_weapon
            self.equipped_weapon = weapon
            return f"You equipped {weapon.name} and unequipped {old_weapon.name}."
        else:
            self.equipped_weapon = weapon
            return f"You equipped {weapon.name}."
    
    def equip_armor(self, armor: Item) -> str:
        """Equip armor"""
        if armor.item_type != ItemType.ARMOR:
            return f"{armor.name} is not armor!"
        
        if self.equipped_armor:
            old_armor = self.equipped_armor
            self.equipped_armor = armor
            return f"You equipped {armor.name} and unequipped {old_armor.name}."
        else:
            self.equipped_armor = armor
            return f"You equipped {armor.name}."


@dataclass
class Quest:
    """Represents a quest in the game"""
    name: str
    description: str
    objectives: List[str]
    completed_objectives: List[bool] = field(default_factory=list)
    completed: bool = False
    reward_gold: int = 0
    reward_exp: int = 0
    reward_items: List[Item] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.completed_objectives:
            self.completed_objectives = [False] * len(self.objectives)
    
    def complete_objective(self, index: int):
        """Mark an objective as complete"""
        if 0 <= index < len(self.objectives):
            self.completed_objectives[index] = True
            if all(self.completed_objectives):
                self.completed = True
    
    def get_progress(self) -> str:
        """Get quest progress as string"""
        progress = []
        for i, obj in enumerate(self.objectives):
            status = "✓" if self.completed_objectives[i] else "○"
            progress.append(f"{status} {obj}")
        return "\n".join(progress)


class Enemy:
    """Enemy character for combat"""
    def __init__(self, name: str, health: int, attack: int, defense: int, 
                 exp_reward: int, gold_reward: int, loot: List[Item] = None):
        self.name = name
        self.health = health
        self.max_health = health
        self.attack = attack
        self.defense = defense
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward
        self.loot = loot or []
    
    def take_damage(self, damage: int) -> int:
        """Apply damage to enemy"""
        actual_damage = max(1, damage - self.defense)
        self.health = max(0, self.health - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """Check if enemy is alive"""
        return self.health > 0


class Location:
    """Represents a location in the game world"""
    def __init__(self, name: str, description: str, connections: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.connections = connections or {}
        self.visited = False
        self.npcs = []
        self.items = []
        self.enemies = []


class StoryGame:
    """Main game class managing all game systems"""
    
    def __init__(self):
        self.state = GameState.MENU
        self.player: Optional[Character] = None
        self.current_location: Optional[Location] = None
        self.locations: Dict[str, Location] = {}
        self.quests: List[Quest] = []
        self.story_flags: Dict[str, bool] = {}
        self.chapter = 1
        self.save_file = "savegame.json"
        
        self.initialize_game_world()
        self.initialize_items()
    
    def initialize_items(self):
        """Initialize all game items"""
        self.all_items = {
            # Weapons
            "rusty_sword": Item(
                "Rusty Sword", ItemType.WEAPON,
                "An old, rusty sword. Better than nothing.",
                value=10, attack_bonus=3
            ),
            "iron_sword": Item(
                "Iron Sword", ItemType.WEAPON,
                "A sturdy iron sword.",
                value=50, attack_bonus=7
            ),
            "steel_sword": Item(
                "Steel Sword", ItemType.WEAPON,
                "A finely crafted steel blade.",
                value=150, attack_bonus=12
            ),
            "legendary_blade": Item(
                "Legendary Blade of Light", ItemType.WEAPON,
                "A mythical sword that glows with inner light.",
                value=1000, attack_bonus=25
            ),
            
            # Armor
            "leather_armor": Item(
                "Leather Armor", ItemType.ARMOR,
                "Basic leather protection.",
                value=30, defense_bonus=3
            ),
            "chainmail": Item(
                "Chainmail Armor", ItemType.ARMOR,
                "Heavy chainmail that offers good protection.",
                value=100, defense_bonus=8
            ),
            "plate_armor": Item(
                "Plate Armor", ItemType.ARMOR,
                "Full plate armor for maximum defense.",
                value=300, defense_bonus=15
            ),
            
            # Consumables
            "health_potion": Item(
                "Health Potion", ItemType.CONSUMABLE,
                "Restores 30 health points.",
                value=25, health_restore=30, usable=True
            ),
            "greater_health_potion": Item(
                "Greater Health Potion", ItemType.CONSUMABLE,
                "Restores 60 health points.",
                value=50, health_restore=60, usable=True
            ),
            
            # Key Items
            "ancient_key": Item(
                "Ancient Key", ItemType.KEY_ITEM,
                "An ornate key covered in mystical runes.",
                value=0
            ),
            "royal_seal": Item(
                "Royal Seal", ItemType.KEY_ITEM,
                "The official seal of the kingdom.",
                value=0
            ),
            "crystal_shard": Item(
                "Crystal Shard", ItemType.QUEST_ITEM,
                "A fragment of a magical crystal.",
                value=0
            ),
        }
    
    def initialize_game_world(self):
        """Create the game world with locations and connections"""
        # Create locations
        self.locations = {
            "village": Location(
                "Willowbrook Village",
                "A peaceful village nestled in a valley. Smoke rises from chimneys and "
                "villagers go about their daily business. To the north lies the dark forest, "
                "to the east the mountain path, and south leads to the ancient ruins.",
                {"north": "forest", "east": "mountain", "south": "ruins", "west": "tavern"}
            ),
            "tavern": Location(
                "The Rusty Tankard Tavern",
                "A cozy tavern filled with the smell of ale and roasted meat. "
                "Adventurers and merchants gather here to share tales and rumors.",
                {"east": "village"}
            ),
            "forest": Location(
                "Dark Forest",
                "Ancient trees tower overhead, blocking out most sunlight. Strange sounds "
                "echo through the woods. A path leads deeper into the forest.",
                {"south": "village", "north": "forest_deep"}
            ),
            "forest_deep": Location(
                "Deep Forest",
                "The forest grows darker here. An eerie mist clings to the ground. "
                "You sense a powerful presence nearby.",
                {"south": "forest", "east": "witch_hut"}
            ),
            "witch_hut": Location(
                "Witch's Hut",
                "A ramshackle hut made of twisted wood and bones. Magical energy crackles "
                "in the air around it.",
                {"west": "forest_deep"}
            ),
            "mountain": Location(
                "Mountain Path",
                "A treacherous path winds up the mountainside. The air grows thin and cold.",
                {"west": "village", "north": "mountain_peak"}
            ),
            "mountain_peak": Location(
                "Mountain Peak",
                "The peak of the mountain offers a breathtaking view. An ancient temple "
                "stands here, weathered by countless storms.",
                {"south": "mountain", "enter": "temple"}
            ),
            "temple": Location(
                "Ancient Temple",
                "Inside the temple, mystical symbols glow on the walls. An altar stands "
                "at the center, radiating power.",
                {"exit": "mountain_peak"}
            ),
            "ruins": Location(
                "Ancient Ruins",
                "Crumbling stone structures hint at a once-great civilization. "
                "Strange markings cover the walls.",
                {"north": "village", "down": "catacombs"}
            ),
            "catacombs": Location(
                "Catacombs",
                "Dark tunnels wind beneath the ruins. The air is stale and oppressive.",
                {"up": "ruins", "deeper": "throne_room"}
            ),
            "throne_room": Location(
                "Forgotten Throne Room",
                "A massive chamber with a dark throne at its center. This is where the "
                "Shadow King awaits...",
                {"back": "catacombs"}
            ),
        }
    
    def create_player(self, name: str):
        """Create a new player character"""
        self.player = Character(
            name=name,
            health=100,
            max_health=100,
            attack=10,
            defense=5,
            level=1,
            experience=0,
            gold=50
        )
        
        # Give starting items
        self.player.add_item(self.all_items["rusty_sword"])
        self.player.add_item(self.all_items["leather_armor"])
        self.player.add_item(self.all_items["health_potion"])
        self.player.add_item(self.all_items["health_potion"])
        
        # Equip starting gear
        self.player.equip_weapon(self.all_items["rusty_sword"])
        self.player.equip_armor(self.all_items["leather_armor"])
        
        self.current_location = self.locations["village"]
    
    def create_enemy(self, enemy_type: str) -> Enemy:
        """Create an enemy based on type"""
        enemies = {
            "goblin": Enemy(
                "Goblin", 30, 8, 2, 25, 10,
                [self.all_items["health_potion"]]
            ),
            "wolf": Enemy(
                "Dire Wolf", 40, 12, 3, 30, 15,
                [self.all_items["health_potion"]]
            ),
            "bandit": Enemy(
                "Bandit", 50, 15, 5, 40, 25,
                [self.all_items["iron_sword"], self.all_items["health_potion"]]
            ),
            "dark_knight": Enemy(
                "Dark Knight", 80, 20, 10, 75, 50,
                [self.all_items["steel_sword"], self.all_items["chainmail"]]
            ),
            "shadow_beast": Enemy(
                "Shadow Beast", 100, 25, 8, 100, 75,
                [self.all_items["greater_health_potion"], self.all_items["crystal_shard"]]
            ),
            "shadow_king": Enemy(
                "Shadow King", 200, 35, 15, 500, 1000,
                [self.all_items["legendary_blade"], self.all_items["royal_seal"]]
            ),
        }
        
        return enemies.get(enemy_type, enemies["goblin"])
    
    def start_new_game(self):
        """Start a new game"""
        self.clear_screen()
        self.print_banner()
        print("\n=== Welcome to the Chronicles of Destiny ===\n")
        print("In a world torn by darkness, a hero must rise...")
        print("Your choices will shape the fate of the realm.\n")
        
        name = input("Enter your character's name: ").strip()
        if not name:
            name = "Hero"
        
        self.create_player(name)
        self.state = GameState.PLAYING
        
        # Add starting quests
        self.add_quest(Quest(
            "The Village Elder's Request",
            "The village elder has asked you to investigate strange occurrences in the Dark Forest.",
            ["Travel to the Dark Forest", "Investigate the source of darkness", "Report back to the elder"],
            reward_gold=100,
            reward_exp=50
        ))
        
        self.clear_screen()
        self.show_prologue()
        self.game_loop()
    
    def show_prologue(self):
        """Show the game's prologue"""
        print("\n" + "="*70)
        print("PROLOGUE: The Gathering Darkness")
        print("="*70)
        print(f"\nGreetings, {self.player.name}.")
        print("\nThe village of Willowbrook has been your home for as long as you can")
        print("remember. But recently, darkness has been spreading across the land.")
        print("\nStrange creatures have been spotted in the Dark Forest. Travelers")
        print("speak of an ancient evil awakening. The village elder believes you")
        print("have the potential to become the hero the realm needs.")
        print("\nYour journey begins now...")
        print("\n" + "="*70)
        input("\nPress Enter to continue...")
    
    def game_loop(self):
        """Main game loop"""
        while self.state == GameState.PLAYING:
            self.clear_screen()
            self.show_status()
            self.show_location()
            self.show_menu()
            
            choice = input("\nWhat would you like to do? ").strip().lower()
            self.handle_input(choice)
            
            if not self.player.is_alive():
                self.state = GameState.GAME_OVER
                self.game_over()
    
    def show_status(self):
        """Display player status"""
        print(f"\n{'='*70}")
        print(f"Chapter {self.chapter} | {self.player.name} - Level {self.player.level}")
        print(f"{'='*70}")
        print(f"Health: {self.player.health}/{self.player.max_health} | "
              f"Attack: {self.player.get_total_attack()} | "
              f"Defense: {self.player.get_total_defense()} | "
              f"Gold: {self.player.gold}")
        print(f"Experience: {self.player.experience}/{self.player.level * 100}")
        print(f"{'='*70}\n")
    
    def show_location(self):
        """Display current location"""
        loc = self.current_location
        print(f"📍 {loc.name}")
        print(f"{loc.description}\n")
        
        if not loc.visited:
            loc.visited = True
            self.trigger_location_event()
    
    def trigger_location_event(self):
        """Trigger events based on location"""
        loc_name = self.current_location.name
        
        # Forest encounters
        if "forest" in loc_name.lower() and random.random() < 0.4:
            print("⚠️  A hostile creature appears!\n")
            input("Press Enter to continue...")
            enemy_type = "wolf" if "deep" in loc_name.lower() else "goblin"
            self.start_combat(self.create_enemy(enemy_type))
        
        # Mountain encounters
        elif "mountain" in loc_name.lower() and random.random() < 0.3:
            print("⚠️  A bandit blocks your path!\n")
            input("Press Enter to continue...")
            self.start_combat(self.create_enemy("bandit"))
        
        # Catacombs encounters
        elif "catacomb" in loc_name.lower():
            print("⚠️  Something evil lurks in the darkness!\n")
            input("Press Enter to continue...")
            self.start_combat(self.create_enemy("shadow_beast"))
        
        # Throne room - final boss
        elif "throne" in loc_name.lower() and not self.story_flags.get("defeated_shadow_king"):
            print("\n" + "="*70)
            print("The Shadow King rises from his throne!")
            print("="*70)
            print("\n'So, another fool comes to challenge me...'")
            print("'You will fall like all the others!'\n")
            input("Press Enter to face your destiny...")
            self.start_combat(self.create_enemy("shadow_king"))
            if not self.player.is_alive():
                return
            self.story_flags["defeated_shadow_king"] = True
            self.victory()
    
    def show_menu(self):
        """Display available actions"""
        print("Available actions:")
        print("  [m]ove - Travel to another location")
        print("  [i]nventory - Manage your items")
        print("  [q]uests - View your quests")
        print("  [s]tats - View detailed character stats")
        print("  [r]est - Rest to restore health (costs 20 gold)")
        print("  [save] - Save your game")
        print("  [load] - Load a saved game")
        print("  [help] - Show help")
        print("  [quit] - Quit game")
    
    def handle_input(self, choice: str):
        """Handle player input"""
        if choice in ['m', 'move']:
            self.move_to_location()
        elif choice in ['i', 'inventory']:
            self.show_inventory()
        elif choice in ['q', 'quests']:
            self.show_quests()
        elif choice in ['s', 'stats']:
            self.show_detailed_stats()
        elif choice in ['r', 'rest']:
            self.rest()
        elif choice == 'save':
            self.save_game()
        elif choice == 'load':
            self.load_game()
        elif choice == 'help':
            self.show_help()
        elif choice == 'quit':
            if self.confirm_quit():
                sys.exit(0)
        else:
            print("\nInvalid choice. Type 'help' for available commands.")
            input("Press Enter to continue...")
    
    def move_to_location(self):
        """Handle movement to new location"""
        print("\nWhere would you like to go?")
        connections = self.current_location.connections
        
        if not connections:
            print("There's nowhere to go from here.")
            input("Press Enter to continue...")
            return
        
        for direction, loc_key in connections.items():
            loc = self.locations.get(loc_key)
            if loc:
                print(f"  [{direction}] - {loc.name}")
        print("  [back] - Stay here")
        
        choice = input("\nChoose direction: ").strip().lower()
        
        if choice == 'back':
            return
        
        if choice in connections:
            new_loc_key = connections[choice]
            if new_loc_key in self.locations:
                self.current_location = self.locations[new_loc_key]
                print(f"\nYou travel to {self.current_location.name}...")
                input("Press Enter to continue...")
            else:
                print("That location doesn't exist yet.")
                input("Press Enter to continue...")
        else:
            print("Invalid direction.")
            input("Press Enter to continue...")
    
    def show_inventory(self):
        """Display and manage inventory"""
        while True:
            self.clear_screen()
            print("\n=== INVENTORY ===\n")
            print(f"Gold: {self.player.gold}")
            print(f"\nEquipped Weapon: {self.player.equipped_weapon.name if self.player.equipped_weapon else 'None'}")
            print(f"Equipped Armor: {self.player.equipped_armor.name if self.player.equipped_armor else 'None'}")
            print("\nItems:")
            
            if not self.player.inventory:
                print("  (empty)")
            else:
                for i, item in enumerate(self.player.inventory, 1):
                    equipped = ""
                    if item == self.player.equipped_weapon or item == self.player.equipped_armor:
                        equipped = " (equipped)"
                    print(f"  {i}. {item.name}{equipped} - {item.description}")
            
            print("\n[number] - Use/Equip item | [back] - Return")
            choice = input("\nChoice: ").strip().lower()
            
            if choice == 'back':
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.player.inventory):
                    self.use_item(self.player.inventory[idx])
                else:
                    print("Invalid item number.")
                    input("Press Enter to continue...")
            except ValueError:
                if choice != 'back':
                    print("Invalid input.")
                    input("Press Enter to continue...")
    
    def use_item(self, item: Item):
        """Use or equip an item"""
        print(f"\n{item.name}: {item.description}")
        
        if item.item_type == ItemType.WEAPON:
            print(self.player.equip_weapon(item))
        elif item.item_type == ItemType.ARMOR:
            print(self.player.equip_armor(item))
        elif item.usable:
            result = item.use(self.player)
            print(result)
            if item.health_restore > 0:
                self.player.remove_item(item)
        else:
            print("This item cannot be used directly.")
        
        input("\nPress Enter to continue...")
    
    def show_quests(self):
        """Display quest log"""
        self.clear_screen()
        print("\n=== QUEST LOG ===\n")
        
        if not self.quests:
            print("You have no active quests.")
        else:
            for i, quest in enumerate(self.quests, 1):
                status = "✓ COMPLETED" if quest.completed else "◯ ACTIVE"
                print(f"{i}. {quest.name} [{status}]")
                print(f"   {quest.description}")
                print(f"\n   Objectives:")
                print(f"   {quest.get_progress()}")
                print()
        
        input("Press Enter to continue...")
    
    def add_quest(self, quest: Quest):
        """Add a new quest"""
        self.quests.append(quest)
    
    def show_detailed_stats(self):
        """Show detailed character statistics"""
        self.clear_screen()
        print("\n=== CHARACTER STATISTICS ===\n")
        print(f"Name: {self.player.name}")
        print(f"Level: {self.player.level}")
        print(f"Experience: {self.player.experience}/{self.player.level * 100}")
        print(f"\nHealth: {self.player.health}/{self.player.max_health}")
        print(f"Base Attack: {self.player.attack}")
        print(f"Total Attack: {self.player.get_total_attack()}")
        print(f"Base Defense: {self.player.defense}")
        print(f"Total Defense: {self.player.get_total_defense()}")
        print(f"\nGold: {self.player.gold}")
        print(f"Items: {len(self.player.inventory)}")
        
        input("\nPress Enter to continue...")
    
    def rest(self):
        """Rest to restore health"""
        cost = 20
        if self.player.gold < cost:
            print(f"\nYou don't have enough gold to rest. (Need {cost} gold)")
            input("Press Enter to continue...")
            return
        
        if self.player.health == self.player.max_health:
            print("\nYou're already at full health!")
            input("Press Enter to continue...")
            return
        
        self.player.gold -= cost
        old_health = self.player.health
        self.player.health = self.player.max_health
        healed = self.player.health - old_health
        
        print(f"\nYou rest and restore {healed} health for {cost} gold.")
        input("Press Enter to continue...")
    
    def start_combat(self, enemy: Enemy):
        """Initiate combat with an enemy"""
        self.state = GameState.COMBAT
        print(f"\n⚔️  COMBAT START: {enemy.name} ⚔️\n")
        
        while enemy.is_alive() and self.player.is_alive():
            self.clear_screen()
            print(f"\n{'='*70}")
            print(f"⚔️  COMBAT: {self.player.name} vs {enemy.name}")
            print(f"{'='*70}")
            print(f"\nYour Health: {self.player.health}/{self.player.max_health}")
            print(f"{enemy.name} Health: {enemy.health}/{enemy.max_health}")
            print(f"\nYour Attack: {self.player.get_total_attack()} | Your Defense: {self.player.get_total_defense()}")
            print(f"Enemy Attack: {enemy.attack} | Enemy Defense: {enemy.defense}")
            print(f"\n{'='*70}")
            
            print("\n[a]ttack - Attack the enemy")
            print("[i]tem - Use an item")
            print("[r]un - Attempt to flee")
            
            choice = input("\nWhat will you do? ").strip().lower()
            
            if choice == 'a':
                self.combat_attack(enemy)
            elif choice == 'i':
                self.combat_use_item()
            elif choice == 'r':
                if self.combat_flee():
                    break
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
                continue
            
            # Enemy's turn
            if enemy.is_alive():
                damage = enemy.attack
                actual_damage = self.player.take_damage(damage)
                print(f"\n{enemy.name} attacks for {actual_damage} damage!")
                input("Press Enter to continue...")
        
        self.state = GameState.PLAYING
        
        if not enemy.is_alive():
            self.combat_victory(enemy)
    
    def combat_attack(self, enemy: Enemy):
        """Player attacks enemy"""
        damage = self.player.get_total_attack()
        # Add some randomness
        damage = random.randint(int(damage * 0.8), int(damage * 1.2))
        
        actual_damage = enemy.take_damage(damage)
        print(f"\nYou attack {enemy.name} for {actual_damage} damage!")
        input("Press Enter to continue...")
    
    def combat_use_item(self):
        """Use item during combat"""
        consumables = [item for item in self.player.inventory if item.usable]
        
        if not consumables:
            print("\nYou have no usable items!")
            input("Press Enter to continue...")
            return
        
        print("\nUsable items:")
        for i, item in enumerate(consumables, 1):
            print(f"  {i}. {item.name} - {item.description}")
        print("  [back] - Cancel")
        
        choice = input("\nChoose item: ").strip().lower()
        
        if choice == 'back':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(consumables):
                item = consumables[idx]
                result = item.use(self.player)
                print(f"\n{result}")
                if item.health_restore > 0:
                    self.player.remove_item(item)
                input("Press Enter to continue...")
            else:
                print("Invalid item number.")
                input("Press Enter to continue...")
        except ValueError:
            print("Invalid input.")
            input("Press Enter to continue...")
    
    def combat_flee(self) -> bool:
        """Attempt to flee from combat"""
        if random.random() < 0.5:
            print("\nYou successfully fled from combat!")
            input("Press Enter to continue...")
            return True
        else:
            print("\nYou failed to escape!")
            input("Press Enter to continue...")
            return False
    
    def combat_victory(self, enemy: Enemy):
        """Handle combat victory"""
        print(f"\n{'='*70}")
        print(f"⭐ VICTORY! You defeated {enemy.name}!")
        print(f"{'='*70}")
        
        # Rewards
        self.player.gain_experience(enemy.exp_reward)
        self.player.gold += enemy.gold_reward
        
        print(f"\nGained {enemy.exp_reward} experience and {enemy.gold_reward} gold!")
        
        # Loot
        if enemy.loot:
            print("\nLoot obtained:")
            for item in enemy.loot:
                # Random chance to drop item
                if random.random() < 0.6:
                    self.player.add_item(item)
                    print(f"  + {item.name}")
        
        # Check for level up
        if self.player.experience == 0:  # Just leveled up
            print(f"\n🎉 LEVEL UP! You are now level {self.player.level}!")
            print(f"Health +10, Attack +2, Defense +1")
        
        input("\nPress Enter to continue...")
    
    def show_help(self):
        """Display help information"""
        self.clear_screen()
        print("\n=== HELP ===\n")
        print("This is a text-based story RPG. Navigate through the world,")
        print("complete quests, fight enemies, and uncover the mystery of")
        print("the Shadow King.\n")
        print("Commands:")
        print("  move - Travel to connected locations")
        print("  inventory - View and use items")
        print("  quests - Check your active quests")
        print("  stats - View character statistics")
        print("  rest - Spend gold to restore health")
        print("  save - Save your current progress")
        print("  load - Load a previously saved game")
        print("\nCombat:")
        print("  attack - Attack the enemy")
        print("  item - Use a consumable item")
        print("  run - Try to flee (50% chance)")
        print("\nTips:")
        print("  - Explore all locations to find items and encounters")
        print("  - Complete quests for rewards")
        print("  - Level up by defeating enemies")
        print("  - Equip better weapons and armor when you find them")
        print("  - Save frequently!")
        
        input("\nPress Enter to continue...")
    
    def save_game(self):
        """Save the game state"""
        try:
            save_data = {
                "player": {
                    "name": self.player.name,
                    "health": self.player.health,
                    "max_health": self.player.max_health,
                    "attack": self.player.attack,
                    "defense": self.player.defense,
                    "level": self.player.level,
                    "experience": self.player.experience,
                    "gold": self.player.gold,
                    "inventory": [{"name": item.name} for item in self.player.inventory],
                    "equipped_weapon": self.player.equipped_weapon.name if self.player.equipped_weapon else None,
                    "equipped_armor": self.player.equipped_armor.name if self.player.equipped_armor else None,
                },
                "current_location": self.current_location.name,
                "chapter": self.chapter,
                "story_flags": self.story_flags,
                "visited_locations": [name for name, loc in self.locations.items() if loc.visited]
            }
            
            with open(self.save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print("\nGame saved successfully!")
            input("Press Enter to continue...")
        except Exception as e:
            print(f"\nError saving game: {e}")
            input("Press Enter to continue...")
    
    def load_game(self):
        """Load a saved game"""
        if not os.path.exists(self.save_file):
            print("\nNo saved game found!")
            input("Press Enter to continue...")
            return
        
        try:
            with open(self.save_file, 'r') as f:
                save_data = json.load(f)
            
            # Restore player
            player_data = save_data["player"]
            self.player = Character(
                name=player_data["name"],
                health=player_data["health"],
                max_health=player_data["max_health"],
                attack=player_data["attack"],
                defense=player_data["defense"],
                level=player_data["level"],
                experience=player_data["experience"],
                gold=player_data["gold"]
            )
            
            # Restore inventory
            for item_data in player_data["inventory"]:
                item_name_key = item_data["name"].lower().replace(" ", "_")
                if item_name_key in self.all_items:
                    self.player.add_item(self.all_items[item_name_key])
            
            # Restore equipment
            if player_data["equipped_weapon"]:
                weapon_key = player_data["equipped_weapon"].lower().replace(" ", "_")
                if weapon_key in self.all_items:
                    self.player.equipped_weapon = self.all_items[weapon_key]
            
            if player_data["equipped_armor"]:
                armor_key = player_data["equipped_armor"].lower().replace(" ", "_")
                if armor_key in self.all_items:
                    self.player.equipped_armor = self.all_items[armor_key]
            
            # Restore location
            for loc_name, loc in self.locations.items():
                if loc.name == save_data["current_location"]:
                    self.current_location = loc
                    break
            
            # Restore other data
            self.chapter = save_data.get("chapter", 1)
            self.story_flags = save_data.get("story_flags", {})
            
            # Mark visited locations
            for loc_key in save_data.get("visited_locations", []):
                if loc_key in self.locations:
                    self.locations[loc_key].visited = True
            
            self.state = GameState.PLAYING
            print("\nGame loaded successfully!")
            input("Press Enter to continue...")
            
        except Exception as e:
            print(f"\nError loading game: {e}")
            input("Press Enter to continue...")
    
    def game_over(self):
        """Handle game over"""
        self.clear_screen()
        print("\n" + "="*70)
        print("💀 GAME OVER 💀")
        print("="*70)
        print(f"\n{self.player.name} has fallen...")
        print("The darkness spreads across the realm.")
        print("Perhaps another hero will rise to take your place.")
        print("\n" + "="*70)
        input("\nPress Enter to exit...")
        sys.exit(0)
    
    def victory(self):
        """Handle game victory"""
        self.clear_screen()
        print("\n" + "="*70)
        print("🎉 VICTORY! 🎉")
        print("="*70)
        print(f"\nThe Shadow King falls, his dark power dissipating into nothingness.")
        print(f"\n{self.player.name}, you have saved the realm from eternal darkness!")
        print("\nThe villagers of Willowbrook will sing songs of your heroic deeds")
        print("for generations to come. Peace returns to the land.")
        print("\nYou are a true Champion of Light!")
        print("\n" + "="*70)
        print(f"\nFinal Stats:")
        print(f"  Level: {self.player.level}")
        print(f"  Total Gold: {self.player.gold}")
        print(f"  Enemies Defeated: Many")
        print("\nThank you for playing Chronicles of Destiny!")
        print("="*70)
        self.state = GameState.VICTORY
        input("\nPress Enter to exit...")
        sys.exit(0)
    
    def confirm_quit(self) -> bool:
        """Confirm quit action"""
        choice = input("\nAre you sure you want to quit? (y/n): ").strip().lower()
        return choice == 'y'
    
    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Print game banner"""
        banner = """
        ╔═══════════════════════════════════════════════════════════════════╗
        ║                                                                   ║
        ║           ⚔️  CHRONICLES OF DESTINY ⚔️                            ║
        ║                                                                   ║
        ║              A Complex Story-Based RPG Adventure                  ║
        ║                                                                   ║
        ╚═══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def main_menu(self):
        """Display main menu"""
        while True:
            self.clear_screen()
            self.print_banner()
            print("\n=== MAIN MENU ===\n")
            print("1. New Game")
            print("2. Load Game")
            print("3. Quit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.start_new_game()
            elif choice == '2':
                self.load_game()
                if self.state == GameState.PLAYING:
                    self.game_loop()
            elif choice == '3':
                print("\nThanks for playing!")
                sys.exit(0)
            else:
                print("\nInvalid choice!")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    game = StoryGame()
    game.main_menu()


if __name__ == "__main__":
    main()
