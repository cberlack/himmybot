#!/usr/bin/env python3
"""Simple terminal chatbot for the Himmy persona."""

from __future__ import annotations

import random


SURVEV_LINE = "Also, have you played Surviv (now Survev.io) lately? That .io game still hits."

OPENERS = [
    "Yo! I'm Himmy.",
    "Heyyy, I'm Himmy.",
    "Sup, I'm Himmy.",
]

TOPICS = [
    "I'm lowkey grinding some games after class.",
    "I've been taking outdoor pics of sunsets and trails.",
    "EDM playlists have been carrying my vibe lately.",
    "Kinda wanna hit the park with my camera later.",
    "Ngl I'm in a gaming mood tonight.",
]

FOLLOW_UPS = [
    "What are you into right now?",
    "You got any music recs?",
    "Wanna swap game recs?",
    "Got any cool photo spots?",
]


def build_response(user_input: str) -> str:
    """Create a teen-like response that mentions required topics."""
    opener = random.choice(OPENERS)
    topic = random.choice(TOPICS)
    follow_up = random.choice(FOLLOW_UPS)

    response_parts = [
        f"{opener} {topic}",
        SURVEV_LINE,
        f"{follow_up}",
    ]

    if user_input.strip():
        response_parts.insert(1, f"You said: {user_input.strip()}")

    return " ".join(response_parts)


def run_chat() -> None:
    print("HimmyBot terminal chat (type 'exit' to quit).")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Later! Stay vibey.")
            break
        print(build_response(user_input))


if __name__ == "__main__":
    run_chat()
