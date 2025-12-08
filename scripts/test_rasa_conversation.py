#!/usr/bin/env python3
# scripts/test_recommendation.py
# Run end-to-end: fill profile form, ask for learning path, assert recommendation happens.

import requests
import time
import sys

BASE = "http://localhost:5005"
SENDER = "test_user_1"
WAIT = 0.5

# Conversation (form completion) - matching user's actual conversation
messages = [
    "Hi",
    "i am computer engineering student and i want to learn AI",  # triggers form
    "computer engineering",  # degree
    "5",  # semester
    "3.22",  # gpa
    "Python",  # skills
    "1 hour",  # time_commitment
    "AI",  # interests
    "Learn AI"  # learning_goal - should complete form and trigger utter_profile_ready
]

# Follow-up that should trigger action_recommend_learning_path
follow_up = "What should I learn next?"

def send(msg):
    r = requests.post(f"{BASE}/webhooks/rest/webhook", json={"sender": SENDER, "message": msg}, timeout=8)
    r.raise_for_status()
    return r.json()

def get_tracker():
    r = requests.get(f"{BASE}/conversations/{SENDER}/tracker")
    r.raise_for_status()
    return r.json()

def print_bot_resp(resp):
    if not resp:
        print("[BOT] (no response)")
        return
    for m in resp:
        print("[BOT]", m.get("text") or m)

def main():
    print("Testing end-to-end recommendation (Rasa REST at", BASE, ")")
    for i, m in enumerate(messages, 1):
        print(f"\n[USER] ({i}) {m}")
        resp = send(m)
        print_bot_resp(resp)
        time.sleep(WAIT)

    # Ask for a recommendation
    print(f"\n[USER] -> {follow_up}")
    resp = send(follow_up)
    print_bot_resp(resp)

    # Check tracker for action execution
    time.sleep(0.6)
    tracker = get_tracker()
    events = tracker.get("events", [])
    # Find last ActionExecuted events (reverse for latest)
    last_actions = [e for e in reversed(events) if e.get("event") == "action"]
    executed_names = [a.get("name") for a in last_actions[:10]]
    print("\nLast actions (most recent first):", executed_names[:10])

    # Pass conditions:
    # 1) action_recommend_learning_path executed OR
    # 2) bot's text contains expected recommendation phrase
    recommendation_done = False

    if "action_recommend_learning_path" in executed_names:
        recommendation_done = True
        print("ACTION: action_recommend_learning_path was executed.")

    # also check bot responses for a recommendation-like phrase
    bot_texts = " ".join([m.get("text","").lower() for m in resp])
    if "learning path" in bot_texts or "recommend" in bot_texts or "here are" in bot_texts:
        recommendation_done = True
        print("BOT_REPLY indicates a recommendation.")

    if not recommendation_done:
        print("\nERROR: No recommendation detected.")
        print("Tracker slots:", tracker.get("slots"))
        sys.exit(2)

    print("\nSUCCESS: Recommendation delivered.")

if __name__ == '__main__':
    main()