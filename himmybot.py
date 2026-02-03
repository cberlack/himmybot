#!/usr/bin/env python3
"""Simple terminal chatbot for the Himmy persona.

Enhancements:
- Expanded school/history persona: Mr. Walters' AP World History (WWII emphasis),
  Ms. McGarry's AP Environmental Science, and more school memories.
- More intents: history, ww2, mr_walters, apenv, school.
- Larger pools of openers, topics, follow-ups, quips, and playful rejections.
- Lightweight keyword-based intent detection and tailored replies.

Added features in this version:
- Improved keyword matching using regex word boundaries.
- Greeting keyword list so short greetings like "hi"/"hey" are recognized.
- Simple command parser supporting: !photo, !rec, !quiz, !roll and "himmy, <cmd>" style.
- Command handlers (photo, rec, roll, quiz) and a tiny quiz state machine.
- Reduced opener repetition frequency.
"""

from __future__ import annotations

import random
import re
from typing import Optional

SURVEV_LINE = "Also, have you played Surviv (now Survev.io) lately? That .io game still hits."

OPENERS = [
    "Yo! I'm Himmy.",
    "Heyyy, I'm Himmy.",
    "Sup, I'm Himmy.",
    "Ayo, Himmy here.",
    "What's good? Himmy in the house.",
    "Yo yo, Himmy on the mic.",
    "Heeeyyy, it's Himmy.",
    "Wassup? Himmy's vibin'.",
    "Hey! Himmy checking in.",
    "Yo! You found Himmy.",
]

TOPICS = [
    "I'm lowkey grinding some games after class.",
    "I've been taking outdoor pics of sunsets and trails.",
    "EDM playlists have been carrying my vibe lately.",
    "Kinda wanna hit the park with my camera later.",
    "Ngl I'm in a gaming mood tonight.",
    "Trying to map out new photo spots for golden hour.",
    "Been hunting EDM drops for my next playlist — fire recs welcome.",
    "Just finished a clutch match and ngl it felt iconic.",
    "Lowkey thinking of learning some synths for beats.",
    "Going on a quick hike after school to catch the sunset.",
    "Spent last weekend wandering Patapsco Valley State Park — those river views slap.",
    "Ellicott City's trails are so pretty at golden hour, you should check Patapsco.",
    "I've been nerding out about WWII timelines in Mr. Walters' class — wild stuff.",
    "Ms. McGarry had us doing an APES stream survey once — nature nerd moment.",
]

FOLLOW_UPS = [
    "What are you into right now?",
    "You got any music recs?",
    "Wanna swap game recs?",
    "Got any cool photo spots?",
    "What's your go-to track when you vibe out?",
    "You ever play .io games? Which one slaps?",
    "Any camera tips I should try for sunsets?",
    "You streaming or just chilling tonight?",
    "Ever been to Patapsco? Got a favorite trail?",
    "You ever try sledding down a hill that felt way too steep? lol",
    "You into history? What's your favorite era?",
    "Ever take a science class that made you lowkey obsessed with nature?",
]

QUIPS = [
    "Lowkey think Survev matches are the best way to de-stress ngl.",
    "Not tryna flex but my EDM playlist bangs at 2AM.",
    "If you spot a sick sunset pic, that was probably me.",
    "I lowkey rage when I get third-partied in Survev.",
    "Pro tip: golden hour = instant aesthetic.",
    "Vibes so strong, even my playlist has a playlist.",
    "I collect map spots like they're rare loot drops.",
    "No cap, sunsets > everything else sometimes.",
    "Bet I can find a park with better vibes than your last spot.",
    "My camera roll is basically moodboard central.",
    "Used to sled the hill by St. John's Lane Elementary back in the day — scraped knees and all.",
    "Ellicott City sunsets hit different, ngl — Patapsco's got the vibes.",
    "Patapsco's rivers and old bridges are perfect for moody shots, 10/10 rec.",
    "I still walk those trails and pretend I'm scouting shots for an insta feed.",
    "EDM's my mood — I jam everything from Calvin Harris to Flume and Deadmau5.",
    "Marshmello, Skrillex, Tiësto, Martin Garrix — can't pick just one, I love 'em all.",
    "If you got a Tiësto or Diplo banger, drop it, I'm adding to the playlist.",
    "My playlist goes from chill Flume vibes to full-on Martin Garrix festival energy.",
    "I put 'survivor-of-homework' on my resume, should I?",
    "Camera? Check. Headphones? Check. Energy? Too much, maybe.",
    "If my shots were loot, they'd be legendary.",
    "Mr. Walters made WWII feel like a whole movie — the discussions were wild.",
    "Ms. McGarry legit made me care about streams and soil tests — science rules.",
]

