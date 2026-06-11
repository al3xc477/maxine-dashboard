#!/usr/bin/env python3
"""
Maxine Dashboard — Auto Deploy to GitHub Pages
Watches Maxine_Dashboard.html for changes and publishes automatically.
Run once; leave it running in the background while working with Claude.
"""

import os, sys, time, base64, json
import requests
import threading
import subprocess
from urllib import request, error

# ── Config ──────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # set via env var; never hardcode
REPO_NAME    = "maxine-dashboard"
HTML_FILE    = "Maxine_Dashboard.html"
POLL_SECS    = 4          # check for file changes every 4 seconds
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH  = os.path.join(SCRIPT_DIR, HTML_FILE)

# ── Firebase bug-watcher / auto-fix config ───────────────────────────────────
FIREBASE_BASE      = "https://maxine-sync-default-rtdb.europe-west1.firebasedatabase.app"
WORKING_DIR        = SCRIPT_DIR
FIREBASE_BUGS_URL  = f"{FIREBASE_BASE}/horizon-bugs.json"
FIREBASE_CONFIG_URL = f"{FIREBASE_BASE}/horizon-config/apiKey.json"
ANTHROPIC_API_URL  = "https://api.anthropic.com/v1/messages"
BUG_POLL_INTERVAL  = 30
FIX_TIMEOUT        = 300
REVIEW_QUEUE_PATH  = os.path.join(WORKING_DIR, "review_queue.md")

SIMPLE_KW = [
    "typo", "label", "text", "color", "colour", "spacing", "margin", "padding",
    "alignment", "wording", "rename", "tooltip", "placeholder", "icon",
]
COMPLEX_KW = [
    "crash", "data loss", "sync", "firebase", "migration", "bkt", "zpd", "dfs",
    "formula", "skill", "observation", "calculation", "engine", "race condition",
    "corruption", "infinite loop", "performance",
]
# ─────────────────────────────────────────────────────────────────────────────

def get_firebase_api_key():
    r = requests.get(FIREBASE_CONFIG_URL, timeout=20)
    r.raise_for_status()
    return r.json()

def classify_bug(bug):
    text = f"{bug.get('title', '')} {bug.get('description', '')}".lower()
    for kw in COMPLEX_KW:
        if kw in text:
            return "complex"
    for kw in SIMPLE_KW:
        if kw in text:
            return "simple"
    return "complex"

def build_fix_prompt(bug):
    title = bug.get("title", "")
    description = bug.get("description", "")
    steps = bug.get("steps", "")
    return f"""You are an autonomous bug-fixing agent for the Maxine Activity Companion dashboard.

A bug has been reported:

TITLE: {title}
DESCRIPTION: {description}
STEPS TO REPRODUCE: {steps}

The dashboard is a single self-contained file: Maxine_Dashboard.html in the current working directory.

Investigate the bug, then fix it directly in Maxine_Dashboard.html.

HARD CONSTRAINTS:
Do NOT touch: SKILLS, SKILLS_CUSTOM_SEED, observations, skillStatus, DFS formula, ZPD engine, BKT, migration functions, Firebase read/write logic, child profile data, PER_CHILD_KEYS, syncPull, loadChildWorkingSet.
Do NOT change any learning-model math, scoring weights, or mastery thresholds.
Do NOT alter the Firebase sync protocol, key names, or data shapes.
Do NOT refactor unrelated code, rename functions, or reformat untouched sections.
Do NOT add external dependencies, CDN scripts, or network calls.
Make the SMALLEST possible change that fixes the reported bug.
Preserve all existing behavior outside the scope of this bug.
If fixing the bug safely would require touching any of the protected areas above, do NOT make the change — instead explain why it must go to manual review.

After making the fix, briefly summarize what you changed and why."""

def update_bug_status(key, status):
    url = f"{FIREBASE_BASE}/horizon-bugs/{key}/status.json"
    r = requests.put(url, data=json.dumps(status), timeout=20)
    r.raise_for_status()
    return r.json()

