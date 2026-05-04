import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

# Comma-separated list of recipient emails
RECIPIENTS = [e.strip() for e in os.environ.get("RECIPIENT_EMAILS", GMAIL_USER).split(",") if e.strip()]


def _build_diff_html(changes: list[dict]) -> str:
    if not changes:
        return ""

    rows = ""
    for c in changes:
        old_won = c["old"].get("won", 0)
        new_won = c["new"].get("won", 0)
        old_leading = c["old"].get("leading", 0)
        new_leading = c["new"].get("leading", 0)
        old_total = c["old"].get("total", 0)
        new_total = c["new"].get("total", 0)

        def diff_cell(old, new):
            if old == new:
                return f"<td style='padding:6px 12px;text-align:center'>{new}</td>"
            arrow = "▲" if new > old else "▼"
            color = "#16a34a" if new > old else "#dc2626"
            return (
                f"<td style='padding:6px 12px;text-align:center;color:{color};font-weight:bold'>"
                f"{new} {arrow}</td>"
            )

        rows += (
            f"<tr>"
            f"<td style='padding:6px 12px'>{c['state']}</td>"
            f"<td style='padding:6px 12px'>{c['party']}</td>"
            + diff_cell(old_won, new_won)
            + diff_cell(old_leading, new_leading)
            + diff_cell(old_total, new_total)
            + f"</tr>"
        )

    return f"""
    <h2 style="color:#1d4ed8">What Changed</h2>
    <table style="border-collapse:collapse;font-family:sans-serif;font-size:14px;margin-bottom:24px">
      <thead>
        <tr style="background:#f1f5f9">
          <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #cbd5e1">State</th>
          <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #cbd5e1">Party</th>
          <th style="padding:8px 12px;text-align:center;border-bottom:2px solid #cbd5e1">Won</th>
          <th style="padding:8px 12px;text-align:center;border-bottom:2px solid #cbd5e1">Leading</th>
          <th style="padding:8px 12px;text-align:center;border-bottom:2px solid #cbd5e1">Total</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """


def _build_full_results_html(data: dict) -> str:
    html = f'<h2 style="color:#1d4ed8">Full Results Snapshot</h2>'
    html += f'<p style="color:#64748b;font-size:13px">{data.get("timestamp", "")}</p>'

    for state, parties in data.get("states", {}).items():
        if not parties:
            continue
        rows = "".join(
            f"<tr>"
            f"<td style='padding:5px 10px'>{p['party']}</td>"
            f"<td style='padding:5px 10px;text-align:center'>{p['won']}</td>"
            f"<td style='padding:5px 10px;text-align:center'>{p['leading']}</td>"
            f"<td style='padding:5px 10px;text-align:center'>{p['total']}</td>"
            f"</tr>"
            for p in parties
        )
        html += f"""
        <h3 style="margin-top:20px;color:#334155">{state}</h3>
        <table style="border-collapse:collapse;font-family:sans-serif;font-size:13px;margin-bottom:8px">
          <thead>
            <tr style="background:#f8fafc">
              <th style="padding:6px 10px;text-align:left;border-bottom:1px solid #e2e8f0">Party</th>
              <th style="padding:6px 10px;text-align:center;border-bottom:1px solid #e2e8f0">Won</th>
              <th style="padding:6px 10px;text-align:center;border-bottom:1px solid #e2e8f0">Leading</th>
              <th style="padding:6px 10px;text-align:center;border-bottom:1px solid #e2e8f0">Total</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        """

    return html


def send_alert(new_data: dict, changes: list[dict]) -> None:
    subject = f"[Election Alert] Results updated — {new_data.get('timestamp', '')}"

    body = f"""
    <html><body style="font-family:sans-serif;max-width:800px;margin:auto;padding:20px">
      <h1 style="color:#0f172a">ECI Election Results Update</h1>
      <p>The election results page has been updated. Below are the changes and the full current snapshot.</p>
      {_build_diff_html(changes)}
      <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0">
      {_build_full_results_html(new_data)}
      <p style="color:#94a3b8;font-size:12px;margin-top:32px">
        Source: <a href="https://results.eci.gov.in/ResultAcGenMay2026/index.htm">ECI Results Page</a>
      </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print(f"[notifier] Email sent to: {', '.join(RECIPIENTS)}")
