import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

RECIPIENTS = [e.strip() for e in os.environ.get("RECIPIENT_EMAILS", GMAIL_USER).split(",") if e.strip()]

# Total assembly constituencies per state
STATE_TOTALS = {
    "Assam": 126,
    "Kerala": 140,
    "Puducherry": 30,
    "Tamil Nadu": 234,
    "West Bengal": 294,
}

# Rough party colour map (fallback to grey)
PARTY_COLORS = {
    "BJP": "#FF6B00",
    "INC": "#19AAED",
    "AITC": "#20C997",
    "DMK": "#CC0000",
    "ADMK": "#006400",
    "TVK": "#8B0000",
    "CPI(M)": "#CC0000",
    "CPI": "#E63946",
    "IUML": "#1B4332",
    "PMK": "#6A4C93",
    "AINRC": "#F4A261",
    "AGP": "#2D6A4F",
    "BOPF": "#457B9D",
    "AIUDF": "#023E8A",
    "VCK": "#370617",
    "BGPM": "#1D3557",
}

STYLES = """
<style>
  body { margin:0; padding:0; background:#F0F4F8; font-family:'Segoe UI',Arial,sans-serif; }
  .wrapper { max-width:680px; margin:0 auto; background:#F0F4F8; padding:24px 16px; }
  .header { background:linear-gradient(135deg,#1A237E 0%,#283593 60%,#FF6F00 100%);
            border-radius:12px; padding:32px 28px; margin-bottom:24px; text-align:center; }
  .header h1 { color:#fff; margin:0 0 4px; font-size:22px; letter-spacing:.4px; }
  .header p  { color:rgba(255,255,255,.8); margin:0; font-size:13px; }
  .badge { display:inline-block; background:rgba(255,255,255,.18); color:#fff;
           border-radius:20px; padding:4px 14px; font-size:12px; margin-top:10px; }
  .summary-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
                  gap:12px; margin-bottom:24px; }
  .summary-card { background:#fff; border-radius:10px; padding:14px 12px; text-align:center;
                  box-shadow:0 1px 4px rgba(0,0,0,.08); }
  .summary-card .state-name { font-size:11px; color:#64748B; font-weight:600;
                               text-transform:uppercase; letter-spacing:.5px; margin-bottom:6px; }
  .summary-card .seats-filed { font-size:20px; font-weight:700; color:#1E293B; line-height:1; }
  .summary-card .seats-total { font-size:11px; color:#94A3B8; margin-top:2px; }
  .progress-bar { background:#E2E8F0; border-radius:4px; height:5px; margin-top:8px; overflow:hidden; }
  .progress-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#3B82F6,#6366F1); }
  .state-card { background:#fff; border-radius:12px; margin-bottom:20px;
                box-shadow:0 1px 6px rgba(0,0,0,.07); overflow:hidden; }
  .state-header { padding:14px 20px; border-bottom:1px solid #F1F5F9;
                  display:flex; justify-content:space-between; align-items:center; }
  .state-header h2 { margin:0; font-size:16px; color:#0F172A; font-weight:700; }
  .state-header .meta { font-size:12px; color:#94A3B8; }
  table { width:100%; border-collapse:collapse; }
  thead th { background:#F8FAFC; padding:10px 14px; text-align:left;
             font-size:11px; color:#64748B; font-weight:700; text-transform:uppercase;
             letter-spacing:.5px; border-bottom:1px solid #E2E8F0; }
  thead th.num { text-align:center; }
  tbody tr { border-bottom:1px solid #F1F5F9; transition:background .15s; }
  tbody tr:last-child { border-bottom:none; }
  tbody tr:hover { background:#F8FAFC; }
  tbody td { padding:10px 14px; font-size:13px; color:#334155; }
  tbody td.num { text-align:center; font-weight:600; }
  .rank { display:inline-block; width:20px; height:20px; border-radius:50%;
          background:#F1F5F9; color:#64748B; font-size:10px; font-weight:700;
          text-align:center; line-height:20px; margin-right:8px; }
  .rank-1 { background:#FEF3C7; color:#92400E; }
  .rank-2 { background:#F1F5F9; color:#475569; }
  .rank-3 { background:#FEF9EE; color:#78350F; }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%;
         margin-right:6px; vertical-align:middle; }
  .won-badge { background:#DCFCE7; color:#166534; border-radius:4px;
               padding:2px 7px; font-size:11px; font-weight:700; }
  .leading-badge { background:#DBEAFE; color:#1E40AF; border-radius:4px;
                   padding:2px 7px; font-size:11px; font-weight:700; }
  .total-badge { background:#F1F5F9; color:#334155; border-radius:4px;
                 padding:2px 7px; font-size:11px; font-weight:600; }
  .diff-up   { color:#16A34A; font-weight:700; }
  .diff-down { color:#DC2626; font-weight:700; }
  .diff-table thead th { background:#FFF7ED; }
  .change-row td { vertical-align:middle; }
  .footer { text-align:center; padding:20px 0 8px; color:#94A3B8; font-size:12px; }
  .footer a { color:#6366F1; text-decoration:none; }
  .section-title { font-size:13px; font-weight:700; color:#475569; text-transform:uppercase;
                   letter-spacing:.6px; margin:0 0 12px; }
</style>
"""


