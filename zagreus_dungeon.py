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
        
        # Body parts
        self.left_arm = True
        self.right_arm = True
        self.left_leg = True
        self.right_leg = True
        self.left_eye = True
        self.right_eye = True
        
        # Inventory
        self.inventory = []
        self.equipped = {
            "weapon": None,
            "light": None,
            "armor": None,
            "accessory": None
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
        
        effects = {"damage_taken": 0, "damage_dealt": 0, "status": []}
        
        # Parse action intent
        if "dodge" in action or "evade" in action or "roll" in action:
            success_chance = self.state.agility * 10 + (50 if self.state.equipped["light"] else 0)
            success_chance -= 20 if not self.state.left_leg or not self.state.right_leg else 0
            
            if random.randint(1, 100) < success_chance:
                return (True, "You successfully dodge the attack!", effects)
            else:
                effects["damage_taken"] = random.randint(10, 25)
                return (False, f"You fail to dodge and take {effects['damage_taken']} damage!", effects)
        
        # Attack actions
        weak_points = enemy.get("weaknesses", [])
        if any(word in action for word in ["eye", "eyes"]):
            if "eye" in weak_points or enemy_type == "rat":
                damage = random.randint(20, 40) + self.state.strength
                effects["damage_dealt"] = damage
                return (True, f"You strike the creature's eye! Critical hit for {damage} damage!", effects)
            else:
                effects["damage_taken"] = random.randint(5, 15)
                return (False, f"The creature has no vulnerable eyes. It counters, dealing {effects['damage_taken']} damage!", effects)
        
        if any(word in action for word in ["head", "skull", "brain"]):
            hit_chance = 40 + self.state.agility * 5
            if random.randint(1, 100) < hit_chance:
                damage = random.randint(15, 30) + self.state.strength
                effects["damage_dealt"] = damage
                return (True, f"You bash the creature's head for {damage} damage!", effects)
            else:
                effects["damage_taken"] = random.randint(10, 20)
                return (False, f"You miss the head! The creature retaliates for {effects['damage_taken']} damage!", effects)
        
        if any(word in action for word in ["leg", "legs", "knee"]):
            if "legs" in weak_points:
                damage = random.randint(15, 25) + self.state.strength
                effects["damage_dealt"] = damage
                effects["status"].append("enemy_slowed")
                return (True, f"You cripple its leg! {damage} damage and it's slowed!", effects)
            else:
                damage = random.randint(5, 15) + self.state.strength
                effects["damage_dealt"] = damage
                return (True, f"You hit its leg for {damage} damage.", effects)
        
        # Generic attack
        weapon_bonus = 10 if self.state.equipped["weapon"] else 0
        light_bonus = 10 if self.state.equipped["light"] else -20
        damage = max(1, random.randint(5, 15) + self.state.strength + weapon_bonus + light_bonus)
        effects["damage_dealt"] = damage
        
        # Counter attack chance
        if random.randint(1, 100) > 50:
            effects["damage_taken"] = random.randint(8, 18)
            return (True, f"You deal {damage} damage but take {effects['damage_taken']} in return!", effects)
        
        return (True, f"You strike for {damage} damage!", effects)
    
    def _evaluate_exploration(self, action: str, context: Dict) -> Tuple[bool, str, Dict]:
        effects = {}
        location = context.get("location", "unknown")
        
        # Light-dependent actions
        if "search" in action or "look" in action or "examine" in action:
            if not self.state.equipped["light"] and random.randint(1, 100) > DARKNESS_FAILURE_THRESHOLD:
                return (False, "It's too dark to see anything clearly. You fumble around blindly.", effects)
            
            if "search" in action:
                find_chance = FIND_CHANCE_WITH_LIGHT if self.state.equipped["light"] else FIND_CHANCE_WITHOUT_LIGHT
                if random.randint(1, 100) < find_chance:
                    effects["found_item"] = True
                    return (True, "You find something useful in the darkness!", effects)
                else:
                    return (False, "You search but find nothing of value.", effects)
        
        # Climbing/athletic actions
        if "climb" in action or "jump" in action:
            if not self.state.left_arm or not self.state.right_arm:
                return (False, "You can't climb with your injured arms!", effects)
            
            success_chance = self.state.agility * 8 + self.state.strength * 5
            if random.randint(1, 100) < success_chance:
                return (True, "You successfully make the climb!", effects)
            else:
                effects["damage_taken"] = random.randint(10, 30)
                return (False, f"You fall! Taking {effects['damage_taken']} damage!", effects)
        
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
        
        self.nodes["restart"] = "RESTART"
    
    def show_status(self):
        """Display current player status"""
        print("\n" + "="*60)
        print("STATUS:")
        print(f"Health: {self.state.health}/{self.state.max_health} | Stamina: {self.state.stamina}/{self.state.max_stamina}")
        print(f"Hunger: {self.state.hunger}/100 | Wetness: {self.state.wetness}/100 | Temp: {self.state.temperature}/100")
        print(f"Sanity: {self.state.sanity}/100")
        
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
        equipped_items = [f"{slot}: {item}" for slot, item in self.state.equipped.items() if item]
        if equipped_items:
            print(f"Equipped: {', '.join(equipped_items)}")
        else:
            print("Equipped: Nothing")
        
        # Inventory
        if self.state.inventory:
            print(f"Inventory: {', '.join(self.state.inventory)}")
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
        
        # Hunger increases over time
        if self.state.turn_count % 5 == 0:
            self.state.hunger += 5
            if self.state.hunger >= 100:
                return "death_starvation"
        
        # Wetness decreases slowly
        if self.state.wetness > 0:
            self.state.wetness -= 2
        
        # Health degradation from untreated wounds
        if self.state.health < self.state.max_health and self.state.turn_count % 10 == 0:
            if random.randint(1, 100) > 70:
                self.state.health -= 5
                print("[Your wound worsens...]")
                if self.state.health <= 0:
                    return "death_infection"
        
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
