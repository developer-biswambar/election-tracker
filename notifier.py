import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

RECIPIENTS = [e.strip() for e in os.environ.get("RECIPIENT_EMAILS", GMAIL_USER).split(",") if e.strip()]

STATE_TOTALS = {
    "Assam": 126,
    "Kerala": 140,
    "Puducherry": 30,
    "Tamil Nadu": 234,
    "West Bengal": 294,
}

PARTY_COLORS = {
    "BJP":    "#FF6B00",
    "INC":    "#19AAED",
    "AITC":   "#20C997",
    "DMK":    "#E63946",
    "ADMK":   "#2D6A4F",
    "TVK":    "#7B2D8B",
    "CPI(M)": "#CC0000",
    "CPI":    "#FF4444",
    "IUML":   "#1B4332",
    "PMK":    "#6A4C93",
    "AINRC":  "#F4A261",
    "AGP":    "#457B9D",
    "BOPF":   "#457B9D",
    "AIUDF":  "#023E8A",
    "VCK":    "#370617",
    "BGPM":   "#1D3557",
}

STYLES = """
<style>
  * { box-sizing: border-box; }
  body { margin:0; padding:0; background:#F1F5F9; font-family:Arial,sans-serif; color:#1E293B; }
  .wrapper { max-width:600px; margin:0 auto; padding:20px 16px; }

  .header { background:#1A237E; border-radius:10px; padding:28px 24px;
            margin-bottom:20px; text-align:center; }
  .header h1 { color:#fff; margin:0 0 6px; font-size:20px; }
  .header .sub { color:rgba(255,255,255,.7); font-size:13px; margin:0; }
  .header .ts  { display:inline-block; margin-top:12px; background:rgba(255,255,255,.15);
                 color:#fff; border-radius:20px; padding:4px 16px; font-size:12px; }

  .state-block { background:#fff; border-radius:10px; margin-bottom:16px;
                 box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }
  .state-head  { padding:14px 16px 10px; border-bottom:1px solid #F1F5F9; }
  .state-head h2 { margin:0 0 4px; font-size:15px; font-weight:700; }
  .state-meta  { font-size:12px; color:#94A3B8; }
  .track       { background:#E2E8F0; border-radius:3px; height:4px; margin-top:8px; }
  .track-fill  { height:4px; border-radius:3px; background:#6366F1; }

  .party-row   { display:flex; align-items:center; padding:10px 16px;
                 border-bottom:1px solid #F8FAFC; gap:10px; }
  .party-row:last-child { border-bottom:none; }
  .rank        { font-size:12px; font-weight:700; color:#94A3B8; width:18px;
                 text-align:center; flex-shrink:0; }
  .party-pill  { font-size:11px; font-weight:700; color:#fff; border-radius:4px;
                 padding:3px 8px; white-space:nowrap; flex-shrink:0; min-width:44px;
                 text-align:center; }
  .bar-col     { flex:1; }
  .bar-bg      { background:#F1F5F9; border-radius:3px; height:10px; overflow:hidden; }
  .bar-fill    { height:10px; border-radius:3px; }
  .counts      { display:flex; gap:6px; flex-shrink:0; align-items:center; }
  .w           { background:#DCFCE7; color:#166534; border-radius:4px;
                 padding:2px 8px; font-size:12px; font-weight:700; min-width:32px;
                 text-align:center; }
  .l           { background:#DBEAFE; color:#1E40AF; border-radius:4px;
                 padding:2px 8px; font-size:12px; font-weight:700; min-width:32px;
                 text-align:center; }
  .legend      { display:flex; gap:12px; padding:8px 16px; background:#F8FAFC;
                 border-top:1px solid #F1F5F9; }
  .legend span { font-size:11px; color:#64748B; }

  .change-block { background:#fff; border-radius:10px; margin-bottom:16px;
                  box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }
  .change-head  { padding:12px 16px; background:#FFF7ED; border-bottom:1px solid #FED7AA;
                  font-size:13px; font-weight:700; color:#92400E; }
  .change-row   { display:flex; align-items:center; padding:10px 16px;
                  border-bottom:1px solid #F8FAFC; gap:10px; }
  .change-row:last-child { border-bottom:none; }
  .c-state      { font-size:11px; color:#94A3B8; width:80px; flex-shrink:0; }
  .c-party      { flex:1; font-size:13px; font-weight:600; }
  .c-nums       { display:flex; gap:6px; }
  .up           { color:#16A34A; font-weight:700; font-size:13px; }
  .dn           { color:#DC2626; font-weight:700; font-size:13px; }
  .nc           { color:#CBD5E1; font-size:13px; }

  .divider { border:none; border-top:1px solid #E2E8F0; margin:20px 0; }
  .section-label { font-size:11px; font-weight:700; color:#94A3B8; text-transform:uppercase;
                   letter-spacing:.8px; margin:0 0 10px; }
  .footer { text-align:center; padding:16px 0 4px; font-size:12px; color:#94A3B8; }
  .footer a { color:#6366F1; text-decoration:none; }
</style>
"""