def _party_color(party_name: str) -> str:
    for abbr, color in PARTY_COLORS.items():
        if abbr in party_name:
            return color
    return "#94A3B8"


def _build_summary_cards(data: dict) -> str:
    cards = ""
    for state, parties in data.get("states", {}).items():
        filed = sum(p["total"] for p in parties)
        total = STATE_TOTALS.get(state, 1)
        pct = min(int(filed / total * 100), 100)
        cards += f"""
        <div class="summary-card">
          <div class="state-name">{state}</div>
          <div class="seats-filed">{filed}</div>
          <div class="seats-total">of {total} seats</div>
          <div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
        </div>"""
    return f'<div class="summary-grid">{cards}</div>'


def _build_state_table(state: str, parties: list[dict]) -> str:
    if not parties:
        return ""
    filed = sum(p["total"] for p in parties)
    total = STATE_TOTALS.get(state, "?")
    rows = ""
    for i, p in enumerate(parties, 1):
        rank_cls = f"rank-{i}" if i <= 3 else ""
        color = _party_color(p["party"])
        won_cell = f'<span class="won-badge">{p["won"]}</span>' if p["won"] else f'<span style="color:#CBD5E1">0</span>'
        leading_cell = f'<span class="leading-badge">{p["leading"]}</span>' if p["leading"] else f'<span style="color:#CBD5E1">0</span>'
        total_cell = f'<span class="total-badge">{p["total"]}</span>'
        rows += f"""
        <tr>
          <td>
            <span class="rank {rank_cls}">{i}</span>
            <span class="dot" style="background:{color}"></span>
            {p['party']}
          </td>
          <td class="num">{won_cell}</td>
          <td class="num">{leading_cell}</td>
          <td class="num">{total_cell}</td>
        </tr>"""
    return f"""
    <div class="state-card">
      <div class="state-header">
        <h2>{state}</h2>
        <span class="meta">{filed} / {total} results in</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Party</th>
            <th class="num">Won</th>
            <th class="num">Leading</th>
            <th class="num">Total</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def _build_full_results_html(data: dict) -> str:
    timestamp = data.get("timestamp", "")
    cards = _build_summary_cards(data)
    state_tables = "".join(
        _build_state_table(state, parties)
        for state, parties in data.get("states", {}).items()
        if parties
    )
    return f"""
    {cards}
    <p class="section-title">State-wise Breakdown</p>
    {state_tables}
    <p style="color:#94A3B8;font-size:12px;margin-top:4px">{timestamp}</p>
    """


def _build_diff_html(changes: list[dict]) -> str:
    if not changes:
        return ""

    rows = ""
    for c in changes:
        def diff_cell(old, new, kind):
            badge_cls = "won-badge" if kind == "won" else "leading-badge" if kind == "leading" else "total-badge"
            if old == new:
                return f'<td class="num"><span class="{badge_cls}">{new}</span></td>'
            arrow = "▲" if new > old else "▼"
            cls = "diff-up" if new > old else "diff-down"
            return (
                f'<td class="num"><span class="{badge_cls}">{new}</span> '
                f'<span class="{cls}" style="font-size:11px">{arrow}{abs(new-old)}</span></td>'
            )

        color = _party_color(c["party"])
        rows += f"""
        <tr class="change-row">
          <td style="font-size:12px;color:#64748B">{c['state']}</td>
          <td><span class="dot" style="background:{color}"></span>{c['party']}</td>
          {diff_cell(c['old'].get('won',0),    c['new'].get('won',0),    'won')}
          {diff_cell(c['old'].get('leading',0), c['new'].get('leading',0), 'leading')}
          {diff_cell(c['old'].get('total',0),  c['new'].get('total',0),  'total')}
        </tr>"""

    return f"""
    <p class="section-title">What Changed</p>
    <div class="state-card" style="margin-bottom:24px">
      <table class="diff-table">
        <thead>
          <tr>
            <th>State</th><th>Party</th>
            <th class="num">Won</th><th class="num">Leading</th><th class="num">Total</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <p class="section-title">Full Snapshot</p>
    """


def _send(subject: str, html_content: str) -> None:
    body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">{STYLES}</head>
<body>
<div class="wrapper">
  {html_content}
  <div class="footer">
    <a href="https://results.eci.gov.in/ResultAcGenMay2026/index.htm">View on ECI Website</a>
    &nbsp;·&nbsp; Election Commission of India
  </div>
</div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print(f"[notifier] Email sent to: {', '.join(RECIPIENTS)}")


def send_alert(new_data: dict, changes: list[dict]) -> None:
    timestamp = new_data.get("timestamp", "")
    subject = f"[Election Alert] Results updated — {timestamp}"
    header = f"""
    <div class="header">
      <h1>&#9889; Election Results Updated</h1>
      <p>Seat counts have changed since the last check</p>
      <span class="badge">&#128197; {timestamp}</span>
    </div>"""
    _send(subject, header + _build_diff_html(changes) + _build_full_results_html(new_data))


def send_digest(data: dict) -> None:
    timestamp = data.get("timestamp", "")
    subject = f"[Election Digest] Current results — {timestamp}"
    header = f"""
    <div class="header">
      <h1>&#128240; Election Results Digest</h1>
      <p>Periodic snapshot of all constituency results</p>
      <span class="badge">&#128197; {timestamp}</span>
    </div>"""
    _send(subject, header + _build_full_results_html(data))
