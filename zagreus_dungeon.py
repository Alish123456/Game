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

# Status effect damage constants
STATUS_DAMAGE_BLEEDING = 3
STATUS_DAMAGE_POISONED = 5
STATUS_DAMAGE_BURNING = 8
STATUS_DAMAGE_INFECTED = 4
STAMINA_DRAIN_POISONED = 5
MAX_HEALTH_LOSS_INFECTED = 1

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
        
        # Status effects that modify combat but don't deal damage here
        # (damage is applied in process_node_effects)
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
                # Check for blinding effect
                if random.randint(1, 100) > 70:
                    effects["status"].append("enemy_blinded")
                    return (True, f"You strike the creature's eye! Critical hit for {damage} damage! It's blinded!", effects)
                return (True, f"You strike the creature's eye! Critical hit for {damage} damage!", effects)
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
        
        # More complete paths to reduce missing nodes
        self.nodes["past_ghoul_quick"] = StoryNode(
            "past_ghoul_quick",
            """You move past the ghoul's corpse quickly, not wanting to linger.
The corridor continues ahead. You hear water dripping somewhere.
The torch reveals three paths: left leads upward, center continues straight,
right slopes downward.""",
            [
                {"text": "Take the upward path", "next": "upward_path"},
                {"text": "Continue straight", "next": "straight_path"},
                {"text": "Descend the right path", "next": "downward_path"},
                {"text": "Search this area first", "next": "search_junction"}
            ]
        )
        
        self.nodes["rest_after_ghoul"] = StoryNode(
            "rest_after_ghoul",
            """You lean against the wall, breathing heavily. The fight took a lot out of you.
Your hands shake. You're hurt but alive. After a few moments, your breathing steadies.

Health recovered slightly. Stamina recovered.""",
            [
                {"text": "Search the area now", "next": "search_victim_body"},
                {"text": "Continue onward", "next": "past_ghoul_quick"},
                {"text": "Tend to your new wounds", "next": "tend_combat_wounds"}
            ]
        )
        
        self.nodes["run_past_ghoul"] = StoryNode(
            "run_past_ghoul",
            """You use the ghoul's fear of fire to dash past it! You run down the corridor!
The creature hisses but doesn't pursue immediately. You've bought yourself time.""",
            [
                {"text": "Keep running", "next": "run_from_ghoul"},
                {"text": "Find a defensible position", "next": "find_defensive_spot"},
                {"text": "Hide and ambush if it follows", "next": "ambush_setup"}
            ]
        )
        
        self.nodes["backing_away_ghoul"] = StoryNode(
            "backing_away_ghoul",
            """You back away slowly, torch held out defensively. The ghoul maintains distance,
respecting the fire. You're in a stalemate. You reach a junction—you can go left or right.""",
            [
                {"text": "Take the left path quickly", "next": "left_from_ghoul"},
                {"text": "Take the right path", "next": "right_from_ghoul"},
                {"text": "Throw torch at it and run", "next": "torch_throw_run"},
                {"text": "Stand ground and fight", "next": "fight_ghoul_torch"}
            ]
        )
        
        self.nodes["run_down_stairs"] = StoryNode(
            "run_down_stairs",
            """You dash down the stairs, taking them two at a time! The ghoul's claws scrape
behind you! Down, down into darkness. The stairs end abruptly—you tumble forward!

You land hard in complete darkness. The ghoul's shrieks echo from above but it
doesn't follow down here. Something must scare even the ghouls about this place.""",
            [
                {"text": "Use your torch if you still have it", "next": "light_lower_level"},
                {"text": "Feel your way in darkness", "next": "lower_level_dark"},
                {"text": "Stay still and listen", "next": "listen_lower_level"}
            ]
        )
        
        self.nodes["door_escape"] = StoryNode(
            "door_escape",
            """You try the door—it's unlocked! You burst through and slam it behind you!
You hear the ghoul crash against it. You throw the bolt. The door shudders but holds.

You're in a guardroom. Empty. There's armor on a rack, weapons on the wall,
and another door on the far side.""",
            [
                {"text": "Take armor and weapons", "next": "equip_guard_gear"},
                {"text": "Go through the far door quickly", "next": "far_door_exit"},
                {"text": "Search the room thoroughly", "next": "search_guardroom"},
                {"text": "Barricade the door better", "next": "barricade_door"}
            ]
        )
        
        self.nodes["squeeze_crack"] = StoryNode(
            "squeeze_crack",
            """You squeeze through the narrow crack in the wall! Your shoulders scrape painfully.
You hear the ghoul's claws on the other side but it can't fit through!

You're safe for now. You're in a narrow passage between walls. You can hear sounds
from rooms on either side through the thin walls.""",
            [
                {"text": "Follow the passage", "next": "between_walls_passage"},
                {"text": "Listen through the walls", "next": "listen_through_walls"},
                {"text": "Look for a way into one of the rooms", "next": "find_wall_opening"}
            ]
        )
        
        self.nodes["cornered_fight_ghoul"] = StoryNode(
            "cornered_fight_ghoul",
            """You're cornered! The ghoul knows it. It advances slowly, savoring your fear.
You have no choice but to fight for your life!

[DESPERATE COMBAT]""",
            [
                {"text": "Fight with everything you have", "next": "desperate_ghoul_fight"},
                {"text": "Try a desperate gambit", "next": "desperate_gambit"},
                {"text": "Surrender to death", "next": "death_combat"}
            ]
        )
        
        self.nodes["hide_from_ghoul"] = StoryNode(
            "hide_from_ghoul",
            """You find a dark alcove and press yourself into it, holding your breath.
The ghoul's footsteps approach. It sniffs the air. Can it smell you?

It stops right in front of your hiding spot...""",
            [
                {"text": "Stay perfectly still", "next": "hide_success_ghoul"},
                {"text": "Leap out and attack by surprise", "next": "surprise_attack_ghoul"},
                {"text": "Run before it finds you", "next": "run_from_hiding"}
            ]
        )
        
        self.nodes["fight_ghoul_distance"] = StoryNode(
            "fight_ghoul_distance",
            """With some distance between you, you ready yourself for combat.
The ghoul circles warily. This will be a tough fight.""",
            [
                {"text": "Attack aggressively", "next": "fight_ghoul_torch"},
                {"text": "Fight defensively", "next": "defensive_ghoul_fight"},
                {"text": "Try to lead it into a trap", "next": "trap_ghoul"}
            ]
        )
        
        self.nodes["torch_strike_wounded"] = StoryNode(
            "torch_strike_wounded",
            """You jump back and strike with the torch! The flame catches the wounded ghoul's
face! It shrieks and falls backward. One more good hit should finish it!""",
            [
                {"text": "Finish it off", "next": "finish_ghoul"},
                {"text": "Let it flee and escape yourself", "next": "let_ghoul_flee"}
            ]
        )
        
        self.nodes["stomp_ghoul"] = StoryNode(
            "stomp_ghoul",
            """You stomp down hard on the ghoul's head! CRACK! The creature goes limp.
You've killed it! But in the process, you've hurt your leg badly.

Victory, but at a cost. Leg injured. Movement impaired.""",
            [
                {"text": "Search the area", "next": "search_victim_body"},
                {"text": "Tend to your leg", "next": "tend_leg_injury"},
                {"text": "Move on despite the pain", "next": "past_ghoul_quick"}
            ]
        )
        
        self.nodes["run_past_wounded_ghoul"] = StoryNode(
            "run_past_wounded_ghoul",
            """You run past the wounded ghoul while it's down! It swipes at you but misses!
You're past it! You run down the corridor, putting distance between you and it.""",
            [
                {"text": "Keep running", "next": "run_from_ghoul"},
                {"text": "Stop and catch your breath", "next": "catch_breath"},
                {"text": "Find a place to hide", "next": "hide_from_ghoul"}
            ]
        )
        
        self.nodes["search_for_food"] = StoryNode(
            "search_for_food",
            """You search the area desperately for food. Your hunger is overwhelming.
You find some mushrooms growing in the dark, damp corner. They could be edible...
or deadly poisonous. You also spot some beetles crawling on the wall.""",
            [
                {"text": "Eat the mushrooms carefully", "next": "eat_mushrooms"},
                {"text": "Eat the beetles—protein is protein", "next": "eat_beetles"},
                {"text": "Search more before eating anything", "next": "search_more_food"},
                {"text": "Resist and move on hungry", "next": "resist_eating"}
            ]
        )
        
        self.nodes["past_ghoul_with_meat"] = StoryNode(
            "past_ghoul_with_meat",
            """You move on, the wrapped human flesh hidden in your pack.
The weight of what you've done (or might do) presses on you.
Your sanity is fragile. The dungeon changes people.""",
            [
                {"text": "Continue forward", "next": "past_ghoul_quick"},
                {"text": "Examine your conscience", "next": "moral_reflection"},
                {"text": "Search the victim's body anyway", "next": "search_victim_body"}
            ]
        )
        
        self.nodes["throw_meat_away"] = StoryNode(
            "throw_meat_away",
            """You throw the wrapped meat away in disgust. What were you thinking?
You're not a monster. Not yet. Your sanity stabilizes slightly.

You've held onto your humanity. For now.""",
            [
                {"text": "Search for real food elsewhere", "next": "search_for_food"},
                {"text": "Continue without eating", "next": "past_ghoul_quick"},
                {"text": "Search the victim's body for supplies", "next": "search_victim_body"}
            ]
        )
        
        self.nodes["meditate_sanity"] = StoryNode(
            "meditate_sanity",
            """You sit and try to center yourself. You focus on your breathing.
In... out... You remember who you were. Who you are. Who you want to be.

The whispers fade. Your sanity improves slightly. You're still in hell,
but you're still you.""",
            [
                {"text": "Continue with renewed purpose", "next": "past_ghoul_quick"},
                {"text": "Rest a bit longer", "next": "rest_longer"},
                {"text": "Search the area now", "next": "search_victim_body"}
            ]
        )
        
        self.nodes["rest_with_herbs"] = StoryNode(
            "rest_with_herbs",
            """You rest while the herbs work their healing magic. The pain in your side lessens.
The bleeding has stopped. You feel significantly better.

Health restored by 15! Infection risk reduced!""",
            [
                {"text": "Continue onward refreshed", "next": "equip_dagger_continue"},
                {"text": "Take stock of your situation", "next": "assess_situation"}
            ]
        )
        
        self.nodes["herbs_for_later"] = StoryNode(
            "herbs_for_later",
            """You save the remaining herbs for later. Smart. Resources are precious here.

Herbs added to inventory.""",
            [
                {"text": "Continue onward", "next": "equip_dagger_continue"}
            ]
        )
        
        self.nodes["drink_all_water"] = StoryNode(
            "drink_all_water",
            """You drink all the water. It helps immensely! But now the waterskin is empty.
You'll need to find more water eventually.

Stamina fully restored! Thirst quenched!""",
            [
                {"text": "Continue onward", "next": "equip_dagger_continue"},
                {"text": "Refill waterskin if possible", "next": "refill_water"}
            ]
        )
        
        self.nodes["water_clean_wound"] = StoryNode(
            "water_clean_wound",
            """You use some water to clean your wound. It stings but feels cleaner.
The water is precious, but preventing infection is worth it.

Infection risk reduced! Water partially used.""",
            [
                {"text": "Continue onward", "next": "equip_dagger_continue"},
                {"text": "Bandage it as well", "next": "bandage_after_clean"}
            ]
        )
        
        self.nodes["keep_note"] = StoryNode(
            "keep_note",
            """You carefully fold the note and keep it. The information about the Harvester
and the trophy room might save your life.

Note added to inventory.""",
            [
                {"text": "Continue onward", "next": "equip_dagger_continue"},
                {"text": "Read it again more carefully", "next": "reread_note"}
            ]
        )
        
        self.nodes["hide_observe"] = StoryNode(
            "hide_observe",
            """You hide behind a pillar and observe. The three paths remain before you.
You hear footsteps from the wide hallway getting closer.
A foul smell wafts from the narrow passage.
The stairs remain silent.""",
            [
                {"text": "Wait to see who's coming", "next": "wait_for_footsteps"},
                {"text": "Take the foul passage while hidden", "next": "sewer_passage"},
                {"text": "Descend the stairs quietly", "next": "descend_stairs"}
            ]
        )
        
        self.nodes["attack_guard"] = StoryNode(
            "attack_guard",
            """You attack the guard without warning! He's caught by surprise!
You have the advantage of initiative but he's trained and armored!

[COMBAT]""",
            [
                {"text": "Go for his throat with dagger", "next": "guard_throat_attack"},
                {"text": "Knock away his spear first", "next": "disarm_guard"},
                {"text": "Tackle him to the ground", "next": "tackle_guard"}
            ]
        )
        
        self.nodes["surrender_guard"] = StoryNode(
            "surrender_guard",
            """You drop your weapons and raise your hands. "I surrender."

The guard looks relieved. "Finally, some sense. Come with me."
He gestures with his spear toward a side door.

Is this a trick? Or genuine mercy?""",
            [
                {"text": "Go with him peacefully", "next": "follow_guard"},
                {"text": "Attack when his guard is down", "next": "betray_surrender"},
                {"text": "Run at the last second", "next": "run_from_escort"}
            ]
        )
        
        self.nodes["run_from_guard"] = StoryNode(
            "run_from_guard",
            """You turn and run! The guard shouts "Stop!" and gives chase!
You run back the way you came. You can take the sewer or the stairs!""",
            [
                {"text": "Take the sewer passage", "next": "sewer_passage"},
                {"text": "Take the stairs down", "next": "descend_stairs"},
                {"text": "Turn and fight—running is futile", "next": "stop_and_fight_guard"}
            ]
        )

        # Custom AI nodes for new content
        self.nodes["custom_junction"] = "CUSTOM_AI"
        self.nodes["custom_rest_combat"] = "CUSTOM_AI"
        self.nodes["custom_past_ghoul"] = "CUSTOM_AI"
        self.nodes["custom_ghoul_standoff"] = "CUSTOM_AI"
        self.nodes["custom_lower_level"] = "CUSTOM_AI"
        self.nodes["custom_guardroom_escape"] = "CUSTOM_AI"
        self.nodes["custom_crack_passage"] = "CUSTOM_AI"
        self.nodes["custom_hiding"] = "CUSTOM_AI"
        self.nodes["custom_injured_victory"] = "CUSTOM_AI"
        self.nodes["custom_escape_wounded"] = "CUSTOM_AI"
        self.nodes["custom_food_search"] = "CUSTOM_AI"
        self.nodes["custom_dark_choice"] = "CUSTOM_AI"
        self.nodes["custom_throw_meat"] = "CUSTOM_AI"
        self.nodes["custom_meditate"] = "CUSTOM_AI"
        self.nodes["custom_herbal_rest"] = "CUSTOM_AI"
        self.nodes["custom_save_herbs"] = "CUSTOM_AI"
        self.nodes["custom_drink_all"] = "CUSTOM_AI"
        self.nodes["custom_clean_wound"] = "CUSTOM_AI"
        self.nodes["custom_keep_note"] = "CUSTOM_AI"
        self.nodes["custom_hide_observe"] = "CUSTOM_AI"
        self.nodes["custom_guard_combat"] = "CUSTOM_AI"
        self.nodes["custom_surrender"] = "CUSTOM_AI"
        self.nodes["custom_run_guard"] = "CUSTOM_AI"
        
        # Add more critical story completion nodes to fill gaps
        # These complete major pathways
        
        self.nodes["appeal_guard"] = StoryNode(
            "appeal_guard",
            """You appeal to his humanity. "You're not like them. I can see it in your eyes.
You don't want to be here either. We're both trapped by the Overseer.
Help me escape and I'll help you get out too."

The guard wavers. His grip on the spear loosens. "I... I have a family above.
They'll kill them if I betray my post."

You see genuine fear in his eyes.""",
            [
                {"text": "Offer to save his family too", "next": "promise_save_family"},
                {"text": "Tell him his family is likely already dead", "next": "harsh_truth"},
                {"text": "Back off and find another way", "next": "leave_guard_alone"}
            ]
        )
        
        self.nodes["attack_distracted_guard"] = StoryNode(
            "attack_distracted_guard",
            """While he's distracted by your words, you strike! Your dagger flashes!
The guard gasps, stumbling back. He's wounded but not dead. He raises his spear
in defense, but he's slower now. Blood flows from his side.""",
            [
                {"text": "Press the attack", "next": "finish_wounded_guard"},
                {"text": "Demand he surrender", "next": "demand_guard_yield"},
                {"text": "Run while he's injured", "next": "run_from_wounded_guard"}
            ]
        )
        
        self.nodes["confront_overseer"] = StoryNode(
            "confront_overseer",
            """You burst through the door! The Overseer spins to face you!
He's a tall man in a stained apron, holding surgical tools.
Behind him, the trophy room is filled with jars containing... body parts.

"Zagreus!" he says with genuine surprise. "You survived! Remarkable!
You'll make an excellent addition to my collection!"

He raises a strange device—it hums with energy.""",
            [
                {"text": "Attack him immediately", "next": "fight_overseer"},
                {"text": "Dodge and find cover", "next": "cover_from_overseer"},
                {"text": "Try to talk him down", "next": "talk_overseer"},
                {"text": "Look for the key first", "next": "grab_key_quick"}
            ]
        )
        
        self.nodes["sneak_trophy_room"] = StoryNode(
            "sneak_trophy_room",
            """You open the door quietly and slip inside. The Overseer has his back to you,
examining one of his horrific trophies. The key hangs on a hook near his desk.

You could sneak to the key, or attack him from behind.""",
            [
                {"text": "Sneak to the key", "next": "steal_key_stealth"},
                {"text": "Attack from behind", "next": "backstab_overseer"},
                {"text": "Wait for better opportunity", "next": "wait_in_trophy_room"}
            ]
        )
        
        self.nodes["listen_overseer"] = StoryNode(
            "listen_overseer",
            """You listen at the door. The Overseer is talking to himself:
"The Harvester needs fresh eyes. These ones are too old. Ah, but where
to find willing donors? Ha! Willing! As if anyone has a choice here.
The experiments must continue. Immortality is within reach!"

He's completely mad. And dangerous.""",
            [
                {"text": "Burst in now", "next": "confront_overseer"},
                {"text": "Sneak in quietly", "next": "sneak_trophy_room"},
                {"text": "Leave and find another way", "next": "avoid_overseer"}
            ]
        )
        
        # More custom AI nodes
        self.nodes["custom_appeal"] = "CUSTOM_AI"
        self.nodes["custom_overseer_fight"] = "CUSTOM_AI"
        self.nodes["custom_sneak_trophy"] = "CUSTOM_AI"
        self.nodes["custom_listen_overseer"] = "CUSTOM_AI"

        # Continue adding more comprehensive paths
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
                {"text": "Make a sudden loud noise to scare it", "next": "scare_creature"}
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
                {"text": "Move away from the voice—might be a trap", "next": "away_from_voice"}
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
                {"text": "Rest against the wall briefly", "next": "rest_in_dark"}
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
                {"text": "Play dead next to the corpse", "next": "play_dead_ceiling"}
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
                {"text": "Beg for forgiveness", "next": "apologize_guard"}
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
                {"text": "Ignore it and search for other exit", "next": "search_exit_urgent"}
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
                {"text": "Describe a trap location", "next": "trap_location"}
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
                {"text": "Bite his ankle", "next": "bite_guard"}
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
                {"text": "Roll away and create distance", "next": "create_distance"}
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
                {"text": "Try to talk him down mid-combat", "next": "talk_during_combat"}
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
                {"text": "Attack while he's distracted by grief", "next": "attack_emotional_guard"}
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
                {"text": "Turn and fight in the corridor", "next": "corridor_fight"}
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
                {"text": "Rest despite the risk—you need recovery", "next": "risk_rest"}
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
                {"text": "Leave it open in case you need to retreat", "next": "grate_open_continue"}
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
                {"text": "Eat the dried meat now for energy", "next": "eat_dried_meat_safe"}
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
                {"text": "Eat the meat for energy", "next": "eat_dried_meat_safe"}
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
                {"text": "Take the rest of the items and go", "next": "bundle_and_exit"}
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
                {"text": "Dive underwater for passage", "next": "underwater_passage"}
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
                {"text": "Scream for help one last time", "next": "final_scream"}
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
                {"text": "Feel energized to explore more", "next": "bundle_and_exit"}
            ]
        )
        
        self.nodes["surface_for_air"] = StoryNode(
            "surface_for_air",
            """You surface, gasping for air. Your lungs burn. The water continues to rise.
You've located the underwater passage but need to commit to swimming through it
before the cell fills completely.""",
            [
                {"text": "Take a deep breath and go for it", "next": "underwater_passage"},
                {"text": "Search for another way", "next": "panic_search"}
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
                {"text": "Give up and find the grate instead", "next": "panic_search"}
            ]
        )
        
        self.nodes["rest_after_climb"] = StoryNode(
            "rest_after_climb",
            """You rest against the cold stone, catching your breath. The climb took everything
out of you. Your muscles shake with exhaustion. But you made it. You're out of the cell.

Stamina recovered partially.""",
            [
                {"text": "Continue when ready", "next": "drainage_tunnel"},
                {"text": "Check your wounds while resting", "next": "check_wounds_passage"}
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
                {"text": "Rest here briefly", "next": "rest_chamber"}
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
                {"text": "Check inventory—did you lose anything?", "next": "check_inventory_swim"}
            ]
        )
        
        self.nodes["bash_lock_desperate"] = StoryNode(
            "bash_lock_desperate",
            """You bash the lock with your fists! Pain shoots through your hands!
The lock doesn't budge. The water is at your lips now. You're out of time!

This isn't working!""",
            [
                {"text": "Dive for underwater passage—last chance!", "next": "dive_last_chance"},
                {"text": "Keep bashing—it has to work!", "next": "death_drowning"}
            ]
        )
        
        self.nodes["rinse_wound_water"] = StoryNode(
            "rinse_wound_water",
            """You use water from the drainage tunnel to rinse your wound.
It's not clean water—this might make things worse. But you do your best.

Risk of infection increased slightly.""",
            [
                {"text": "Continue onward", "next": "drainage_tunnel"},
                {"text": "Try to bandage it as well", "next": "bind_wound_cloth"}
            ]
        )
        
        self.nodes["bind_wound_cloth"] = StoryNode(
            "bind_wound_cloth",
            """You tear strips from your already tattered clothes and bind your wound tightly.
It's not medical care, but it helps stop the bleeding.

Bleeding reduced. Health stabilized.""",
            [
                {"text": "Continue forward", "next": "drainage_tunnel"},
                {"text": "Rest briefly", "next": "rest_tunnel"}
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
                {"text": "Look for more symbols", "next": "search_more_symbols"}
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
                {"text": "Drink it immediately", "next": "drink_mystery_vial"}
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
                {"text": "Hide quickly", "next": "hide_near_guard"}
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
                {"text": "Look for a way through", "next": "navigate_grave"}
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
                {"text": "Investigate what he fears", "next": "investigate_door"}
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
                {"text": "Release and finish with torch", "next": "chain_to_torch_finish"}
            ]
        )
        
        self.nodes["switch_to_torch"] = StoryNode(
            "switch_to_torch",
            """You drop the chain and grab the torch with both hands! The ghoul lunges!
You thrust the flame into its face! It shrieks and recoils, but it's not done yet!""",
            [
                {"text": "Press the attack with fire", "next": "ghoul_eyes_torch"},
                {"text": "Create distance and reassess", "next": "create_combat_distance"}
            ]
        )
        
        self.nodes["strangle_ghoul"] = StoryNode(
            "strangle_ghoul",
            """You wrap the chain around the ghoul's throat and pull! It gags and claws
at the chain. You hold on with all your strength. It's a battle of endurance now.
Your muscles burn. The ghoul weakens. It's almost done!""",
            [
                {"text": "Hold on until it dies", "next": "strangle_ghoul_death"},
                {"text": "Let go and escape while it's weak", "next": "escape_weak_ghoul"}
            ]
        )
        
        self.nodes["retreat_from_ghoul"] = StoryNode(
            "retreat_from_ghoul",
            """You back away from the fight, creating distance. The ghoul circles you warily.
You have a moment to think. You're wounded. It's wounded. This could go either way.""",
            [
                {"text": "Continue fighting more carefully", "next": "fight_ghoul_torch"},
                {"text": "Run while you can", "next": "run_from_ghoul"},
                {"text": "Try to negotiate somehow", "next": "talk_to_ghoul"}
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
                {"text": "Move on quickly", "next": "past_ghoul_quick"}
            ]
        )
        
        self.nodes["escape_burning_ghoul"] = StoryNode(
            "escape_burning_ghoul",
            """While it's distracted by the flames, you run! The ghoul's shrieks echo behind you
but you don't look back. You've escaped but didn't finish it. It might recover.""",
            [
                {"text": "Keep running", "next": "run_from_ghoul"},
                {"text": "Find a place to hide", "next": "hide_from_ghoul"}
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
                {"text": "Scream for help", "next": "scream_help"}
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
                {"text": "Take only the metal chain and leave", "next": "take_chain_death"},
                {"text": "Recoil in horror and back away", "next": "recoil_panic_death"},
                {"text": "Use the chain as a weapon", "next": "chain_weapon_death"}
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
                {"text": "Eat the moldy bread immediately", "next": "eat_moldy_bread"}
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
        
        # New deadly versions of choices
        self.nodes["take_chain_death"] = StoryNode(
            "take_chain_death",
            """You grab the chain, avoiding the corpse. A mistake.
The chain is attached to the shackle, which is bolted to the floor.
You waste precious time trying to break it free. The water rises.

By the time you realize the chain won't break, it's too late.
The water is over your head. You try to swim but your strength is gone.

CAUSE OF DEATH: Drowned while wasting time on a useless chain
SURVIVAL TIME: 4 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["recoil_panic_death"] = StoryNode(
            "recoil_panic_death",
            """You recoil from the corpse in terror. The stench, the decay—it overwhelms you.
You back away but slip on the slick floor. Your head cracks against stone.

Dazed, you go under the water. You try to surface but your vision is blurred.
Which way is up? You're disoriented. You breathe in water.

CAUSE OF DEATH: Head injury and drowning (panic killed you)
SURVIVAL TIME: 3 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["chain_weapon_death"] = StoryNode(
            "chain_weapon_death",
            """You wrap the chain around your fist, preparing to fight... what?
There's nothing here but you and a corpse. You've wasted time on a weapon
you don't need while the water rises.

By the time you realize your mistake, the water is at your neck.
You try to find an exit but it's too late. You're too slow.

The chain—now a useless weight—drags you down as you try to swim.

CAUSE OF DEATH: Drowned (wasted time preparing for nonexistent threat)
SURVIVAL TIME: 4 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["after_corpse_loot"] = StoryNode(
            "after_corpse_loot",
            """With the tinderbox secure in your pocket, you pocket the coins too.
You now have a potential source of light—if you can find something to burn.
The water continues to rise. It's now at your shoulders.""",
            [
                {"text": "Search for a door or exit urgently", "next": "search_exit_urgent"},
                {"text": "Try to light the tinderbox to see better", "next": "light_tinderbox_wet"},
                {"text": "Climb onto the corpse to stay above water", "next": "climb_corpse"}
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
                {"text": "Take a deep breath and dive for another way", "next": "dive_last_chance"}
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
                {"text": "Call out to see if anyone responds", "next": "call_out_corridor"}
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
                {"text": "Investigate the chewing sound from a distance", "next": "investigate_chewing"}
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
                {"text": "Examine the walls more closely with the torch", "next": "examine_walls_torch"}
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
                {"text": "Throw something to distract it and slip past", "next": "distract_ghoul"}
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
                {"text": "Hide and observe first", "next": "hide_observe"}
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
                {"text": "Run back and take another path", "next": "run_from_guard"}
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
                {"text": "Attack while he's distracted", "next": "attack_distracted_guard"}
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
                {"text": "Let yourself fall and roll", "next": "fall_and_roll"}
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
                {"text": "Call for help", "next": "call_help_sewer"}
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
                {"text": "Use tinderbox to make light", "next": "use_tinderbox_dark"}
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
                {"text": "Go back up and try another path", "next": "back_up_stairs"}
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
                {"text": "Wait and listen more", "next": "listen_overseer"}
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
                {"text": "Give up and search the water instead", "next": "search_cell_water"}
            ]
        )
        
        self.nodes["climb_wall_holds"] = StoryNode(
            "climb_wall_holds",
            """You grip the carved holds and pull yourself up out of the water.
Your wounded side screams in protest, but fear drives you upward.
Hand over hand, you climb in complete darkness. The holds are slippery with algae.
Suddenly, your hand slips! You're dangling by one arm, twelve feet above the water.""",
            [
                {"text": "Pull yourself back up with sheer willpower", "next": "climb_slip_death"},
                {"text": "Drop back into the water safely", "next": "back_to_water"},
                {"text": "Try to swing to grab another hold", "next": "swing_fail_death"}
            ]
        )
        
        self.nodes["climb_slip_death"] = StoryNode(
            "climb_slip_death",
            """You try to pull yourself up with your wounded body. Your muscles shake.
Your grip fails. You fall!

You crash into the water from twelve feet up. Your head hits the stone floor beneath.
Everything goes dark. You float face-down in the rising water.

CAUSE OF DEATH: Fall from climbing attempt, drowned while unconscious
SURVIVAL TIME: 6 minutes

Ambition without caution kills. The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["swing_fail_death"] = StoryNode(
            "swing_fail_death",
            """You swing your body, trying to reach another hold.
Your wounded side tears open from the strain. The pain is blinding.
Your grip fails. You fall!

You hit the water hard. Blood clouds around you from your reopened wound.
You're too weak to swim. The water is too deep now. You sink.

CAUSE OF DEATH: Fall and blood loss, drowned
SURVIVAL TIME: 6 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
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
                {"text": "Look back through the grate", "next": "look_back_grate"}
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
                {"text": "Leave it and keep searching", "next": "continue_wall_search"}
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
                {"text": "Eat the dried meat immediately", "next": "eat_dried_meat"}
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
                {"text": "Dive underwater to find a way out", "next": "underwater_passage"}
            ]
        )
        
        self.nodes["stand_conserve"] = StoryNode(
            "stand_conserve",
            """You try to stand still and conserve energy, hoping to outlast the rising water.
But the cold is brutal. You're already shivering violently.

The water rises past your waist... your chest... your neck...
You realize too late—standing still was a death sentence.

The cold has sapped too much of your strength. Your limbs won't respond.
The water reaches your mouth. You try to swim but you're too weak, too cold.

CAUSE OF DEATH: Hypothermia and drowning (chose to wait instead of act)
SURVIVAL TIME: 5 minutes

Sometimes inaction is the deadliest choice. The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["panic_search"] = StoryNode(
            "panic_search",
            """You thrash through the water, hands scrambling against the walls.
Your panic makes you clumsy. You slip, go under, come up choking.
The water is at your chin. In your frantic search, your hand finds—
a drainage grate near the ceiling! The water flows through it!""",
            [
                {"text": "Try to open it desperately", "next": "find_drainage_grate"},
                {"text": "Take a deep breath and dive for another way", "next": "underwater_passage"}
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
                {"text": "Feel around the passage entrance", "next": "feel_passage_entrance"}
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
                {"text": "Move toward the breathing sound", "next": "toward_breathing"}
            ]
        )
        
        self.nodes["scream_help"] = StoryNode(
            "scream_help",
            """You scream at the top of your lungs. "HELP! SOMEONE HELP ME!"
Your voice echoes off the stone walls, but no reply comes.
Wait... you hear footsteps above. Someone is coming!

A grating sound—metal on stone. A voice from above, raspy and cruel:
"Well, well. Still alive down there, are we? You're tougher than you look, Zagreus."

A torch appears at the opening above. You see a face—not a guard, but one of your 
former companions. The one who betrayed you. He grins sadistically down at you,
clearly enjoying your suffering.""",
            [
                {"text": "Beg for mercy", "next": "beg_betrayer_mercy"},
                {"text": "Offer him money to help", "next": "bribe_betrayer"},
                {"text": "Curse him and his family", "next": "curse_betrayer"},
                {"text": "Stay silent and stare", "next": "silent_stare_betrayer"}
            ]
        )
        
        self.nodes["beg_betrayer_mercy"] = StoryNode(
            "beg_betrayer_mercy",
            """You beg for your life. "Please! We were friends! Pull me up!"

The betrayer laughs cruelly. "Friends? You were always too trusting, Zagreus.
That's what made it so easy. You actually believed my lies!"

He spits into the water. "Here, let me help you!" He throws down a rope—
but it's far too short, dangling well above your reach.

He cackles with sadistic glee. "Oh, did I miscalculate? How clumsy of me!"

The water is rising faster now. He's clearly enjoying watching you drown.""",
            [
                {"text": "Jump desperately for the rope", "next": "jump_fail_drown"},
                {"text": "Scream curses at him", "next": "curse_betrayer_rage"},
                {"text": "Ignore him and search for another way", "next": "search_wall_desperate"}
            ]
        )
        
        # New nodes for betrayer interaction (replaces guard nodes)
        self.nodes["jump_fail_drown"] = StoryNode(
            "jump_fail_drown",
            """You jump with all your might, fingers grasping for the rope!
You miss by a full arm's length. You try again, exhausting yourself.
The betrayer watches, amused. "Dance, prisoner, dance! Just like old times!"

Your third jump is weaker. The water is at your mouth now.
You'll never reach the rope—it's impossible. He made sure of it.
The hole is too deep, the rope too short. He wants you to die here.

Your only hope is finding another way out of this hell hole.""",
            [
                {"text": "One last desperate search of the walls", "next": "find_hidden_crack"},
                {"text": "Dive underwater for any passage", "next": "dive_last_chance"},
                {"text": "Give up and accept death", "next": "death_drowning"}
            ]
        )
        
        self.nodes["find_hidden_crack"] = StoryNode(
            "find_hidden_crack",
            """Your hands frantically search the slime-covered walls one final time.
Wait—there! A crack in the stonework, barely wide enough for a person.
Hidden beneath the waterline, impossible to see, but you can feel it.

The betrayer's voice echoes from above: "Still struggling? How pathetic!"

You have seconds left. This crack might be your only chance.""",
            [
                {"text": "Squeeze through the crack immediately", "next": "crack_escape"},
                {"text": "Take a breath and dive through underwater", "next": "underwater_crack_passage"}
            ]
        )
        
        self.nodes["crack_escape"] = StoryNode(
            "crack_escape",
            """You force yourself through the narrow crack in the wall!
Stone scrapes your shoulders raw. Your wound tears open wider.
You're barely squeezing through—it's so tight you can't breathe.

Behind you, the betrayer's laughter fades. "Where did you—? NO! That crack
was supposed to be sealed! Guards! GUARDS!"

You push through with desperate strength. Finally, you tumble out the other side
into a dark, narrow passage. Behind you, the crack is flooding with water.
You crawl forward frantically as water chases you up the sloping passage.

After what feels like an eternity, the passage levels out. The water stops rising.
You're safe. Barely. But you escaped the hell hole.""",
            [
                {"text": "Catch your breath and assess injuries", "next": "assess_after_crack"},
                {"text": "Keep moving before they find you", "next": "hidden_passage_forward"},
                {"text": "Tend to your bleeding wound", "next": "emergency_wound_care"}
            ]
        )
        
        self.nodes["underwater_crack_passage"] = StoryNode(
            "underwater_crack_passage",
            """You take the deepest breath possible and dive toward the crack.
The water is murky and foul. You pull yourself through the submerged opening.
It's tighter than you thought—your shoulders barely fit. You're stuck halfway!

Panic threatens to overwhelm you. Your lungs burn. You twist, scrape, push—
and suddenly you're through! You surface in a flooded passage, gasping.

The passage ahead slopes upward. You swim toward air, toward survival.""",
            [
                {"text": "Swim up the passage desperately", "next": "flooded_passage_escape"},
                {"text": "Rest briefly before continuing", "next": "rest_in_water_death"}
            ]
        )
        
        self.nodes["rest_in_water_death"] = StoryNode(
            "rest_in_water_death",
            """You try to rest, treading water. But you're too exhausted, too wounded.
Your strength gives out. You slip beneath the surface. The cold water fills your lungs.

You escaped the betrayer's mockery, but not his trap.

CAUSE OF DEATH: Drowned in flooded passage
SURVIVAL TIME: 6 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["flooded_passage_escape"] = StoryNode(
            "flooded_passage_escape",
            """You swim with desperate strength up the sloping passage.
The water level drops. Your head breaks the surface more often.
Finally, you pull yourself onto dry stone, coughing up water.

You're in a narrow service tunnel—probably used for maintenance centuries ago.
The betrayer's voice is distant now, echoing from far away.
You escaped. But you're badly wounded, freezing, and deep in the dungeon.""",
            [
                {"text": "Crawl forward through the tunnel", "next": "service_tunnel_exploration"},
                {"text": "Check your wounds before moving", "next": "assess_after_crack"},
                {"text": "Listen for pursuit", "next": "listen_for_guards"}
            ]
        )
        
        self.nodes["curse_betrayer_rage"] = StoryNode(
            "curse_betrayer_rage",
            """You scream every curse you know at him. "May the gods damn you! 
May your family suffer! May you die alone and forgotten, you coward!"

The betrayer's face darkens with rage. "How DARE you!" He picks up a large rock.
"Die then, former friend!" He hurls it down at your head with all his strength!

The rock crashes into the water—missing you by inches but creating a huge splash.
You go under, disoriented. When you surface, gasping, he's gone.

But the water is at your chin now. His rage might have saved you by forcing
him to leave, but you're still drowning.""",
            [
                {"text": "Search the walls one last time", "next": "find_hidden_crack"},
                {"text": "Dive for an underwater exit", "next": "dive_last_chance"},
                {"text": "Float and hope for a miracle", "next": "death_drowning"}
            ]
        )
        
        self.nodes["bribe_betrayer"] = StoryNode(
            "bribe_betrayer",
            """You call up: "I have gold! Hidden! Pull me up and I'll tell you where!"

The betrayer's eyes gleam with greed, then he laughs. "Nice try, Zagreus!
But I already took all your gold. Remember? That's how I lured you here!
You always were too trusting. That gold is long gone—spent on wine and whores!"

He spits into the water. "Any other bright ideas before you drown?"

The water is at your chin. He's clearly not going to help.""",
            [
                {"text": "Search desperately for another way out", "next": "find_hidden_crack"},
                {"text": "Curse him with your last breaths", "next": "curse_betrayer_rage"},
                {"text": "Dive underwater to find escape", "next": "dive_last_chance"}
            ]
        )
        
        self.nodes["silent_stare_betrayer"] = StoryNode(
            "silent_stare_betrayer",
            """You say nothing. You just stare at him with cold, hard eyes full of hate.
The betrayer shifts uncomfortably. Something in your gaze unsettles him.
"What? Stop looking at me like that!" But you don't break eye contact.

"F-fine! Rot down there for all I care!" He turns to leave, rattled.
But in his haste, he drops his torch. It falls into the water with a hiss,
plunging everything into darkness.

"Damn it!" you hear him curse above. Then his footsteps fade.
The water is at your mouth. Darkness. Rising water. Death approaching.""",
            [
                {"text": "Search blindly for a way out", "next": "find_hidden_crack"},
                {"text": "Dive down in the darkness", "next": "dive_last_chance"},
                {"text": "Accept your fate", "next": "death_drowning"}
            ]
        )
        
        self.nodes["curse_guard"] = StoryNode(
            "curse_guard",
            """You scream curses at the figure above. "May the gods damn you! May your family suffer!
May you die alone and forgotten!"

A voice laughs—but it's your betrayer.
"Still have fire in you? Good! Makes it more entertaining to watch you drown!"

He tosses down a small object—it splashes into the water near you.
"A gift! For old times' sake!" Then he's gone, laughing.

You search in the dark water and find it—a small vial. Poison? Medicine? 
You'll never know if you don't take the risk.""",
            [
                {"text": "Drink the mysterious vial", "next": "drink_mystery_vial"},
                {"text": "Ignore it and search for exit", "next": "find_hidden_crack"},
                {"text": "Throw it away in disgust", "next": "dive_last_chance"}
            ]
        )
        
        self.nodes["drink_mystery_vial"] = StoryNode(
            "drink_mystery_vial",
            """You uncork the vial and drink it down. It burns like fire!
Your vision blurs. Your heart races. Is it poison? Or...

Suddenly, strength surges through your body! It's a combat stimulant—illegal and dangerous,
but effective. Your muscles bulge with unnatural energy. The pain fades.

But this won't last long. And the side effects will be brutal.
You have maybe five minutes of enhanced strength.""",
            [
                {"text": "Use the strength to force the crack wider", "next": "force_crack_open"},
                {"text": "Dive with enhanced power", "next": "powered_dive_escape"},
                {"text": "Waste time marveling at the power", "next": "stimulant_wears_off_death"}
            ]
        )
        
        self.nodes["force_crack_open"] = StoryNode(
            "force_crack_open",
            """With your enhanced strength, you grip the edges of the hidden crack
and PULL with inhuman force! The ancient stone gives way—crumbling!
You tear the opening wider, making it passable!

Your muscles scream in protest but you don't stop. You force your way through
just as the stimulant wears off. Pain crashes back into you like a wave.

You collapse on the other side, in a service tunnel. Safe. Barely.""",
            [
                {"text": "Assess the damage to your body", "next": "stimulant_aftermath"},
                {"text": "Keep moving before collapse", "next": "service_tunnel_exploration"}
            ]
        )
        
        self.nodes["powered_dive_escape"] = StoryNode(
            "powered_dive_escape",
            """You take a massive breath and dive down with enhanced strength!
You swim deeper than you thought possible, pulling yourself through the underwater
passages with powerful strokes. Your muscles don't tire. You don't need air—or so it feels.

But then the stimulant wears off. Suddenly. All at once.

You're deep underwater, in darkness, and your strength is GONE.
Your lungs burn. You can't remember which way is up. Panic sets in.""",
            [
                {"text": "Calm yourself and feel for current", "next": "underwater_survival"},
                {"text": "Swim randomly in desperation", "next": "death_drowning_deep"},
                {"text": "Give up and breathe in water", "next": "death_drowning"}
            ]
        )
        
        self.nodes["stimulant_wears_off_death"] = StoryNode(
            "stimulant_wears_off_death",
            """You marvel at the power coursing through you, testing your strength.
But you waste precious seconds. The stimulant wears off suddenly.

The crash is brutal. Your heart stutters. Your muscles seize up.
The water is over your head now. You try to swim but your body won't respond.

The drug's side effects—muscle paralysis—hit you all at once.
You sink beneath the water, unable to move, unable to even struggle.

CAUSE OF DEATH: Stimulant overdose and drowning
SURVIVAL TIME: 7 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["underwater_survival"] = StoryNode(
            "underwater_survival",
            """You force yourself to be calm. Feel for the current. Water flows somewhere.
You feel a subtle pull—upward! You swim toward it with your remaining strength.

Your lungs are screaming. Your vision darkens. But you keep going.
Suddenly your head breaks the surface! You gasp, pulling in precious air.

You're in a flooded chamber, but there's air. You can breathe. You survived.""",
            [
                {"text": "Swim to find solid ground", "next": "flooded_chamber_exploration"},
                {"text": "Float and rest before continuing", "next": "rest_in_water_death"}
            ]
        )
        
        self.nodes["death_drowning_deep"] = StoryNode(
            "death_drowning_deep",
            """You swim blindly in the darkness, using your last energy.
But you chose wrong. You swim deeper into the flooded tunnels.

Your lungs give out. You breathe in water. Darkness takes you.

CAUSE OF DEATH: Drowned in deep underwater tunnels
SURVIVAL TIME: 8 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        # New nodes for escape routes and aftermath
        self.nodes["assess_after_crack"] = StoryNode(
            "assess_after_crack",
            """You examine yourself in the dim passage. You're a mess:
- Deep wound on your side (bleeding heavily now)
- Shoulders scraped raw from squeezing through
- Hypothermic from the cold water
- Exhausted beyond measure

You're alive, but barely. You need treatment soon or you'll die from blood loss.""",
            [
                {"text": "Tear cloth to bandage the worst wounds", "next": "emergency_bandage"},
                {"text": "Push forward despite injuries", "next": "hidden_passage_forward"},
                {"text": "Rest here briefly", "next": "rest_and_bleed_death"}
            ]
        )
        
        self.nodes["emergency_bandage"] = StoryNode(
            "emergency_bandage",
            """You tear strips from your soaked clothing and bind your worst wounds.
It's crude and the cloth is filthy, but it slows the bleeding.
You'll likely get infected, but that's a problem for later.

Right now, you just need to survive the next hour.""",
            [
                {"text": "Continue through the passage", "next": "hidden_passage_forward"},
                {"text": "Search the passage for supplies", "next": "search_service_tunnel"}
            ]
        )
        
        self.nodes["rest_and_bleed_death"] = StoryNode(
            "rest_and_bleed_death",
            """You sit down to rest, just for a moment. But you're losing too much blood.
The cold seeps into your bones. Your vision dims. You slump against the wall.

You escaped the betrayer, but not death.

CAUSE OF DEATH: Blood loss and hypothermia
SURVIVAL TIME: 9 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["hidden_passage_forward"] = StoryNode(
            "hidden_passage_forward",
            """You crawl forward through the narrow passage. It twists and turns,
clearly designed for drainage, not travel. Rats scatter before you.

After what feels like an eternity, the passage opens into a larger space.
You emerge in an abandoned storage room. Rotting crates, broken barrels,
and—blessed relief—a dry corner where you can rest.""",
            [
                {"text": "Search the crates for supplies", "next": "search_storage_room"},
                {"text": "Rest in the dry corner", "next": "rest_in_storage"},
                {"text": "Keep moving—they might search here", "next": "exit_storage_room"}
            ]
        )
        
        self.nodes["emergency_wound_care"] = StoryNode(
            "emergency_wound_care",
            """You examine your wound more closely. It's bad—very bad.
The edges are jagged. Something sharp tore through your flesh when you fell.
You're bleeding steadily. You need real medical attention or you'll die.

But you have nothing. No bandages, no medicine, nothing.""",
            [
                {"text": "Tear clothing for crude bandages", "next": "emergency_bandage"},
                {"text": "Try to find fire to cauterize later", "next": "hidden_passage_forward"},
                {"text": "Ignore it and keep moving", "next": "hidden_passage_forward"}
            ]
        )
        
        self.nodes["service_tunnel_exploration"] = StoryNode(
            "service_tunnel_exploration",
            """The service tunnel is narrow but navigable. Ancient maintenance passages,
probably forgotten for centuries. You crawl through, leaving a trail of blood.

You find old tool marks on the walls, signs of long-dead workers.
The tunnel branches ahead—left slopes down, right slopes up.""",
            [
                {"text": "Take the upward path", "next": "tunnel_upward"},
                {"text": "Take the downward path", "next": "tunnel_downward"},
                {"text": "Rest here before deciding", "next": "rest_and_bleed_death"}
            ]
        )
        
        self.nodes["listen_for_guards"] = StoryNode(
            "listen_for_guards",
            """You press your ear to the cold stone, listening intently.
Distant voices... footsteps... but fading. They're searching, but not here.
Not yet. The betrayer must have told them you escaped into the passages.

You have time, but not much. They'll find this tunnel eventually.""",
            [
                {"text": "Move quickly before they find you", "next": "service_tunnel_exploration"},
                {"text": "Hide and wait for them to pass", "next": "hide_in_tunnel"},
                {"text": "Set a trap for pursuers", "next": "tunnel_trap"}
            ]
        )
        
        self.nodes["stimulant_aftermath"] = StoryNode(
            "stimulant_aftermath",
            """The stimulant has worn off completely. The aftermath is brutal.
Your muscles ache like you've been beaten with hammers. Your heart races erratically.
Your hands shake uncontrollably. The drug's side effects are severe.

But you're alive. And you're out of that hell hole.""",
            [
                {"text": "Push through the pain", "next": "service_tunnel_exploration"},
                {"text": "Rest until the shaking stops", "next": "rest_stimulant_death"},
                {"text": "Search for water to dilute the drug", "next": "search_for_water"}
            ]
        )
        
        self.nodes["rest_stimulant_death"] = StoryNode(
            "rest_stimulant_death",
            """You try to rest, but the stimulant's effects won't let you.
Your heart beats faster... and faster... too fast.

Cardiac arrest. The illegal drug stops your heart.
You clutch your chest, gasping, then collapse.

CAUSE OF DEATH: Heart failure from combat stimulant
SURVIVAL TIME: 10 minutes

The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
        )
        
        self.nodes["flooded_chamber_exploration"] = StoryNode(
            "flooded_chamber_exploration",
            """You swim through the flooded chamber, searching for an exit.
The water is dark and cold. Your limbs are numb. But you keep going.

Finally, you find a ledge—solid stone. You pull yourself up, gasping.
You're in some kind of cistern. Water storage from ages past.
There's a ladder built into the wall, leading up into darkness.""",
            [
                {"text": "Climb the ladder immediately", "next": "climb_cistern_ladder"},
                {"text": "Rest on the ledge first", "next": "rest_on_ledge"},
                {"text": "Search the cistern for supplies", "next": "search_cistern"}
            ]
        )
        
        self.nodes["search_wall_desperate"] = StoryNode(
            "search_wall_desperate",
            """You ignore the betrayer's taunts and frantically search the walls.
Your hands are numb from the cold. The water is at your chin.
You have mere seconds. There must be something—anything!

Your hand finds it—a crack. A hidden crack in the stonework!""",
            [
                {"text": "Force yourself through the crack", "next": "crack_escape"},
                {"text": "Take a breath and dive through underwater", "next": "underwater_crack_passage"}
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
                {"text": "Run for the exit door", "next": "run_exit_guardroom"}
            ]
        )

        # Add more missing nodes
        self.nodes["back_to_water"] = StoryNode(
            "back_to_water",
            """You let go and drop back into the water with a splash.
A wise choice—climbing was suicide with your injuries.
The water is even higher now—it's at your shoulders.

As you land, your hand brushes against something in the wall underwater—
a crack! Hidden beneath the waterline. You might be able to squeeze through!""",
            [
                {"text": "Force yourself through the crack immediately", "next": "crack_escape"},
                {"text": "Dive through the crack underwater", "next": "underwater_crack_passage"},
                {"text": "Ignore it and search elsewhere", "next": "ignore_crack_death"}
            ]
        )
        
        self.nodes["ignore_crack_death"] = StoryNode(
            "ignore_crack_death",
            """You ignore the crack—a fatal mistake.
You search elsewhere but find nothing. The water rises to your chin, your mouth, your nose.

You had your chance. You let it slip away.

CAUSE OF DEATH: Drowned (ignored the only escape route)
SURVIVAL TIME: 7 minutes

Sometimes the obvious choice is the right one. The dungeon claims another victim.""",
            [{"text": "Start over", "next": "restart"}]
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
                {"text": "Rest briefly to recover", "next": "rest_after_climb"}
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
                {"text": "Dive down for underwater passage", "next": "underwater_passage"}
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
                {"text": "Keep pulling until you pass out", "next": "death_drowning"}
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
                {"text": "Crawl out of water immediately", "next": "crawl_from_water"}
            ]
        )
        
        self.nodes["pick_lock_grate"] = StoryNode(
            "pick_lock_grate",
            """You try to pick the lock with your fingers, feeling for the mechanism.
It's too dark to see, and you're not a locksmith. The water rises to your lips.
You're out of time. This isn't working!""",
            [
                {"text": "Give up and dive for another way", "next": "dive_last_chance"},
                {"text": "Bash the lock with something", "next": "bash_lock_desperate"}
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
                {"text": "Tear fabric to bandage wound", "next": "bandage_wound_tunnel"}
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
                {"text": "Tear cloth from clothes to bind it", "next": "bind_wound_cloth"}
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
                {"text": "Go back and take the blood trail instead", "next": "blood_trail"}
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
                {"text": "Drink the spirits for the pain", "next": "drink_spirits"}
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
                {"text": "Read more entries", "next": "read_journal_more"}
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
                {"text": "Back away while maintaining distance", "next": "backing_away_ghoul"}
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
                {"text": "Turn and fight—you're cornered", "next": "cornered_fight_ghoul"}
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
                {"text": "Turn and fight now that you have distance", "next": "fight_ghoul_distance"}
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
                {"text": "Retreat and reassess", "next": "retreat_from_ghoul"}
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
                {"text": "Set it fully ablaze with the torch", "next": "ghoul_eyes_torch"}
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
                {"text": "Run past it while it's down", "next": "run_past_wounded_ghoul"}
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
                {"text": "Search the victim's body for supplies instead", "next": "search_victim_body"}
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
                {"text": "Search the victim for other items", "next": "search_victim_body"}
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
                {"text": "Sit among the bones and wait", "next": "wait_in_bones"}
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
                {"text": "Take a moment to center yourself", "next": "meditate_sanity"}
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
                {"text": "Take remaining herbs for later", "next": "herbs_for_later"}
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
                {"text": "Use some to clean your wound", "next": "water_clean_wound"}
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
                {"text": "Keep the note for reference", "next": "keep_note"}
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
                {"text": "Move slowly and carefully", "next": "careful_sewer"}
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
                {"text": "Go back up and try the sewers instead", "next": "sewer_passage"}
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
                {"text": "Run before anyone sees you", "next": "flee_murder_scene"}
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
                {"text": "Attack him while he's gesturing", "next": "surprise_attack_guard"}
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
                {"text": "Trace the symbols with your finger", "next": "touch_symbols"}
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
                {"text": "Wait and observe longer", "next": "observe_guard"}
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
                {"text": "Hide in the shadows quickly", "next": "quick_hide"}
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
                {"text": "Run back the way you came", "next": "run_from_darkness"}
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
                {"text": "Play dead on the ground", "next": "play_dead"}
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
                {"text": "Throw something to distract it", "next": "distract_feeding_ghoul"}
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
        
        # Equipment with durability tracking
        equipped_items = []
        for slot, item in self.state.equipped.items():
            if item:
                # Only show durability for items that actually degrade
                if slot in ["weapon", "armor", "light"]:
                    durability = self.state.equipment_durability.get(slot, 100)
                    equipped_items.append(f"{slot}: {item} ({durability}%)")
                else:
                    equipped_items.append(f"{slot}: {item}")
        
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
                # Apply ongoing damage/effects BEFORE decrementing
                if effect == "bleeding":
                    self.state.health -= STATUS_DAMAGE_BLEEDING
                    print(f"[Bleeding: -{STATUS_DAMAGE_BLEEDING} health]")
                elif effect == "poisoned":
                    self.state.health -= STATUS_DAMAGE_POISONED
                    self.state.stamina -= STAMINA_DRAIN_POISONED
                    print(f"[Poisoned: -{STATUS_DAMAGE_POISONED} health, -{STAMINA_DRAIN_POISONED} stamina]")
                elif effect == "burning":
                    self.state.health -= STATUS_DAMAGE_BURNING
                    print(f"[Burning: -{STATUS_DAMAGE_BURNING} health]")
                elif effect == "infected":
                    self.state.health -= STATUS_DAMAGE_INFECTED
                    self.state.max_health -= MAX_HEALTH_LOSS_INFECTED
                    print(f"[Infected: -{STATUS_DAMAGE_INFECTED} health, max health reduced]")
                
                # Now decrement the turn counter
                self.state.status_effects[effect] = turns - 1
        
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
        
        # Equipment durability - only track weapon, armor, light
        # (accessories and offhand items don't degrade)
        if self.state.turn_count % 8 == 0:
            for slot in ["weapon", "armor", "light"]:
                if self.state.equipped[slot] and self.state.equipment_durability.get(slot, 0) > 0:
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
        print("Few lead to survival. Choose wisely.")
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