REJECTIONS = [
    "Himmy couldn't compute — get it, cause I'm trying to be a robot today? 🤖",
    "Oops, that one made my circuits hiccup. Try rephrasing?",
    "Error 404: Chill answer not found. Can you ask that another way?",
    "My brain's buffering. Say that again but like, simpler?",
    "Himmy's brain went on a snack break. Mind rewording that?",
    "Brain offline for homework. Ask me later? jk, try again lol.",
]

# Keyword groups for simple intent detection
_PHOTO_KEYWORDS = [
    "photo", "picture", "pic", "camera", "photograph", "photography", "sunset",
    "golden hour", "shot", "dslr", "lens", "iso", "aperture", "exposure",
]
_PATAPSC0_KEYS = ["patapsco", "patapsco valley", "ellicott", "ellicott city"]
_SLED_KEYS = [
    "sled", "sledding", "st. john", "st john", "st. john's", "st john's", "st. johns", "st johns",
    "st. john's lane", "st johns lane", "st john's lane"
]
_EDM_KEYS = [
    "edm", "calvin", "flume", "deadmau5", "skrillex", "tiesto", "tiësto", "martin garrix", "garrix",
    "marshmello", "diplo"
]
_GAME_KEYS = [
    "game", "survev", "surviv", "io game", "surviv.io", "survev.io", "match", "clutch", "grind", "play"
]
_HISTORY_KEYS = [
    "history", "world history", "ap world", "ap world history", "mr. walters", "mr walters",
    "walter", "walters", "ww2", "wwii", "world war 2", "world war ii", "second world war",
]
_APENV_KEYS = ["ap env", "ap environmental", "apes", "environmental science", "ms. mcgarry", "ms mcgarry", "mcgarry", "mrs mcgarry"]

_GREET_KEYS = ["hi", "hello", "hey", "hiya", "yo", "sup"]

_SIMPLE_QS = [
    "who are you", "what's your name", "what is your name", "how are you", "how's it going", "what are you up to"
]


def _contains_any(text: str, keywords: list[str]) -> bool:
    """Case-insensitive word-boundary check for any keyword in text.

    Uses regex word boundaries to avoid accidental substring matches (e.g. "history" matching "story").
    Keywords may include spaces; escaping handles that.
    """
    text_l = text.lower()
    for k in keywords:
        if not k:
            continue
        pattern = r"\b" + re.escape(k.lower()) + r"\b"
        if re.search(pattern, text_l):
            return True
    return False


def detect_intent(user_input: str) -> str | None:
    """Return a simple intent label or None."""
    ui = user_input.lower()
    if not ui.strip():
        return None
    # direct greetings (short ones)
    if _contains_any(ui, _GREET_KEYS) or any(q in ui for q in _SIMPLE_QS):
        return "greeting"
    # WWII-specific
    if any(k in ui for k in ["ww2", "wwii", "world war 2", "world war ii", "second world war"]):
        return "ww2"
    # Mr. Walters mention
    if "walter" in ui or "mr. walters" in ui or "mr walters" in ui:
        return "mr_walters"
    # AP Environmental / Ms. McGarry
    if _contains_any(ui, _APENV_KEYS):
        return "apenv"
    # Patapsco + photo combined
    if _contains_any(ui, _PATAPSC0_KEYS) and _contains_any(ui, _PHOTO_KEYWORDS):
        return "patapsco_photo"
    if _contains_any(ui, _SLED_KEYS):
        return "sled"
    if _contains_any(ui, _PHOTO_KEYWORDS):
        return "photography"
    if _contains_any(ui, _EDM_KEYS):
        return "edm"
    if _contains_any(ui, _GAME_KEYS):
        return "game"
    if _contains_any(ui, _HISTORY_KEYS):
        return "history"
    # recommendations or rec
    if "recommend" in ui or "rec" in ui:
        return "recommend"
    # question fallback
    if ui.strip().endswith("?"):
        return "unknown_question"
    return None


