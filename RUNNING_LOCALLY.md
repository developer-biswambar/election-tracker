# Running Locally on Mac (without Docker)

## Prerequisites

- Python 3.12+ — check with `python3 --version`
- A Gmail account with 2-Step Verification enabled

---

## 1. Clone the repo and enter the directory

```bash
git clone <your-repo-url>
cd election-tracker
```

---

## 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Your terminal prompt will change to show `(venv)` when it's active.

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Get a Gmail App Password

Regular Gmail passwords won't work — you need an App Password.

1. Go to https://myaccount.google.com/apppasswords
2. Sign in with your Google account
3. Under "App name", type `Election Tracker` and click **Create**
4. Copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)

> **Note:** If you don't see the App Passwords option, make sure 2-Step Verification is turned on at https://myaccount.google.com/security

---

## 5. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```
GMAIL_USER=biswambarp43@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop
RECIPIENT_EMAILS=biswambarp43@gmail.com
CHECK_INTERVAL_SECONDS=300
```

To notify multiple people, add them comma-separated:

```
RECIPIENT_EMAILS=biswambarp43@gmail.com,friend@example.com
```

---

## 6. Run the monitor

```bash
source venv/bin/activate   # skip if already active
export $(cat .env | xargs)
python monitor.py
```

You should see:

```
[monitor] Starting. Checking every 300s.
[monitor] Fetching results at 10:23:01...
[monitor] No snapshot found — saving baseline, no email sent.
```

The first run saves a baseline — no email is sent. From the second run onward, any change in party seat counts triggers an email.

---

## 7. Keep it running in the background (optional)

Use `nohup` so the process survives closing your terminal:

```bash
nohup python monitor.py > election-monitor.log 2>&1 &
echo $! > monitor.pid
```

To check logs:

```bash
tail -f election-monitor.log
```

To stop it:

```bash
kill $(cat monitor.pid)
```

---

## 8. Deactivate the virtual environment when done

```bash
deactivate
```
