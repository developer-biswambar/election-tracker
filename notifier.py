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
  body { margin:0; padding:0; background:#F1F5F9; font-family:Arial,sans-serif; color:#1E293B; }
  .wrapper { max-width:680px; margin:0 auto; padding:16px; }

  .header { background:#1A237E; border-radius:10px; padding:24px;
            margin-bottom:16px; text-align:center; }
  .header h1  { color:#fff; margin:0 0 4px; font-size:19px; }
  .header .sub { color:rgba(255,255,255,.7); font-size:12px; margin:0; }
  .header .ts  { display:inline-block; margin-top:10px; background:rgba(255,255,255,.15);
                 color:#fff; border-radius:20px; padding:3px 14px; font-size:11px; }

  .section-label { font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase;
                   letter-spacing:.8px; margin:0 0 8px; }

  /* state card rendered as an HTML table cell — styles apply inside each cell */
  .sc { background:#fff; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.08);
        overflow:hidden; vertical-align:top; }
  .sh { padding:10px 12px 8px; border-bottom:1px solid #F1F5F9; }
  .sh h2 { margin:0 0 2px; font-size:13px; font-weight:700; }
  .sh .sm { font-size:10px; color:#94A3B8; }
  .trk { background:#E2E8F0; border-radius:3px; height:3px; margin-top:6px; }
  .trf { height:3px; border-radius:3px; background:#6366F1; }

  /* column header row inside each card */
  .ch { background:#F8FAFC; border-bottom:1px solid #E2E8F0; }
  .ch td { padding:4px 8px; font-size:9px; font-weight:700; text-transform:uppercase;
           letter-spacing:.5px; color:#94A3B8; }
  .ch td.cw { color:#166534; text-align:center; }
  .ch td.cl { color:#1E40AF; text-align:center; }

  /* party rows */
  .pr td { padding:5px 8px; font-size:11px; border-bottom:1px solid #F8FAFC;
           vertical-align:middle; }
  .pr:last-child td { border-bottom:none; }
  .rk { color:#CBD5E1; font-size:10px; font-weight:700; text-align:center; width:14px; }
  .pp { border-radius:3px; color:#fff; font-size:9px; font-weight:700;
        padding:2px 5px; white-space:nowrap; text-align:center; }
  .bar-td { width:35%; }
  .bb { background:#F1F5F9; border-radius:2px; height:7px; overflow:hidden; }
  .bf { height:7px; border-radius:2px; }
  .wn { background:#DCFCE7; color:#166534; border-radius:3px; padding:1px 5px;
        font-size:10px; font-weight:700; text-align:center; display:block; }
  .ld { background:#DBEAFE; color:#1E40AF; border-radius:3px; padding:1px 5px;
        font-size:10px; font-weight:700; text-align:center; display:block; }

  /* change block */
  .change-block { background:#fff; border-radius:8px; margin-bottom:12px;
                  box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }
  .change-head  { padding:10px 14px; background:#FFF7ED; border-bottom:1px solid #FED7AA;
                  font-size:12px; font-weight:700; color:#92400E; }
  .cr td { padding:7px 14px; font-size:12px; border-bottom:1px solid #F8FAFC;
           vertical-align:middle; }
  .cr:last-child td { border-bottom:none; }
  .up { color:#16A34A; font-weight:700; }
  .dn { color:#DC2626; font-weight:700; }
  .nc { color:#CBD5E1; }

  .divider { border:none; border-top:1px solid #E2E8F0; margin:14px 0; }
  .footer { text-align:center; padding:12px 0 4px; font-size:11px; color:#94A3B8; }
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


def _state_card(state: str, parties: list[dict]) -> str:
    """Returns the inner HTML for one state card (to be placed in a <td class='sc'>)."""
    if not parties:
        return ""
    total_seats = STATE_TOTALS.get(state, 1)
    counted = sum(p["total"] for p in parties)
    pct = min(int(counted / total_seats * 100), 100)
    max_seats = max((p["total"] for p in parties), default=1)

    rows = ""
    for i, p in enumerate(parties, 1):
        color = _party_color(p["party"])
        bar_w = int(p["total"] / max_seats * 100)
        rows += f"""
        <tr class="pr">
          <td class="rk">{i}</td>
          <td><span class="pp" style="background:{color}">{_abbr(p['party'])}</span></td>
          <td class="bar-td"><div class="bb"><div class="bf" style="width:{bar_w}%;background:{color}66"></div></div></td>
          <td><span class="wn">{p['won']}</span></td>
          <td><span class="ld">{p['leading']}</span></td>
        </tr>"""

    return f"""
    <div class="sh">
      <h2>{state}</h2>
      <div class="sm">{counted} / {total_seats} seats &nbsp;({pct}%)</div>
      <div class="trk"><div class="trf" style="width:{pct}%"></div></div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
      <tr class="ch">
        <td colspan="3"></td>
        <td class="cw">Won</td>
        <td class="cl">Leading</td>
      </tr>
      {rows}
    </table>"""


def _build_results_html(data: dict) -> str:
    states = [(s, p) for s, p in data.get("states", {}).items() if p]
    # Pair states into rows of 2
    grid_rows = ""
    for i in range(0, len(states), 2):
        left_state, left_parties = states[i]
        left_html = _state_card(left_state, left_parties)

        if i + 1 < len(states):
            right_state, right_parties = states[i + 1]
            right_html = _state_card(right_state, right_parties)
            right_cell = f'<td width="8"></td><td class="sc" width="49%">{right_html}</td>'
        else:
            right_cell = '<td width="8"></td><td width="49%"></td>'

        grid_rows += f"""
        <tr>
          <td class="sc" width="49%">{left_html}</td>
          {right_cell}
        </tr>
        <tr><td colspan="3" height="10"></td></tr>"""

    ts = data.get("timestamp", "")
    return f"""
    <p class="section-label">State-wise Results</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
      {grid_rows}
    </table>
    <p style="font-size:10px;color:#CBD5E1;margin-top:4px">{ts}</p>
    """


def _build_diff_html(changes: list[dict]) -> str:
    if not changes:
        return ""

    rows = ""
    for c in changes:
        def cell(old, new, label):
            if old == new:
                return f'<span class="nc">{label} {new}</span>'
            arrow, cls = ("▲", "up") if new > old else ("▼", "dn")
            return f'<span class="{cls}">{label} {new} {arrow}{abs(new - old)}</span>'

        color = _party_color(c["party"])
        rows += f"""
        <tr class="cr">
          <td style="color:#94A3B8;font-size:11px;white-space:nowrap">{c['state']}</td>
          <td><span class="pp" style="background:{color}">{_abbr(c['party'])}</span></td>
          <td style="font-size:12px;font-weight:600">{c['party'].split(' - ')[0] if ' - ' in c['party'] else c['party']}</td>
          <td style="white-space:nowrap">{cell(c['old'].get('won',0), c['new'].get('won',0), 'W')}</td>
          <td style="white-space:nowrap">{cell(c['old'].get('leading',0), c['new'].get('leading',0), 'L')}</td>
        </tr>"""

    return f"""
    <div class="change-block">
      <div class="change-head">&#128308; What changed</div>
      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
        {rows}
      </table>
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