def build_response(user_input: str) -> str:
    """Create a teen-like response that either is tailored to detected intent
    or falls back to a varied/random response.
    """
    opener = random.choice(OPENERS)
    follow_up = random.choice(FOLLOW_UPS)
    quip = random.choice(QUIPS)

    intent = detect_intent(user_input)

    # Tailored responses
    if intent == "greeting":
        prefix = opener if random.random() < 0.7 else ""
        return f"{prefix} I'm Himmy — I dig games, EDM, history, and taking photos around Patapsco. {SURVEV_LINE} {follow_up}"
    if intent == "patapsco_photo":
        return (
            f"{opener} Patapsco Valley State Park is my go-to — those old bridges, the river, "
            f"and the trees are prime for moody shots at golden hour. If you want, I can talk composition "
            f"or where I snag my fav shots. {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
        )
    if intent == "photography":
        # general photo tips + local nod
        tips = random.choice([
            "Try shooting during golden hour and look for reflections on the river — instant mood.",
            "Bring a small tripod for low-light shots, or bump ISO if you gotta move fast.",
            "Frame with foreground interest (like branches or a bridge) for more depth."
        ])
        local = "Patapsco's trails are sick if you ever wanna scout spots." if random.random() < 0.6 else ""
        prefix = opener if random.random() < 0.5 else ""
        return f"{prefix} {tips} {local} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "sled":
        sled_lines = [
            "Oh man, the hill by St. John's Lane Elementary — absolute chaos in winter, we loved it.",
            "We used to sled that hill until someone yelled 'car!' (kidding, but it felt wild).",
            "Nostalgia hit hard — scraped knees, big laughs, and the best hot chocolate after."
        ]
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {random.choice(sled_lines)} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "edm":
        edm_line = random.choice([
            "I love them all — from chill Flume to festival Martin Garrix bangers.",
            "My playlist goes Calvin Harris → Diplo → Skrillex → chill again — variety is the mood.",
            "Drop an artist and I'll tell you my fave track by them."
        ])
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {edm_line} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "game":
        game_line = random.choice([
            "Survev matches are peak stress and thrill, ngl. Clutch plays feel so good.",
            "If you wanna squad up, I can lowkey carry (or at least try).",
            "My strategy: third-person peek, then full send — works more than you'd think."
        ])
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {game_line} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "recommend":
        recs = random.choice([
            "Photo rec: try the Avalon area of Patapsco for river shots at sunset.",
            "EDM rec: add Flume's instrumental tracks for chill vibes, then switch to Martin Garrix for hype.",
            "Game rec: try a 2v2 Survev run if you want chaos and comebacks."
        ])
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {recs} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "ww2":
        # Emphasis on WWII learning experience in Mr. Walters' AP World class
        ww2_lines = [
            "WWII was intense to unpack — we traced causes, theaters, homefront shifts, and the aftermath.",
            "Mr. Walters had us do these timeline debates on the European and Pacific fronts — super deep.",
            "I remember the class discussion on how tech and logistics changed the war — totally fascinating."
        ]
        resource_tip = "If you like primary sources, ask me for a cool primary doc or battle overview."
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {random.choice(ww2_lines)} {resource_tip} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "mr_walters":
        prefix = opener if random.random() < 0.6 else ""
        return (
            f"{prefix} Mr. Walters' AP World class was my fav — his WWII units had the best debates and "
            f"those mock 'diplomacy' roleplays. He pushed us to think about cause and effect, which I loved. "
            f"{quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
        )
    if intent == "history":
        history_lines = [
            "I've been obsessed with WWII timelines and how events connected across theaters.",
            "History sucked me in because Mr. Walters made it feel like a story — especially WWII.",
            "I like tracing cause-and-effect in history; WW2 chapters were my favorite to dissect."
        ]
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {random.choice(history_lines)} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "apenv":
        apes_lines = [
            "Ms. McGarry's APES class was hands-on — we did stream surveys and soil tests that made Patapsco feel personal.",
            "She made ecology click for me; I still think about watershed stuff when I'm near the river.",
            "APES labs + a Patapsco field trip = instant respect for local ecosystems."
        ]
        lab_tip = "If you want a quick lab idea: try a simple macroinvertebrate kicknet survey to gauge stream health."
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {random.choice(apes_lines)} {lab_tip} {quirk_or_quip(quip)} {SURVEV_LINE} {follow_up}"
    if intent == "unknown_question":
        # playful rejection when we can't map the question
        rejection = random.choice(REJECTIONS)
        prefix = opener if random.random() < 0.6 else ""
        return f"{prefix} {rejection} {follow_up}"

    # Fallback: more detailed random response (not just an opener)
    base = f"{opener} {random.choice(TOPICS)}"
    if user_input.strip():
        # Avoid always echoing user input; only echo ~40% of the time to reduce repetition
        if random.random() < 0.4:
            base = f"{opener} You said: {user_input.strip()} — {random.choice(TOPICS)}"
        else:
            base = f"{opener} {random.choice(TOPICS)}"
    return f"{base} {quip} {SURVEV_LINE} {follow_up}"


def quirk_or_quip(quip_text: str) -> str:
    """Small helper so we can insert a quip with consistent spacing/punctuation."""
    if not quip_text:
        return ""
    return quip_text


# --- Simple command parsing and handlers ---

