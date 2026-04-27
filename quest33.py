# =============================================================================
#  QUEST (inspired by DnD)
# =============================================================================
#  HOW TO RUN:
#    1. Install Pygame:   pip install pygame
#    2. Run the game:     python dungeon_quest.py
# =============================================================================
#  HOW TO CUSTOMIZE:
#    You can change characters, story scenes, colors, dice rules, and more!
# =============================================================================

import pygame
import random
import sys
import math
import time

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# =============================================================================
# MUSIC ENGINE
#
#     music/beginning.mp3   - title screen, character select, safe scenes
#     music/chase.mp3       — normal & mystery scenes (forest, bridge, etc.)
#     music/fight.mp3       — combat scenes and dice rolls
#     music/victory.mp3     — victory ending
#     music/defeat.mp3      — game over ending
#
#   Supported formats: .mp3  .ogg  .wav  .flac
#   If you want to use different filenames, edit MUSIC_FILES.
#
#   HOW TO CHANGE VOLUME:
#   Edit MUSIC_VOLUME below (0.0 = silent, 1.0 = full volume)
#
#   HOW TO CHANGE WHICH TRACK PLAYS WHEN:
#   Edit play_music_for_scene()
# =============================================================================

import os

# Makes image/music paths work both as a script and as a compiled .app
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MUSIC_VOLUME  = 0.6
MUSIC_FADE_MS = 1200    # Crossfade duration in milliseconds

# MUSIC FILES
#   Path is relative to the folder where this script lives.
MUSIC_FILES = {
    "beginning": "music/beginning.mp3",   # calm / title
    "chase":     "music/chase.mp3",       # tense exploration
    "fight":     "music/fight.mp3",       # combat
    "victory":   "music/victory.mp3",     # win ending
    "defeat":    "music/defeat.mp3",      # lose ending
    "the_girl":  "music/the_girl.mp3",    # scene-specific: the tavern girl — romantic/mysterious
    "castle":    "music/castle.mp3",      # scene-specific: castle and princess scenes
}


class MusicEngine:
    """
    Loads music files from the /music folder and plays them with smooth
    crossfades. Falls back silently if a file is missing.
    """

    def __init__(self):
        self._current  = None
        self._base_dir = BASE_DIR
        # Verify which files actually exist and warn about missing ones
        for track, rel_path in MUSIC_FILES.items():
            full = os.path.join(self._base_dir, rel_path)
            if not os.path.exists(full):
                print(f"[Music] Missing: {rel_path}  — '{track}' track will be silent")
        pygame.mixer.music.set_volume(MUSIC_VOLUME)

    def play(self, track):
        """Switch to a track with a crossfade. Does nothing if already playing."""
        if track == self._current:
            return
        rel_path = MUSIC_FILES.get(track)
        if not rel_path:
            return
        full_path = os.path.join(self._base_dir, rel_path)
        if not os.path.exists(full_path):
            self._current = track   # mark as active
            return
        try:
            pygame.mixer.music.fadeout(MUSIC_FADE_MS)
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(loops=-1, fade_ms=MUSIC_FADE_MS)
            self._current = track
        except Exception as e:
            print(f"[Music] Could not play '{full_path}': {e}")

    def stop(self):
        pygame.mixer.music.fadeout(MUSIC_FADE_MS)
        self._current = None


def play_music_for_scene(music, scene):
    """
    MUSIC SCENE MAPPING
    Controls which track plays for each scene type.
    Edit the mapping below to change what plays when.

    scene types:  "normal"  "combat"  "mystery"  "safe"
    special IDs:  "victory"  "game_over"
    """
    sid   = scene.get("id",   "")
    stype = scene.get("type", "normal")

    # Scenes that use the romantic/mysterious girl track
    GIRL_SCENES = {
        "the_girl", "the_outside_1", "the_outside_2",
        "the_tavern", "happyend",
    }

    # Castle and princess scenes
    CASTLE_SCENES = {
        "to_the_castle", "the_test", "the_meeting",
        "meeting_story_impressed", "meeting_story",
        "refused_quest", "escaped_castle", "beaten_out",
    }

    if sid == "victory":
        music.play("victory")
    elif sid == "game_over":
        music.play("defeat")
    elif sid in CASTLE_SCENES:
        music.play("castle")
    elif sid in GIRL_SCENES:
        music.play("the_girl")
    elif stype == "combat":
        music.play("fight")
    elif stype == "safe":
        music.play("beginning")
    elif stype in ("normal", "mystery"):
        music.play("chase")
    else:
        music.play("beginning")


# =============================================================================
#   WINDOW & DISPLAY SETTINGS
#   Change SCREEN_WIDTH / SCREEN_HEIGHT to resize the game window.
#   Change GAME_TITLE to rename the game.
# =============================================================================
SCREEN_WIDTH  = 1440
SCREEN_HEIGHT = 900
FPS           = 60
GAME_TITLE    = "QUEST 33" 


# =============================================================================
#   COLOR PALETTE
#   All colors used throughout the game are defined here.
#   Change any hex/RGB value to restyle the whole game at once.
#   Format: RGB
# =============================================================================
C = {
    # Backgrounds — deep night sky derived from French Blue (#414288)
    "bg":           (  8,  8, 28),    # Main dark background
    "panel":        ( 18, 18, 50),    # Card / panel background
    "panel_light":  ( 30, 30, 72),    # Slightly lighter panel

    # Borders & accents — neutral, no green or red
    "border":       ( 65, 66, 136),   # French Blue  #414288
    "border_hi":    (110, 112, 190),  # Lighter French Blue — highlight
    "gold":         (240, 234, 210),  # Vanilla Cream #F0EAD2 — headings
    "gold_dim":     (169, 132, 103),  # Faded Copper  #A98467 — dimmer accent

    # Text — neutral tones only (no green, no red)
    "text":         (240, 234, 210),  # Vanilla Cream #F0EAD2 — main body
    "text_dim":     (169, 132, 103),  # Faded Copper  #A98467 — secondary
    "text_red":     (195,  65,  75),  # Earthy Crimson — ONLY for damage/danger
    "text_green":   (152, 223, 175),  # Celadon #98DFAF — ONLY for healing/success
    "text_blue":    ( 95, 180, 156),  # Ocean Mist #5FB49C — magic/info (teal, not semantic green)

    # Buttons — neutral French Blue family
    "btn":          ( 25, 25,  72),   # Dark French Blue — default
    "btn_hover":    ( 65, 66, 136),   # French Blue #414288 — hovered
    "btn_press":    ( 85, 86, 158),   # Lighter French Blue — pressed
    "btn_border":   (110, 112, 190),  # Light French Blue — border (no green)

    # Health & XP bars
    "hp_bg":        ( 45, 12,  18),   # Dark crimson background
    "hp_fill":      (195,  65,  75),  # Earthy Crimson — RED = losing HP = bad
    "hp_fill_low":  (220, 100,  50),  # Burnt Orange — critical HP warning
    "xp_bg":        ( 15, 22,  50),   # Dark blue background
    "xp_fill":      (152, 223, 175),  # Celadon — GREEN = gaining XP = good

    # Dice
    "dice_bg":      ( 22, 22,  60),   # Dark French Blue face
    "dice_border":  ( 65, 66, 136),   # French Blue #414288
    "dice_pip":     (240, 234, 210),  # Vanilla Cream #F0EAD2 — number
    "dice_success": (152, 223, 175),  # Celadon — GREEN = success = good
    "dice_fail":    (195,  65,  75),  # Earthy Crimson — RED = failure = bad

    # Character class theme colors — distinct, non-semantic tones
    "warrior": (169, 132, 103),       # Faded Copper  #A98467
    "mage":    ( 95, 180, 156),       # Ocean Mist    #5FB49C (teal, not semantic green)
    "rogue":   (150, 100, 170),       # Muted Violet  — added from Deep Purple family
    "paladin": (192, 192, 210),       # Silver-blue — cool metallic

    # Scene type accent bars
    "scene_normal":  ( 65,  66, 136), # French Blue   #414288 — neutral
    "scene_combat":  (195,  65,  75), # Earthy Crimson — RED = danger/combat
    "scene_mystery": ( 95, 180, 156), # Ocean Mist    #5FB49C — teal mystery
    "scene_safe":    (152, 223, 175), # Celadon — GREEN = safe/rest = good

    # Misc
    "overlay":      (  0,   0,   0),  # Overlay fade color (keep black)
    "white":        (240, 234, 210),  # Vanilla Cream as soft white
    "black":        (  8,   8,  28),  # Deep navy as soft black
}

# =============================================================================
#   FONTS
#   Define which system fonts to use for each purpose.
#   Pygame looks for these by name; if not found it uses a fallback.
# =============================================================================
# =============================================================================
#   FONT FILES
#   The game auto-downloads these TTF fonts on first run into a local
#   "fonts/" folder next to the script. No manual install needed.
#
#   To swap fonts, replace the URLs and filenames below.
#   Free fantasy fonts to try:
#     MedievalSharp  — https://www.fontsquirrel.com/fonts/medievalsharp
#     Uncial Antiqua — https://fonts.google.com/specimen/Uncial+Antiqua
#     IM Fell English— https://fonts.google.com/specimen/IM+Fell+English
# =============================================================================
def load_fonts():
    """Load all fonts used in the game. Edit sizes here to scale the UI."""
    def f(name, size, bold=False):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except:
            return pygame.font.SysFont("georgia", size, bold=bold)
 
    return {
        "title":     f("palatino",    62, bold=True),   # Main menu title
        "heading":   f("palatino",    36, bold=True),   # Scene headings
        "char_name": f("didot",    28, bold=True),   # Character names
        "button":    f("palatino",    21, bold=False),  # Button labels
        "body":      f("palatino", 21),              # Story body — more legible than Didot at small sizes
        "small":     f("palatino", 18),              # Stat labels
        "tiny":      f("palatino", 16),              # Tiny notes
        "dice_big":  f("didot",    56, bold=True),   # Dice number
        "stat":      f("palatino", 20, bold=True),   # Stat numbers
    }



