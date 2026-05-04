import os
from twilio.rest import Client

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "")
FROM_NUMBER = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # sandbox default

# Comma-separated list of recipient WhatsApp numbers, e.g. +919876543210,+447911123456
RECIPIENTS = [
    f"whatsapp:{n.strip()}"
    for n in os.environ.get("WHATSAPP_RECIPIENTS", "").split(",")
    if n.strip()
]

ENABLED = bool(ACCOUNT_SID and AUTH_TOKEN and RECIPIENTS)


def _client() -> Client:
    return Client(ACCOUNT_SID, AUTH_TOKEN)


def _abbr(name: str) -> str:
    return name.split(" - ")[-1].strip() if " - " in name else name


def _send_all(body: str) -> None:
    if not ENABLED:
        print("[whatsapp] Skipped — TWILIO credentials or WHATSAPP_RECIPIENTS not set.")
        return
    client = _client()
    for to in RECIPIENTS:
        client.messages.create(from_=FROM_NUMBER, to=to, body=body)
    print(f"[whatsapp] Message sent to {len(RECIPIENTS)} recipient(s).")


def _format_diff(changes: list[dict]) -> str:
    lines = []
    # Group by state for readability
    by_state: dict[str, list] = {}
    for c in changes:
        by_state.setdefault(c["state"], []).append(c)

    for state, items in by_state.items():
        lines.append(f"*{state}*")
        for c in items:
            abbr = _abbr(c["party"])
            parts = []
            for key, label in [("won", "Won"), ("leading", "Leading")]:
                old, new = c["old"].get(key, 0), c["new"].get(key, 0)
                if old != new:
                    arrow = "▲" if new > old else "▼"
                    parts.append(f"{label}: {old}→{new} {arrow}{abs(new - old)}")
            if parts:
                lines.append(f"  • {abbr}: {', '.join(parts)}")
    return "\n".join(lines)


def _format_snapshot(data: dict) -> str:
    lines = []
    for state, parties in data.get("states", {}).items():
        if not parties:
            continue
        lines.append(f"\n*{state}*")
        for i, p in enumerate(parties[:5], 1):  # top 5 per state to keep message concise
            abbr = _abbr(p["party"])
            lines.append(f"  {i}. {abbr} — W:{p['won']}  L:{p['leading']}")
        if len(parties) > 5:
            lines.append(f"  _+{len(parties) - 5} more parties_")
    return "\n".join(lines)


def send_whatsapp_alert(new_data: dict, changes: list[dict]) -> None:
    ts = new_data.get("timestamp", "")
    body = (
        f"🔴 *Election Results Updated*\n"
        f"_{ts}_\n\n"
        f"*Changes:*\n"
        f"{_format_diff(changes)}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"*Current Snapshot (Top 5)*"
        f"{_format_snapshot(new_data)}"
    )
    _send_all(body)


def send_whatsapp_digest(data: dict) -> None:
    ts = data.get("timestamp", "")
    body = (
        f"📊 *Election Results Digest*\n"
        f"_{ts}_\n"
        f"━━━━━━━━━━━━━━"
        f"{_format_snapshot(data)}\n\n"
        f"_Top 5 parties per state shown. Won (W) · Leading (L)_"
    )
    _send_all(body)
