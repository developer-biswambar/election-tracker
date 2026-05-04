from curl_cffi.requests import Session
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://results.eci.gov.in/ResultAcGenMay2026"

STATES = {
    "Assam": "S03",
    "Kerala": "S11",
    "Puducherry": "U07",
    "Tamil Nadu": "S22",
    "West Bengal": "S25",
}

# impersonate= makes curl_cffi mimic Chrome's TLS fingerprint, which defeats
# fingerprint-based blocking that ignores plain User-Agent spoofing
_session = Session(impersonate="chrome124")


def _warm_up_session() -> None:
    try:
        _session.get(f"{BASE_URL}/index.htm", timeout=30)
    except Exception:
        pass


def fetch_state_results(state_code: str) -> list[dict]:
    url = f"{BASE_URL}/partywiseresult-{state_code}.htm"
    resp = _session.get(
        url,
        headers={"Referer": f"{BASE_URL}/index.htm"},
        timeout=30,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    table = None
    for t in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in t.find_all("th")]
        if "party" in headers and "won" in headers:
            table = t
            break

    if not table:
        return []

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) >= 4:
            rows.append({
                "party": cells[0],
                "won": int(cells[1]) if cells[1].isdigit() else 0,
                "leading": int(cells[2]) if cells[2].isdigit() else 0,
                "total": int(cells[3]) if cells[3].isdigit() else 0,
            })

    return rows


def fetch_timestamp() -> str:
    url = f"{BASE_URL}/index.htm"
    try:
        resp = _session.get(url, timeout=30)
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup.find_all(string=True):
            if "Last Updated" in tag:
                return tag.strip()
    except Exception:
        pass
    return datetime.now().strftime("Fetched at %I:%M %p on %d/%m/%Y")


def fetch_all_results() -> dict:
    _warm_up_session()
    results = {}
    for state_name, state_code in STATES.items():
        try:
            results[state_name] = fetch_state_results(state_code)
        except Exception as e:
            print(f"[scraper] Failed to fetch {state_name}: {e}")
            results[state_name] = []

    return {
        "timestamp": fetch_timestamp(),
        "states": results,
    }
