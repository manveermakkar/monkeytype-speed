"""
Fetches recent MonkeyType test results via the public API and appends any
results not already logged to results.json.

Requires the MONKEYTYPE_APE_KEY environment variable to be set.
Docs / ApeKey setup: https://monkeytype.com/settings (search "ape key")
"""

import os
import json
import sys

import requests

API_BASE = "https://api.monkeytype.com"
LOG_FILE = "results.json"
FETCH_LIMIT = 50  # how many recent results to pull each run

APE_KEY = os.environ.get("MONKEYTYPE_APE_KEY")
if not APE_KEY:
    sys.exit("MONKEYTYPE_APE_KEY environment variable is not set.")

HEADERS = {"Authorization": f"ApeKey {APE_KEY}"}


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_log(entries):
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2, sort_keys=True)


def fetch_recent_results(limit=FETCH_LIMIT):
    resp = requests.get(
        f"{API_BASE}/results",
        headers=HEADERS,
        params={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    # The API may wrap the array in a "data" key, or return it directly —
    # handle both shapes defensively.
    return body.get("data", body) if isinstance(body, dict) else body


def normalize(entry):
    """Keep only the fields worth logging long-term."""
    return {
        "timestamp": entry.get("timestamp"),
        "mode": entry.get("mode"),
        "mode2": entry.get("mode2"),
        "wpm": entry.get("wpm"),
        "rawWpm": entry.get("rawWpm", entry.get("raw")),
        "accuracy": entry.get("acc"),
        "consistency": entry.get("consistency"),
        "language": entry.get("language"),
    }
def fetch_recent_results(limit=FETCH_LIMIT):
    try:
        resp = requests.get(
            f"{API_BASE}/results",
            headers=HEADERS,
            params={"limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"API Error: Status {resp.status_code}")
        print(f"Response: {resp.text}")
        raise
    
    body = resp.json()
    return body.get("data", body) if isinstance(body, dict) else body  


def main():
    existing = load_log()
    known_timestamps = {e["timestamp"] for e in existing}

    fetched = fetch_recent_results()
    new_entries = [
        normalize(e) for e in fetched if e.get("timestamp") not in known_timestamps
    ]

    if not new_entries:
        print("No new results since last sync.")
        return

    combined = existing + new_entries
    combined.sort(key=lambda e: e["timestamp"] or 0)
    save_log(combined)
    print(f"Added {len(new_entries)} new result(s). Total logged: {len(combined)}.")


if __name__ == "__main__":
    main()
