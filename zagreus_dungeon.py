#!/usr/bin/env python3
"""
Zagreus' Descent - A Dark Dungeon Crawler Story Game
Inspired by Fear and Hunger aesthetic and gameplay
"""

import sys
import random
import json
import os
from typing import Dict, List, Optional, Tuple, Any

# Game constants
DARKNESS_FAILURE_THRESHOLD = 30
FIND_CHANCE_WITH_LIGHT = 40
FIND_CHANCE_WITHOUT_LIGHT = 10
MAX_INPUT_LENGTH = 500
MAX_INPUT_RETRIES = 5

# Game state class
class GameState:
    def __init__(self):
        # Player stats
        self.health = 60
        self.max_health = 100
        self.stamina = 50
        self.max_stamina = 100
        self.strength = 5
        self.agility = 5
        self.mind = 5
        
        # Conditions
        self.hunger = 30  # 0-100, higher is worse
        self.wetness = 80  # starts wet from flood
        self.temperature = 40  # 0-100, 50 is neutral
        self.sanity = 70
        self.fear = 20  # 0-100, affects Harvester detection
        
        # Status effects
        self.status_effects = {
            "bleeding": 0,  # turns remaining
            "poisoned": 0,
            "burning": 0,
            "infected": 0,
            "stunned": 0,
            "blessed": 0,
            "cursed": 0,
            "hasted": 0,
            "slowed": 0
        }
        
        # Body parts
        self.left_arm = True
        self.right_arm = True
        self.left_leg = True
        self.right_leg = True
        self.left_eye = True
        self.right_eye = True
        
        # Inventory
        self.inventory = []
        self.max_inventory = 10  # Weight/space limit
        self.equipped = {
            "weapon": None,
            "light": None,
            "armor": None,
            "accessory": None,
            "offhand": None  # shield, secondary weapon, etc.
        }
        
        # Equipment durability
        self.equipment_durability = {
            "weapon": 100,
            "armor": 100,
            "light": 100
        }
        
        # Combat modifiers
        self.combat_bonus = {
            "damage": 0,
            "defense": 0,
            "accuracy": 0,
            "critical_chance": 0
        }
        
        # Story flags
        self.flags = set()
        self.location = "flooded_cell"
        self.turn_count = 0
        self.deaths = 0
        
        # Discovered paths
        self.visited_nodes = set()
        self.node_history = []  # Ordered list for tracking previous nodes

# AI Dungeon Master for dynamic responses
class DungeonMaster:
    def __init__(self, state: GameState):
        self.state = state
        
    def evaluate_action(self, action: str, context: Dict) -> Tuple[bool, str, Dict]:
        """
        Evaluate player's custom action in context
        Returns: (success, description, effects)
        """
        action_lower = action.lower()
        
        # Combat evaluation
        if context.get("in_combat"):
            return self._evaluate_combat(action_lower, context)
        
        # Exploration evaluation
        return self._evaluate_exploration(action_lower, context)
    
    def _evaluate_combat(self, action: str, context: Dict) -> Tuple[bool, str, Dict]:
        enemy = context.get("enemy", {})
        enemy_type = enemy.get("type", "unknown")
        enemy_health = context.get("enemy_health", 40)
        
        effects = {"damage_taken": 0, "damage_dealt": 0, "status": []}
        
        # Check for status effects affecting combat
        accuracy_mod = 0
        damage_mod = 0
        
        if self.state.status_effects["stunned"] > 0:
            return (False, "You're stunned and cannot act effectively this turn!", effects)
        
        if self.state.status_effects["poisoned"] > 0:
            effects["damage_taken"] += 3
            
        if self.state.status_effects["bleeding"] > 0:
            effects["damage_taken"] += 2
        
        if self.state.status_effects["hasted"] > 0:
            accuracy_mod += 15
            
        if self.state.status_effects["slowed"] > 0:
            accuracy_mod -= 15
        
        # Parse action intent - defensive actions
        if "dodge" in action or "evade" in action or "roll" in action:
            success_chance = self.state.agility * 10 + (50 if self.state.equipped["light"] else 0) + accuracy_mod
            success_chance -= 20 if not self.state.left_leg or not self.state.right_leg else 0
            success_chance -= 30 if self.state.wetness > 60 else 0  # slippery
            
            if random.randint(1, 100) < success_chance:
                return (True, "You successfully dodge the attack!", effects)
            else:
                effects["damage_taken"] = random.randint(10, 25)
                if self.state.equipped["armor"]:
                    effects["damage_taken"] = max(5, effects["damage_taken"] - 10)
                return (False, f"You fail to dodge and take {effects['damage_taken']} damage!", effects)
        
        if "block" in action or "parry" in action or "defend" in action:
            if not self.state.equipped["weapon"] and not self.state.equipped["offhand"]:
                effects["damage_taken"] = random.randint(15, 30)
                return (False, f"You have nothing to block with! Take {effects['damage_taken']} damage!", effects)
            
            block_chance = 60 + self.state.strength * 5 + accuracy_mod
            if random.randint(1, 100) < block_chance:
                effects["damage_taken"] = random.randint(2, 8)
                return (True, f"You block the attack! Only take {effects['damage_taken']} damage!", effects)
            else:
                effects["damage_taken"] = random.randint(12, 20)
                return (False, f"Your block fails! Take {effects['damage_taken']} damage!", effects)
        
        # Attack actions - targeting specific body parts
        weak_points = enemy.get("weaknesses", [])
        
        if any(word in action for word in ["eye", "eyes"]):
            if "eye" in weak_points or enemy_type == "rat" or enemy_type == "ghoul":
                damage = random.randint(20, 40) + self.state.strength + damage_mod
                if self.state.equipped["weapon"]:
                    damage += 15
                effects["damage_dealt"] = damage
                if random.randint(1, 100) > 70:
                    effects["status"].append("enemy_blinded")
                return (True, f"You strike the creature's eye! Critical hit for {damage} damage! It's blinded!", effects)
            else:
                hit_chance = 30 + self.state.agility * 3
                if random.randint(1, 100) < hit_chance:
                    damage = random.randint(10, 20) + self.state.strength
                    effects["damage_dealt"] = damage
                    return (True, f"You hit for {damage} damage, but eyes aren't its weak point.", effects)
                else:
                    effects["damage_taken"] = random.randint(5, 15)
                    return (False, f"The creature has no vulnerable eyes. It counters, dealing {effects['damage_taken']} damage!", effects)
        
        if any(word in action for word in ["head", "skull", "brain"]):
            hit_chance = 40 + self.state.agility * 5 + accuracy_mod
            if self.state.equipped["light"]:
                hit_chance += 20
            
            if random.randint(1, 100) < hit_chance:
                damage = random.randint(15, 30) + self.state.strength + damage_mod
                if self.state.equipped["weapon"]:
                    damage += 10
                effects["damage_dealt"] = damage
                if random.randint(1, 100) > 85:
                    effects["status"].append("enemy_stunned")
                    return (True, f"You bash the creature's head for {damage} damage! It's stunned!", effects)
                return (True, f"You bash the creature's head for {damage} damage!", effects)
            else:
                effects["damage_taken"] = random.randint(10, 20)
                return (False, f"You miss the head! The creature retaliates for {effects['damage_taken']} damage!", effects)
        
        if any(word in action for word in ["leg", "legs", "knee"]):
            if "legs" in weak_points:
                damage = random.randint(15, 25) + self.state.strength + damage_mod
                if self.state.equipped["weapon"]:
                    damage += 8
                effects["damage_dealt"] = damage
                effects["status"].append("enemy_slowed")
                return (True, f"You cripple its leg! {damage} damage and it's slowed!", effects)
            else:
                damage = random.randint(5, 15) + self.state.strength
                if self.state.equipped["weapon"]:
                    damage += 5
                effects["damage_dealt"] = damage
                return (True, f"You hit its leg for {damage} damage.", effects)
        
        if any(word in action for word in ["throat", "neck"]):
            hit_chance = 35 + self.state.agility * 4 + accuracy_mod
            if random.randint(1, 100) < hit_chance:
                damage = random.randint(25, 45) + self.state.strength + damage_mod
                if self.state.equipped["weapon"]:
                    damage += 20
                effects["damage_dealt"] = damage
                effects["status"].append("enemy_bleeding")
                return (True, f"CRITICAL! You slash its throat for {damage} damage! It's bleeding out!", effects)
            else:
                effects["damage_taken"] = random.randint(15, 25)
                return (False, f"You miss the critical strike! It savages you for {effects['damage_taken']} damage!", effects)
        
        # Fire attacks
        if "fire" in action or "burn" in action or "torch" in action:
            if self.state.equipped["light"] and "torch" in self.state.equipped["light"].lower():
                if "fire" in weak_points or enemy_type == "ghoul":
                    damage = random.randint(30, 50)
                    effects["damage_dealt"] = damage
                    effects["status"].append("enemy_burning")
                    return (True, f"You set it ablaze! {damage} damage! It's burning!", effects)
                else:
                    damage = random.randint(10, 20)
                    effects["damage_dealt"] = damage
                    return (True, f"You burn it for {damage} damage, but it's not very effective.", effects)
            else:
                return (False, "You have no fire source!", effects)
        
        # Tactical actions
        if "feint" in action or "fake" in action or "trick" in action:
            trick_chance = 40 + self.state.mind * 8
            if random.randint(1, 100) < trick_chance:
                effects["status"].append("enemy_open")
                return (True, "You successfully feint! The enemy is open for a follow-up attack!", effects)
            else:
                effects["damage_taken"] = random.randint(8, 16)
                return (False, f"Your feint fails! You're exposed! Take {effects['damage_taken']} damage!", effects)
        
        if "grapple" in action or "wrestle" in action or "grab" in action:
            if self.state.strength < 4:
                return (False, "You're not strong enough to grapple effectively!", effects)
            
            grapple_chance = 50 + self.state.strength * 10 - (20 if enemy_type in ["ghoul", "harvester"] else 0)
            if random.randint(1, 100) < grapple_chance:
                effects["status"].append("enemy_grappled")
                return (True, "You successfully grapple the creature! It's restrained!", effects)
            else:
                effects["damage_taken"] = random.randint(12, 22)
                return (False, f"The grapple fails! It breaks free and strikes you for {effects['damage_taken']} damage!", effects)
        
        # Generic attack
        weapon_bonus = 10 if self.state.equipped["weapon"] else 0
        light_bonus = 10 if self.state.equipped["light"] else -20
        
        # Critical hit chance
        crit_chance = 5 + self.state.agility + self.state.combat_bonus["critical_chance"]
        is_crit = random.randint(1, 100) <= crit_chance
        
        damage = max(1, random.randint(5, 15) + self.state.strength + weapon_bonus + light_bonus + damage_mod + self.state.combat_bonus["damage"])
        
        if is_crit:
            damage = int(damage * 2)
            effects["damage_dealt"] = damage
            effects["status"].append("critical_hit")
            return (True, f"CRITICAL HIT! You deal {damage} damage!", effects)
        else:
            effects["damage_dealt"] = damage
        
        # Counter attack chance
        counter_chance = 50 - self.state.agility * 3 - accuracy_mod
        if self.state.equipped["armor"]:
            counter_chance -= 15
            
        if random.randint(1, 100) < counter_chance:
            counter_damage = random.randint(8, 18)
            if self.state.equipped["armor"]:
                counter_damage = max(3, counter_damage - 8)
            effects["damage_taken"] = counter_damage
            return (True, f"You deal {damage} damage but take {counter_damage} in return!", effects)
        
        return (True, f"You strike for {damage} damage!", effects)
    
    def _evaluate_exploration(self, action: str, context: Dict) -> Tuple[bool, str, Dict]:
        effects = {}
        location = context.get("location", "unknown")
        
        # Stealth actions
        if "sneak" in action or "stealth" in action or "quiet" in action:
            stealth_chance = 40 + self.state.agility * 8
            stealth_chance -= 20 if self.state.wetness > 50 else 0  # wet = noisy
            stealth_chance -= 15 if self.state.equipped["armor"] else 0  # armor = noisy
            stealth_chance += 10 if not self.state.equipped["light"] else -10  # light gives away
            
            if random.randint(1, 100) < stealth_chance:
                return (True, "You move silently through the shadows, undetected.", effects)
            else:
                effects["detected"] = True
                return (False, "You make noise! Something has noticed you!", effects)
        
        # Light-dependent actions
        if "search" in action or "look" in action or "examine" in action:
            if not self.state.equipped["light"] and random.randint(1, 100) > DARKNESS_FAILURE_THRESHOLD:
                return (False, "It's too dark to see anything clearly. You fumble around blindly.", effects)
            
            if "search" in action:
                find_chance = FIND_CHANCE_WITH_LIGHT if self.state.equipped["light"] else FIND_CHANCE_WITHOUT_LIGHT
                find_chance += self.state.mind * 3  # perception
                
                if random.randint(1, 100) < find_chance:
                    effects["found_item"] = True
                    items = ["healing herbs", "rusty dagger", "torch", "dried food", "rope", "lockpick"]
                    effects["item_name"] = random.choice(items)
                    return (True, f"You find {effects['item_name']}!", effects)
                else:
                    return (False, "You search but find nothing of value.", effects)
        
        # Climbing/athletic actions
        if "climb" in action or "jump" in action or "leap" in action:
            if not self.state.left_arm or not self.state.right_arm:
                return (False, "You can't climb with your injured arms!", effects)
            
            if not self.state.left_leg or not self.state.right_leg:
                effects["difficulty"] = "very hard"
                
            success_chance = self.state.agility * 8 + self.state.strength * 5
            success_chance -= 20 if self.state.wetness > 60 else 0
            success_chance -= 15 if self.state.stamina < 30 else 0
            success_chance += 10 if self.state.equipped["rope"] else 0
            
            if random.randint(1, 100) < success_chance:
                effects["stamina_cost"] = 15
                return (True, "You successfully make the climb!", effects)
            else:
                effects["damage_taken"] = random.randint(10, 30)
                effects["stamina_cost"] = 10
                return (False, f"You fall! Taking {effects['damage_taken']} damage!", effects)
        
        # Swimming actions
        if "swim" in action or "dive" in action or "underwater" in action:
            swim_chance = 60 + self.state.stamina // 10
            swim_chance -= 20 if self.state.equipped["armor"] else 0
            swim_chance -= 30 if not self.state.left_arm or not self.state.right_arm else 0
            
            if random.randint(1, 100) < swim_chance:
                effects["stamina_cost"] = 20
                effects["wetness_increase"] = 20
                return (True, "You swim successfully through the water.", effects)
            else:
                effects["damage_taken"] = random.randint(5, 15)
                effects["stamina_cost"] = 25
                effects["wetness_increase"] = 30
                return (False, f"You struggle in the water! Taking {effects['damage_taken']} damage from exhaustion!", effects)
        
        # Persuasion/social actions
        if "persuade" in action or "convince" in action or "talk" in action or "negotiate" in action:
            persuasion_chance = 30 + self.state.mind * 7
            persuasion_chance += 15 if self.state.sanity > 70 else -15  # sanity affects speech
            
            if random.randint(1, 100) < persuasion_chance:
                return (True, "Your words seem to have an effect...", effects)
            else:
                return (False, "Your attempt to persuade fails to convince them.", effects)
        
        # Intelligence/puzzle actions
        if "solve" in action or "decipher" in action or "puzzle" in action or "read" in action:
            intelligence_chance = 30 + self.state.mind * 10
            intelligence_chance += 20 if self.state.equipped["light"] else -30
            intelligence_chance -= 20 if self.state.sanity < 50 else 0
            
            if random.randint(1, 100) < intelligence_chance:
                effects["puzzle_solved"] = True
                return (True, "You figure it out! The solution becomes clear.", effects)
            else:
                return (False, "The puzzle eludes you. You can't make sense of it.", effects)
        
        # Trap detection/disarming
        if "trap" in action or "disarm" in action or "disable" in action:
            trap_chance = 35 + self.state.agility * 6 + self.state.mind * 4
            trap_chance += 25 if "lockpick" in str(self.state.inventory) else 0
            
            if random.randint(1, 100) < trap_chance:
                return (True, "You successfully identify and disarm the trap!", effects)
            else:
                effects["damage_taken"] = random.randint(15, 35)
                return (False, f"You trigger the trap! Taking {effects['damage_taken']} damage!", effects)
        
        # Healing/medical actions
        if "heal" in action or "bandage" in action or "medicine" in action:
            if "healing herbs" in str(self.state.inventory) or "medical supplies" in str(self.state.inventory):
                effects["health_restored"] = random.randint(15, 30)
                effects["remove_item"] = "healing herbs"
                return (True, f"You treat your wounds, restoring {effects['health_restored']} health!", effects)
            else:
                effects["health_restored"] = random.randint(3, 8)
                return (True, f"You do your best with no supplies, restoring {effects['health_restored']} health.", effects)
        
        # Breaking objects
        if "break" in action or "smash" in action or "destroy" in action:
            break_chance = 50 + self.state.strength * 10
            break_chance += 20 if self.state.equipped["weapon"] else 0
            
            if random.randint(1, 100) < break_chance:
                effects["object_broken"] = True
                return (True, "You smash it apart!", effects)
            else:
                effects["damage_taken"] = random.randint(3, 10)
                return (False, f"It doesn't break! You hurt yourself for {effects['damage_taken']} damage!", effects)
        
        # Listening/perception
        if "listen" in action or "hear" in action:
            perception_chance = 40 + self.state.mind * 8
            perception_chance -= 30 if self.state.sanity < 40 else 0  # hallucinations
            
            if random.randint(1, 100) < perception_chance:
                effects["information"] = "You hear something important..."
                return (True, "You listen carefully and hear valuable information.", effects)
            else:
                return (False, "You hear only the ambient sounds of the dungeon.", effects)
        
        # Hiding
        if "hide" in action or "conceal" in action:
            hide_chance = 45 + self.state.agility * 7
            hide_chance -= 25 if self.state.equipped["light"] else 0
            hide_chance -= 15 if self.state.equipped["armor"] else 0
            
            if random.randint(1, 100) < hide_chance:
                effects["hidden"] = True
                return (True, "You find a hiding spot and conceal yourself.", effects)
            else:
                return (False, "There's nowhere to hide! You remain exposed!", effects)
        
        # Default
        return (True, "You attempt your action...", effects)