def run_auto_fix(key, bug):
    prompt = build_fix_prompt(bug)
    tmp = os.path.join(WORKING_DIR, f".fix_prompt_{key}.txt")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(prompt)
    except Exception as e:
        print(f"  ⚠️  Could not write tmp prompt for {key}: {e}")

    update_bug_status(key, "fixing")
    try:
        result = subprocess.run(
            ["claude", "--dangerously-skip-permissions", "-p", prompt],
            cwd=WORKING_DIR,
            timeout=FIX_TIMEOUT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            update_bug_status(key, "fixed")
            print(f"  ✅ Auto-fixed bug {key}")
        else:
            update_bug_status(key, "failed")
            print(f"  ❌ Auto-fix failed for {key}: {result.stderr.strip()[:300]}")
    except subprocess.TimeoutExpired:
        update_bug_status(key, "failed")
        print(f"  ❌ Auto-fix timed out for {key}")
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass

def append_review_queue(key, bug):
    title = bug.get("title", "")
    description = bug.get("description", "")
    steps = bug.get("steps", "")
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"\n## [{ts}] Bug {key}\n"
        f"- **Title:** {title}\n"
        f"- **Description:** {description}\n"
        f"- **Steps:** {steps}\n"
    )
    with open(REVIEW_QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(entry)
    update_bug_status(key, "review")
    print(f"  📋 Queued bug {key} for manual review")

def process_new_bugs():
    r = requests.get(FIREBASE_BUGS_URL, timeout=20)
    r.raise_for_status()
    bugs = r.json()
    if not bugs:
        return
    for key, bug in bugs.items():
        if not isinstance(bug, dict):
            continue
        if bug.get("status", "new") != "new":
            continue
        kind = classify_bug(bug)
        if kind == "simple":
            run_auto_fix(key, bug)
        else:
            append_review_queue(key, bug)

def bug_watcher_loop():
    print(f"  🐞 Bug watcher started (poll every {BUG_POLL_INTERVAL}s)")
    while True:
        try:
            process_new_bugs()
        except Exception as e:
            print(f"\n  ⚠️  Bug watcher error: {e}")
        time.sleep(BUG_POLL_INTERVAL)

def api(method, endpoint, data=None):
    url  = f"https://api.github.com{endpoint}"
    body = json.dumps(data).encode() if data else None
    req  = request.Request(url, data=body, method=method, headers={
        "Authorization":        f"Bearer {GITHUB_TOKEN}",
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type":         "application/json",
        "User-Agent":           "maxine-deploy",
    })
    try:
        with request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body}")

def setup(owner):
    # Create repo if it doesn't exist
    try:
        api("POST", "/user/repos", {
            "name": REPO_NAME, "private": False, "auto_init": True,
            "description": "Maxine Activity Dashboard"
        })
        print(f"  ✅ Created repo {owner}/{REPO_NAME}")
        time.sleep(3)
    except RuntimeError as e:
        if "already exists" in str(e) or "422" in str(e):
            print(f"  ✓  Repo {owner}/{REPO_NAME} already exists")
        else:
            raise

    # Enable GitHub Pages
    try:
        api("POST", f"/repos/{owner}/{REPO_NAME}/pages", {
            "source": {"branch": "main", "path": "/"}
        })
        print(f"  ✅ GitHub Pages enabled")
    except RuntimeError as e:
        if "409" in str(e) or "already" in str(e).lower():
            print(f"  ✓  GitHub Pages already active")
        else:
            print(f"  ⚠  Pages: {e}")

def get_sha(owner):
    try:
        r = api("GET", f"/repos/{owner}/{REPO_NAME}/contents/{HTML_FILE}")
        return r.get("sha")
    except:
        return None

def deploy(owner, sha):
    with open(HTML_PATH, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    data = {"message": "Update dashboard", "content": content, "branch": "main"}
    if sha:
        data["sha"] = sha
    result = api("PUT", f"/repos/{owner}/{REPO_NAME}/contents/{HTML_FILE}", data)
    return result.get("content", {}).get("sha", sha)

# ── Main ─────────────────────────────────────────────────────────────────────
print("\n🚀 Maxine Dashboard — Auto Deploy")
print("=" * 44)

try:
    owner = api("GET", "/user")["login"]
    print(f"  GitHub user : {owner}")
except RuntimeError as e:
    print(f"  ❌ Token error: {e}")
    sys.exit(1)

setup(owner)

url = f"https://{owner}.github.io/{REPO_NAME}/{HTML_FILE}"
print(f"\n  📎 URL  →  {url}")
print(f"  📁 File →  {HTML_PATH}")
print(f"\n  Watching for changes every {POLL_SECS}s…")
print("  (keep this window open while working with Claude)\n")

# Write URL to a small text file so you can find it easily
url_file = os.path.join(SCRIPT_DIR, "dashboard_url.txt")
with open(url_file, "w") as f:
    f.write(url + "\n")

last_mtime = 0
current_sha = get_sha(owner)

# Deploy immediately on first run
try:
    if not os.path.exists(HTML_PATH):
        print(f"  ❌ File not found: {HTML_PATH}")
        sys.exit(1)
    mtime = os.path.getmtime(HTML_PATH)
    print(f"  🔄 Initial deploy…")
    current_sha = deploy(owner, current_sha)
    last_mtime  = mtime
    print(f"  ✅ Live at {url}\n")
except RuntimeError as e:
    print(f"  ❌ Deploy failed: {e}\n")

# Start the Firebase bug-watcher / auto-fix loop in a background daemon thread.
threading.Thread(target=bug_watcher_loop, daemon=True).start()

# Watch loop
while True:
    try:
        mtime = os.path.getmtime(HTML_PATH)
        if mtime != last_mtime:
            ts = time.strftime("%H:%M:%S")
            print(f"  [{ts}] Change detected — deploying…", end=" ", flush=True)
            current_sha = deploy(owner, current_sha)
            last_mtime  = mtime
            print("✅ done")
    except RuntimeError as e:
        print(f"\n  ⚠️  Deploy error: {e}")
    except KeyboardInterrupt:
        print("\n\n  Stopped. Run again when working with Claude.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n  ⚠️  {e}")
    time.sleep(POLL_SECS)
