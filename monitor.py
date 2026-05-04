import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from scraper import fetch_all_results
from notifier import send_alert

SNAPSHOT_PATH = Path(os.environ.get("SNAPSHOT_PATH", "/data/snapshot.json"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL_SECONDS", 300))


def load_snapshot() -> dict | None:
    if SNAPSHOT_PATH.exists():
        with open(SNAPSHOT_PATH) as f:
            return json.load(f)
    return None


def save_snapshot(data: dict) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def compute_changes(old: dict, new: dict) -> list[dict]:
    changes = []
    old_states = old.get("states", {})
    new_states = new.get("states", {})

    for state, new_parties in new_states.items():
        old_parties = old_states.get(state, [])
        old_map = {p["party"]: p for p in old_parties}
        new_map = {p["party"]: p for p in new_parties}

        all_parties = set(old_map) | set(new_map)
        for party in all_parties:
            o = old_map.get(party, {"won": 0, "leading": 0, "total": 0})
            n = new_map.get(party, {"won": 0, "leading": 0, "total": 0})
            if o["won"] != n["won"] or o["leading"] != n["leading"] or o["total"] != n["total"]:
                changes.append({"state": state, "party": party, "old": o, "new": n})

    return changes


def run_once() -> None:
    print(f"[monitor] Fetching results at {datetime.now().strftime('%H:%M:%S')}...")
    try:
        new_data = fetch_all_results()
    except Exception as e:
        print(f"[monitor] Fetch failed: {e}")
        return

    old_data = load_snapshot()

    if old_data is None:
        print("[monitor] No snapshot found — saving baseline, no email sent.")
        save_snapshot(new_data)
        return

    changes = compute_changes(old_data, new_data)

    if changes:
        print(f"[monitor] {len(changes)} change(s) detected — sending email.")
        try:
            send_alert(new_data, changes)
        except Exception as e:
            print(f"[monitor] Email failed: {e}")
        save_snapshot(new_data)
    else:
        print("[monitor] No changes detected.")


def main() -> None:
    print(f"[monitor] Starting. Checking every {CHECK_INTERVAL}s.")
    while True:
        run_once()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