# Story nodes - the decision tree
class StoryNode:
    def __init__(self, node_id: str, description: str, choices: List[Dict], 
                 on_enter=None, combat=None):
        self.node_id = node_id
        self.description = description
        self.choices = choices  # List of {text, next_node, condition, effects}
        self.on_enter = on_enter  # Function to call when entering
        self.combat = combat  # Combat info if any

# Game engine
class ZagreusGame:
    def __init__(self):
        self.state = GameState()
        self.dm = DungeonMaster(self.state)
        self.nodes = {}
        self.current_node = None
        self._build_story_tree()
    
    def _build_story_tree(self):
        """Build the massive story tree"""
        
        # Continue adding more complex paths and scenarios
        self.nodes["listen_darkness"] = StoryNode(
            "listen_darkness",
            """You hold perfectly still, barely breathing. You listen intently.
The breathing is... wrong. Too deep. Too wet. Whatever it is, it's big.
You hear it shift its weight. Claws scrape on stone. It's moving—but not toward you.
It's circling. Hunting. It knows something is here but can't pinpoint you yet.""",
            [
                {"text": "Remain absolutely still", "next": "stay_frozen"},
                {"text": "Try to move away silently", "next": "silent_retreat"},
                {"text": "Feel for a weapon on the ground", "next": "feel_for_weapon"},
                {"text": "Make a sudden loud noise to scare it", "next": "scare_creature"},
                {"text": "Custom action", "next": "custom_dark_hunt"}
            ]
        )
        
        self.nodes["call_darkness"] = StoryNode(
            "call_darkness",
            """You call out: "Hello? Who's there?"

The breathing stops. Complete silence. For a moment, nothing.
Then a voice responds—human, but barely: "Leave... this place... while you can..."
The voice is hoarse, pained. Someone else is trapped down here.""",
            [
                {"text": "Ask who they are", "next": "ask_identity"},
                {"text": "Ask for help finding a way out", "next": "ask_help_escape"},
                {"text": "Move toward the voice", "next": "approach_voice"},
                {"text": "Move away from the voice—might be a trap", "next": "away_from_voice"},
                {"text": "Custom action", "next": "custom_voice_dark"}
            ]
        )
        
        self.nodes["away_from_sound"] = StoryNode(
            "away_from_sound",
            """You feel your way along the wall, moving away from the breathing.
Your hands find a passage—narrow but navigable. You slip into it.
The breathing sound fades behind you. You've avoided whatever it was.

The passage continues in darkness. You feel a breeze—air flow from somewhere ahead.""",
            [
                {"text": "Follow the breeze carefully", "next": "follow_breeze"},
                {"text": "Continue feeling along the wall", "next": "continue_in_dark"},
                {"text": "Rest against the wall briefly", "next": "rest_in_dark"},
                {"text": "Custom action", "next": "custom_dark_passage"}
            ]
        )
        
        self.nodes["toward_breathing"] = StoryNode(
            "toward_breathing",
            """You move toward the breathing sound. Foolish or brave—hard to say.
As you approach, you can smell it—rot, decay, and something chemical.
Your foot hits something soft. You reach down. It's a body. Fresh. Still warm.

The breathing is right above you. IT'S ON THE CEILING.""",
            [
                {"text": "Dive away immediately", "next": "dive_from_ceiling"},
                {"text": "Look up into the darkness", "next": "look_up_ceiling"},
                {"text": "Run blindly forward", "next": "blind_run"},
                {"text": "Play dead next to the corpse", "next": "play_dead_ceiling"},
                {"text": "Custom action", "next": "custom_ceiling_horror"}
            ]
        )
        
        self.nodes["curse_guard"] = StoryNode(
            "curse_guard",
            """You scream curses at him. "May the gods damn you! May your family suffer!
May you die alone and forgotten, you coward!"

The guard's face darkens with rage. "How dare you!" He picks up a rock.
"Die then, prisoner!" He hurls it at your head!""",
            [
                {"text": "Dodge underwater", "next": "dodge_rock"},
                {"text": "Catch the rock", "next": "catch_rock"},
                {"text": "Take the hit and glare at him", "next": "take_rock_hit"},
                {"text": "Beg for forgiveness", "next": "apologize_guard"},
                {"text": "Custom action", "next": "custom_angry_guard"}
            ]
        )
        
        self.nodes["silent_stare"] = StoryNode(
            "silent_stare",
            """You say nothing. You just stare at him with cold, hard eyes.
The guard shifts uncomfortably. Something in your gaze unsettles him.
"What? Stop looking at me like that!" But you don't break eye contact.

He wavers. "Fine! Rot down there for all I care!" He leaves abruptly.
But he drops something in his haste—a small metal file for his spear.
It falls into the water with a splash.""",
            [
                {"text": "Dive for the metal file", "next": "get_metal_file"},
                {"text": "Ignore it and search for other exit", "next": "search_exit_urgent"},
                {"text": "Custom action", "next": "custom_file_drop"}
            ]
        )
        
        self.nodes["bribe_guard_above"] = StoryNode(
            "bribe_guard_above",
            """You call up: "I have gold! Hidden! Pull me up and I'll tell you where!"

The guard laughs. "Gold? In a prisoner cell? Nice try."
"It's true! I hid it before they took me! Three hundred gold crowns!"

He pauses. Greed wars with duty on his face. "...Where?"
"Pull me up first!"
"Tell me first!"

You're at an impasse. The water rises to your chin.""",
            [
                {"text": "Make up a convincing location", "next": "lie_about_gold"},
                {"text": "Tell him the truth—there is no gold", "next": "admit_no_gold"},
                {"text": "Describe a trap location", "next": "trap_location"},
                {"text": "Custom action", "next": "custom_bribe"}
            ]
        )
        
        self.nodes["swing_to_ledge"] = StoryNode(
            "swing_to_ledge",
            """You release the rope and swing your body toward the ledge!
Your fingers catch the stone edge—barely! You hang there, scrambling for purchase.
The guard stomps on your fingers! "No! You don't deserve to live!"

Pain shoots through your hand but you don't let go.""",
            [
                {"text": "Grab his foot and pull him down", "next": "pull_guard_down"},
                {"text": "Endure and pull yourself up", "next": "endure_and_climb"},
                {"text": "Let go and drop to avoid being crushed", "next": "drop_from_ledge"},
                {"text": "Bite his ankle", "next": "bite_guard"},
                {"text": "Custom action", "next": "custom_ledge_struggle"}
            ]
        )
        
        self.nodes["rush_guard_guardroom"] = StoryNode(
            "rush_guard_guardroom",
            """You rush the guard before he can arm himself! You tackle him hard!
Both of you crash into the weapon rack. Swords and spears clatter to the floor.
You grapple, rolling across the ground. He's stronger than you expected.""",
            [
                {"text": "Grab a weapon from the fallen rack", "next": "grab_fallen_weapon"},
                {"text": "Choke him with your hands", "next": "choke_guard"},
                {"text": "Headbutt him", "next": "headbutt_guard"},
                {"text": "Roll away and create distance", "next": "create_distance"},
                {"text": "Custom action", "next": "custom_guardroom_fight"}
            ]
        )
        
        self.nodes["grab_weapon_rack"] = StoryNode(
            "grab_weapon_rack",
            """You dash to the weapon rack and grab a sword! It's heavier than you expected.
The guard also grabs a sword. You face each other, weapons drawn.
"I don't want to kill you," the guard says. "But I will if I must."

He's trained. You're not. This will be difficult.""",
            [
                {"text": "Attack first aggressively", "next": "attack_guard_first"},
                {"text": "Defend and wait for opening", "next": "defend_wait"},
                {"text": "Throw the sword at him and run", "next": "throw_sword_run"},
                {"text": "Try to talk him down mid-combat", "next": "talk_during_combat"},
                {"text": "Custom action", "next": "custom_sword_duel"}
            ]
        )
        
        self.nodes["talk_down_guard"] = StoryNode(
            "talk_down_guard",
            """You raise your hands. "Please. I'm not your enemy. The Overseer is.
He experiments on prisoners. He created the Harvester. How many good guards
has that thing killed? We're both victims here."

The guard hesitates. His sword lowers slightly. "The Harvester... it took my brother."
Grief crosses his face. "I've wanted to leave this cursed place for months."

You might be getting through to him.""",
            [
                {"text": "Offer to escape together", "next": "ally_guard"},
                {"text": "Press the emotional advantage", "next": "press_emotion"},
                {"text": "Attack while he's distracted by grief", "next": "attack_emotional_guard"},
                {"text": "Custom action", "next": "custom_guard_emotion"}
            ]
        )
        
        self.nodes["run_exit_guardroom"] = StoryNode(
            "run_exit_guardroom",
            """You run for the exit door! The guard lunges, trying to grab you!
His fingers brush your shoulder but you slip free! You burst through the door
into another corridor. You hear him chasing behind you.

You need to lose him—the corridor branches ahead.""",
            [
                {"text": "Take the left corridor", "next": "left_corridor"},
                {"text": "Take the right corridor", "next": "right_corridor"},
                {"text": "Find a place to hide", "next": "hide_from_guard"},
                {"text": "Turn and fight in the corridor", "next": "corridor_fight"},
                {"text": "Custom action", "next": "custom_corridor_chase"}
            ]
        )

        # Add more complex survival scenarios
        self.nodes["check_wounds_passage"] = StoryNode(
            "check_wounds_passage",
            """You examine yourself in the dim passage. You're in bad shape:
- Deep puncture wound in your side (bleeding slowly)
- Multiple cuts and scrapes (from the climb)
- Bruised ribs (probably cracked)
- Hypothermia symptoms (shivering, confusion)

You need treatment soon or infection will set in. You also need to warm up.""",
            [
                {"text": "Tear clothing to bandage wounds", "next": "bandage_wounds_cloth"},
                {"text": "Try to find herbs or medicine ahead", "next": "search_for_medicine"},
                {"text": "Move quickly to generate warmth", "next": "move_for_warmth"},
                {"text": "Rest despite the risk—you need recovery", "next": "risk_rest"},
                {"text": "Custom action", "next": "custom_medical"}
            ]
        )
        
        self.nodes["look_back_grate"] = StoryNode(
            "look_back_grate",
            """You look back through the grate. The cell is completely flooded now.
The water churns with the current of the drainage. If you'd waited even
thirty seconds longer, you'd be dead. The corpse floats past the opening.

You see something else too—an albino rat, swimming. It looks at you with
intelligent eyes, almost like it's judging your choices. Then it disappears.""",
            [
                {"text": "Close the grate and continue", "next": "drainage_tunnel"},
                {"text": "Leave it open in case you need to retreat", "next": "grate_open_continue"},
                {"text": "Custom action", "next": "custom_look_back"}
            ]
        )
        
        self.nodes["save_health_potion"] = StoryNode(
            "save_health_potion",
            """You pocket the health potion for when you really need it.
The knife is good quality—well-balanced for throwing or close combat.
The dried meat should keep you from starving for now.

Equipped: Steel knife
Inventory: Health potion, dried meat

The water reaches your chest. Time to find the way out!""",
            [
                {"text": "Search for exit with new confidence", "next": "find_drainage_grate"},
                {"text": "Eat the dried meat now for energy", "next": "eat_dried_meat_safe"},
                {"text": "Custom action", "next": "custom_equipped"}
            ]
        )
        
        self.nodes["knife_meat_only"] = StoryNode(
            "knife_meat_only",
            """You take the knife and meat, leaving the mysterious potion.
Better safe than sorry—that liquid could be anything.
The knife feels good in your hand. The meat is preserved well.

Equipped: Steel knife
Inventory: Dried meat

The water continues to rise. You need to move now!""",
            [
                {"text": "Search for exit", "next": "find_drainage_grate"},
                {"text": "Eat the meat for energy", "next": "eat_dried_meat_safe"},
                {"text": "Custom action", "next": "custom_knife_only"}
            ]
        )
        
        self.nodes["eat_dried_meat"] = StoryNode(
            "eat_dried_meat",
            """You eat the dried meat immediately. Your hunger was worse than you realized.
The meat is tough but flavorful—venison, properly cured.
You feel significantly better. Energy returns to your limbs.

Hunger reduced significantly! Stamina restored!

The water is still rising though. You need to escape!""",
            [
                {"text": "Search for exit with renewed energy", "next": "find_drainage_grate"},
                {"text": "Take the rest of the items and go", "next": "bundle_and_exit"},
                {"text": "Custom action", "next": "custom_after_eating"}
            ]
        )

        # Add more branching paths
        self.nodes["bundle_and_exit"] = StoryNode(
            "bundle_and_exit",
            """You take the entire bundle, wrapping it carefully to keep it dry.
No time to examine everything now—the water is at your shoulders!
You need to find the drainage grate or underwater passage immediately!""",
            [
                {"text": "Search frantically for the grate", "next": "find_drainage_grate"},
                {"text": "Dive underwater for passage", "next": "underwater_passage"},
                {"text": "Custom action", "next": "custom_bundle_urgent"}
            ]
        )
        
        self.nodes["continue_wall_search"] = StoryNode(
            "continue_wall_search",
            """You leave the bundle and continue searching. Bad choice.
The water is rising fast—past your shoulders, past your neck.
You find nothing else. The water reaches your mouth. Your chin. Your nose.

You have mere seconds to act!""",
            [
                {"text": "Go back for the bundle", "next": "rush_back_bundle"},
                {"text": "Dive for underwater passage", "next": "dive_last_chance"},
                {"text": "Scream for help one last time", "next": "final_scream"},
                {"text": "Custom action", "next": "custom_last_moment"}
            ]
        )

        # More custom AI nodes
        self.nodes["custom_iron_maiden"] = "CUSTOM_AI"
        self.nodes["custom_wound_care"] = "CUSTOM_AI"
        self.nodes["custom_journal"] = "CUSTOM_AI"
        self.nodes["custom_post_distract"] = "CUSTOM_AI"
        self.nodes["custom_chase"] = "CUSTOM_AI"
        self.nodes["custom_resist_cannibalism"] = "CUSTOM_AI"
        self.nodes["custom_meat_decision"] = "CUSTOM_AI"
        self.nodes["custom_insane_chamber"] = "CUSTOM_AI"
        self.nodes["custom_fight_madness"] = "CUSTOM_AI"
        self.nodes["custom_herbs"] = "CUSTOM_AI"
        self.nodes["custom_waterskin"] = "CUSTOM_AI"
        self.nodes["custom_note"] = "CUSTOM_AI"
        self.nodes["custom_sewer_entrance"] = "CUSTOM_AI"
        self.nodes["custom_lower_stairs"] = "CUSTOM_AI"
        self.nodes["custom_betrayal"] = "CUSTOM_AI"
        self.nodes["custom_guard_patience"] = "CUSTOM_AI"
        self.nodes["custom_dark_hunt"] = "CUSTOM_AI"
        self.nodes["custom_voice_dark"] = "CUSTOM_AI"
        self.nodes["custom_dark_passage"] = "CUSTOM_AI"
        self.nodes["custom_ceiling_horror"] = "CUSTOM_AI"
        self.nodes["custom_angry_guard"] = "CUSTOM_AI"
        self.nodes["custom_file_drop"] = "CUSTOM_AI"
        self.nodes["custom_bribe"] = "CUSTOM_AI"
        self.nodes["custom_ledge_struggle"] = "CUSTOM_AI"
        self.nodes["custom_guardroom_fight"] = "CUSTOM_AI"
        self.nodes["custom_sword_duel"] = "CUSTOM_AI"
        self.nodes["custom_guard_emotion"] = "CUSTOM_AI"
        self.nodes["custom_corridor_chase"] = "CUSTOM_AI"
        self.nodes["custom_medical"] = "CUSTOM_AI"
        self.nodes["custom_look_back"] = "CUSTOM_AI"
        self.nodes["custom_equipped"] = "CUSTOM_AI"
        self.nodes["custom_knife_only"] = "CUSTOM_AI"
        self.nodes["custom_after_eating"] = "CUSTOM_AI"
        self.nodes["custom_bundle_urgent"] = "CUSTOM_AI"
        self.nodes["custom_last_moment"] = "CUSTOM_AI"

        # Add more comprehensive death scenarios
        self.nodes["death_hypothermia"] = StoryNode(
            "death_hypothermia",
            """The cold finally takes you. Your wet clothes sapped all warmth from your body.
You stop shivering—not a good sign. Warmth spreads through you... a lie your body tells.
You lie down to rest. Just for a moment. You never wake up.

CAUSE OF DEATH: Hypothermia
SURVIVAL TIME: varies

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["death_wounds"] = StoryNode(
            "death_wounds",
            """You've accumulated too many injuries. Blood loss, pain, infection—your body
gives up. You collapse, unable to continue. The dungeon floor is cold against your cheek.
You close your eyes...

CAUSE OF DEATH: Multiple wounds and blood loss
SURVIVAL TIME: varies

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        # Add all the missing story nodes referenced in the game
        self.nodes["eat_dried_meat_safe"] = StoryNode(
            "eat_dried_meat_safe",
            """You eat the dried meat. It's properly preserved—no mold, no poison.
The nutrition helps significantly. You feel your strength returning.

Hunger reduced by 40! Health restored by 10!""",
            [
                {"text": "Continue searching for exit", "next": "find_drainage_grate"},
                {"text": "Feel energized to explore more", "next": "bundle_and_exit"},
                {"text": "Custom action", "next": "custom_after_safe_meat"}
            ]
        )
        
        self.nodes["surface_for_air"] = StoryNode(
            "surface_for_air",
            """You surface, gasping for air. Your lungs burn. The water continues to rise.
You've located the underwater passage but need to commit to swimming through it
before the cell fills completely.""",
            [
                {"text": "Take a deep breath and go for it", "next": "underwater_passage"},
                {"text": "Search for another way", "next": "panic_search"},
                {"text": "Custom action", "next": "custom_surface"}
            ]
        )
        
        self.nodes["feel_passage_entrance"] = StoryNode(
            "feel_passage_entrance",
            """You feel around the passage entrance underwater. It's narrow—very narrow.
You'll have to squeeze through, and there's no guarantee of air on the other side.
Your lungs are already burning. Decision time!""",
            [
                {"text": "Swim through immediately", "next": "underwater_passage"},
                {"text": "Surface for one more breath first", "next": "surface_for_air"},
                {"text": "Give up and find the grate instead", "next": "panic_search"},
                {"text": "Custom action", "next": "custom_passage_feel"}
            ]
        )
        
        self.nodes["rest_after_climb"] = StoryNode(
            "rest_after_climb",
            """You rest against the cold stone, catching your breath. The climb took everything
out of you. Your muscles shake with exhaustion. But you made it. You're out of the cell.

Stamina recovered partially.""",
            [
                {"text": "Continue when ready", "next": "drainage_tunnel"},
                {"text": "Check your wounds while resting", "next": "check_wounds_passage"},
                {"text": "Custom action", "next": "custom_rest_climb"}
            ]
        )
        
        self.nodes["assess_new_chamber"] = StoryNode(
            "assess_new_chamber",
            """You catch your breath and look around. You're in a circular chamber with a domed
ceiling. Phosphorescent moss provides dim light. Three passages lead out of this room.
There are ancient carvings on the walls—warnings, you think.""",
            [
                {"text": "Examine the carvings", "next": "examine_chamber_carvings"},
                {"text": "Take the left passage", "next": "left_chamber_passage"},
                {"text": "Take the center passage", "next": "center_chamber_passage"},
                {"text": "Take the right passage", "next": "right_chamber_passage"},
                {"text": "Rest here briefly", "next": "rest_chamber"},
                {"text": "Custom action", "next": "custom_chamber"}
            ]
        )
        
        self.nodes["crawl_from_water"] = StoryNode(
            "crawl_from_water",
            """You drag yourself out of the water onto a stone ledge. You're soaked, freezing,
and exhausted, but alive. You lie there for a moment, just breathing.
You made it through the underwater passage. Barely.""",
            [
                {"text": "Assess your surroundings", "next": "assess_new_chamber"},
                {"text": "Try to warm yourself", "next": "warm_yourself"},
                {"text": "Check inventory—did you lose anything?", "next": "check_inventory_swim"},
                {"text": "Custom action", "next": "custom_crawl_water"}
            ]
        )
        
        self.nodes["bash_lock_desperate"] = StoryNode(
            "bash_lock_desperate",
            """You bash the lock with your fists! Pain shoots through your hands!
The lock doesn't budge. The water is at your lips now. You're out of time!

This isn't working!""",
            [
                {"text": "Dive for underwater passage—last chance!", "next": "dive_last_chance"},
                {"text": "Keep bashing—it has to work!", "next": "death_drowning"},
                {"text": "Custom action", "next": "custom_bash_lock"}
            ]
        )
        
        self.nodes["rinse_wound_water"] = StoryNode(
            "rinse_wound_water",
            """You use water from the drainage tunnel to rinse your wound.
It's not clean water—this might make things worse. But you do your best.

Risk of infection increased slightly.""",
            [
                {"text": "Continue onward", "next": "drainage_tunnel"},
                {"text": "Try to bandage it as well", "next": "bind_wound_cloth"},
                {"text": "Custom action", "next": "custom_rinse"}
            ]
        )
        
        self.nodes["bind_wound_cloth"] = StoryNode(
            "bind_wound_cloth",
            """You tear strips from your already tattered clothes and bind your wound tightly.
It's not medical care, but it helps stop the bleeding.

Bleeding reduced. Health stabilized.""",
            [
                {"text": "Continue forward", "next": "drainage_tunnel"},
                {"text": "Rest briefly", "next": "rest_tunnel"},
                {"text": "Custom action", "next": "custom_bind"}
            ]
        )
        
        self.nodes["decipher_symbols"] = StoryNode(
            "decipher_symbols",
            """You study the symbols intensely. With time, patterns emerge:
"Seven seals protect the deep. Seven keys unlock the way.
The Harvester walks between walls. Fire blinds its many eyes.
The Overseer's throne sits above bones. His key opens all doors."

This is valuable information about the dungeon's layout and secrets.""",
            [
                {"text": "Memorize this and continue", "next": "torch_corridor"},
                {"text": "Look for more symbols", "next": "search_more_symbols"},
                {"text": "Custom action", "next": "custom_decipher"}
            ]
        )
        
        self.nodes["touch_symbols"] = StoryNode(
            "touch_symbols",
            """You trace the glowing symbols with your finger. They're warm!
As you touch them, they glow brighter. Suddenly, a hidden compartment opens
in the wall—you triggered a mechanism! Inside, you find a small glass vial
containing glowing blue liquid.""",
            [
                {"text": "Take the vial carefully", "next": "take_mysterious_vial"},
                {"text": "Leave it—could be cursed", "next": "leave_vial"},
                {"text": "Drink it immediately", "next": "drink_mystery_vial"},
                {"text": "Custom action", "next": "custom_vial"}
            ]
        )
        
        self.nodes["sneak_past_guard"] = StoryNode(
            "sneak_past_guard",
            """You move like a shadow, holding your breath. The guard snores softly.
Step by careful step, you edge past him. Your heart pounds.
You're almost past—then your foot bumps an empty bottle!

The guard stirs. His eyes begin to open!""",
            [
                {"text": "Freeze completely", "next": "freeze_guard"},
                {"text": "Run for it!", "next": "run_from_waking_guard"},
                {"text": "Attack him while he's vulnerable", "next": "attack_sleeping_guard"},
                {"text": "Hide quickly", "next": "hide_near_guard"},
                {"text": "Custom action", "next": "custom_guard_wake"}
            ]
        )
        
        self.nodes["side_passage_down"] = StoryNode(
            "side_passage_down",
            """You take the narrow side passage. It slopes steeply downward.
The walls close in. You have to turn sideways to fit through in places.
The passage eventually opens into a larger space—you smell something terrible.

You've entered what appears to be a mass grave. Bodies everywhere.""",
            [
                {"text": "Search the bodies for items", "next": "search_mass_grave"},
                {"text": "Leave immediately—this is cursed", "next": "flee_mass_grave"},
                {"text": "Say a prayer for the dead", "next": "pray_for_dead"},
                {"text": "Look for a way through", "next": "navigate_grave"},
                {"text": "Custom action", "next": "custom_mass_grave"}
            ]
        )
        
        self.nodes["observe_guard"] = StoryNode(
            "observe_guard",
            """You watch the guard carefully. He's older, tired. He keeps checking a locket
around his neck—a picture of someone. A daughter, perhaps?
He seems sad rather than cruel. Every few minutes, he glances nervously
at a doorway to his right. He's afraid of something.""",
            [
                {"text": "Approach him openly and talk", "next": "approach_guard_talk"},
                {"text": "Sneak past while he's distracted", "next": "sneak_past_guard"},
                {"text": "Investigate what he fears", "next": "investigate_door"},
                {"text": "Custom action", "next": "custom_observe"}
            ]
        )
        
        # Add more complete combat paths
        self.nodes["chain_second_strike"] = StoryNode(
            "chain_second_strike",
            """You swing the chain again with all your might! This time you catch it around
the ghoul's neck! You pull tight, choking it! The creature thrashes wildly,
claws raking the air. It's weakening!""",
            [
                {"text": "Keep choking until it stops moving", "next": "strangle_ghoul_death"},
                {"text": "Throw it against the wall", "next": "wall_slam_ghoul"},
                {"text": "Release and finish with torch", "next": "chain_to_torch_finish"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["switch_to_torch"] = StoryNode(
            "switch_to_torch",
            """You drop the chain and grab the torch with both hands! The ghoul lunges!
You thrust the flame into its face! It shrieks and recoils, but it's not done yet!""",
            [
                {"text": "Press the attack with fire", "next": "ghoul_eyes_torch"},
                {"text": "Create distance and reassess", "next": "create_combat_distance"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["strangle_ghoul"] = StoryNode(
            "strangle_ghoul",
            """You wrap the chain around the ghoul's throat and pull! It gags and claws
at the chain. You hold on with all your strength. It's a battle of endurance now.
Your muscles burn. The ghoul weakens. It's almost done!""",
            [
                {"text": "Hold on until it dies", "next": "strangle_ghoul_death"},
                {"text": "Let go and escape while it's weak", "next": "escape_weak_ghoul"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["retreat_from_ghoul"] = StoryNode(
            "retreat_from_ghoul",
            """You back away from the fight, creating distance. The ghoul circles you warily.
You have a moment to think. You're wounded. It's wounded. This could go either way.""",
            [
                {"text": "Continue fighting more carefully", "next": "fight_ghoul_torch"},
                {"text": "Run while you can", "next": "run_from_ghoul"},
                {"text": "Try to negotiate somehow", "next": "talk_to_ghoul"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["finish_burning_ghoul"] = StoryNode(
            "finish_burning_ghoul",
            """While it's on fire and panicking, you strike again! You bash it with the torch!
The creature falls, flames consuming its dry flesh. It twitches once, twice, then stills.

Victory! But you're hurt and tired. Combat is exhausting.""",
            [
                {"text": "Search the area", "next": "search_victim_body"},
                {"text": "Rest and recover", "next": "rest_after_ghoul"},
                {"text": "Move on quickly", "next": "past_ghoul_quick"},
                {"text": "Custom action", "next": "custom_post_combat"}
            ]
        )
        
        self.nodes["escape_burning_ghoul"] = StoryNode(
            "escape_burning_ghoul",
            """While it's distracted by the flames, you run! The ghoul's shrieks echo behind you
but you don't look back. You've escaped but didn't finish it. It might recover.""",
            [
                {"text": "Keep running", "next": "run_from_ghoul"},
                {"text": "Find a place to hide", "next": "hide_from_ghoul"},
                {"text": "Custom action", "next": "custom_escape_combat"}
            ]
        )

        # Add custom AI nodes for new paths
        self.nodes["custom_after_safe_meat"] = "CUSTOM_AI"
        self.nodes["custom_surface"] = "CUSTOM_AI"
        self.nodes["custom_passage_feel"] = "CUSTOM_AI"
        self.nodes["custom_rest_climb"] = "CUSTOM_AI"
        self.nodes["custom_chamber"] = "CUSTOM_AI"
        self.nodes["custom_crawl_water"] = "CUSTOM_AI"
        self.nodes["custom_bash_lock"] = "CUSTOM_AI"
        self.nodes["custom_rinse"] = "CUSTOM_AI"
        self.nodes["custom_bind"] = "CUSTOM_AI"
        self.nodes["custom_decipher"] = "CUSTOM_AI"
        self.nodes["custom_vial"] = "CUSTOM_AI"
        self.nodes["custom_guard_wake"] = "CUSTOM_AI"
        self.nodes["custom_mass_grave"] = "CUSTOM_AI"
        self.nodes["custom_observe"] = "CUSTOM_AI"
        self.nodes["custom_post_combat"] = "CUSTOM_AI"
        self.nodes["custom_escape_combat"] = "CUSTOM_AI"

        # Starting node - flooded cell
        self.nodes["start"] = StoryNode(
            "start",
            """You awaken in cold, murky water that reaches your chest. 
The last thing you remember is the betrayal—someone pushed you into this hole.
Your head throbs with pain, and you feel a deep wound on your side.
The water is rising slowly. The dungeon is pitch black, save for a faint 
phosphorescent glow from the moss on the walls.

Your body aches. You're wounded, cold, and wet.
The betrayer left you here to drown... but you survived. Barely.""",
            [
                {"text": "Search the murky water for anything useful", "next": "search_cell_water"},
                {"text": "Feel along the walls for a way out", "next": "feel_walls"},
                {"text": "Try to stand and conserve energy", "next": "stand_conserve"},
                {"text": "Dive underwater to search the bottom", "next": "dive_underwater"},
                {"text": "Scream for help", "next": "scream_help"},
                {"text": "Custom action", "next": "custom_start"}
            ]
        )
        
        self.nodes["search_cell_water"] = StoryNode(
            "search_cell_water",
            """You plunge your hands into the frigid water, feeling around blindly.
Your fingers brush against something... metal. A rusted shackle attached to a chain.
Then something else—soft, decaying. A corpse floats just beneath the surface.
The stench makes you gag.""",
            [
                {"text": "Search the corpse thoroughly", "next": "search_corpse"},
                {"text": "Take only the metal chain and leave", "next": "take_chain"},
                {"text": "Recoil in horror and back away", "next": "recoil_corpse"},
                {"text": "Use the chain as a weapon", "next": "chain_weapon"},
                {"text": "Custom action", "next": "custom_search_water"}
            ]
        )
        
        self.nodes["search_corpse"] = StoryNode(
            "search_corpse",
            """Fighting back nausea, you pat down the waterlogged corpse.
The body has been here for weeks, bloated and partially eaten by rats.
You find a small tinderbox—miraculously, it's in a sealed leather pouch.
You also find 3 copper coins and a moldy piece of bread.""",
            [
                {"text": "Take everything and continue", "next": "after_corpse_loot"},
                {"text": "Take only the tinderbox", "next": "tinderbox_only"},
                {"text": "Eat the moldy bread immediately", "next": "eat_moldy_bread"},
                {"text": "Custom action", "next": "custom_corpse"}
            ]
        )
        
        self.nodes["eat_moldy_bread"] = StoryNode(
            "eat_moldy_bread",
            """You're so hungry that you don't care about the mold.
You shove the soggy bread into your mouth.
It tastes like death and rot, but you swallow it anyway.

Minutes pass. Your stomach begins to cramp violently.
The mold was toxic—deadly poisonous fungus, not regular bread mold.
Your vision blurs as foam forms at your lips...""",
            [
                {"text": "[DEATH] Convulse and drown in the water", "next": "death_poison"}
            ]
        )
        
        self.nodes["tinderbox_only"] = StoryNode(
            "tinderbox_only",
            """You take only the tinderbox, leaving the questionable food and coins.
The tinderbox might save your life if you can dry it and find fuel.
The water continues to rise. You need to move now.""",
            [
                {"text": "Search for an exit urgently", "next": "search_exit_urgent"},
                {"text": "Dive underwater to find a way out", "next": "underwater_passage"}
            ]
        )
        
        self.nodes["death_poison"] = StoryNode(
            "death_poison",
            """You die from fungal poisoning, your body joining the other corpses in the flooded cell.

CAUSE OF DEATH: Ate poisonous moldy bread
SURVIVAL TIME: 3 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["take_chain"] = StoryNode(
            "take_chain",
            """You grab the chain and wrap it around your hand, avoiding the corpse.
The metal is cold and heavy. It could be used as a weapon.
The water continues to rise around you.""",
            [
                {"text": "Search for an exit", "next": "search_exit_urgent"},
                {"text": "Dive underwater", "next": "underwater_passage"}
            ]
        )
        
        self.nodes["recoil_corpse"] = StoryNode(
            "recoil_corpse",
            """You recoil from the corpse in horror. The stench, the decay—it's too much.
You back away, but in your panic, you slip on the slick floor.
Your head goes underwater. You come up sputtering and gasping.
The water is rising fast now. You need to act!""",
            [
                {"text": "Overcome your fear and search the corpse", "next": "search_corpse"},
                {"text": "Search for an exit immediately", "next": "search_exit_urgent"},
                {"text": "Dive to find another way", "next": "underwater_passage"}
            ]
        )
        
        self.nodes["chain_weapon"] = StoryNode(
            "chain_weapon",
            """You grab the chain and wrap it around your fist. It's heavy and rusty,
but it could work as a makeshift weapon. The links are solid.
You feel slightly more prepared, though still in mortal danger from the rising water.""",
            [
                {"text": "Use the chain to search for an exit", "next": "search_exit_urgent"},
                {"text": "Dive underwater with the chain", "next": "underwater_passage"}
            ]
        )
        
        self.nodes["after_corpse_loot"] = StoryNode(
            "after_corpse_loot",
            """With the tinderbox secure in your pocket, you pocket the coins too.
You now have a potential source of light—if you can find something to burn.
The water continues to rise. It's now at your shoulders.""",
            [
                {"text": "Search for a door or exit urgently", "next": "search_exit_urgent"},
                {"text": "Try to light the tinderbox to see better", "next": "light_tinderbox_wet"},
                {"text": "Climb onto the corpse to stay above water", "next": "climb_corpse"},
                {"text": "Custom action", "next": "custom_after_loot"}
            ]
        )
        
        self.nodes["search_exit_urgent"] = StoryNode(
            "search_exit_urgent",
            """You search frantically along the walls. The water is at your neck now!
Your hands find something—a drainage grate near the ceiling!""",
            [
                {"text": "Try to open the grate", "next": "find_drainage_grate"}
            ]
        )
        
        self.nodes["light_tinderbox_wet"] = StoryNode(
            "light_tinderbox_wet",
            """You try to strike the flint, but everything is soaked.
The water has rendered it temporarily useless.
You'll need to dry it first, or find dry materials.""",
            [
                {"text": "Give up and search for exit", "next": "search_exit_urgent"},
                {"text": "Try to dry it with your wet clothes (futile)", "next": "futile_dry"},
                {"text": "Keep it for later when you find dry area", "next": "search_exit_urgent"},
            ]
        )
        
        self.nodes["climb_corpse"] = StoryNode(
            "climb_corpse",
            """You try to use the floating corpse as a platform.
As you push down on it, the bloated body bursts open beneath your weight.
Putrid gases and decay wash over you. The smell is overwhelming.
You slip and go under the water, swallowing some of the contaminated fluid.

You surface, gagging and retching.""",
            [
                {"text": "Push forward despite the horror", "next": "contaminated_continue"},
                {"text": "Panic and thrash around", "next": "panic_thrash"},
                {"text": "Try to induce vomiting", "next": "induce_vomit"}
            ]
        )
        
        self.nodes["contaminated_continue"] = StoryNode(
            "contaminated_continue",
            """You steel your nerves and continue. You've swallowed corpse water,
but you might survive if you find help soon. You feel feverish already.
The water is at your neck now. You MUST find an exit immediately.""",
            [
                {"text": "Frantically search the walls", "next": "find_drainage_grate"},
                {"text": "Dive down to find underwater passage", "next": "underwater_passage"},
                {"text": "Float and conserve energy", "next": "death_drowning"}
            ]
        )
        
        self.nodes["find_drainage_grate"] = StoryNode(
            "find_drainage_grate",
            """Your hands find it—a drainage grate near the ceiling!
The water is flowing through it, meaning there's a passage beyond.
But the grate is locked with a rusted iron lock.
The water is at your chin now.""",
            [
                {"text": "Smash the lock with the chain", "next": "smash_lock_chain"},
                {"text": "Try to pick the lock", "next": "pick_lock_grate"},
                {"text": "Pull at the grate desperately", "next": "pull_grate"},
                {"text": "Take a deep breath and dive for another way", "next": "dive_last_chance"},
                {"text": "Custom action", "next": "custom_grate"}
            ]
        )
        
        self.nodes["smash_lock_chain"] = StoryNode(
            "smash_lock_chain",
            """You swing the chain with all your might at the rusted lock.
CLANG! CLANG! CLANG!
The third strike breaks it! The grate swings open.
You pull yourself through just as the water fills the cell completely.

You're in a narrow drainage tunnel, coughing up water.
It's still dark, but you're alive. The tunnel slopes upward ahead.""",
            [
                {"text": "Crawl forward up the tunnel", "next": "drainage_tunnel"},
                {"text": "Rest here briefly to catch your breath", "next": "rest_tunnel"},
                {"text": "Check your wounds", "next": "check_wounds_tunnel"}
            ]
        )
        
        self.nodes["drainage_tunnel"] = StoryNode(
            "drainage_tunnel",
            """You crawl through the filthy tunnel. Rats scatter as you advance.
The tunnel is barely wide enough for you to squeeze through.
After several minutes, you see a dim light ahead—not sunlight, but torchlight!

You emerge into a larger corridor. Stone walls, ancient and covered in strange symbols.
This is the dungeon proper. You hear distant sounds: dripping water, 
something scraping against stone, and... was that a scream?""",
            [
                {"text": "Head toward the torch light source", "next": "torch_corridor"},
                {"text": "Examine the symbols on the walls", "next": "examine_symbols"},
                {"text": "Move quietly and cautiously", "next": "stealth_corridor"},
                {"text": "Call out to see if anyone responds", "next": "call_out_corridor"},
                {"text": "Custom action", "next": "custom_corridor"}
            ]
        )
        
        self.nodes["torch_corridor"] = StoryNode(
            "torch_corridor",
            """You approach the source of light—a torch mounted in a sconce on the wall.
It's still burning, which means someone was here recently.
Next to it, you see two paths: one leading left into darkness, 
one leading right where you hear the sound of... chewing?""",
            [
                {"text": "Take the torch from the sconce", "next": "take_torch"},
                {"text": "Go left into the dark passage", "next": "dark_passage_left"},
                {"text": "Go right toward the chewing sound", "next": "chewing_sound_right"},
                {"text": "Investigate the chewing sound from a distance", "next": "investigate_chewing"},
                {"text": "Custom action", "next": "custom_torch_corridor"}
            ]
        )
        
        self.nodes["take_torch"] = StoryNode(
            "take_torch",
            """You grab the torch. Finally, you have light!
The flickering flame reveals the corridor more clearly.
Blood stains on the floor leading right. Scratch marks on the walls leading left.
You can now see your own condition: your clothes are torn, you have a deep gash
on your side still bleeding slowly, and you're shivering from the cold.""",
            [
                {"text": "Follow the blood trail right", "next": "blood_trail"},
                {"text": "Follow the scratch marks left", "next": "scratch_marks"},
                {"text": "Tend to your wound quickly", "next": "tend_wound_torch"},
                {"text": "Examine the walls more closely with the torch", "next": "examine_walls_torch"},
                {"text": "Custom action", "next": "custom_with_torch"}
            ]
        )
        
        self.nodes["blood_trail"] = StoryNode(
            "blood_trail",
            """You follow the blood trail. It leads to a gruesome scene:
A partially devoured body lies against the wall. Fresh. The flesh is still warm.
Standing over it is a creature—hunched, humanoid but wrong. Its skin is pale and
stretched tight over elongated bones. It turns to face you with milky white eyes.

A GHOUL. It hisses, blood dripping from its mouth.
It's between you and the passage beyond.""",
            [
                {"text": "Fight the ghoul with the torch", "next": "fight_ghoul_torch"},
                {"text": "Try to scare it away with fire", "next": "scare_ghoul_fire"},
                {"text": "Run back the way you came", "next": "run_from_ghoul"},
                {"text": "Throw something to distract it and slip past", "next": "distract_ghoul"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["fight_ghoul_torch"] = StoryNode(
            "fight_ghoul_torch",
            """You swing the torch at the ghoul. It lunges at you with inhuman speed!
[COMBAT INITIATED]""",
            [
                {"text": "Aim for its eyes with the torch", "next": "ghoul_eyes_torch"},
                {"text": "Bash it with the chain in your other hand", "next": "ghoul_chain_bash"},
                {"text": "Dodge and strike from the side", "next": "ghoul_dodge_strike"},
                {"text": "Kick it and create distance", "next": "ghoul_kick"},
                {"text": "Custom combat action", "next": "combat_ghoul"}
            ],
            combat={"enemy": {"type": "ghoul", "health": 40, "weaknesses": ["fire", "eyes"]}}
        )
        
        self.nodes["ghoul_eyes_torch"] = StoryNode(
            "ghoul_eyes_torch",
            """You thrust the burning torch directly at the ghoul's face!
The creature shrieks as the flame sears its sensitive eyes. It reels back,
clawing at its face. You press the advantage and strike again, setting its
dry skin ablaze. The ghoul flails in agony before collapsing.

Victory! But you're exhausted and hurt. You took some scratches in the fight.""",
            [
                {"text": "Search the ghoul's victim's body", "next": "search_victim_body"},
                {"text": "Move past quickly before more come", "next": "past_ghoul_quick"},
                {"text": "Rest and catch your breath", "next": "rest_after_ghoul"},
                {"text": "Eat some of the fresh corpse (you're starving)", "next": "cannibalism_option"}
            ]
        )
        
        self.nodes["cannibalism_option"] = StoryNode(
            "cannibalism_option",
            """You look at the fresh corpse. You're so hungry...
Your hands shake as you consider the unthinkable.
This is a line. Once crossed, there's no going back.""",
            [
                {"text": "Resist the urge and move on", "next": "resist_cannibalism"},
                {"text": "Give in to hunger and eat", "next": "embrace_cannibalism"},
                {"text": "Take some meat for later (maybe)", "next": "take_meat_later"}
            ]
        )
        
        self.nodes["embrace_cannibalism"] = StoryNode(
            "embrace_cannibalism",
            """You carve flesh from the corpse and force yourself to eat it raw.
It's disgusting. You vomit once, then eat again. Your hunger abates.
But something inside you has broken. Your sanity cracks.

You hear whispers now. The dungeon speaks to you.
The darkness feels... welcoming.""",
            [
                {"text": "Continue deeper into the dungeon", "next": "deeper_insane"},
                {"text": "Try to maintain your humanity", "next": "fight_insanity"}
            ]
        )
        
        self.nodes["search_victim_body"] = StoryNode(
            "search_victim_body",
            """You search the body. You find:
- A rusty dagger (better than nothing!)
- A waterskin (half full)
- A small pouch with herbs (might be medicinal?)
- A note, blood-stained and barely readable

The note says: "The Overseer's key is in the trophy room. Beware the Harvester."
""",
            [
                {"text": "Equip the dagger and continue", "next": "equip_dagger_continue"},
                {"text": "Use herbs to treat your wound", "next": "use_herbs_wound"},
                {"text": "Drink from the waterskin", "next": "drink_waterskin"},
                {"text": "Read the note more carefully", "next": "read_note_carefully"}
            ]
        )
        
        self.nodes["equip_dagger_continue"] = StoryNode(
            "equip_dagger_continue",
            """You arm yourself with the dagger and press forward.
The corridor ahead splits into three paths:
1. A wide hallway with ornate pillars - looks important
2. A narrow passage with a foul smell - sewers maybe?
3. A staircase going down - deeper into the dungeon

You hear footsteps echoing from the wide hallway.
A gurgling sound from the narrow passage.
Silence from the stairs.""",
            [
                {"text": "Take the wide hallway toward the footsteps", "next": "wide_hallway"},
                {"text": "Brave the narrow, foul passage", "next": "sewer_passage"},
                {"text": "Descend the stairs", "next": "descend_stairs"},
                {"text": "Hide and observe first", "next": "hide_observe"},
                {"text": "Custom action", "next": "custom_three_paths"}
            ]
        )
        
        self.nodes["wide_hallway"] = StoryNode(
            "wide_hallway",
            """You enter the wide hallway. The footsteps stop.
Before you stands a GUARD—armored, armed with a spear, and alert.
He sees you immediately. His eyes widen.

"Another prisoner? How did you escape your cell?"
He levels his spear at you. "Stay where you are!"

He seems... nervous. Maybe he can be reasoned with?""",
            [
                {"text": "Try to talk your way out", "next": "talk_guard"},
                {"text": "Attack him while he's talking", "next": "attack_guard"},
                {"text": "Surrender", "next": "surrender_guard"},
                {"text": "Run back and take another path", "next": "run_from_guard"},
                {"text": "Custom action", "next": "custom_guard_encounter"}
            ]
        )
        
        self.nodes["talk_guard"] = StoryNode(
            "talk_guard",
            """You raise your hands slowly. "I'm not a prisoner. I was betrayed and left to die.
I'm Zagreus. I have no quarrel with you."

The guard hesitates. "Zagreus? I heard that name... You're supposed to be dead.
They said you were drowned in the punishment cells."

He lowers his spear slightly. "Look, I don't care about the politics upstairs.
But if the Overseer finds you alive, he'll have my head. I can't let you pass."

He seems conflicted.""",
            [
                {"text": "Offer him the copper coins to look the other way", "next": "bribe_guard"},
                {"text": "Tell him you'll go quietly back", "next": "lie_to_guard"},
                {"text": "Appeal to his humanity", "next": "appeal_guard"},
                {"text": "Attack while he's distracted", "next": "attack_distracted_guard"},
                {"text": "Custom action", "next": "custom_guard_talk"}
            ]
        )
        
        self.nodes["bribe_guard"] = StoryNode(
            "bribe_guard",
            """You offer him the 3 copper coins. "Just look the other way. You never saw me."

He laughs bitterly. "Three coppers? That's your life's worth?"
But he takes them anyway. "Fine. But go the other way. The trophy room
is that way anyway—Overseer's quarters. Go through the sewers or the lower levels.
And if anyone asks, I never saw you."

He steps aside.""",
            [
                {"text": "Thank him and head to the sewer passage", "next": "sewer_passage_after_guard"},
                {"text": "Thank him and take the stairs down", "next": "stairs_after_guard"},
                {"text": "Stab him while his guard is down", "next": "betray_guard"},
                {"text": "Ask him about the Harvester", "next": "ask_about_harvester"}
            ]
        )
        
        self.nodes["ask_about_harvester"] = StoryNode(
            "ask_about_harvester",
            """The guard's face goes pale. "The Harvester? You've heard of it then.
It's the Overseer's pet. A thing. Not human, not animal. It collects...
parts. Limbs, organs, eyes. Don't let it catch you alone.
It moves through the walls. You'll hear it before you see it—a wet dragging sound."

He shudders. "Now go. Before I change my mind."
""",
            [
                {"text": "Head to the sewer passage", "next": "sewer_passage_after_guard"},
                {"text": "Take the stairs down", "next": "stairs_after_guard"},
                {"text": "Ask more questions", "next": "guard_impatient"}
            ]
        )
        
        # Add many more nodes for different paths...
        self.nodes["sewer_passage_after_guard"] = StoryNode(
            "sewer_passage_after_guard",
            """You enter the sewer passage. The smell is overwhelming—waste, rot, and something
chemical. The walls are slick with moisture. Your torch reveals rats scurrying away.
The passage narrows. You have to crouch. Then crawl.

Suddenly, the floor gives way beneath you!""",
            [
                {"text": "Grab onto something!", "next": "grab_sewer_fall"},
                {"text": "Drop the torch and use both hands", "next": "drop_torch_fall"},
                {"text": "Let yourself fall and roll", "next": "fall_and_roll"},
                {"text": "Custom action", "next": "custom_sewer_fall"}
            ]
        )
        
        self.nodes["grab_sewer_fall"] = StoryNode(
            "grab_sewer_fall",
            """You grab a pipe on the wall! The torch falls from your other hand, 
tumbling into the darkness below. You hear it splash into water far below.
You're hanging by one arm in complete darkness now.
Your wounded side screams in pain. You're losing your grip...""",
            [
                {"text": "Pull yourself up", "next": "pull_up_sewer"},
                {"text": "Drop down carefully", "next": "drop_into_sewer"},
                {"text": "Call for help", "next": "call_help_sewer"},
                {"text": "Custom action", "next": "custom_hanging"}
            ]
        )
        
        self.nodes["pull_up_sewer"] = StoryNode(
            "pull_up_sewer",
            """You summon your remaining strength and pull yourself up.
Your muscles burn. Your wound reopens, blood flowing freely.
But you make it! You're back on solid ground, but in complete darkness now.
Your torch is gone.

You hear something moving ahead in the darkness. Heavy breathing.
Not human.""",
            [
                {"text": "Feel your way forward slowly", "next": "feel_forward_dark"},
                {"text": "Stay perfectly still and quiet", "next": "stay_still_dark"},
                {"text": "Back away carefully", "next": "back_away_dark"},
                {"text": "Use tinderbox to make light", "next": "use_tinderbox_dark"},
                {"text": "Custom action", "next": "custom_dark_sewer"}
            ]
        )
        
        # Add path for deep exploration
        self.nodes["descend_stairs"] = StoryNode(
            "descend_stairs",
            """You descend the stone stairs. They spiral down and down.
After what feels like hundreds of steps, you reach a landing.
Before you is a massive iron door with strange symbols etched into it.
The symbols seem to move in the torchlight—an optical illusion?

There's a mechanism: three rotating wheels with symbols. A lock puzzle.
Next to it, written in blood: "Truth, Pain, Void"
""",
            [
                {"text": "Try to solve the puzzle", "next": "solve_door_puzzle"},
                {"text": "Try to force the door open", "next": "force_iron_door"},
                {"text": "Examine the symbols more carefully", "next": "examine_door_symbols"},
                {"text": "Go back up and try another path", "next": "back_up_stairs"},
                {"text": "Custom action", "next": "custom_iron_door"}
            ]
        )
        
        # Victory paths
        self.nodes["trophy_room_entrance"] = StoryNode(
            "trophy_room_entrance",
            """After navigating through countless horrors, you stand before the trophy room.
The door is ornate, made of dark wood with gold inlays.
You can hear someone inside—talking to themselves.

"Yes, yes, another specimen for the collection..."

The Overseer. The one who orchestrated your betrayal and imprisonment.""",
            [
                {"text": "Burst in and confront him", "next": "confront_overseer"},
                {"text": "Sneak in quietly", "next": "sneak_trophy_room"},
                {"text": "Wait and listen more", "next": "listen_overseer"},
                {"text": "Custom action", "next": "custom_trophy_room"}
            ]
        )
        
        # Multiple endings
        self.nodes["ending_escape_sewers"] = StoryNode(
            "ending_escape_sewers",
            """You crawl through the final sewer pipe and emerge into the river outside.
The moonlight has never looked so beautiful. You're alive.
But you're broken—mentally and physically scarred by the dungeon.

You escaped, but at what cost? Your wounds may never fully heal.
The memories will haunt you forever.

ENDING 8/100: BROKEN ESCAPE
You survived, but you'll never be whole again.

[GAME OVER - Time survived: 14 minutes]""",
            [{"text": "Play again?", "next": "restart"}]
        )
        
        self.nodes["ending_kill_overseer"] = StoryNode(
            "ending_kill_overseer",
            """You stand over the Overseer's body, his key in your hand.
The dungeon's exit is now open to you. But you've become something else
in this darkness. A killer. A survivor at any cost.

As you step out into freedom, you wonder: did you escape the dungeon,
or did it escape with you?

ENDING 7/100: DARK FREEDOM
You are free, but darkness lives in your heart now.

[GAME OVER - Time survived: 15 minutes]""",
            [{"text": "Play again?", "next": "restart"}]
        )
        
        # Death scenarios
        self.nodes["death_drowning"] = StoryNode(
            "death_drowning",
            """The water fills your mouth and lungs. You tried to float, to conserve energy,
but the water rose too fast. Your last thought is of your betrayer, smiling.

CAUSE OF DEATH: Drowned in flooded cell
SURVIVAL TIME: 2 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["death_harvester"] = StoryNode(
            "death_harvester",
            """You hear the wet dragging sound growing closer. Then you see it.
The Harvester is a nightmare made flesh—a collection of stolen body parts,
sewn together in a mockery of human form. Too many arms. Too many eyes.
All of them taken from previous victims.

It moves faster than should be possible. You try to run but—

It takes your eyes first. You scream. Then your legs.
Then everything goes dark.

Your parts will become part of the collection.

CAUSE OF DEATH: Harvested
SURVIVAL TIME: 8 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        # Combat and custom action nodes
        self.nodes["combat_ghoul"] = "COMBAT_AI"  # Special marker for AI combat
        self.nodes["custom_start"] = "CUSTOM_AI"
        self.nodes["custom_search_water"] = "CUSTOM_AI"
        self.nodes["custom_corpse"] = "CUSTOM_AI"
        self.nodes["custom_after_loot"] = "CUSTOM_AI"
        self.nodes["custom_grate"] = "CUSTOM_AI"
        self.nodes["custom_corridor"] = "CUSTOM_AI"
        self.nodes["custom_torch_corridor"] = "CUSTOM_AI"
        self.nodes["custom_with_torch"] = "CUSTOM_AI"
        self.nodes["custom_guard_encounter"] = "CUSTOM_AI"
        self.nodes["custom_guard_talk"] = "CUSTOM_AI"
        self.nodes["custom_sewer_fall"] = "CUSTOM_AI"
        self.nodes["custom_hanging"] = "CUSTOM_AI"
        self.nodes["custom_dark_sewer"] = "CUSTOM_AI"
        self.nodes["custom_iron_door"] = "CUSTOM_AI"
        self.nodes["custom_trophy_room"] = "CUSTOM_AI"
        
        # Add many more nodes to reach hundreds of paths and deaths...
        # For brevity, I'll add a few more key ones
        
        self.nodes["death_starvation"] = StoryNode(
            "death_starvation",
            """Your hunger finally claims you. You collapse against the cold stone.
Your body has nothing left. You tried to survive, but the dungeon
doesn't care about your will to live.

CAUSE OF DEATH: Starvation
SURVIVAL TIME: varies

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["death_infection"] = StoryNode(
            "death_infection",
            """The wound on your side has festered. Infection spreads through your body.
Fever consumes you. You hallucinate, seeing things that aren't there.
Eventually, you can't tell reality from nightmare. Then you stop caring.

CAUSE OF DEATH: Infected wound
SURVIVAL TIME: varies

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        # Add missing nodes that are referenced but not defined
        self.nodes["feel_walls"] = StoryNode(
            "feel_walls",
            """You press your hands against the cold, slimy stone walls, feeling desperately
for any crack, ledge, or opening. Your fingers trace ancient carvings—symbols you 
don't recognize. Then you feel it: a small recess, almost like a handhold.
Above it, what feels like another. Someone carved climbing holds into the wall!""",
            [
                {"text": "Attempt to climb out of the rising water", "next": "climb_wall_holds"},
                {"text": "Feel further along the wall for something else", "next": "continue_feeling_wall"},
                {"text": "Give up and search the water instead", "next": "search_cell_water"},
                {"text": "Custom action", "next": "custom_feel_walls"}
            ]
        )
        
        self.nodes["climb_wall_holds"] = StoryNode(
            "climb_wall_holds",
            """You grip the carved holds and pull yourself up out of the water.
Your wounded side screams in protest, but fear drives you upward.
Hand over hand, you climb in complete darkness. The holds are slippery with algae.
Suddenly, your hand slips! You're dangling by one arm, twelve feet above the water.""",
            [
                {"text": "Pull yourself back up with sheer willpower", "next": "successful_climb"},
                {"text": "Drop back into the water safely", "next": "back_to_water"},
                {"text": "Try to swing to grab another hold", "next": "swing_for_hold"},
                {"text": "Custom action", "next": "custom_climb"}
            ]
        )
        
        self.nodes["successful_climb"] = StoryNode(
            "successful_climb",
            """With a desperate surge of strength, you pull yourself up.
You find the next hold, and the next. Finally, your head bumps against something—
a grate! You push it open and haul yourself through into a narrow passage.
You collapse, gasping and shaking. Behind you, water pours through the opening.
You made it out, but barely. The passage ahead is dark and cramped.""",
            [
                {"text": "Crawl forward immediately", "next": "drainage_tunnel"},
                {"text": "Rest and examine your wounds", "next": "check_wounds_passage"},
                {"text": "Look back through the grate", "next": "look_back_grate"},
                {"text": "Custom action", "next": "custom_after_climb"}
            ]
        )
        
        self.nodes["continue_feeling_wall"] = StoryNode(
            "continue_feeling_wall",
            """You continue feeling along the wall, ignoring the climbing holds.
Further along, your hand finds something else—a small alcove.
Inside it, you feel fabric. A bundle of some kind, wrapped in oilcloth.
It's been placed here deliberately, hidden from casual inspection.""",
            [
                {"text": "Unwrap the bundle carefully", "next": "unwrap_hidden_bundle"},
                {"text": "Take it and search for an exit first", "next": "bundle_and_exit"},
                {"text": "Leave it and keep searching", "next": "continue_wall_search"},
                {"text": "Custom action", "next": "custom_bundle"}
            ]
        )
        
        self.nodes["unwrap_hidden_bundle"] = StoryNode(
            "unwrap_hidden_bundle",
            """You unwrap the oilcloth bundle. Inside, you find:
- A pristine steel knife, freshly oiled and sharp
- A vial of red liquid (labeled "Health" in rough script)
- A tightly wrapped piece of dried meat
- A note: "For those who search—there is always hope. -M"

Someone hid this for escaped prisoners. How many others tried before you?""",
            [
                {"text": "Take everything and drink the health potion", "next": "drink_health_potion"},
                {"text": "Take everything but save the potion", "next": "save_health_potion"},
                {"text": "Take only the knife and meat", "next": "knife_meat_only"},
                {"text": "Eat the dried meat immediately", "next": "eat_dried_meat"},
                {"text": "Custom action", "next": "custom_hidden_items"}
            ]
        )
        
        self.nodes["drink_health_potion"] = StoryNode(
            "drink_health_potion",
            """You uncork the vial and drink. The liquid burns going down, but warmth
spreads through your body. Your wound knits slightly—not completely, but enough
to stop the bleeding. You feel stronger, more alert. Health restored significantly!

The water is at your shoulders now. Time to move!""",
            [
                {"text": "Search for exit with renewed vigor", "next": "find_drainage_grate"},
                {"text": "Dive underwater to find a way out", "next": "underwater_passage"},
                {"text": "Custom action", "next": "custom_after_potion"}
            ]
        )
        
        self.nodes["stand_conserve"] = StoryNode(
            "stand_conserve",
            """You stand still, trying to conserve your energy and warmth.
The cold water saps your strength with every passing second.
You shiver uncontrollably. Your wound throbs with each heartbeat.
The water rises past your waist... your chest... your neck...

You realize this was a mistake. You need to act NOW!""",
            [
                {"text": "Frantically search for an exit", "next": "panic_search"},
                {"text": "Dive down to find underwater passage", "next": "underwater_passage"},
                {"text": "Call for help desperately", "next": "scream_help"},
                {"text": "Custom action", "next": "custom_panic"}
            ]
        )
        
        self.nodes["panic_search"] = StoryNode(
            "panic_search",
            """You thrash through the water, hands scrambling against the walls.
Your panic makes you clumsy. You slip, go under, come up choking.
The water is at your chin. In your frantic search, your hand finds—
a drainage grate near the ceiling! The water flows through it!""",
            [
                {"text": "Try to open it desperately", "next": "find_drainage_grate"},
                {"text": "Take a deep breath and dive for another way", "next": "underwater_passage"},
                {"text": "Custom action", "next": "custom_grate_panic"}
            ]
        )
        
        self.nodes["dive_underwater"] = StoryNode(
            "dive_underwater",
            """You take a deep breath and plunge beneath the murky water.
In the absolute darkness, you feel your way along the bottom.
Your lungs begin to burn. You feel stone, slime, and then—
a current! Water is being pulled somewhere. An underwater passage!""",
            [
                {"text": "Follow the current through the passage", "next": "underwater_passage"},
                {"text": "Surface for air first", "next": "surface_for_air"},
                {"text": "Feel around the passage entrance", "next": "feel_passage_entrance"},
                {"text": "Custom action", "next": "custom_underwater"}
            ]
        )
        
        self.nodes["underwater_passage"] = StoryNode(
            "underwater_passage",
            """You swim into the underwater passage. The current pulls you along.
Your lungs scream for air. The passage is narrow—you scrape against the sides.
Just when you think you'll drown, your head breaks the surface!

You gasp and cough, pulling yourself up onto a stone ledge. You're in a larger
chamber now, completely dark. Water drips from stalactites above. You hear... 
something moving in the darkness. Breathing that isn't yours.""",
            [
                {"text": "Stay perfectly still and listen", "next": "listen_darkness"},
                {"text": "Call out to whatever is there", "next": "call_darkness"},
                {"text": "Feel your way along the wall away from the sound", "next": "away_from_sound"},
                {"text": "Move toward the breathing sound", "next": "toward_breathing"},
                {"text": "Custom action", "next": "custom_dark_chamber"}
            ]
        )
        
        self.nodes["scream_help"] = StoryNode(
            "scream_help",
            """You scream at the top of your lungs. "HELP! SOMEONE HELP ME!"
Your voice echoes off the stone walls, but no reply comes.
Wait... you hear footsteps above. Someone is coming!

A grating sound—metal on stone. A voice from above, raspy and cruel:
"Well, well. Still alive down there, are we? You're tougher than you look, Zagreus."

A torch appears at the opening above. You see a face—one of the guards.
He sneers down at you.""",
            [
                {"text": "Beg for mercy", "next": "beg_guard_mercy"},
                {"text": "Offer him money to help", "next": "bribe_guard_above"},
                {"text": "Curse him and his family", "next": "curse_guard"},
                {"text": "Stay silent and stare", "next": "silent_stare"},
                {"text": "Custom action", "next": "custom_guard_above"}
            ]
        )
        
        self.nodes["beg_guard_mercy"] = StoryNode(
            "beg_guard_mercy",
            """You beg for your life. "Please! I don't deserve this! Pull me up!"

The guard laughs. "Deserve? You murdered Lord Theron's daughter, or so they say.
Whether you did or not doesn't matter. You made enemies of powerful people."

He spits into the water. "But... I'm not without mercy. Catch!"

He throws down a rope. But it's too short—it dangles three feet above your reach.
He laughs harder. "Oops! My mistake!"

The water is rising faster now.""",
            [
                {"text": "Jump for the rope", "next": "jump_for_rope"},
                {"text": "Scream curses at him", "next": "curse_cruel_guard"},
                {"text": "Ignore him and search for another way", "next": "search_exit_urgent"},
                {"text": "Custom action", "next": "custom_rope_taunt"}
            ]
        )
        
        self.nodes["jump_for_rope"] = StoryNode(
            "jump_for_rope",
            """You jump with all your might, fingers grasping for the rope!
You miss it by inches. You try again. And again.
The guard watches, amused. "Dance, prisoner, dance!"

On your fourth jump, your fingers brush the rope—and you grab it!
You pull yourself up, hand over hand. The guard's eyes widen.
"No! You weren't supposed to—" He tries to pull the rope back up.

Too late. You're already climbing. He can't pull you and the rope up together.""",
            [
                {"text": "Climb faster before he cuts the rope", "next": "climb_rope_fast"},
                {"text": "Try to swing to grab the ledge", "next": "swing_to_ledge"},
                {"text": "Custom action", "next": "custom_rope_climb"}
            ]
        )
        
        self.nodes["climb_rope_fast"] = StoryNode(
            "climb_rope_fast",
            """You climb with desperate speed. The guard fumbles for his knife to cut the rope.
You're almost there! He starts sawing at the rope—
You lunge for the ledge! Your hands catch the stone edge just as the rope gives way.

The guard stumbles back, shocked. You haul yourself up and over.
You're in a guardroom—small, with a table, chairs, and weapon rack.
The guard backs toward the weapon rack, reaching for a sword.""",
            [
                {"text": "Rush him before he gets the sword", "next": "rush_guard_guardroom"},
                {"text": "Grab a weapon from the rack yourself", "next": "grab_weapon_rack"},
                {"text": "Try to talk him down", "next": "talk_down_guard"},
                {"text": "Run for the exit door", "next": "run_exit_guardroom"},
                {"text": "Custom action", "next": "custom_guardroom"}
            ]
        )

        # Add more missing nodes
        self.nodes["back_to_water"] = StoryNode(
            "back_to_water",
            """You let go and drop back into the water with a splash.
Better to be safe than fall from higher up.
The water is even higher now—it's at your shoulders.
You need to find another way out, quickly!""",
            [
                {"text": "Try climbing again more carefully", "next": "climb_wall_holds"},
                {"text": "Search the water for items", "next": "search_cell_water"},
                {"text": "Dive underwater to find a passage", "next": "dive_underwater"},
                {"text": "Custom action", "next": "custom_back_water"}
            ]
        )
        
        self.nodes["swing_for_hold"] = StoryNode(
            "swing_for_hold",
            """You swing your body, trying to reach another hold.
The momentum builds. You release at the peak of your swing—
Your hand finds purchase! You've caught another hold!

Breathing hard, you continue climbing. Each movement is agony, but you persist.
Finally, you reach the top and pull yourself through a grate into a passage.""",
            [
                {"text": "Crawl forward into the passage", "next": "drainage_tunnel"},
                {"text": "Rest briefly to recover", "next": "rest_after_climb"},
                {"text": "Custom action", "next": "custom_climb_success"}
            ]
        )
        
        self.nodes["panic_thrash"] = StoryNode(
            "panic_thrash",
            """You panic completely, thrashing in the contaminated water.
You swallow more of it. You can't think straight. You can't find which way is up.
Your vision darkens. Your movements slow. The cold claims you.

CAUSE OF DEATH: Panic-induced drowning in contaminated water
SURVIVAL TIME: 4 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["induce_vomit"] = StoryNode(
            "induce_vomit",
            """You stick your fingers down your throat, forcing yourself to vomit.
You retch violently, expelling the contaminated water.
It might not be enough—you swallowed so much—but it's better than nothing.

You feel weak and dizzy, but more clear-headed than before.
The water is at your neck. You MUST move now!""",
            [
                {"text": "Search frantically for exit", "next": "find_drainage_grate"},
                {"text": "Dive down for underwater passage", "next": "underwater_passage"},
                {"text": "Custom action", "next": "custom_after_vomit"}
            ]
        )
        
        self.nodes["pull_grate"] = StoryNode(
            "pull_grate",
            """You grab the grate with both hands and pull with all your strength.
The rusted metal groans. The lock holds. You pull harder—your wound tears open,
blood mixing with the water. The grate doesn't budge.

The water is at your mouth now. You have seconds left!""",
            [
                {"text": "Take final deep breath and dive for another way", "next": "dive_last_chance"},
                {"text": "Keep pulling until you pass out", "next": "death_drowning"},
                {"text": "Custom action", "next": "custom_final_moments"}
            ]
        )
        
        self.nodes["dive_last_chance"] = StoryNode(
            "dive_last_chance",
            """You take the deepest breath you can manage and dive under.
Swimming down, down through the murky water. Your hands find the bottom.
You feel along desperately. There—a hole! Water is draining through it!

You squeeze through, scraping skin off your shoulders. The passage is tight.
You can't turn around. You can only go forward. Your lungs burn.
Then—blessed air! You surface in another chamber, coughing and gasping.""",
            [
                {"text": "Catch your breath and assess situation", "next": "assess_new_chamber"},
                {"text": "Crawl out of water immediately", "next": "crawl_from_water"},
                {"text": "Custom action", "next": "custom_new_chamber"}
            ]
        )
        
        self.nodes["pick_lock_grate"] = StoryNode(
            "pick_lock_grate",
            """You try to pick the lock with your fingers, feeling for the mechanism.
It's too dark to see, and you're not a locksmith. The water rises to your lips.
You're out of time. This isn't working!""",
            [
                {"text": "Give up and dive for another way", "next": "dive_last_chance"},
                {"text": "Bash the lock with something", "next": "bash_lock_desperate"},
                {"text": "Custom action", "next": "custom_lock_attempt"}
            ]
        )

        # Add more combat and story nodes
        self.nodes["rest_tunnel"] = StoryNode(
            "rest_tunnel",
            """You lean against the tunnel wall, catching your breath.
Your body shivers uncontrollably from the cold. Your wound throbs.
You need to keep moving or you'll go into shock, but a moment's rest helps.

Rested slightly. Stamina recovered partially.""",
            [
                {"text": "Continue up the tunnel", "next": "drainage_tunnel"},
                {"text": "Tear fabric to bandage wound", "next": "bandage_wound_tunnel"},
                {"text": "Custom action", "next": "custom_rest_tunnel"}
            ]
        )
        
        self.nodes["check_wounds_tunnel"] = StoryNode(
            "check_wounds_tunnel",
            """You examine yourself. The wound on your side is deep—a puncture wound.
It's not bleeding heavily, but it's dirty. In this filthy environment, infection
is almost guaranteed unless you treat it. You have no medical supplies.

You could:
- Cauterize it with fire (painful but effective)
- Rinse it with water (might help, might make it worse)
- Leave it and hope for the best
- Find clean cloth to bind it""",
            [
                {"text": "Continue without treatment—no time", "next": "drainage_tunnel"},
                {"text": "Rinse with water from the tunnel", "next": "rinse_wound_water"},
                {"text": "Tear cloth from clothes to bind it", "next": "bind_wound_cloth"},
                {"text": "Custom action", "next": "custom_wound_treatment"}
            ]
        )

        # More story paths and nodes
        self.nodes["scratch_marks"] = StoryNode(
            "scratch_marks",
            """You follow the scratch marks carved into the walls. They're deep gouges—
made by something with claws. Or fingernails worn to bloody stubs.
The marks lead you down a twisting corridor. The blood trail from the other
direction converges with this path ahead. Both paths meet at a junction.

In the center of the junction stands an iron maiden—medieval torture device.
Blood pools beneath it. The scratches on the floor lead TO it, not from it.""",
            [
                {"text": "Examine the iron maiden carefully", "next": "examine_iron_maiden"},
                {"text": "Go around it and continue", "next": "past_iron_maiden"},
                {"text": "Check if anyone is inside it", "next": "check_inside_maiden"},
                {"text": "Go back and take the blood trail instead", "next": "blood_trail"},
                {"text": "Custom action", "next": "custom_iron_maiden"}
            ]
        )
        
        self.nodes["tend_wound_torch"] = StoryNode(
            "tend_wound_torch",
            """You use the torch to examine your wound closely. It's bad—a deep puncture
in your side. You tear a strip from your shirt and bind it tightly.
The torch flame flickers. If you had something to sterilize it with...

You notice a bottle of spirits half-empty on the floor—probably from the corpse.""",
            [
                {"text": "Use the spirits to clean the wound (painful)", "next": "sterilize_wound"},
                {"text": "Just keep the bandage and continue", "next": "bandaged_continue"},
                {"text": "Drink the spirits for the pain", "next": "drink_spirits"},
                {"text": "Custom action", "next": "custom_wound_care"}
            ]
        )
        
        self.nodes["examine_walls_torch"] = StoryNode(
            "examine_walls_torch",
            """With the torch, you examine the walls closely. You see more now:
- Names carved into the stone. Hundreds of them. All prisoners who died here.
- Strange symbols that seem to writhe in the torchlight
- A hidden alcove containing a small leather journal

You open the journal. The last entry reads:
"Day 47: The Harvester came again. It took Marcus. Only Elena and I remain.
We found a map to the trophy room. The Overseer keeps the exit key there.
But between here and there... gods help us."

A map is sketched on the next page.""",
            [
                {"text": "Study the map carefully", "next": "study_map"},
                {"text": "Take journal and move on", "next": "take_journal_move"},
                {"text": "Read more entries", "next": "read_journal_more"},
                {"text": "Custom action", "next": "custom_journal"}
            ]
        )
        
        self.nodes["scare_ghoul_fire"] = StoryNode(
            "scare_ghoul_fire",
            """You wave the torch aggressively at the ghoul, shouting.
The creature recoils from the flame—ghouls fear fire.
It hisses and backs away, but doesn't flee completely.
It circles you, looking for an opening. You have the advantage for now.""",
            [
                {"text": "Press the attack with fire", "next": "fight_ghoul_torch"},
                {"text": "Use the opportunity to run past", "next": "run_past_ghoul"},
                {"text": "Back away while maintaining distance", "next": "backing_away_ghoul"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["run_from_ghoul"] = StoryNode(
            "run_from_ghoul",
            """You turn and run! The ghoul shrieks and gives chase!
You sprint through the corridors, the sound of claws on stone behind you.
You take a turn—another turn—you're lost now but still running.

Ahead, you see three paths: stairs going down, a door, and a narrow crack.""",
            [
                {"text": "Take the stairs down", "next": "run_down_stairs"},
                {"text": "Try the door", "next": "door_escape"},
                {"text": "Squeeze through the crack", "next": "squeeze_crack"},
                {"text": "Turn and fight—you're cornered", "next": "cornered_fight_ghoul"},
                {"text": "Custom action", "next": "custom_chase"}
            ]
        )
        
        self.nodes["distract_ghoul"] = StoryNode(
            "distract_ghoul",
            """You throw... what? You have very little. You throw one of your copper coins!
It clatters against the far wall. The ghoul's head snaps toward the sound.
For a moment, it's distracted. You dart past it, holding your breath.

You're past! But you hear it realize the trick. It's coming after you!""",
            [
                {"text": "Keep running", "next": "run_from_ghoul"},
                {"text": "Hide quickly", "next": "hide_from_ghoul"},
                {"text": "Turn and fight now that you have distance", "next": "fight_ghoul_distance"},
                {"text": "Custom action", "next": "custom_post_distract"}
            ]
        )
        
        self.nodes["ghoul_chain_bash"] = StoryNode(
            "ghoul_chain_bash",
            """You swing the heavy chain at the ghoul! It connects with a sickening crack!
The creature staggers but recovers quickly. It lunges at you with claws extended.
You barely dodge—it catches your arm, tearing fabric and skin.""",
            [
                {"text": "Swing the chain again", "next": "chain_second_strike"},
                {"text": "Drop chain and grab the torch", "next": "switch_to_torch"},
                {"text": "Strangle it with the chain", "next": "strangle_ghoul"},
                {"text": "Retreat and reassess", "next": "retreat_from_ghoul"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["ghoul_dodge_strike"] = StoryNode(
            "ghoul_dodge_strike",
            """You dodge to the side as the ghoul lunges! It misses by inches!
You strike from the side with the torch. The flame catches its dry flesh!
The ghoul shrieks and rolls, trying to put out the fire.
You have a critical moment—press the advantage or escape!""",
            [
                {"text": "Finish it while it's vulnerable", "next": "finish_burning_ghoul"},
                {"text": "Run while it's distracted", "next": "escape_burning_ghoul"},
                {"text": "Set it fully ablaze with the torch", "next": "ghoul_eyes_torch"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["ghoul_kick"] = StoryNode(
            "ghoul_kick",
            """You kick out hard! Your foot connects with the ghoul's knee.
You hear a crack—you've broken something! The creature drops to one knee,
snarling. But now it's even more dangerous—a wounded animal fighting for survival.
It swipes at your legs with its claws!""",
            [
                {"text": "Jump back and strike with torch", "next": "torch_strike_wounded"},
                {"text": "Stomp on its head", "next": "stomp_ghoul"},
                {"text": "Run past it while it's down", "next": "run_past_wounded_ghoul"},
                {"text": "Custom action", "next": "combat_ghoul"}
            ]
        )
        
        self.nodes["resist_cannibalism"] = StoryNode(
            "resist_cannibalism",
            """You turn away from the corpse. You're better than that.
Even starving, even in hell, you'll remain human.
Your humanity is all you have left. You won't surrender it.

But gods, you're so hungry...""",
            [
                {"text": "Search the area for other food", "next": "search_for_food"},
                {"text": "Move on despite the hunger", "next": "past_ghoul_quick"},
                {"text": "Search the victim's body for supplies instead", "next": "search_victim_body"},
                {"text": "Custom action", "next": "custom_resist_cannibalism"}
            ]
        )
        
        self.nodes["take_meat_later"] = StoryNode(
            "take_meat_later",
            """You carve some flesh from the corpse and wrap it in fabric.
You don't eat it now... but you have it. Just in case.
The act weighs on you. Your sanity decreases slightly.
You can feel yourself changing. The dungeon is getting into your head.""",
            [
                {"text": "Continue with the meat hidden away", "next": "past_ghoul_with_meat"},
                {"text": "Throw it away—this was wrong", "next": "throw_meat_away"},
                {"text": "Search the victim for other items", "next": "search_victim_body"},
                {"text": "Custom action", "next": "custom_meat_decision"}
            ]
        )
        
        self.nodes["deeper_insane"] = StoryNode(
            "deeper_insane",
            """You continue deeper. But you're different now. The whispers make sense.
The darkness is comforting. You begin to see things that aren't there.
Or are they? Reality becomes fluid.

You find yourself in a chamber filled with bones. So many bones.
A figure sits in the center—hooded, waiting. It gestures for you to approach.""",
            [
                {"text": "Approach the hooded figure", "next": "approach_dark_figure"},
                {"text": "Attack the figure", "next": "attack_dark_figure"},
                {"text": "Run away screaming", "next": "run_insane"},
                {"text": "Sit among the bones and wait", "next": "wait_in_bones"},
                {"text": "Custom action", "next": "custom_insane_chamber"}
            ]
        )
        
        self.nodes["fight_insanity"] = StoryNode(
            "fight_insanity",
            """You fight the whispers in your head. You recite your name: Zagreus.
You remember who you were before this. You hold onto your memories like a lifeline.
The whispers fade... slightly. Your sanity stabilizes, but you're forever changed.

You can continue now, but the temptation is always there, whispering.""",
            [
                {"text": "Continue forward with renewed resolve", "next": "past_ghoul_quick"},
                {"text": "Search the area thoroughly", "next": "search_victim_body"},
                {"text": "Take a moment to center yourself", "next": "meditate_sanity"},
                {"text": "Custom action", "next": "custom_fight_madness"}
            ]
        )
        
        self.nodes["use_herbs_wound"] = StoryNode(
            "use_herbs_wound",
            """You examine the herbs. Some you recognize—yarrow for bleeding, sage for
infection. You make a crude poultice and apply it to your wound.
It stings terribly, but the bleeding slows. This might save you from infection.

Health improved slightly. Wound stabilized.""",
            [
                {"text": "Continue onward", "next": "equip_dagger_continue"},
                {"text": "Rest a moment while the herbs work", "next": "rest_with_herbs"},
                {"text": "Take remaining herbs for later", "next": "herbs_for_later"},
                {"text": "Custom action", "next": "custom_herbs"}
            ]
        )
        
        self.nodes["drink_waterskin"] = StoryNode(
            "drink_waterskin",
            """You drink from the waterskin. The water is stale but clean.
It helps. You feel less weak. Dehydration was affecting you more than you realized.

Stamina restored partially.""",
            [
                {"text": "Save the rest and continue", "next": "equip_dagger_continue"},
                {"text": "Drink it all now", "next": "drink_all_water"},
                {"text": "Use some to clean your wound", "next": "water_clean_wound"},
                {"text": "Custom action", "next": "custom_waterskin"}
            ]
        )
        
        self.nodes["read_note_carefully"] = StoryNode(
            "read_note_carefully",
            """You study the note more carefully. There's more written in tiny script:
"The Overseer experiments on prisoners. Seeks immortality through harvesting.
The creature—the Harvester—is his failed first attempt. It hunts for parts
to complete itself. The trophy room contains his research and the master key.

Beware: The Harvester can sense fear. Remain calm or it will find you faster.
It cannot tolerate bright light—fire is your best defense."

This is valuable information.""",
            [
                {"text": "Memorize this and continue", "next": "equip_dagger_continue"},
                {"text": "Keep the note for reference", "next": "keep_note"},
                {"text": "Custom action", "next": "custom_note"}
            ]
        )
        
        self.nodes["sewer_passage"] = StoryNode(
            "sewer_passage",
            """You enter the narrow, foul-smelling passage. The walls are slick with moisture
and filth. Rats scatter as you approach. The smell is overwhelming.
The passage slopes downward. You hear water flowing ahead—a sewer stream.

The passage is so narrow you have to crawl in places.""",
            [
                {"text": "Continue through the sewers", "next": "sewer_passage_after_guard"},
                {"text": "Turn back—this is too dangerous", "next": "wide_hallway"},
                {"text": "Move slowly and carefully", "next": "careful_sewer"},
                {"text": "Custom action", "next": "custom_sewer_entrance"}
            ]
        )
        
        self.nodes["stairs_after_guard"] = StoryNode(
            "stairs_after_guard",
            """You thank the guard and descend the stairs. They spiral down into darkness.
The air grows colder. You count 73 steps before reaching a landing.

Before you is a massive iron door with strange symbols. This must be the lower
levels the guard mentioned. Very few who enter here return.""",
            [
                {"text": "Examine the door", "next": "descend_stairs"},
                {"text": "Continue down further", "next": "deeper_descent"},
                {"text": "Go back up and try the sewers instead", "next": "sewer_passage"},
                {"text": "Custom action", "next": "custom_lower_stairs"}
            ]
        )
        
        self.nodes["betray_guard"] = StoryNode(
            "betray_guard",
            """As the guard turns to leave, you strike! You stab him in the back with your dagger!
He gasps, eyes wide with shock and betrayal. "I... helped you..."
He falls to his knees, then collapses. He's dead.

You've killed someone who showed you mercy. Your sanity decreases significantly.
The darkness in your heart grows. But you now have his armor and spear.""",
            [
                {"text": "Take his equipment and move on", "next": "loot_guard_body"},
                {"text": "Feel remorse and say a prayer", "next": "remorse_guard"},
                {"text": "Hide the body quickly", "next": "hide_guard_body"},
                {"text": "Run before anyone sees you", "next": "flee_murder_scene"},
                {"text": "Custom action", "next": "custom_betrayal"}
            ]
        )
        
        self.nodes["guard_impatient"] = StoryNode(
            "guard_impatient",
            """The guard's face hardens. "Enough questions! You think I have all day?
Someone might come. Go NOW before I change my mind!"

He points his spear toward the sewer passage. His patience is exhausted.""",
            [
                {"text": "Thank him and go to sewers", "next": "sewer_passage_after_guard"},
                {"text": "Thank him and take the stairs", "next": "stairs_after_guard"},
                {"text": "Attack him while he's gesturing", "next": "surprise_attack_guard"},
                {"text": "Custom action", "next": "custom_guard_patience"}
            ]
        )

        # Add nodes for alternate paths
        self.nodes["examine_symbols"] = StoryNode(
            "examine_symbols",
            """You study the strange symbols carved into the stone walls.
They're ancient—older than the dungeon itself. The style is familiar...
These are warning glyphs. You can make out fragments of meaning:

"...beneath... harvester of flesh... door sealed... seven keys..."

The symbols seem to glow faintly with that same phosphorescent light.
There's more here, but it would take time to decipher fully.""",
            [
                {"text": "Continue examining symbols closely", "next": "decipher_symbols"},
                {"text": "Move on—no time for archaeology", "next": "torch_corridor"},
                {"text": "Trace the symbols with your finger", "next": "touch_symbols"},
                {"text": "Custom action", "next": "custom_symbols"}
            ]
        )
        
        self.nodes["stealth_corridor"] = StoryNode(
            "stealth_corridor",
            """You move quietly, keeping to the shadows. Your bare feet make no sound
on the cold stone. You reach a corner and peek around it carefully.

Ahead, you see the source of light—a torch in a sconce. Next to it, a guard
sits on a stool, half-asleep. Beyond him, the corridor continues into darkness.
To your left, a narrow side passage slopes downward.""",
            [
                {"text": "Sneak past the sleeping guard", "next": "sneak_past_guard"},
                {"text": "Take the side passage", "next": "side_passage_down"},
                {"text": "Wait and observe longer", "next": "observe_guard"},
                {"text": "Custom action", "next": "custom_stealth"}
            ]
        )
        
        self.nodes["call_out_corridor"] = StoryNode(
            "call_out_corridor",
            """You call out: "Hello? Is anyone there?"

Your voice echoes through the stone corridors. Silence follows.
Then—footsteps. Running. Multiple people. Getting closer fast.

You've alerted the guards!""",
            [
                {"text": "Run back into the drainage tunnel", "next": "run_back_tunnel"},
                {"text": "Stand your ground and face them", "next": "face_guards"},
                {"text": "Hide in the shadows quickly", "next": "quick_hide"},
                {"text": "Custom action", "next": "custom_guards_coming"}
            ]
        )

        # Expand combat paths
        self.nodes["dark_passage_left"] = StoryNode(
            "dark_passage_left",
            """You venture left into the dark passage without taking the torch.
The darkness is absolute. You can't see your hand in front of your face.
You feel your way forward, hands on the walls.

Something skitters across your foot. Rats, probably. Or something worse.
The passage turns. You follow it. Then you hear it—breathing. Heavy. Close.
Something is RIGHT IN FRONT OF YOU in the darkness.""",
            [
                {"text": "Back away slowly and quietly", "next": "back_away_creature"},
                {"text": "Strike out at whatever it is", "next": "strike_blind"},
                {"text": "Stay perfectly still", "next": "freeze_darkness"},
                {"text": "Run back the way you came", "next": "run_from_darkness"},
                {"text": "Custom action", "next": "custom_dark_creature"}
            ]
        )
        
        self.nodes["chewing_sound_right"] = StoryNode(
            "chewing_sound_right",
            """You go right, toward the chewing sound, without the torch.
In the darkness, you almost trip over something—the corpse of a prisoner.
Fresh. Still warm. Something is feeding on it RIGHT NOW.

You hear the chewing stop. Whatever it is knows you're there.
A wet growl emanates from the darkness. Claws scrape on stone.
It's coming for you!""",
            [
                {"text": "Run back to the torch", "next": "run_to_torch"},
                {"text": "Fight in the darkness", "next": "fight_blind"},
                {"text": "Play dead on the ground", "next": "play_dead"},
                {"text": "Custom action", "next": "custom_fight_dark"}
            ]
        )
        
        self.nodes["investigate_chewing"] = StoryNode(
            "investigate_chewing",
            """You approach the chewing sound cautiously, still near the lit area.
You can see now—it's a GHOUL, crouched over a fresh corpse. Its pale skin
stretches over inhuman bones. It hasn't noticed you yet, too focused on its meal.

You have the advantage of surprise.""",
            [
                {"text": "Take the torch and attack while it's distracted", "next": "torch_sneak_attack"},
                {"text": "Try to sneak past while it feeds", "next": "sneak_past_ghoul"},
                {"text": "Go back and take the other path", "next": "dark_passage_left"},
                {"text": "Throw something to distract it", "next": "distract_feeding_ghoul"},
                {"text": "Custom action", "next": "custom_ghoul_surprise"}
            ]
        )

        # More death scenarios
        self.nodes["death_combat_generic"] = StoryNode(
            "death_combat_generic",
            """The creature overwhelms you. Your desperate attacks are not enough.
Claws tear into your flesh. Teeth find your throat. The pain is brief.
Darkness takes you.

CAUSE OF DEATH: Killed in combat
SURVIVAL TIME: varies

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["death_combat"] = StoryNode(
            "death_combat",
            """You fight valiantly, but you're wounded, exhausted, and unarmed.
The battle is brief and brutal. Your broken body joins countless others
who thought they could fight their way out.

CAUSE OF DEATH: Combat wounds
SURVIVAL TIME: varies

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )

        # Add custom action handlers
        self.nodes["custom_feel_walls"] = "CUSTOM_AI"
        self.nodes["custom_climb"] = "CUSTOM_AI"
        self.nodes["custom_after_climb"] = "CUSTOM_AI"
        self.nodes["custom_bundle"] = "CUSTOM_AI"
        self.nodes["custom_hidden_items"] = "CUSTOM_AI"
        self.nodes["custom_after_potion"] = "CUSTOM_AI"
        self.nodes["custom_panic"] = "CUSTOM_AI"
        self.nodes["custom_grate_panic"] = "CUSTOM_AI"
        self.nodes["custom_underwater"] = "CUSTOM_AI"
        self.nodes["custom_dark_chamber"] = "CUSTOM_AI"
        self.nodes["custom_guard_above"] = "CUSTOM_AI"
        self.nodes["custom_rope_taunt"] = "CUSTOM_AI"
        self.nodes["custom_rope_climb"] = "CUSTOM_AI"
        self.nodes["custom_guardroom"] = "CUSTOM_AI"
        self.nodes["custom_back_water"] = "CUSTOM_AI"
        self.nodes["custom_climb_success"] = "CUSTOM_AI"
        self.nodes["custom_after_vomit"] = "CUSTOM_AI"
        self.nodes["custom_final_moments"] = "CUSTOM_AI"
        self.nodes["custom_new_chamber"] = "CUSTOM_AI"
        self.nodes["custom_lock_attempt"] = "CUSTOM_AI"
        self.nodes["custom_rest_tunnel"] = "CUSTOM_AI"
        self.nodes["custom_wound_treatment"] = "CUSTOM_AI"
        self.nodes["custom_symbols"] = "CUSTOM_AI"
        self.nodes["custom_stealth"] = "CUSTOM_AI"
        self.nodes["custom_guards_coming"] = "CUSTOM_AI"
        self.nodes["custom_dark_creature"] = "CUSTOM_AI"
        self.nodes["custom_fight_dark"] = "CUSTOM_AI"
        self.nodes["custom_ghoul_surprise"] = "CUSTOM_AI"
        
        self.nodes["restart"] = "RESTART"
    
    def show_status(self):
        """Display current player status"""
        print("\n" + "="*60)
        print("STATUS:")
        print(f"Health: {self.state.health}/{self.state.max_health} | Stamina: {self.state.stamina}/{self.state.max_stamina}")
        print(f"Hunger: {self.state.hunger}/100 | Wetness: {self.state.wetness}/100 | Temp: {self.state.temperature}/100")
        print(f"Sanity: {self.state.sanity}/100 | Fear: {self.state.fear}/100")
        
        # Active status effects
        active_effects = [name for name, turns in self.state.status_effects.items() if turns > 0]
        if active_effects:
            effects_str = ", ".join([f"{eff}({self.state.status_effects[eff]})" for eff in active_effects])
            print(f"Status Effects: {effects_str}")
        
        # Body status
        injuries = []
        if not self.state.left_arm: injuries.append("Missing left arm")
        if not self.state.right_arm: injuries.append("Missing right arm")
        if not self.state.left_leg: injuries.append("Missing left leg")
        if not self.state.right_leg: injuries.append("Missing right leg")
        if not self.state.left_eye or not self.state.right_eye: injuries.append("Vision impaired")
        
        if injuries:
            print(f"Injuries: {', '.join(injuries)}")
        
        # Equipment
        equipped_items = []
        for slot, item in self.state.equipped.items():
            if item:
                durability = self.state.equipment_durability.get(slot, 100)
                equipped_items.append(f"{slot}: {item} ({durability}%)")
        
        if equipped_items:
            print(f"Equipped: {', '.join(equipped_items)}")
        else:
            print("Equipped: Nothing")
        
        # Inventory
        if self.state.inventory:
            inv_str = ', '.join(self.state.inventory[:5])
            if len(self.state.inventory) > 5:
                inv_str += f" (+{len(self.state.inventory) - 5} more)"
            print(f"Inventory ({len(self.state.inventory)}/{self.state.max_inventory}): {inv_str}")
        else:
            print("Inventory: Empty")
        
        print("="*60 + "\n")
    
    def handle_custom_action(self, context_node: str):
        """Handle custom AI-driven player actions"""
        print("\n[Custom Action Mode - Describe what you want to do]")
        action = input("> ").strip()
        
        # Validate and sanitize input
        if len(action) > MAX_INPUT_LENGTH:
            action = action[:MAX_INPUT_LENGTH]
            print(f"[Input truncated to {MAX_INPUT_LENGTH} characters]")
        
        if not action:
            print("You do nothing and waste time...")
            return self.find_next_node_from_ai(context_node, False, "")
        
        # Get context
        context = {
            "location": self.state.location,
            "in_combat": "combat" in context_node.lower() or "fight" in context_node.lower()
        }
        
        if context["in_combat"]:
            # Add enemy info based on current context
            if "ghoul" in context_node:
                context["enemy"] = {
                    "type": "ghoul",
                    "weaknesses": ["fire", "eyes"],
                    "health": 40
                }
        
        success, description, effects = self.dm.evaluate_action(action, context)
        
        print(f"\n{description}")
        
        # Apply effects
        if "damage_taken" in effects:
            self.state.health -= effects["damage_taken"]
            if self.state.health <= 0:
                return "death_combat"
        
        if "damage_dealt" in effects and context.get("in_combat"):
            # If significant damage, might kill enemy
            if effects["damage_dealt"] > 30:
                print("You've dealt a devastating blow!")
                return self.find_next_victory_node(context_node)
        
        # Find appropriate next node based on success/failure
        return self.find_next_node_from_ai(context_node, success, action)
    
    def find_next_node_from_ai(self, current: str, success: bool, action: str):
        """Intelligently route to next node based on AI outcome"""
        # This would be more sophisticated in full implementation
        # For now, route to a reasonable next node
        if "start" in current:
            return "after_corpse_loot"
        elif "combat" in current or "fight" in current:
            if success:
                return "search_victim_body"
            else:
                return "death_combat_generic"
        else:
            return "drainage_tunnel"  # Safe fallback
    
    def find_next_victory_node(self, context: str):
        """Find victory node after combat success"""
        if "ghoul" in context:
            return "search_victim_body"
        return "drainage_tunnel"
    
    def process_node_effects(self, node_id: str):
        """Process any automatic effects when entering a node"""
        self.state.turn_count += 1
        self.state.visited_nodes.add(node_id)
        self.state.node_history.append(node_id)  # Track order
        
        # Process status effects
        for effect, turns in list(self.state.status_effects.items()):
            if turns > 0:
                self.state.status_effects[effect] = turns - 1
                
                # Apply ongoing damage/effects
                if effect == "bleeding" and turns > 0:
                    self.state.health -= 3
                    print(f"[Bleeding: -{3} health]")
                elif effect == "poisoned" and turns > 0:
                    self.state.health -= 5
                    self.state.stamina -= 5
                    print(f"[Poisoned: -{5} health, -{5} stamina]")
                elif effect == "burning" and turns > 0:
                    self.state.health -= 8
                    print(f"[Burning: -{8} health]")
                elif effect == "infected" and turns > 0:
                    self.state.health -= 4
                    self.state.max_health -= 1
                    print(f"[Infected: -{4} health, max health reduced]")
        
        # Hunger increases over time
        if self.state.turn_count % 5 == 0:
            self.state.hunger += 5
            if self.state.hunger >= 100:
                return "death_starvation"
        
        # Wetness decreases slowly if not in water
        if self.state.wetness > 0 and "water" not in node_id.lower():
            self.state.wetness -= 3
        
        # Temperature effects
        if self.state.wetness > 60 and self.state.temperature < 50:
            self.state.temperature -= 2
            if self.state.temperature <= 20:
                self.state.health -= 5
                print("[Hypothermia: -{5} health]")
                if self.state.health <= 0:
                    return "death_hypothermia"
        
        # Equipment durability
        if self.state.turn_count % 8 == 0:
            for slot in ["weapon", "armor", "light"]:
                if self.state.equipped[slot] and self.state.equipment_durability[slot] > 0:
                    self.state.equipment_durability[slot] -= 5
                    if self.state.equipment_durability[slot] <= 0:
                        print(f"[Your {slot} breaks from wear!]")
                        self.state.equipped[slot] = None
                        self.state.equipment_durability[slot] = 0
        
        # Stamina recovery when not in combat
        if "combat" not in node_id.lower() and "fight" not in node_id.lower():
            self.state.stamina = min(self.state.max_stamina, self.state.stamina + 5)
        
        # Fear affects Harvester detection
        if self.state.fear > 75 and random.randint(1, 100) > 90:
            print("[You sense the Harvester is getting closer...]")
            self.state.fear += 5
        
        # Sanity effects
        if self.state.sanity < 30:
            if random.randint(1, 100) > 70:
                print("[Hallucination: The walls seem to breathe...]")
        
        # Health degradation from untreated wounds
        if self.state.health < self.state.max_health and self.state.turn_count % 10 == 0:
            if random.randint(1, 100) > 70 and self.state.status_effects["infected"] == 0:
                self.state.health -= 5
                print("[Your wound worsens...]")
                if self.state.health <= 0:
                    return "death_infection"
        
        # Death from accumulated damage
        if self.state.health <= 0:
            return "death_wounds"
        
        return None
    
    def run(self):
        """Main game loop"""
        print("\n" + "="*60)
        print("ZAGREUS' DESCENT")
        print("A Dark Dungeon Crawler")
        print("="*60)
        print("\nYou were betrayed. Left to drown in a flooded cell.")
        print("But you survived. Now you must escape the dungeon.")
        print("\nThis is a game of choices. Most lead to death.")
        print("Some lead to freedom. Type the number of your choice,")
        print("or choose 'Custom action' to describe your own action.")
        print("\nGood luck. You'll need it.")
        print("="*60)
        input("\nPress Enter to begin...")
        
        self.current_node = "start"
        
        while True:
            # Check for automatic death conditions
            death_node = self.process_node_effects(self.current_node)
            if death_node:
                self.current_node = death_node
            
            # Handle restart
            if self.current_node == "RESTART":
                print("\n\nRestarting game...")
                self.__init__()
                self.current_node = "start"
                continue
            
            # Get current node
            node = self.nodes.get(self.current_node)
            if not node:
                print(f"Error: Node '{self.current_node}' not found!")
                print(f"Available nodes: {len(self.nodes)} total")
                print("The game encountered an error. Please report this issue.")
                break
            
            # Handle custom AI nodes (check if node is a string marker)
            if isinstance(node, str) and node == "CUSTOM_AI":
                prev_node = self.state.node_history[-2] if len(self.state.node_history) > 1 else "start"
                self.current_node = self.handle_custom_action(prev_node)
                continue
            
            if isinstance(node, str) and node == "COMBAT_AI":
                prev_node = self.state.node_history[-2] if len(self.state.node_history) > 1 else "start"
                self.current_node = self.handle_custom_action(prev_node)
                continue
            
            # Show status
            self.show_status()
            
            # Show description
            print("\n" + "="*60)
            print(node.description)
            print("="*60)
            
            # Show choices
            print("\nWhat do you do?\n")
            for i, choice in enumerate(node.choices, 1):
                print(f"{i}. {choice['text']}")
            
            # Get player input
            retry_count = 0
            while retry_count < MAX_INPUT_RETRIES:
                try:
                    choice_input = input("\n> ").strip()
                    choice_num = int(choice_input)
                    if 1 <= choice_num <= len(node.choices):
                        chosen = node.choices[choice_num - 1]
                        self.current_node = chosen["next"]
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(node.choices)}")
                        retry_count += 1
                except ValueError:
                    print("Please enter a valid number")
                    retry_count += 1
                except KeyboardInterrupt:
                    print("\n\nGame interrupted. Thanks for playing!")
                    return
            
            if retry_count >= MAX_INPUT_RETRIES:
                print("\nToo many invalid inputs. Game ended.")
                return

def main():
    """Entry point"""
    try:
        game = ZagreusGame()
        game.run()
    except KeyboardInterrupt:
        print("\n\nGame ended. Thanks for playing!")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        print("The dungeon glitches... reality breaks...")

if __name__ == "__main__":
    main()
