# 🗺️ ZAGREUS' DESCENT - PATH ANALYSIS

## 📊 FROM START NODE - 5 PATHS

### PATH 1: search_cell_water ✅ MOST VIABLE
**Status:** Working, many branches  
**Depth:** 20+ nodes deep  
**Divergence Points:** 19  
**Outcomes:** Multiple (deaths, escapes, ongoing)

**Key Branches:**
1. search_corpse (major junction)
   - tinderbox_only → OPTIMAL
   - after_corpse_loot → balanced
   - greedy_loot_corpse → creature attack!
   - eat_moldy_bread → poison death

2. drainage_tunnel (checkpoint)
   - torch_corridor → main route
   - examine_symbols → lore/knowledge
   - stealth_corridor → alternate
   - call_out_corridor → risky

3. blood_trail (ghoul encounter)
   - fight_ghoul_torch → combat
   - scare_ghoul_fire → avoidance
   - run_from_ghoul → escape
   - distract_ghoul → stealth

4. wide_hallway (guard encounter)
   - talk_guard → diplomacy
   - attack_guard → combat
   - surrender_guard → risky
   - run_from_guard → escape

**Working Endings:**
- ✅ Multiple escape routes
- ✅ Guard alliance path
- ✅ Stealth escape
- ✅ Combat victories

---

### PATH 2: feel_walls ⚠️ DANGEROUS
**Status:** Quick death or joins Path 1  
**Depth:** 3 nodes  
**Divergence Points:** 2  
**Outcomes:** Mostly deaths

**Branches:**
1. climb_wall_holds
   - climb_slip_death 💀
   - swing_fail_death 💀
   - back_to_water → joins search_cell_water

2. continue_feeling_wall → ?
3. search_cell_water → joins Path 1

**Verdict:** High risk, low reward. Better to start with Path 1.

---

### PATH 3: stand_conserve ❌ BROKEN
**Status:** LEADS NOWHERE  
**Depth:** 1 node  
**Outcome:** Immediate restart

**Issue:** Only leads to "restart" node - NEEDS FIXING

**Suggested Fix:**
```
stand_conserve should lead to:
- death_drowning (timer runs out)
- LESSON: "You waited too long. The water filled the cell."
```

---

### PATH 4: dive_underwater ✅ ALTERNATE ROUTE
**Status:** Working, different path  
**Depth:** 20 nodes  
**Divergence Points:** 18  
**Outcomes:** Joins main path eventually

**Key Features:**
- underwater_passage → dark exploration
- listen_darkness → creature encounter
- Eventually joins drainage_tunnel (same as Path 1)

**Verdict:** Viable alternative start, more dangerous.

---

### PATH 5: scream_help 🏆 SHORTEST ESCAPE!
**Status:** Has a 5-step ending!  
**Depth:** 5 nodes  
**Outcome:** crack_escape ending

**The Path:**
```
start
→ scream_help
→ beg_betrayer_mercy
→ jump_fail_drown
→ find_hidden_crack
→ crack_escape ✅
```

**Issue:** This is TOO SHORT and TOO EASY!

**Needs:** More challenge, traps, or make crack harder to find.

---

## 🎯 MAIN VIABLE PATH (Longest Complete)

```
start
→ search_cell_water (search the water)
→ search_corpse (examine floating corpse)
→ after_corpse_loot (take tinderbox + coins) ← OPTIMAL
→ search_exit_urgent (find way out)
→ find_drainage_grate (discover grate)
→ smash_lock_chain (break it with chain)
→ drainage_tunnel (🏁 CHECKPOINT 1)
→ torch_corridor (lit corridor)
→ take_torch (grab torch)
→ blood_trail (follow blood)
→ fight_ghoul_torch (combat initiated) ⚔️
→ ghoul_eyes_torch (attack weakness)
→ search_victim_body (loot body)
→ equip_dagger_continue (take dagger)
→ wide_hallway (guard encounter)
→ talk_guard (diplomacy) 🗣️
→ bribe_guard (offer coins)
→ sewer_passage_after_guard (go to sewer)
→ grab_sewer_fall (avoid fall)
→ pull_up_sewer (climb up)
→ feel_forward_dark (navigate darkness)
→ ... (continues further)
```