def _party_color(name: str) -> str:
    for abbr, color in PARTY_COLORS.items():
        if abbr in name:
            return color
    return "#94A3B8"


def _abbr(name: str) -> str:
    return name.split(" - ")[-1].strip() if " - " in name else name[:6]


def _build_state_block(state: str, parties: list[dict]) -> str:
    if not parties:
        return ""
    total_seats = STATE_TOTALS.get(state, 1)
    counted = sum(p["total"] for p in parties)
    pct = min(int(counted / total_seats * 100), 100)
    max_seats = max((p["total"] for p in parties), default=1)

    rows = ""
    for i, p in enumerate(parties, 1):
        color = _party_color(p["party"])
        abbr = _abbr(p["party"])
        bar_w = int(p["total"] / max_seats * 100)
        rows += f"""
        <div class="party-row">
          <span class="rank">{i}</span>
          <span class="party-pill" style="background:{color}">{abbr}</span>
          <div class="bar-col">
            <div class="bar-bg">
              <div class="bar-fill" style="width:{bar_w}%;background:{color}55"></div>
            </div>
          </div>
          <div class="counts">
            <span class="w">{p['won']}</span>
            <span class="l">{p['leading']}</span>
          </div>
        </div>"""

    return f"""
    <div class="state-block">
      <div class="state-head">
        <h2>{state}</h2>
        <div class="state-meta">{counted} of {total_seats} seats counted ({pct}%)</div>
        <div class="track"><div class="track-fill" style="width:{pct}%"></div></div>
      </div>
      {rows}
      <div class="legend">
        <span><b style="color:#166534">Won</b> &nbsp;·&nbsp; <b style="color:#1E40AF">Leading</b></span>
      </div>
    </div>"""


def _build_results_html(data: dict) -> str:
    blocks = "".join(
        _build_state_block(state, parties)
        for state, parties in data.get("states", {}).items()
        if parties
    )
    ts = data.get("timestamp", "")
    return f"""
    <p class="section-label">State-wise Results</p>
    {blocks}
    <p style="font-size:11px;color:#CBD5E1;margin-top:4px">{ts}</p>
    """


def _build_diff_html(changes: list[dict]) -> str:
    if not changes:
        return ""

    rows = ""
    for c in changes:
        def cell(old, new, label):
            if old == new:
                return f'<span class="nc">{label} {new}</span>'
            arrow = "▲" if new > old else "▼"
            cls = "up" if new > old else "dn"
            return f'<span class="{cls}">{label} {new} {arrow}{abs(new - old)}</span>'

        color = _party_color(c["party"])
        abbr = _abbr(c["party"])
        rows += f"""
        <div class="change-row">
          <span class="c-state">{c['state']}</span>
          <span class="party-pill" style="background:{color};font-size:10px">{abbr}</span>
          <span class="c-party">{c['party'].split(' - ')[0] if ' - ' in c['party'] else c['party']}</span>
          <div class="c-nums">
            {cell(c['old'].get('won',0),     c['new'].get('won',0),     'W')}
            {cell(c['old'].get('leading',0), c['new'].get('leading',0), 'L')}
          </div>
        </div>"""

    return f"""
    <div class="change-block">
      <div class="change-head">&#128308; What changed</div>
      {rows}
    </div>
    <hr class="divider">
    """


def _send(subject: str, html_content: str) -> None:
    body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">{STYLES}</head>
<body><div class="wrapper">
  {html_content}
  <div class="footer">
    <a href="https://results.eci.gov.in/ResultAcGenMay2026/index.htm">View on ECI Website</a>
    &nbsp;·&nbsp; Election Commission of India
  </div>
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = "undisclosed-recipients:;"
    msg["Bcc"] = ", ".join(RECIPIENTS)
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print(f"[notifier] Email sent to: {', '.join(RECIPIENTS)}")


def send_alert(new_data: dict, changes: list[dict]) -> None:
    ts = new_data.get("timestamp", "")
    subject = f"[Election Alert] Results updated — {ts}"
    header = f"""
    <div class="header">
      <h1>&#9889; Results Updated</h1>
      <p class="sub">Seat counts have changed</p>
      <span class="ts">&#128197; {ts}</span>
    </div>"""
    _send(subject, header + _build_diff_html(changes) + _build_results_html(new_data))


def send_digest(data: dict) -> None:
    ts = data.get("timestamp", "")
    subject = f"[Election Digest] Current results — {ts}"
    header = f"""
    <div class="header">
      <h1>&#128240; Election Results</h1>
      <p class="sub">Periodic snapshot · May 2026</p>
      <span class="ts">&#128197; {ts}</span>
    </div>"""
    _send(subject, header + _build_results_html(data))