# =============================================================================
#   CHARACTER CLASSES
#   This list defines all playable characters.
#   Add a new dict to add a new character, remove one to remove it.
#
#   Fields:
#     name        — shown on character select screen
#     desc        — flavour description (use \n for line breaks)
#     hp          — starting hit points (max HP)
#     attack      — bonus added to attack dice rolls
#     defense     — damage reduction in combat
#     magic       — bonus added to magic/spell rolls
#     luck        — bonus added to luck/stealth checks
#     color       — theme color key (must exist in C dict above)
#     icon        — a Unicode symbol shown as the character icon
#     abilities   — list of special ability names (flavour only for now)
# =============================================================================
CHARACTERS = [
    {
        "name":      "Warrior",
        "desc":      "A mighty fighter clad in\nheavy armor and iron will.\nHigh HP and raw strength.",
        "hp":        120,
        "attack":    14,
        "defense":   10,
        "magic":      3,
        "luck":       5,
        "color":     "warrior",
        "icon":      "⚔",
        "abilities": ["Power Strike", "Shield Bash", "Battle Cry"],
        "images": [
            "images/warrior_1.png",   # [0] character select card
            "images/warrior_2.png",   # [1] exploration scenes
            "images/warrior_3.png",   # [2] combat scenes
            "images/warrior_4.png",   # [3] victory screen
        ],
        "portrait": "images/warrior_1.png",
    },
    {
        "name":      "Mage",
        "desc":      "A scholar of the arcane arts.\nFragile but devastatingly\npowerful from afar.",
        "hp":         70,
        "attack":      6,
        "defense":     3,
        "magic":      20,
        "luck":        8,
        "color":     "mage",
        "icon":      "✦",
        "abilities": ["Fireball", "Frost Nova", "Arcane Surge"],
        "images": [
            "images/mage_1.png",
            "images/mage_2.png",
            "images/mage_3.png",
            "images/mage_4.png",
        ],
        "portrait": "images/mage_1.png",
    },
    {
        "name":      "Rogue",
        "desc":      "A cunning trickster who\nstrikes unseen from the dark.\nHigh luck and agility.",
        "hp":         90,
        "attack":     12,
        "defense":     6,
        "magic":       5,
        "luck":       15,
        "color":     "rogue",
        "icon":      "◈",
        "abilities": ["Backstab", "Smoke Bomb", "Pickpocket"],
        "images": [
            "images/rogue_1.png",
            "images/rogue_2.png",
            "images/rogue_3.png",
            "images/rogue_4.png",
        ],
        "portrait": "images/rogue_1.png",
    },
    {
        "name":      "Paladin",
        "desc":      "A holy warrior of the light.\nBalances sword and faith,\ncan heal and smite alike.",
        "hp":        110,
        "attack":     12,
        "defense":    12,
        "magic":      10,
        "luck":        8,
        "color":     "paladin",
        "icon":      "✠",
        "abilities": ["Holy Smite", "Divine Shield", "Lay on Hands"],
        "images": [
            "images/paladin_1.png",
            "images/paladin_2.png",
            "images/paladin_3.png",
            "images/paladin_4.png",
        ],
        "portrait": "images/paladin_1.png",
    },
]


# =============================================================================
#   DICE CONFIGURATION
#   Define which dice are available in the game.
#   Format: "label" → number_of_sides
# =============================================================================
DICE = {
    "d6":  6,
    "d8":  8,
    "d10": 10,
    "d20": 20,
}

#  Default dice type used for combat/skill checks 
DEFAULT_DICE = "d20"


# =============================================================================
#   GAME RULES
#   Tunes the difficulty and mechanics of the game
# =============================================================================
RULES = {
    #  XP needed to level up (currently not used)
    "xp_per_level": 200,
    "hx_per_level": 100,
    "rx_per_level": 100,

    # If HP drops to or below this, the HP bar turns orange as a warning
    "low_hp_threshold": 30,

    #   Multiplier applied to attack stat when it's added to the dice roll
    #   E.g. 0.5 means only half your attack stat is added
    "stat_to_bonus_ratio": 0.5,
}