**Estimated total:** 30-40 nodes to escape

---

## 📈 STATISTICS

### Completion Status:
- **Total Nodes:** 559
- **Parsed Story Nodes:** 180
- **Placeholder Nodes:** 379

### Path Health:
- ✅ **Working Paths:** 3 (search_cell_water, dive_underwater, scream_help)
- ⚠️ **Risky Paths:** 1 (feel_walls)
- ❌ **Broken Paths:** 1 (stand_conserve)

### Endings Found:
- 🏆 **Good Endings:** ~5-8
- 💀 **Death Endings:** 22+
- ⚠️ **Incomplete:** Many placeholder nodes

### Divergence Points:
- **High Branching:** search_corpse, drainage_tunnel, blood_trail, wide_hallway
- **Auto-Checkpoints Needed At:**
  - search_corpse (4 diverging paths)
  - drainage_tunnel (4 diverging paths)
  - blood_trail (4 diverging paths - before ghoul)
  - wide_hallway (4 diverging paths - before guards)

---

## 🔧 FIXES NEEDED

### 1. BROKEN PATHS TO FIX:
- ❌ **stand_conserve** → leads to restart (NEEDS DEATH SCENE)
- ⚠️ **scream_help** → too short, needs more challenge

### 2. PLACEHOLDER NODES (379 total):
Many divergence options lead to "[Under Development]" placeholders.

**Priority to Complete:**
- lie_to_guard
- appeal_guard
- attack_guard
- surrender_guard
- sewer_passage paths
- descend_stairs
- hide_observe
- ALL guard encounter variations
- ALL ghoul combat variations

### 3. AUTO-CHECKPOINTS TO ADD:
Currently: 8 checkpoints
Recommended: Add at these diverging points:
- ✅ search_corpse (already exists)
- ✅ drainage_tunnel (already exists)
- ✅ blood_trail (already exists)
- ✅ wide_hallway (should add: guard_room_entry)
- ➕ equip_dagger_continue (before major junction)
- ➕ bribe_guard (after successful diplomacy)

---

## 🏆 RECOMMENDED OPTIMAL PATH

For best story experience:
```
1. search_cell_water (explore)
2. search_corpse (pragmatic)
3. after_corpse_loot (balanced loot)
4. search_exit_urgent (time pressure)
5. find_drainage_grate (discovery)
6. smash_lock_chain (decisive action)
7. drainage_tunnel (checkpoint - safe!)
8. examine_symbols (learn ghoul weakness)
9. torch_corridor (proceed)
10. take_torch (equip fire)
11. blood_trail (cautious)
12. fight_ghoul_torch (combat - use fire!)
13. ghoul_eyes_torch (exploit weakness learned)
14. search_victim_body (loot reward)
15. equip_dagger_continue (arm yourself)
16. wide_hallway (checkpoint - safe!)
17. talk_guard (smart choice)
18. bribe_guard (use coins you took)
19. ask_about_harvester (get info)
20... (continues to escape)
```

**This path rewards:**
- ✅ Exploration (examining symbols)
- ✅ Logical thinking (using fire on ghoul)
- ✅ Resource management (coins for bribe)
- ✅ Avoiding greed (didn't take everything)

---

## 🎮 SUMMARY

**WORKING:**
- Path 1 (search_cell_water) - MAIN ROUTE
- Path 4 (dive_underwater) - ALTERNATE ROUTE
- Path 5 (scream_help) - SHORT ESCAPE (too easy?)

**NEEDS WORK:**
- Path 2 (feel_walls) - mostly deaths, needs better outcomes
- Path 3 (stand_conserve) - BROKEN, needs death scene

**PLACEHOLDER COUNT:** 379 nodes need completion

**ESTIMATED PLAYTHROUGH:** 
- Shortest: 5 steps (scream_help - needs balancing!)
- Optimal: 30-40 steps (search_cell_water path)
- Full exploration: 100+ nodes if checking all branches

---

Generated: November 2024
Game Version: 2.3