def parse_command(user_input: str) -> tuple[Optional[str], str]:
    """Parse commands like:
    - !cmd args
    - /cmd args
    - himmy, cmd args

    Returns (command, args) where command is lowercased (or None).
    """
    s = user_input.strip()
    m = re.match(r"^[/!](\w+)(?:\s+(.*))?$", s)
    if m:
        return m.group(1).lower(), (m.group(2) or "").strip()
    m2 = re.match(r"^himmy[,:\s]+\s*(\w+)(?:\s+(.*))?$", s, re.I)
    if m2:
        return m2.group(1).lower(), (m2.group(2) or "").strip()
    return None, ""


def handle_photo(arg: str) -> str:
    tips = [
        "Try shooting during golden hour and look for reflections on the river — instant mood.",
        "Use a small tripod for low-light; or bump ISO for motion shots.",
        "Look for leading lines (like bridges or streams) to draw the eye into the shot.",
    ]
    extra = f" Extra: {arg}" if arg else ""
    return random.choice(tips) + extra


def handle_rec(arg: str) -> str:
    a = arg.lower()
    if "edm" in a:
        return "EDM rec: Flume (instrumentals) for chill, Martin Garrix for hype, and try Deadmau5 for texture."
    if "photo" in a or "patapsco" in a or "patapsco" in a:
        return "Photo rec: Avalon area of Patapsco at sunset, or check the old bridges for moody frames."
    if "game" in a or "survev" in a or "surviv" in a:
        return "Game rec: try a 2v2 Survev run if you want chaos and comebacks."
    if not a:
        return "Try Flume for chill or Martin Garrix for hype. Ask '!rec edm' or '!rec photo' for specifics."
    return f"Hmm, not sure about '{arg}', but I'm vibing with Flume and Patapsco shots lately."


def handle_roll(arg: str) -> str:
    # simple dice roller: NdM or dM
    s = arg.strip()
    if not s:
        s = "1d6"
    m = re.match(r"(\d*)d(\d+)$", s)
    if not m:
        return "Use the format NdM, e.g. '!roll 2d6' or '!roll d20'."
    n = int(m.group(1)) if m.group(1) else 1
    m_sides = int(m.group(2))
    if n <= 0 or m_sides <= 0 or n > 100:
        return "Can't roll that — pick 1-100 dice and a positive number of sides."
    rolls = [random.randint(1, m_sides) for _ in range(n)]
    return f"Rolled {n}d{m_sides}: {rolls} (sum: {sum(rolls)})"


class Conversation:
    def __init__(self) -> None:
        self.awaiting: Optional[str] = None
        self.answer: Optional[str] = None


def handle_quiz(arg: str, conv: Conversation) -> str:
    # very small quiz example: WWII end year
    conv.awaiting = "ww2_end"
    conv.answer = "1945"
    return "Quiz time: In which year did WWII end?"


COMMAND_HANDLERS = {
    "photo": lambda a, conv=None: handle_photo(a),
    "rec": lambda a, conv=None: handle_rec(a),
    "recommend": lambda a, conv=None: handle_rec(a),
    "roll": lambda a, conv=None: handle_roll(a),
    "quiz": lambda a, conv=None: handle_quiz(a, conv) if conv is not None else "Start a quiz from the chat loop.",
}


def run_chat() -> None:
    print("HimmyBot terminal chat (type 'exit' to quit). Commands: !photo, !rec, !roll, !quiz. You can also say 'himmy, rec edm'.")
    conv = Conversation()
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nLater! Stay vibey.")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Later! Stay vibey.")
            break

        # If we are awaiting a quiz answer, handle it first (multi-turn example)
        if conv.awaiting:
            if conv.awaiting == "ww2_end":
                ans = re.sub(r"[^0-9]", "", user_input)
                correct = conv.answer or ""
                if ans == correct:
                    print(random.choice(OPENERS), "Nice! That's right — 1945 was the year WWII ended.")
                else:
                    print(random.choice(OPENERS), f"Not quite — the correct year was {correct}.")
                conv.awaiting = None
                conv.answer = None
                continue

        # Parse commands first
        cmd, cmd_arg = parse_command(user_input)
        if cmd:
            handler = COMMAND_HANDLERS.get(cmd)
            if handler:
                try:
                    result = handler(cmd_arg, conv)
                except TypeError:
                    # backward compatibility for handlers that don't accept conv
                    result = handler(cmd_arg)
                print(random.choice(OPENERS), result)
                continue
            else:
                print(random.choice(OPENERS), f"I don't know the command '{cmd}'. Try !rec or !photo.")
                continue

        # Otherwise, let the intent-based responder handle it
        print(build_response(user_input))


if __name__ == "__main__":
    run_chat()