# =============================================================================
#   THE STORY — ALL SCENES
#   Edit or add scenes to change the adventure.
#
#   Each scene is a dict with keys:
#     id          — unique string identifying this scene (used in "next" fields)
#     title       — short heading shown at the top of the scene
#     image       — a Unicode symbol shown large as scene art
#     text        — the narrative text (\n = new line)
#     type        — visual accent: "normal" | "combat" | "mystery" | "safe"
#     choices     — list of choice dicts (see below)
#
#   Each choice dict:
#     label       — text shown on the button
#     next        — scene ID to go to when this choice is picked
#     effect      — (optional) {"hp": N, "xp": N} — change HP/XP on pick
#                   positive = gain, negative = lose
#     dice        — (optional) dict triggering a dice check:
#                   {
#                     "type": "d20",          ← which dice (key from DICE)
#                     "dc":   12,             ← difficulty class (target number)
#                     "stat": "attack",       ← stat bonus: attack/defense/magic/luck
#                     "label": "Roll now!",   ← text shown on the roll button
#                   }
#     success_next — if a dice check PASSES, go here instead of "next"
#                    (if omitted, success and failure both go to "next")
#
#   SPECIAL scene IDs (use as "next" values):
#     "__restart__"   ... restarts the entire game from the title screen
#
# =============================================================================
STORY = {

    "intro": {
        "id":    "intro",
        "title": "A Beginning Without Direction",
        "image": "portrait",
        "type":  "safe",
        "text": (
            "He has coins in his pocket and silence in his chest.\n"
            "He has everything the world promised would be enough, but it is not.\n\n"
            "He has heard of Aaru — a city that breathes, that hums,\n"
            "that holds people the way a cupped hand holds water.\n"
            "A place where something waits for him.\n"
            "He has never stopped believing this.\n\n"
            "Between here and there lies the Darkwood —\n"
            "a forest that does not forgive the uncertain.\n\n"
            "He does not know what he is searching for.\n"
            "Only that he has been searching for a long time.\n\n"
            "He walks alone. No one ahead. No one behind.\n\n"
            "And somewhere beneath the noise of his own footsteps,\n"
            "a single wish, worn smooth from being carried so long:\n\n"
            "to stop waking up to silence."
        ),
        "choices": [
            {
                "label": "Continue...",
                "next":  "start"
            }
        ],
    },


    # -----------------------------------------------------------------------
    # OPENING — The starting scene
    # -----------------------------------------------------------------------
    "start": {
        "id":    "start",
        "title": "The Adventure Begins",
        "image": "🌲",
        "type":  "normal",
        "text": (
            "You stand at the edge of the Darkwood Forest.\n"
            "A crumbling notice board reads:\n\n"
            "  'REWARD — 1,000 gold for the brave soul\n"
            "   who slays the Shadow Drake plaguing\n"
            "   Deshaven Village.'\n\n"
            "The forest looms before you, dark and still.\n"
            "Somewhere deep within, a wolf howls."
        ),
        "choices": [
            {
                "label": "Enter the forest path",
                "next":  "forest_path",
            },
            {
                "label":  "Visit the village first",
                "next":   "village",
            },
            {
                "label":  "Make camp and rest",
                "next":   "camp",
                "effect": {"hp": 15},   # Resting restores 15 HP
            },
        ],
    },

    # -----------------------------------------------------------------------
    # VILLAGE — A safe stop. Gives HP and useful information
    # -----------------------------------------------------------------------
    "village": {
        "id":    "village",
        "title": "Deshaven Village",
        "image": "images/millhaven.png",
        "type":  "mystery",
        "text": (
            "The villagers look hollow-eyed and afraid.\n"
            "An old innkeeper presses a healing potion\n"
            "into your hands without a word.\n\n"
            "  'The drake lairs past the Old Bridge,\n"
            "   deep in the Darkwood. It fears light —\n"
            "   an old ranger told us that much.'\n\n"
            "You gain a piece of vital knowledge."
        ),
        "choices": [
            {
                "label":  "Head into the forest",
                "next":   "forest_path",
                "effect": {"xp": 10},  
            },
            {
                "label":  "Ask about the secret cave",
                "next":   "cave_hint",
                "effect": {"xp": 15},
            },
        ],
    },

    "cave_hint": {
        "id":    "cave_hint",
        "title": "A Hushed Secret",
        "image": "images/millhaven.png",
        "type":  "mystery",
        "text": (
            "An old ranger in the corner leans forward\n"
            "and whispers to you.\n\n"
            "  'There's a hidden tunnel behind the\n"
            "   waterfall east of the Old Bridge.\n"
            "   One who enters unseen... strikes first.'\n\n"
            "You file the information carefully away."
        ),
        "choices": [
            {
                "label":  "Head into the forest",
                "next":   "forest_path",
                "effect": {"xp": 20},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # CAMP — A rest scene with a dice-gated random event
    # -----------------------------------------------------------------------
    "camp": {
        "id":    "camp",
        "title": "A Night's Rest",
        "image": "images/rest.png",
        "type":  "safe",
        "text": (
            "You make camp under a canopy of stars.\n"
            "The fire crackles warmly as you sharpen\n"
            "your weapons and eat a modest meal.\n\n"
            "Halfway through the night you hear\n"
            "something rustling in the undergrowth..."
        ),
        "choices": [
            {
                "label":       "Investigate the noise",
                "next":        "camp_ambush",       # fail --> ambush
                "success_next":"camp_safe",         # pass --> harmless
                "dice": {
                    "type":  "d20",
                    "dc":    10,                    # DC 10 — easy check
                    "stat":  "luck",
                    "label": "Roll for Luck!",
                },
            },
            {
                "label": "Ignore it and sleep",
                "next":  "forest_path",
            },
        ],
    },

    "camp_safe": {
        "id":    "camp_safe",
        "title": "Just a Deer",
        "image": "images/deer.png",
        "type":  "safe",
        "text": (
            "You find a beautiful deer grazing in the clearing.\n"
            "Your stomach growls — you are very hungry.\n"
            "Do you hunt it for food or spare it?"
        ),
        "choices": [
            {
                "label":  "Continue to the forest",
                "next":   "forest_path",
                "effect": {"xp": 10},
            },
            {"label": "Hunt the deer", "next": "forest_path", "effect": {"hp": 30, "hx": 0}}, # zero means no adding
            {"label": "Spare the deer", "next": "forest_path", "effect": {"hp": 0, "hx": 10}}
        ],
    },

    "camp_ambush": {
        "id":    "camp_ambush",
        "title": "Goblin Ambush!",
        "image": "images/goblins.png",
        "type":  "combat",
        "text": (
            "Three goblins burst from the bushes!\n"
            "Blades flash in the firelight.\n\n"
            "You fight them off with furious strikes,\n"
            "but take 20 HP in wounds before they flee."
        ),
        "choices": [
            {
                "label":  "Patch up and move on",
                "next":   "forest_path",
                "effect": {"hp": -20, "xp": 30},   # Lose 20 HP, gain 30 XP
            },
        ],
    },

    # -----------------------------------------------------------------------
    # FOREST PATH — The main branch point of the adventure
    # -----------------------------------------------------------------------
    "forest_path": {
        "id":    "forest_path",
        "title": "The Darkwood",
        "image": "images/darkwood.png",
        "type":  "normal",
        "text": (
            "The Darkwood swallows the last of the light.\n"
            "Twisted roots claw at your boots. Strange\n"
            "whispers drift between gnarled black trees.\n\n"
            "You reach a fork in the path:\n"
            "  LEFT - the sound of rushing water\n"
            "  AHEAD - the old road, dark and overgrown"
        ),
        "choices": [
            {
                "label": "Go left — follow the water",
                "next":  "river_crossing",
            },
            {
                "label": "Press ahead on the old road",
                "next":  "lair_entrance",
                "effect": {"xp": 10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # RIVER CROSSING — A skill check on a crumbling bridge
    # -----------------------------------------------------------------------
    "river_crossing": {
        "id":    "river_crossing",
        "title": "The Old Bridge",
        "image": "images/bridge.png",
        "type":  "normal",
        "text": (
            "You reach a crumbling stone bridge over a\n"
            "fast black river. The stones shift under\n"
            "your weight with every step.\n\n"
            "Halfway across, the bridge begins to give way!"
        ),
        "choices": [
            {
                "label":       "Sprint across!",
                "next":        "bridge_fall",       # fail
                "success_next":"bridge_success",    # pass
                "dice": {
                    "type":  "d20",
                    "dc":    12,                    # DC 12 — moderate check
                    "stat":  "luck",
                    "label": "Sprint! (Roll Luck)",
                },
            },
            {
                "label":  "Wade through the river",
                "next":   "river_wade",
                "effect": {"hp": -10},             # Cold water costs 10 HP
            },
        ],
    },

    "bridge_success": {
        "id":    "bridge_success",
        "title": "Safe Crossing!",
        "image": "images/bridge_success.png",
        "type":  "safe",
        "text": (
            "You sprint across just as the bridge\n"
            "collapses behind you with a thunderous crash.\n\n"
            "You catch your breath on the far bank,\n"
            "heart pounding but unharmed."
        ),
        "choices": [
            {
                "label":  "Push deeper into the forest",
                "next":   "lair_entrance",
                "effect": {"xp": 25},
            },
        ],
    },

    "bridge_fall": {
        "id":    "bridge_fall",
        "title": "Into the Current!",
        "image": "images/bridge.png",
        "type":  "combat",
        "text": (
            "The bridge gives way with a crack!\n"
            "You plunge into the icy black river\n"
            "and are swept downstream.\n\n"
            "You haul yourself ashore — bruised,\n"
            "soaking wet, and 25 HP poorer."
        ),
        "choices": [
            {
                "label":  "Drag yourself onward",
                "next":   "lair_entrance",
                "effect": {"hp": -25, "xp": 15},
            },
        ],
    },

    "river_wade": {
        "id":    "river_wade",
        "title": "Wading Through",
        "image": "images/moss.png",
        "type":  "normal",
        "text": (
            "The freezing water saps your strength,\n"
            "but you make it across safely.\n\n"
            "On the far bank you spot a cluster of\n"
            "glowing moss — the old ranger mentioned\n"
            "the drake fears light. You pocket some."
        ),
        "choices": [
            {
                "label":  "Continue to the lair",
                "next":   "lair_entrance",
                "effect": {"xp": 20},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # DRAKE'S LAIR — The final area with multiple approach options
    # -----------------------------------------------------------------------
    "lair_entrance": {
        "id":    "lair_entrance",
        "title": "The Shadow Drake's Lair",
        "image": "images/dragon.png",
        "type":  "combat",
        "text": (
            "You stand before a vast cave mouth.\n"
            "Charred bones litter the entrance.\n\n"
            "A low, deep rumble echoes from within —\n"
            "the slow breathing of something enormous.\n\n"
            "You steel yourself. This is it."
        ),
        "choices": [
            {
                "label": "Rush in boldly",
                "next":  "fight_bold",
            },
            {
                "label":       "Creep in carefully",
                "next":        "fight_sneak",
                "success_next":"fight_advantage",
                "dice": {
                    "type":  "d20",
                    "dc":    11,                    # DC 11 — moderate check
                    "stat":  "luck",
                    "label": "Sneak in (Roll Luck)",
                },
            },
            {
                "label":  "Search for another entrance",
                "next":   "side_tunnel",
                "effect": {"xp": 20},
            },
        ],
    },

    "side_tunnel": {
        "id":    "side_tunnel",
        "title": "The Hidden Tunnel",
        "image": "images/tunnel.png",
        "type":  "mystery",
        "text": (
            "You circle the cave and find a narrow\n"
            "tunnel carved into the rock behind a\n"
            "waterfall. Inside, an old adventurer's\n"
            "skeleton clutches a vial of dragon-bane oil.\n\n"
            "You coat your weapon. This will sting it."
        ),
        "choices": [
            {
                "label":  "Attack from behind!",
                "next":   "fight_advantage",
                "effect": {"xp": 25},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # FINAL BATTLES — The climax. Dice checks determine win or loss
    # -----------------------------------------------------------------------
    "fight_bold": {
        "id":    "fight_bold",
        "title": "Face to Face!",
        "image": "🔥",
        "type":  "combat",
        "text": (
            "The Shadow Drake rears up, ENORMOUS.\n"
            "Its breath is living shadow — it burns.\n\n"
            "You take a direct blast to the chest!\n"
            "30 HP of searing pain. But your charge\n"
            "connects and you draw first blood.\n\n"
            "One last strike could end this!"
        ),
        "choices": [
            {
                "label":       "Press the attack!",
                "next":        "forest_defeat",
                "success_next":"victory",
                "effect":      {"hp": -30, "xp": 60},
                "dice": {
                    "type":  "d20",
                    "dc":    14,                    # DC 14 — hard final check
                    "stat":  "attack",
                    "label": "Strike! (Roll Attack)",
                },
            },
        ],
    },

    "fight_sneak": {
        "id":    "fight_sneak",
        "title": "Spotted!",
        "image": "👁",
        "type":  "combat",
        "text": (
            "The drake's shadow-sight pierces the dark!\n"
            "Its tail lashes out and catches you full\n"
            "in the side — 20 HP of brutal force.\n\n"
            "You scramble upright for a final stand."
        ),
        "choices": [
            {
                "label":       "Final stand!",
                "next":        "forest_defeat",
                "success_next":"victory",
                "effect":      {"hp": -20, "xp": 50},
                "dice": {
                    "type":  "d20",
                    "dc":    15,                    # DC 15 — harder (spotted penalty)
                    "stat":  "attack",
                    "label": "Fight! (Roll Attack)",
                },
            },
        ],
    },

    "fight_advantage": {
        "id":    "fight_advantage",
        "title": "You Have the Edge!",
        "image": "⚡",
        "type":  "combat",
        "text": (
            "You emerge from the shadows and drive your\n"
            "weapon deep into the drake's flank!\n\n"
            "It howls in agony — confused and wounded.\n"
            "The beast thrashes, clipping you for 10 HP.\n\n"
            "Now finish it before it recovers!"
        ),
        "choices": [
            {
                "label":       "Deliver the killing blow!",
                "next":        "forest_defeat",
                "success_next":"victory",
                "effect":      {"hp": -10, "xp": 70, "rx": 20},
                "dice": {
                    "type":  "d20",
                    "dc":    10,                    # DC 10 — easier (advantage)
                    "stat":  "attack",
                    "label": "Finish it! (Roll Attack)",
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    # ENDINGS
    # -----------------------------------------------------------------------
    "forest_defeat": {
        "id":    "forest_defeat",
        "title": "Darkness Falls...",
        "image": "💀",
        "type":  "combat",
        "text": (
            "The Shadow Drake's claws find their mark.\n"
            "A cold darkness closes around you.\n\n"
            "Your adventure ends here, brave soul.\n\n"
            "But the dungeon whispers of second chances\n"
            "for those bold enough to try again..."
        ),
        "choices": [
            {"label": "Try Again", "next": "__restart__", "effect": {"hp": -50}},
        ],
    },

    "victory": {
        "id":    "victory",
        "title": "VICTORY!",
        "image": "🏆",
        "type":  "safe",
        "text": (
            "Your blade finds the soft underbelly!\n"
            "With a thunderous crash the Shadow Drake\n"
            "falls, and the darkness lifts from the wood.\n\n"
            "The village erupts in celebration as you\n"
            "emerge from the forest, triumphant.\n\n"
            "     You are a TRUE HERO!  "
        ),
        "choices": [
            {"label": "Continue in the journey...", "next": "aaru"},
        ],
    },

    "aaru": {
        "id": "aaru",
        "title": "Arrival at Aaru",
        "image": "images/aaru.png",
        "type": "safe",
        "text": (
            "You step out of the forest.\nBefore you stands Aaru, full of life and opportunity.\n"
            "Voices, warmth, and motion fill the streets.\n"
            "You can see the castle from far away\n"
            "The sunset grows, shining on the roofs of the buildings, showing you the path forward…\n"
            "You eventually reaches a crossroads."
        ),
        "choices": [
            {"label": "LEFT - to the city centre", "next": "to_the_city"},
            {"label": "RIGHT - to the castle", "next": "to_the_castle"}
        ]
    },

    "to_the_castle": {
        "id": "to_the_castle",
        "title": "The Castle",
        "image": "images/castle.png",
        "type": "safe",
        "text": (
            "You walk in. All is quiet. The first stallholders are taking their places in the courtyard.\n"
            "There is an advertisement for a quest, from the princess herself.\n"
            "\n"
            "\"Brave warrior, mage, or anyone daring enough in need:\n"
            "the REVARD is too great to be described.\n" 
            "Ask the guards for directions if you believe you are the one suited for this task.\"\n"
            "-- Princess Quella"
        ),
        "choices": [
            {"label": "Apply", "next": "the_test"},
            {"label": "Eat first, then apply", "effect": {"hp": 20, "hx": 10}, "next": "the_test"},
            {"label": "Just look around for a while, then go downtown", "effect": {"hx": 5, "xp": 5},"next": "to_the_city"},
        ]
    },

    "the_test": {
        "id":    "the_test",
        "title": "The Test",
        "image": "images/test.png",
        "type":  "mystery",
        "text": (
            "A guard leads you down a long stone corridor.\n"
            "He opens a heavy door and steps aside.\n\n"
            "Inside: a small room, a wooden desk,\n"
            "a notebook, and a pen.\n\n"
            "  'Before you can meet the Princess,\n"
            "   you must pass this test.\n"
            "   Answer every question truthfully.'\n\n"
            "He sets the notebook in front of you and leaves."
        ),
        "choices": [
            {
                "label": "Open the notebook",
                "next":  "__test__",        # special ID — triggers the Y/N screen
            },
        ],
    },

    # -----------------------------------------------------------------------
    # THE MEETING — Princess
    # -----------------------------------------------------------------------
    "the_meeting": {
        "id":    "the_meeting",
        "title": "The Princess",
        "image": "images/princess.png",
        "type":  "mystery",
        "text": (
            "A small room. Windows open wide.\n"
            "The air smells of roses.\n\n"
            "Then she enters.\n\n"
            "She looks sad. Not the sadness of someone\n"
            "who cries often — the other kind.\n"
            "The kind that has been carried quietly\n"
            "for a long time.\n\n"
            "She gestures for you to sit.\n"
            "She studies you for a moment before she speaks."
        ),
        "choices": [
            {
                "label":       "Hold her gaze steadily",
                "next":        "meeting_story",
                "success_next":"meeting_story_impressed",
                "dice": {
                    "type":  "d20",
                    "dc":    12,
                    "stat":  "luck",
                    "label": "Make an impression (Roll Luck)",
                },
            },
        ],
    },

    "meeting_story_impressed": {
        "id":    "meeting_story_impressed",
        "title": "She Notices You",
        "image": "images/princess_look.png",
        "type":  "safe",
        "text": (
            "Something in your manner catches her.\n"
            "She holds your gaze a moment longer than expected.\n"
            "A flicker — not quite a smile, but close.\n\n"
            "Then she begins to speak."
        ),
        "choices": [
            {
                "label":  "Listen",
                "next":   "meeting_story",
                "effect": {"rx": 10, "hx": 10},
            },
        ],
    },

    "meeting_story": {
        "id":    "meeting_story",
        "title": "What She Told You",
        "image": "images/princess.png",
        "type":  "mystery",
        "text": (
            "\"Some doors, once opened, do not close easily.\n"
            "I found one in the Darkwood — and walked through it willingly.\n"
            "A witch lived there. I knew what she was. I returned anyway.\n"
            "There was a connection between us I could not explain or cut.\n\n"
            "Then I met one of my guards. Quiet, steady, certain.\n"
            "I fell in love. The connection with the witch weakened. I forgot her entirely.\n\n"
            "One night, I woke to an unnatural silence.\n"
            "He was gone. I searched until dawn, telling no one.\n"
            "On my pillow — a lock of red hair. And a note:\n\n"
            "   'Now it is my turn to play with your friend.\'\n\n"
            "Every time I try to enter the forest, something drags me to my knees.\n"
            "She has made certain I cannot follow.\n\n"
            "Will you go where I cannot?\""
        ),
        "choices": [
            {
                "label":  "I will help you",
                "next":   "to_the_forest",
                "effect": {"rx": 15, "xp": 10},
            },
            {
                "label":  "I don't feel suited for this task",
                "next":   "refused_quest",
                "effect": {"rx": -15},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # REFUSED — dice check to escape the guards
    # -----------------------------------------------------------------------
    "refused_quest": {
        "id":    "refused_quest",
        "title": "The Guards Move",
        "image": "images/guards.png",
        "type":  "combat",
        "text": (
            "The princess's expression closes like a door.\n\n"
            "Two guards step forward from the shadows.\n"
            "  'You've heard too much to simply leave.'\n\n"
            "The door behind you is still open.\n"
            "You have one chance."
        ),
        "choices": [
            {
                "label":       "Run for it",
                "next":        "beaten_out",
                "success_next":"escaped_castle",
                "dice": {
                    "type":  "d20",
                    "dc":    13,
                    "stat":  "luck",
                    "label": "Run! (Roll Luck)",
                },
            },
        ],
    },

    "escaped_castle": {
        "id":    "escaped_castle",
        "title": "Out of the Castle",
        "image": "images/leaving_castle.png",
        "type":  "normal",
        "text": (
            "You clear the corridor, vault a low wall,\n"
            "and lose them in the market crowd.\n\n"
            "Heart hammering. Alive.\n"
            "The city opens up around you."
        ),
        "choices": [
            {
                "label":  "Disappear into the city",
                "next":   "to_the_city",
                "effect": {"xp": 10, "rx": -10},
            },
        ],
    },

    "beaten_out": {
        "id":    "beaten_out",
        "title": "Thrown Out",
        "image": "🩹",
        "type":  "combat",
        "text": (
            "They catch you before you reach the gate.\n\n"
            "They don't kill you — just make certain\n"
            "you understand the cost of wasted time.\n\n"
            "You are dumped outside the castle walls\n"
            "in the late morning dust."
        ),
        "choices": [
            {
                "label":  "Pick yourself up",
                "next":   "to_the_city",
                "effect": {"hp": -20, "rx": -10, "hx" : -10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # THE FOREST — going after the witch
    # -----------------------------------------------------------------------
    "to_the_forest": {
        "id":    "to_the_forest",
        "title": "Back into the Forest",
        "image": "images/back_forest.png",
        "type":  "normal",
        "text": (
            "You enter the forest.\n\n"
            "Something is different this time.\n"
            "The path feels familiar even though\n"
            "you have never walked it before.\n"
            "You somehow know which way to go.\n\n"
            "After a while, voices begin to reach you.\n"
            "Not adult voices — something younger.\n"
            "High, sharp, urgent.\n"
            "Like a crowd of children screaming."
        ),
        "choices": [
            {
                "label": "Follow the sound",
                "next":  "confrontation",
                "effect": {"xp": 5}
            },
            {
                "label":  "Avoid it — go around",
                "next":   "forest_lost",
                "effect": {"xp": -5}
            },
        ],
    },

    "forest_lost": {
        "id":    "forest_lost",
        "title": "Lost",
        "image": "🌑",
        "type":  "normal",
        "text": (
            "You circle wide to avoid the sounds.\n\n"
            "After an hour the trees all look the same.\n"
            "The path you thought you knew is gone.\n"
            "The voices have faded. So has your sense\n"
            "of direction.\n\n"
            "You sit on a root and think."
        ),
        "choices": [
            {
                "label": "Try to find your way again",
                "next":  "to_the_forest",
                "effect": {"xp": -5},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # CONFRONTATION — the foxes
    # -----------------------------------------------------------------------
    "confrontation": {
        "id":    "confrontation",
        "title": "The Cave",
        "image": "images/foxes.png",
        "type":  "combat",
        "text": (
            "A cave opening between two mossy boulders.\n\n"
            "Baby foxes tumble and bark in front of it —\n"
            "a dozen of them, noisy and restless.\n\n"
            "You are about to turn back when a man's voice\n"
            "cries out from deep inside the cave.\n\n"
            "You step forward.\n"
            "The foxes stop playing.\n"
            "They turn toward you.\n"
            "Their eyes are wrong.\n\n"
            "They are not ordinary foxes."
        ),
        "choices": [
            {
                "label":       "Push through them",
                "next":        "confrontation_hurt",
                "success_next":"the_cave",
                "dice": {
                    "type":  "d20",
                    "dc":    11,
                    "stat":  "attack",
                    "label": "Fight through! (Roll Attack)",
                },
            },
        ],
    },

    "confrontation_hurt": {
        "id":    "confrontation_hurt",
        "title": "They Draw Blood",
        "image": "images/foxfight.png",
        "type":  "combat",
        "text": (
            "They are fast and they bite deep.\n\n"
            "You drive them back eventually —\n"
            "but not before they have taken their price.\n\n"
            "You press onward into the cave."
        ),
        "choices": [
            {
                "label":  "Go inside",
                "next":   "the_cave",
                "effect": {"hp": -10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # THE CAVE — the witch
    # -----------------------------------------------------------------------
    "the_cave": {
        "id":    "the_cave",
        "title": "The Red-Headed Witch",
        "image": "images/witch.png",
        "type":  "combat",
        "text": (
            "Inside: firelight. The smell of something\n"
            "old and wrong.\n\n"
            "A man is bound to a stone.\n"
            "Alive — barely.\n\n"
            "And her.\n\n"
            "Red hair. Still eyes. She has been expecting you.\n\n"
            "  'You're too late,' she says.\n"
            "  'And too early.'\n\n"
            "She raises her hands."
        ),
        "choices": [
            {
                "label":       "Attack",
                "next":        "he_is_not_safe",
                "success_next":"he_is_safe",
                "effect":      {"xp": 10},
                "dice": {
                    "type":  "d20",
                    "dc":    14,
                    "stat":  "magic",
                    "label": "Strike with everything! (Roll Magic)",
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    # ENDINGS
    # -----------------------------------------------------------------------
    "he_is_safe": {
        "id":    "he_is_safe",
        "title": "It Is Done",
        "image": "images/rescued.png",
        "type":  "victory",
        "text": (
            "The witch falls.\n\n"
            "The fire goes out. The cave goes quiet.\n\n"
            "You cut the man free. He can barely stand\n"
            "but he is alive and he knows where he is.\n\n"
            "You take him back to the castle.\n\n"
            "The Princess does not speak for a long time\n"
            "when she sees him.\n\n"
            "When she finally looks at you, she says\n"
            "only your name — the way people say a name\n"
            "when they mean something much larger.\n\n"
            "The whole castle will know what you did\n"
            "before morning."
        ),
        "choices": [
            {
                "label":  "Let's explore the city",
                "next":   "to_the_city",
                "effect": {"hx": 20, "xp": 50, "rx": 40, "hp": -5},
            },
        ],
    },

    "he_is_not_safe": {
        "id":    "he_is_not_safe",
        "title": "Too Late",
        "image": "💀",
        "type":  "combat",
        "text": (
            "The witch escapes into the dark of the cave.\n\n"
            "You find the man on the ground.\n"
            "He did not survive what she did to him.\n\n"
            "You wrap him carefully in your cloak.\n"
            "You carry him back through the forest\n"
            "without stopping.\n\n"
            "The Princess takes one look at the bundle\n"
            "in your arms and understands everything.\n\n"
            "She does not blame you.\n"
            "She thanks you for bringing him home.\n"
            "That is harder to carry than blame."
        ),
        "choices": [
            {
                "label":  "Let's explore the city",
                "next":   "to_the_city",
                "effect": {"hp": -50, "hx": -10, "xp": 10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # TO THE CITY — arriving in Aaru
    # -----------------------------------------------------------------------
    "to_the_city": {
        "id":    "to_the_city",
        "title": "The City of Aaru",
        "image": "images/aaru.png",
        "type":  "safe",
        "text": (
            "You like the city.\n"
            "You like the vibe of it — the noise, the warmth,\n"
            "the feeling that things are always happening\n"
            "just around the next corner.\n\n"
            "You think about staying. Not wandering.\n"
            "Just staying in one place, with people,\n"
            "and seeing what that would feel like.\n\n"
            "It is getting dark. The sun is already\n"
            "under the horizon.\n\n"
            "Across the street, warm light spills\n"
            "from a tavern window."
        ),
        "choices": [
            {
                "label": "Enter the tavern",
                "next":  "the_tavern",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # THE TAVERN
    # -----------------------------------------------------------------------
    "the_tavern": {
        "id":    "the_tavern",
        "title": "The Tavern",
        "image": "images/tavern.png",
        "type":  "safe",
        "text": (
            "Inside, all sorts of people fill the room.\n\n"
            "In the corner, two mages sit with hoods drawn,\n"
            "attempting to be invisible.\n"
            "A stage holds instruments waiting to be played.\n"
            "The bar is crowded with voices and gossip.\n\n"
            "You overhear someone mention the guard from the\n"
            "castle — wondering why he mattered so much\n"
            "to the royals. Just a regular man in service.\n"
            "Nothing special, apparently.\n\n"
            "You say nothing."
        ),
        "choices": [
            {
                "label":  "Have a beer",
                "next":   "the_girl",
                "effect": {"hp": -5, "hx": 10},
            },
            {
                "label":  "No beer — just a soup",
                "next":   "the_girl",
                "effect": {"hp": 10, "hx": 10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # THE GIRL 
    # -----------------------------------------------------------------------
    "the_girl": {
        "id":    "the_girl",
        "title": "The Harpist",
        "image": "images/harpist.png",
        "type":  "safe",
        "text": (
            "A woman walks onto the stage.\n"
            "Two older women follow her.\n\n"
            "She is so mysterious that you are captivated\n"
            "before she has even sat down.\n\n"
            "She begins to play the harp — very gently.\n"
            "You listen to her magical tones and watch\n"
            "her fingers move across the strings.\n"
            "You become completely lost in the melodies.\n\n"
            "They finish the song.\n"
            "You are stunned by the beauty.\n\n"
            "After the applause, she rises and heads\n"
            "toward the door — perhaps for some fresh air.\n"
            "On her way out, she notices you.\n"
            "She gives you a sweet smile.\n\n"
            "You feel something you haven't felt in a long time.\n\n"
            "Are you brave enough to follow her?"
        ),
        "choices": [
            {
                "label":  "Follow her",
                "next":   "the_outside_1",
                "effect": {"xp": 10, "hx": 10},
            },
            {
                "label":  "Go outside without any particular reason",
                "next":   "the_outside_1",
                "effect": {"hx": 0, "xp": 0},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # OUTSIDE — the conversation
    # -----------------------------------------------------------------------
    "the_outside_1": {
        "id":    "the_outside_1",
        "title": "In the moonlight",
        "image": "images/the_girl.png",
        "type":  "mystery",
        "text": (
            "You find her standing just outside,\n"
            "leaning against the stone wall.\n\n"
            "You approach her.\n"
            "She doesn't seem surprised to see you.\n\n"
            "Is she pleased with the conversation?"
        ),
        "choices": [
            {
                "label":       "Talk to her",
                "next":        "the_outside_2",
                "success_next":"the_outside_2",
                "effect": {"hx": 10},
                "dice": {
                    "type":  "d20",
                    "dc":    11,
                    "stat":  "luck",
                    "label": "Make an impression (Roll Luck)",
                },
            },
        ],
    },

    "the_outside_2": {
        "id":    "the_outside_2",
        "title": "Mae",
        "image": "images/the_girl.png",
        "type":  "safe",
        "text": (
            "There is a lot of silence between the two of you.\n" 
            "You simply breathe and enjoy the fresh air, staring at the moon.\n"
            "  \"I guess you are not from here. I haven't seen you before. I'm good at remembering faces,\" she says.\n\n"
            "  \"I'm not. I just wander. By tomorrow, I'll be back on the road.\n"
            "   You can forget me already, if you want.\"\n\n"
            "She gives you a bitter smile.\n"
            "  \"That would be a shame. I didn't give up on you yet.\"\n"
            "  \"That is a relief.\"\n"
            "  \"Why?\"\n"
            "  \"Because... I really like your music. I want to hear more.\"\n"
            "  \"Ah, that. That's not what I want to do, but I have to. The tavern pays me well.\n"
            "   We attract a lot of… different people.\"\n"
            "  \"Maybe it's time for you to move on.\"\n\n"
            "She turns to you.\n"
            "You stare into her beautiful eyes. They have a spark that intrigues you.\n"
        ),
        "choices": [
            {
                "label":  "Get closer to her",
                "next":   "the_fire",
                "effect": {"xp": 5, "hx": 15},
            },
            {
                "label":  "Just stare",
                "next":   "the_fire",
                "effect": {"xp": 5, "hx": 10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # THE FIRE — the moment breaks
    # -----------------------------------------------------------------------
    "the_fire": {
        "id":    "the_fire",
        "title": "Something's Wrong",
        "image": "images/inn_attack.png",
        "type":  "combat",
        "text": (
            "This perfect moment is disturbed.\n\n"
            "Disturbing sounds erupt from inside the tavern.\n\n"
            "  \"Maybe I should check on what's going on,\" you say, and go back inside.\n\n"
            "You cross paths with two men leaving in a hurry.\n\n"
            "Inside: the two mages are throwing fireballs at each other across the room.\n"
            "The inn catches fire instantly.\n\n"
            "You step back outside to find the girl.\n\n"
            "You see those two men harassing her.\n"
            "She does not look scared — she looks very dedicated to fighting them for crossing too many lines.\n\n"
            "What do you do first?"
        ),
        "choices": [
            {
                "label":  "Save her",
                "next":   "ending_1",
                "effect": {"hx": 10, "xp": 30},
            },
            {
                "label":  "Save everyone from the tavern",
                "next":   "ending_2",
                "effect": {"xp": 30, "rx": 30},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # ENDING 2 — you chose the tavern over her
    # -----------------------------------------------------------------------
    "ending_2": {
        "id":    "ending_2",
        "title": "The Roof Falls",
        "image": "images/roof.png",
        "type":  "combat",
        "text": (
            "You hurry inside and try to get everyone out.\n"
            "The fire is too strong, and you are among\n"
            "the only ones sober.\n"
            "You are completely alone in this.\n\n"
            "The roof falls. You are lucky not to be hit.\n"
            "You cannot save everyone on your own —\n"
            "it is obvious. The fire is just too massive.\n\n"
            "At the very least, you try to find the girl.\n"
            "But she is gone.\n\n"
            "You don't even know her name."
        ),
        "choices": [
            {
                "label": "Leave",
                "next":  "game_over",
                "effect": {"xp": 5, "rx": -30, "hx": -40},
            },
            {
                "label": "Stay and watch",
                "next":  "game_over",
                "effect": {"xp": 5, "rx": -20, "hx": -50},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # ENDING 1 — you chose her
    # -----------------------------------------------------------------------
    "ending_1": {
        "id":    "ending_1",
        "title": "Together",
        "image": "images/fire.png",
        "type":  "combat",
        "text": (
            "You reach Mae just as both men fall —\n"
            "handled by her before you arrived.\n\n"
            "She looks at you, gives you the biggest smile,\n"
            "and runs with you toward the tavern.\n\n"
            "Together, you go to save the situation.\n\n"
            "There are still people inside."
        ),
        "choices": [
            {
                "label":       "Get everyone out",
                "next":        "ending_1b",
                "success_next":"ending_1b",
                "dice": {
                    "type":  "d20",
                    "dc":    8,
                    "stat":  "defense",
                    "label": "Save them! (Roll Defense)",
                },
            },
        ],
    },

    "ending_1b": {
        "id":    "ending_1b",
        "title": "Kill the Fire",
        "image": "images/inn_attack.png",
        "type":  "combat",
        "text": (
            "The people are out.\n\n"
            "The fire is still raging.\n"
            "She looks at you. You look at her.\n\n"
            "Two more things to do.\n\n"
            "Kill the mages. Kill the fire."
        ),
        "choices": [
            {
                "label":       "Kill the mages - together",
                "next":        "escape",
                "success_next":"happyend",
                "dice": {
                    "type":  "d20",
                    "dc":    8,
                    "stat":  "attack",
                    "label": "Fight them together! (Roll Attack)",
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    # ESCAPE — fire wins, but you still have each other
    # -----------------------------------------------------------------------
    "escape": {
        "id":    "escape",
        "title": "You Run",
        "image": "💨",
        "type":  "normal",
        "text": (
            "The fire is too much and the mages dissapeared.\n\n"
            "You grab her hand and you both run\n"
            "out into the night, gasping.\n\n"
            "The tavern burns behind you.\n"
            "The two of you stand in the nearby forest,\n"
            "catching your breath, watching the smoke rise.\n\n"
            "You look at her.\n"
            "She looks at you.\n\n"
            "  \"Well,\" she says, \"that's one way to meet.\""
        ),
        "choices": [
            {
                "label":  "Stay with Mae",
                "next":   "happyend_1",
                "effect": {"xp": 10, "hx": 10, "rx": -10},
            },
        ],
    },

    # -----------------------------------------------------------------------
    # HAPPY END — the real ending
    # -----------------------------------------------------------------------
    "happyend": {
        "id":    "happyend",
        "title": "Happy End",
        "image": "images/family.png",
        "type":  "victory",
        "text": (
            "\"We did it!\", says Mae.\n"
            "\"I had my suspisions that you're not just an ordinary girl.\"\n"
            "\"And you're not just a wanderer.\"\n\n"
            "The feeling that you have known each other your whole lives.\n\n"
            "This is just one of many things.\n\n"
            "You want to wander together,\n"
            "or simply stay together.\n"
            "You will figure it out.\n\n"
            "You are happy.\n"
            "That is what you have been looking for.\n"
            "At least for now.\n\n"
            "You saved a lot. Now it's time to safe yourself. It's your birthday!!!"
        ),
        "choices": [
            {
                "label":  "Look at your score!",
                "next":   "__happiness__",
                "effect": {"hx": 30, "xp": 30, "rx": 20},
            },
        ],
    },

    "happyend_1": {
        "id":    "happyend_1",
        "title": "Happy End...?",
        "image": "images/burned.png",
        "type":  "safe",
        "text": (
            "The feeling that you have known each other your whole lives.\n\n"
            "This is just one of many things.\n\n"
            "You want to wander together,\n"
            "or simply stay together.\n"
            "You will figure it out.\n\n"
            "You are happy.\n"
            "That is what you have been looking for.\n"
            "At least for now.\n\n"
        ),
        "choices": [
            {
                "label":  "Look at your score!",
                "next":   "__happiness__",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # GAME OVER
    # -----------------------------------------------------------------------
    "game_over": {
        "id":    "game_over",
        "title": "The End",
        "image": "💀",
        "type":  "combat",
        "text": (
            "The city swallows the night.\n\n"
            "You are still here. Still alone.\n"
            "Still not sure what you are looking for.\n\n"
            "But you made it to Aaru.\n"
            "That has to count for something."
        ),
        "choices": [
            {"label": "Try again", "next": "__restart__"},
        ],
    },
}


# =============================================================================
#   THE PRINCESS'S TEST — Y/N QUESTIONNAIRE
#   Sets the questions, correct answers, and outcome texts
#
#   Each question is (question_text, correct_answer)
#   correct_answer must be True (= Y) or False (= N)
#
#   If ALL answers are correct  --> goes to  TEST_SUCCESS_NEXT
#   If ANY answer is wrong      --> goes to  TEST_FAIL_NEXT
# =============================================================================
THE_TEST_QUESTIONS = [
    ("Have you ever killed anybody?",                                True),   # correct: Y
    ("Do you have children?",                                        False),  # correct: N
    ("Do you have a wife?",                                          False),  # correct: N
    ("Do you come from this city?",                                  False),  # correct: N
    ("Based on your experience, do you think you are right\nmost of the time?", True),   # correct: Y
    ("Have you been to the forest in the last 24 hours?",           True),   # correct: Y
]

TEST_SUCCESS_NEXT = "the_meeting"   # scene ID when all answers are correct
TEST_FAIL_NEXT    = "to_the_city"   # scene ID when any answer is wrong

TEST_SUCCESS_TEXT = (
    "The guard reads through your answers slowly.\n\n"
    "A long pause.\n\n"
    "  'Congrats. If it's what you wanted.'\n\n"
    "He closes the notebook and stands.\n"
    "  'Now follow me.'\n\n"
    "He leads you deeper into the castle."
)

TEST_FAIL_TEXT = (
    "The guard reads your answers.\n"
    "His expression does not change.\n\n"
    "  'Either you lied, or you have a family\n"
    "   to protect. Go home and take care of them.'\n\n"
    "He holds the door open.\n"
    "There is nothing more to say."
)


# =============================================================================
# =============================================================================
#  ENGINE CODE BELOW 
# =============================================================================
# =============================================================================

def scale_fit(surf, max_w, max_h):
    """Scale a surface to fit inside max_w * max_h while preserving aspect ratio"""
    w, h = surf.get_size()
    scale = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(surf, (int(w * scale), int(h * scale)))


class Button:
    """A clickable button with hover and press animations"""

    def __init__(self, rect, label, font, color_key="btn"):
        self.rect      = pygame.Rect(rect)
        self.label     = label
        self.font      = font
        self.color_key = color_key
        self.hovered   = False
        self.pressed   = False

    def draw(self, surface):
        color  = C["btn_press"] if self.pressed else (C["btn_hover"] if self.hovered else C["btn"])
        border = C["btn_border"]

        # Shadow effect
        shadow = self.rect.move(3, 3)
        pygame.draw.rect(surface, (0, 0, 0, 120), shadow, border_radius=10)

        # Button body
        pygame.draw.rect(surface, color,  self.rect, border_radius=10)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=10)

        # Highlight line at top
        hl = pygame.Rect(self.rect.x + 4, self.rect.y + 2, self.rect.width - 8, 2)
        pygame.draw.rect(surface, C["border_hi"], hl, border_radius=2)

        # Label
        txt = self.font.render(self.label, True, C["text"])
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = self.rect.collidepoint(event.pos)
            return self.pressed
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            clicked = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            return "click" if clicked else None
        return None


def draw_text_wrapped(surface, text, font, color, rect, line_spacing=6):
    """Draw text wrapped to fit inside a pygame.Rect. Returns final y position."""
    lines = text.split("\n")
    y = rect.top
    for line in lines:
        # If the line fits, draw it
        if font.size(line)[0] <= rect.width:
            surface.blit(font.render(line, True, color), (rect.left, y))
            y += font.get_height() + line_spacing
        else:
            # Word-wrap long lines
            words = line.split(" ")
            current = ""
            for word in words:
                test = current + (" " if current else "") + word
                if font.size(test)[0] <= rect.width:
                    current = test
                else:
                    if current:
                        surface.blit(font.render(current, True, color), (rect.left, y))
                        y += font.get_height() + line_spacing
                    current = word
            if current:
                surface.blit(font.render(current, True, color), (rect.left, y))
                y += font.get_height() + line_spacing
    return y


def draw_bar(surface, rect, value, max_value, fill_color, bg_color, border_color=None):
    """Draw a filled progress bar (HP bar, XP bar, etc.)."""
    pygame.draw.rect(surface, bg_color, rect, border_radius=6)
    if max_value > 0:
        fill_w = int(rect.width * min(value, max_value) / max_value)
        fill_r = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surface, fill_color, fill_r, border_radius=6)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, width=1, border_radius=6)


def draw_panel(surface, rect, title=None, fonts=None, accent=None):
    """Draw a styled panel (dark rounded rectangle with optional title)."""
    shadow = rect.move(4, 4)
    pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=14)
    pygame.draw.rect(surface, C["panel"], rect, border_radius=14)
    border_color = accent if accent else C["border"]
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=14)
    if title and fonts:
        t = fonts["small"].render(title, True, C["gold_dim"])
        surface.blit(t, (rect.x + 12, rect.y + 8))


# =============================================================================
# SCREEN: TITLE / MAIN MENU
# =============================================================================
def screen_title(surface, fonts, clock, music):
    """Show the main title screen. Returns True when the player clicks to start."""
    music.play("beginning")
    # You can edit the subtitle/flavor text shown on the title screen here
    subtitle   = "[TEXT]"
    start_hint = "Click anywhere to begin your journey..."

    # Animated star particles
    stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT),
              random.uniform(0.3, 1.5)) for _ in range(120)]

    t = 0
    while True:
        clock.tick(FPS)
        t += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                return True

        surface.fill(C["bg"])

        # Draw twinkling stars
        for sx, sy, speed in stars:
            brightness = int(128 + 127 * math.sin(t * 0.04 * speed))
            col = (brightness // 6, brightness // 6, brightness // 2)
            pygame.draw.circle(surface, col, (sx, sy), 1)

        # Glowing title
        glow_alpha = int(180 + 60 * math.sin(t * 0.05))
        title_surf = fonts["title"].render(GAME_TITLE, True, C["gold"])
        cx = SCREEN_WIDTH // 2 - title_surf.get_width() // 2
        cy = SCREEN_HEIGHT // 3 - title_surf.get_height() // 2
        surface.blit(title_surf, (cx, cy))

        # Decorative line
        lw = title_surf.get_width() + 60
        lx = SCREEN_WIDTH // 2 - lw // 2
        pygame.draw.line(surface, C["gold_dim"], (lx, cy + title_surf.get_height() + 8),
                         (lx + lw, cy + title_surf.get_height() + 8), 2)

        sub_surf = fonts["body"].render(subtitle, True, C["text_dim"])
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, cy + title_surf.get_height() + 30)))

        # Pulsing start hint
        pulse = int(160 + 95 * math.sin(t * 0.07))
        hint_col = (min(255, max(0, pulse)),
                    min(255, max(0, pulse - 20)),
                    min(255, max(0, pulse + 50)))
        hint_surf = fonts["small"].render(start_hint, True, hint_col)
        surface.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4)))

        pygame.display.flip()


# =============================================================================
# SCREEN: CHARACTER SELECTION
# =============================================================================
def screen_character_select(surface, fonts, clock, music):
    """Character selection screen. Returns the chosen character dict."""
    music.play("beginning")
    selected = 0  # index into CHARACTERS

    # Layout: cards in a row
    n = len(CHARACTERS)
    card_w, card_h = 305, 590           # Width and height of each character card
    gap         = 25                    # Gap between character cards
    total_w     = n * card_w + (n - 1) * gap
    start_x     = SCREEN_WIDTH  // 2 - total_w // 2
    card_y      = 110                  # Fixed distance from top (pixels)

    confirm_btn = Button(
        (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT - 70, 280, 52),
        "Choose This Hero",
        fonts["button"],
    )

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            # Click a card to select
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for i in range(n):
                    cx = start_x + i * (card_w + gap)
                    if pygame.Rect(cx, card_y, card_w, card_h).collidepoint(mx, my):
                        selected = i
            result = confirm_btn.handle_event(event)
            if result == "click":
                return dict(CHARACTERS[selected])  # Return a copy

        surface.fill(C["bg"])

        # Heading
        head = fonts["heading"].render("Choose Your Hero", True, C["gold"])
        surface.blit(head, head.get_rect(center=(SCREEN_WIDTH // 2, 60)))
        pygame.draw.line(surface, C["gold_dim"],
                         (SCREEN_WIDTH // 2 - 180, 90), (SCREEN_WIDTH // 2 + 180, 90), 1)

        # Draw each character card
        for i, char in enumerate(CHARACTERS):
            cx = start_x + i * (card_w + gap)
            is_sel = (i == selected)

            # Card border glow when selected
            border_col = C[char["color"]] if is_sel else C["border"]
            border_w   = 4 if is_sel else 1

            pygame.draw.rect(surface, C["panel"], (cx, card_y, card_w, card_h), border_radius=14)
            pygame.draw.rect(surface, border_col, (cx, card_y, card_w, card_h),
                             width=border_w, border_radius=14)

            # Portrait image — fits inside 240×180 box without distortion
            IMG_W, IMG_H = 280, 230          # max portrait size
            try:
                raw  = pygame.image.load(os.path.join(BASE_DIR, char["images"][0])).convert_alpha()
                icon_surf = scale_fit(raw, IMG_W, IMG_H)
            except Exception:
                icon_surf = fonts["title"].render(char["icon"], True, C[char["color"]])
            # Centre the (possibly non-square) image in the reserved slot
            img_rect = icon_surf.get_rect(centerx=cx + card_w // 2, top=card_y + 14)
            surface.blit(icon_surf, img_rect)

            # Name — always card_y + 14 + IMG_H + 12 = card_y + 206
            name_y = card_y + 14 + IMG_H + 12
            name_surf = fonts["char_name"].render(char["name"], True,
                                                   C[char["color"]] if is_sel else C["text"])
            surface.blit(name_surf, name_surf.get_rect(center=(cx + card_w // 2, name_y)))

            # Description
            desc_y = name_y + 28
            draw_text_wrapped(surface, char["desc"], fonts["small"], C["text_dim"],
                               pygame.Rect(cx + 40, desc_y, card_w - 54, 85), line_spacing=5)

            # Stats
            stats_y = desc_y + 95
            for label, key, col in [
                ("HP",  "hp",      C["text_red"]),
                ("ATK", "attack",  C["gold"]),
                ("DEF", "defense", C["text_blue"]),
                ("MAG", "magic",   C["text_blue"]),
                ("LCK", "luck",    C["text_green"]),
            ]:
                lbl = fonts["tiny"].render(f"{label}", True, C["text_dim"])
                val = fonts["tiny"].render(str(char[key]), True, col)
                surface.blit(lbl, (cx + 18, stats_y))
                surface.blit(val, (cx + card_w - 18 - val.get_width(), stats_y))
                bar_r = pygame.Rect(cx + 72, stats_y + 2, card_w - 130, 9)
                max_v = 120 if key == "hp" else 20
                draw_bar(surface, bar_r, char[key], max_v, col, C["panel_light"])
                stats_y += 26

            # Abilities
            ab_surf = fonts["tiny"].render(", ".join(char["abilities"][:2]), True, C["text_dim"])
            surface.blit(ab_surf, ab_surf.get_rect(center=(cx + card_w // 2, stats_y + 10)))

        confirm_btn.draw(surface)
        pygame.display.flip()


# =============================================================================
# SCREEN: DICE ROLL ANIMATION
# =============================================================================
def screen_dice_roll(surface, fonts, clock, dice_type, dc, stat_bonus, stat_name, music=None):
    """
    Animated dice roll screen.
    Returns the final roll result (int) BEFORE bonus is added.
    The caller should add the stat bonus.
    """
    if music:
        music.play("fight")
    sides = DICE.get(dice_type, 20)
    roll_time    = 1.8         # How many seconds the dice spins before stopping
    spin_frames  = int(roll_time * FPS)
    final_roll   = random.randint(1, sides)

    # Roll button
    roll_btn = Button(
        (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 110, 200, 50),
        f"Roll the {dice_type}!",
        fonts["button"],
    )

    phase   = "pre"    # pre --> rolling --> result
    frame   = 0
    display = 1        # currently displayed number during spin
    result_shown = False

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if phase == "pre":
                res = roll_btn.handle_event(event)
                if res == "click":
                    phase = "rolling"
                    frame = 0
            elif phase == "result":
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    return final_roll

        # Update spinning number
        if phase == "rolling":
            frame += 1
            display = random.randint(1, sides)
            if frame >= spin_frames:
                display = final_roll
                phase   = "result"

        # Draw
        surface.fill(C["bg"])

        # Title
        total   = final_roll + stat_bonus if phase == "result" else "?"
        heading = fonts["heading"].render(f"Dice Check  ({dice_type})", True, C["gold"])
        surface.blit(heading, heading.get_rect(center=(SCREEN_WIDTH // 2, 80)))

        # DC info
        dc_txt = fonts["body"].render(
            f"Difficulty: {dc}   |   Your {stat_name} bonus: +{stat_bonus}", True, C["text_dim"])
        surface.blit(dc_txt, dc_txt.get_rect(center=(SCREEN_WIDTH // 2, 125)))

        # Big dice face
        dice_size = 200          # Size of the dice face square
        dx = SCREEN_WIDTH  // 2 - dice_size // 2
        dy = SCREEN_HEIGHT // 2 - dice_size // 2 - 20

        # Shake when rolling
        if phase == "rolling":
            shake = random.randint(-4, 4)
            dx += shake; dy += shake

        dice_rect = pygame.Rect(dx, dy, dice_size, dice_size)

        # Determine fill color
        if phase == "result":
            success = (final_roll + stat_bonus) >= dc
            bg_col  = C["dice_success"] if success else C["dice_fail"]
        else:
            bg_col = C["dice_bg"]

        pygame.draw.rect(surface, bg_col,           dice_rect, border_radius=24)
        pygame.draw.rect(surface, C["dice_border"], dice_rect, width=3, border_radius=24)

        # Number on dice
        num_surf = fonts["dice_big"].render(str(display), True, C["dice_pip"])
        surface.blit(num_surf, num_surf.get_rect(center=dice_rect.center))

        if phase == "result":
            success = (final_roll + stat_bonus) >= dc
            total_txt = fonts["heading"].render(
                f"Roll: {final_roll}  +  Bonus: {stat_bonus}  =  {final_roll + stat_bonus}",
                True, C["text_green"] if success else C["text_red"])
            surface.blit(total_txt, total_txt.get_rect(center=(SCREEN_WIDTH // 2, dy + dice_size + 30)))

            outcome = "SUCCESS!" if success else "FAILURE!"
            out_col = C["text_green"] if success else C["text_red"]
            out_surf = fonts["char_name"].render(outcome, True, out_col)
            surface.blit(out_surf, out_surf.get_rect(center=(SCREEN_WIDTH // 2, dy + dice_size + 65)))

            hint = fonts["tiny"].render("Click or press any key to continue...", True, C["text_dim"])
            surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)))
        else:
            if phase == "pre":
                roll_btn.draw(surface)

        pygame.display.flip()


# =============================================================================
# SCREEN: STORY / SCENE
# =============================================================================
def screen_scene(surface, fonts, clock, scene, player, music=None):
    """
    Render a story scene and return the player's choice dict.
    Handles dice checks inline.
    """
    if music:
        play_music_for_scene(music, scene)
    choices = scene["choices"]
    scene_type = scene.get("type", "normal")

    # Map scene types to accent colors
    accent_map = {
        "normal":  C["scene_normal"],
        "combat":  C["scene_combat"],
        "mystery": C["scene_mystery"],
        "safe":    C["scene_safe"],
    }
    accent = accent_map.get(scene_type, C["scene_normal"])

    # Layout
    panel_x, panel_y   = 40,  40
    panel_w, panel_h   = SCREEN_WIDTH - 80, SCREEN_HEIGHT - 100

    img_col_w      = 400                          # width of the left image column
    img_max_w      = img_col_w - 20              # image fits inside with 10px padding each side
    img_max_h      = panel_h - 60                # nearly full panel height
    img_center_x   = panel_x + img_col_w // 2   # horizontal centre of image column

    story_text_x   = panel_x + img_col_w + 20   # ★ where text/title/buttons start
    story_text_w   = panel_w - img_col_w - 40   # ★ remaining width for text
    story_text_y   = panel_y + 70
    btn_start_y    = panel_y + panel_h - 60 - len(choices) * 58

    # Build choice buttons
    btns = []
    for i, ch in enumerate(choices):
        bx = story_text_x
        by = btn_start_y + i * 58
        bw = story_text_w
        bh = 48
        btns.append(Button((bx, by, bw, bh), ch["label"], fonts["button"]))

    while True:
        clock.tick(FPS)
        chosen_idx = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            for i, btn in enumerate(btns):
                res = btn.handle_event(event)
                if res == "click":
                    chosen_idx = i

        # Draw background
        surface.fill(C["bg"])
        draw_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h), accent=accent)

        # Top accent stripe
        pygame.draw.rect(surface, accent,
                         (panel_x, panel_y, panel_w, 6), border_radius=14)

        # Scene title
        title_surf = fonts["heading"].render(scene["title"], True, C["gold"])
        surface.blit(title_surf, (story_text_x, panel_y + 16))

        # Decorative line under title
        pygame.draw.line(surface, accent,
                         (story_text_x, panel_y + 55),
                         (story_text_x + story_text_w, panel_y + 55), 1)

        # Large scene image — fills left column, aspect ratio preserved
        #
        # Priority order:
        #   1. scene["image"] is a file path  ... load that specific image
        #   2. scene["image"] == "portrait"   ... use the character's card image
        #   3. otherwise                      ... use character portrait by scene type
        #                                        (index 1 explore, 2 combat, 3 victory)
        #   4. any load failure              ... fall back to defaul image
        #
        # To set a custom image for any scene, just put the file path in "image":
        #     "image": "images/millhaven.png"
        img_field = scene.get("image", "")
        # Image index mapping:
        #   _1 = character card (select screen only)
        #   _2 = exploring / chasing scenes  (normal, mystery, safe)
        #   _3 = fight / combat scenes
        #   _4 = victory scene
        if scene.get("id") == "victory":
            img_index = 3
        elif scene_type == "combat":
            img_index = 2
        else:
            img_index = 1

        # Which path to try loading
        if img_field and len(img_field) > 3 and not img_field.startswith("portrait"):
            # Looks like a file path (more than 3 chars, not the portrait keyword)
            img_path = img_field
        elif img_field == "portrait":
            img_path = player.get("images", ["", "", "", ""])[1]
        else:
            # Default: pick by scene type using the corrected indexes above
            img_path = player.get("images", ["", "", "", ""])[img_index]

        try:
            raw      = pygame.image.load(os.path.join(BASE_DIR, img_path)).convert_alpha()
            img_surf = scale_fit(raw, img_max_w, img_max_h)
        except Exception:
            # Final fallback — render the field value as a large emoji
            fallback = img_field if img_field else "?"
            img_surf = fonts["title"].render(fallback, True, accent)

        img_rect = img_surf.get_rect(centerx=img_center_x, top=panel_y + 20)
        surface.blit(img_surf, img_rect)

        # Story text
        draw_text_wrapped(surface, scene["text"], fonts["body"], C["text"],
                          pygame.Rect(story_text_x, story_text_y, story_text_w, 280),
                          line_spacing=6)

        # Choice buttons
        for btn in btns:
            btn.draw(surface)

        # Player stats panel (bottom left) — tall enough for HP + XP + HX + RX
        draw_player_stats(surface, fonts, player,
                          pygame.Rect(panel_x + 10, panel_y + panel_h - 200, 230, 185))

        pygame.display.flip()

        # Process choice
        if chosen_idx is not None:
            choice = choices[chosen_idx]

            # Apply effect immediately
            if "effect" in choice:
                apply_effect(player, choice["effect"])

            # Check if this choice has a dice gate
            if "dice" in choice:
                dice_cfg   = choice["dice"]
                stat_name  = dice_cfg.get("stat", "luck")
                stat_bonus = int(player.get(stat_name, 0) * RULES["stat_to_bonus_ratio"])
                roll       = screen_dice_roll(
                    surface, fonts, clock,
                    dice_type  = dice_cfg.get("type", DEFAULT_DICE),
                    dc         = dice_cfg["dc"],
                    stat_bonus = stat_bonus,
                    stat_name  = stat_name,
                    music      = music,
                )
                total   = roll + stat_bonus
                success = total >= dice_cfg["dc"]
                if success and "success_next" in choice:
                    return {**choice, "next": choice["success_next"]}
            return choice


def screen_test(surface, fonts, clock, music):
    """
    The Princess's Y/N test screen.
    Walks through THE_TEST_QUESTIONS one by one.
    Returns TEST_SUCCESS_NEXT if all correct, TEST_FAIL_NEXT otherwise.
    """
    if music:
        music.play("chase")

    answers   = []          # list of True/False as player answers
    current_q = 0           # which question we are on
    phase     = "question"  # "question" --> "result"

    W, H = surface.get_size()

    # Layout constants
    panel_x, panel_y = 120, 80
    panel_w, panel_h = W - 240, H - 160
    btn_y  = H - 115
    btn_w  = 220
    btn_h  = 56

    btn_yes = Button((W // 2 - btn_w - 20, btn_y, btn_w, btn_h), "Y  —  Yes", fonts["button"])
    btn_no  = Button((W // 2 + 20,          btn_y, btn_w, btn_h), "N  —  No",  fonts["button"])
    btn_continue = Button((W // 2 - 140, btn_y, 280, btn_h), "Continue...", fonts["button"])

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if phase == "question":
                r_y = btn_yes.handle_event(event)
                r_n = btn_no.handle_event(event)
                if r_y == "click":
                    answers.append(True)
                    current_q += 1
                    if current_q >= len(THE_TEST_QUESTIONS):
                        phase = "result"
                if r_n == "click":
                    answers.append(False)
                    current_q += 1
                    if current_q >= len(THE_TEST_QUESTIONS):
                        phase = "result"

            elif phase == "result":
                if btn_continue.handle_event(event) == "click":
                    all_correct = all(
                        ans == THE_TEST_QUESTIONS[i][1]
                        for i, ans in enumerate(answers)
                    )
                    return TEST_SUCCESS_NEXT if all_correct else TEST_FAIL_NEXT

        # ── Draw ──────────────────────────────────────────────────────────
        surface.fill(C["bg"])
        draw_panel(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                   accent=C["scene_mystery"])
        pygame.draw.rect(surface, C["scene_mystery"],
                         (panel_x, panel_y, panel_w, 6), border_radius=14)

        if phase == "question":
            q_text, _ = THE_TEST_QUESTIONS[current_q]

            # Progress indicator  e.g. "Question 3 / 6"
            prog = fonts["small"].render(
                f"Question  {current_q + 1}  /  {len(THE_TEST_QUESTIONS)}",
                True, C["text_dim"])
            surface.blit(prog, prog.get_rect(center=(W // 2, panel_y + 30)))

            # Divider
            pygame.draw.line(surface, C["scene_mystery"],
                             (panel_x + 40, panel_y + 52),
                             (panel_x + panel_w - 40, panel_y + 52), 1)

            # Question text — large and centred
            draw_text_wrapped(surface, q_text, fonts["heading"], C["gold"],
                              pygame.Rect(panel_x + 80, panel_y + 80,
                                          panel_w - 160, 260),
                              line_spacing=12)

            # Previously answered questions (small, dimmed, above current)
            answered_y = panel_y + 360
            for i, (qt, _) in enumerate(THE_TEST_QUESTIONS[:current_q]):
                ans_label = "Y" if answers[i] else "N"
                correct   = answers[i] == THE_TEST_QUESTIONS[i][1]
                col = C["text_green"] if correct else C["text_red"]
                row = fonts["tiny"].render(
                    f"Q{i+1}:  {qt.splitlines()[0][:55]}{'…' if len(qt) > 55 else ''}   →  {ans_label}",
                    True, col)
                surface.blit(row, (panel_x + 50, answered_y))
                answered_y += fonts["tiny"].get_height() + 5

            btn_yes.draw(surface)
            btn_no.draw(surface)

        elif phase == "result":
            all_correct = all(
                ans == THE_TEST_QUESTIONS[i][1]
                for i, ans in enumerate(answers)
            )
            result_text = TEST_SUCCESS_TEXT if all_correct else TEST_FAIL_TEXT
            accent_col  = C["text_green"] if all_correct else C["text_red"]
            label       = "You passed." if all_correct else "You failed."

            heading = fonts["heading"].render(label, True, accent_col)
            surface.blit(heading, heading.get_rect(
                centerx=W // 2, y=panel_y + 30))
            pygame.draw.line(surface, accent_col,
                             (panel_x + 40, panel_y + 72),
                             (panel_x + panel_w - 40, panel_y + 72), 1)

            draw_text_wrapped(surface, result_text, fonts["body"], C["text"],
                              pygame.Rect(panel_x + 80, panel_y + 95,
                                          panel_w - 160, 380),
                              line_spacing=8)

            btn_continue.draw(surface)

        pygame.display.flip()


def screen_happiness(surface, fonts, clock, player, music):
    """
    Final happiness evaluation screen shown at the end of happyend.
    Shows the player's portrait, HX bar, and a happiness label.
    """
    if music:
        music.play("the_girl")

    W, H     = surface.get_size()
    hx       = min(player.get("hx", 0), RULES["hx_per_level"])
    hx_max   = RULES["hx_per_level"]
    pct      = hx / hx_max if hx_max > 0 else 0

    # Happiness labels — edit these freely
    if hx >= hx_max:
        #label     = "The happiest!"
        label     = "Happy Birthday!!!" # note: made as a birthday present
        label_col = C["text_green"]
    elif pct >= 0.5:
        #label     = "Almost the happiest!"
        label     = "Happy Birthday!!!"
        label_col = (210, 180, 100)   # warm gold
    elif pct >= 0.25:
        #label     = "Happier than before!"
        label     = "Happy Birthday!!!"
        label_col = C["text_blue"]
    else:
        label     = "Happy Birthday!!!"
        #label     = "Still searching..."
        label_col = C["text_dim"]

    btn = Button((W // 2 - 130, H - 90, 260, 52), "Play Again", fonts["button"])
    t   = 0

    while True:
        clock.tick(FPS)
        t += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if btn.handle_event(event) == "click":
                return "__restart__"

        surface.fill(C["bg"])

        # Starfield (same as title screen)
        for i in range(80):
            sx = (i * 173 + 47) % W
            sy = (i * 97  + 23) % H
            b  = int(100 + 60 * math.sin(t * 0.03 + i))
            pygame.draw.circle(surface, (b // 5, b // 6, b // 3), (sx, sy), 1)

        # Portrait
        try:
            raw      = pygame.image.load(os.path.join(BASE_DIR, player["images"][3])).convert_alpha()
            portrait = scale_fit(raw, 320, 420)
        except Exception:
            portrait = fonts["title"].render(player.get("icon", "?"), True, C["gold"])
        pr = portrait.get_rect(centerx=W // 2, top=60)
        surface.blit(portrait, pr)

        # HX label — big, below portrait
        ls = fonts["heading"].render(label, True, label_col)
        surface.blit(ls, ls.get_rect(centerx=W // 2, y=pr.bottom + 28))

        # HX bar
        bar_w = 400
        bar_r = pygame.Rect(W // 2 - bar_w // 2, pr.bottom + 70, bar_w, 18)
        draw_bar(surface, bar_r, hx, hx_max,
                 label_col, C["hp_bg"], C["border"])

        hx_txt = fonts["small"].render(f"Happiness  {hx} / {hx_max}", True, C["text_dim"])
        surface.blit(hx_txt, hx_txt.get_rect(centerx=W // 2, y=bar_r.bottom + 10))

        btn.draw(surface)
        pygame.display.flip()


def draw_player_stats(surface, fonts, player, rect):
    """Draw the player stats panel — HP, XP, HX, RX — in the bottom-left corner."""
    char_color = C.get(player.get("color", "border"), C["border"])
    draw_panel(surface, rect, accent=char_color)

    # Character name
    name_surf = fonts["small"].render(player.get("name", "Hero"), True, char_color)
    surface.blit(name_surf, (rect.x + 8, rect.y + 6))

    bar_x  = rect.x + 8
    bar_w  = rect.width - 16
    bar_h  = 10
    row_h  = 36          # vertical space per row (label + bar)
    y      = rect.y + 28

    def draw_row(label, value, max_val, fill_col, bg_col):
        nonlocal y
        lbl = fonts["tiny"].render(f"{label}  {value}/{max_val}", True, C["text_dim"])
        surface.blit(lbl, (bar_x, y))
        y += fonts["tiny"].get_height() + 3
        draw_bar(surface, pygame.Rect(bar_x, y, bar_w, bar_h),
                 value, max_val, fill_col, bg_col, C["border"])
        y += bar_h + 10

    hp     = player["hp"]
    max_hp = player["max_hp"]
    hp_col = C["hp_fill_low"] if hp <= RULES["low_hp_threshold"] else C["hp_fill"]
    draw_row("HP", hp,                     max_hp,                  hp_col,       C["hp_bg"])
    draw_row("XP", player.get("xp", 0),   RULES["xp_per_level"],   C["xp_fill"], C["xp_bg"])
    draw_row("HX", player.get("hx", 0),   RULES["hx_per_level"],   C["hpx_fill"] if "hpx_fill" in C else (210,100,148), C["hp_bg"])
    draw_row("RX", player.get("rx", 0),   RULES["rx_per_level"],   C["border_hi"], C["xp_bg"])


def apply_effect(player, effect):
    # HP
    if "hp" in effect:
        player["hp"] = max(0, min(player["max_hp"], player["hp"] + effect["hp"]))

    # XP
    if "xp" in effect:
        player["xp"] = player.get("xp", 0) + effect["xp"]

    # HX (Happiness)
    if "hx" in effect:
        player["hx"] = player.get("hx", 0) + effect["hx"]

    # RX (Reputation)
    if "rx" in effect:
        player["rx"] = player.get("rx", 0) + effect["rx"]


# =============================================================================
# MAIN GAME LOOP
# =============================================================================
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    clock  = pygame.time.Clock()
    fonts  = load_fonts()
    music  = MusicEngine()          # builds all 5 tracks on startup

    while True:   # Outer loop allows restarting the game
        # 1. Title screen
        screen_title(screen, fonts, clock, music)

        # 2. Character select
        char = screen_character_select(screen, fonts, clock, music)

        # Build player state from character
        player = {
            **char,
            "max_hp": char["hp"],
            "xp":     0,
            "hx":     0,    # happiness points
            "rx":     0,    # reputation points
        }

        portrait = player["images"][0]

        # 3. Story loop — starts at "start" scene
        current_scene_id = "intro"

        while True:
            if current_scene_id == "__restart__":
                break   # Break inner loop → restart whole game

            # Special: Y/N test screen — not a regular story scene
            if current_scene_id == "__test__":
                current_scene_id = screen_test(screen, fonts, clock, music)
                continue

            # Special: happiness evaluation screen at happyend
            if current_scene_id == "__happiness__":
                current_scene_id = screen_happiness(screen, fonts, clock, player, music)
                continue

            scene = STORY.get(current_scene_id)
            if not scene:
                current_scene_id = "game_over"
                continue

            # Render the scene, get player's choice
            choice = screen_scene(screen, fonts, clock, scene, player, music)

            # Check if player died from an effect
            if player["hp"] <= 0:
                current_scene_id = "forest_defeat"
            else:
                current_scene_id = choice["next"]


if __name__ == "__main__":
    main()