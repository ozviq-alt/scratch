print("DEBUG: 1. Script started")

from curl_cffi import requests
print("DEBUG: 2. Imported curl_cffi")

import time
import json
import os

STUDIO_ID = 51744069
STATE_FILE = "tracked_projects.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

print("DEBUG: 3. Constants loaded")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": f"https://scratch.mit.edu/studios/{STUDIO_ID}/"
}

def safe_request(url, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10, **kwargs)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Network request failed after {max_retries} attempts: {e}")
                return None
            time.sleep(3)
    return None

def send_webhook(message):
    if not WEBHOOK_URL:
        return
    payload = {"content": message} # Compatible with Discord webhooks
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send webhook notification: {e}")

def get_all_studio_projects(studio_id):
    all_projects = []
    offset = 0
    limit = 40

    while True:
        url = f"https://api.scratch.mit.edu/studios/{studio_id}/projects/?limit={limit}&offset={offset}"
        response = safe_request(url, impersonate="chrome")
        if not response or response.status_code != 200:
            break
        batch = response.json()
        if not batch:
            break
        all_projects.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.15)

    return all_projects

def get_project_details(project_id):
    url = f"https://api.scratch.mit.edu/projects/{project_id}"
    response = safe_request(url, headers=HEADERS)
    if response and response.status_code == 200:
        return response.json()
    return None

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("State file was corrupted or invalid. Resetting to empty state.")
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def main():
    print("DEBUG: 4. Entered main function")
    tracked_projects = load_state()
    print("DEBUG: 5. State loaded")
    
    current_projects = get_all_studio_projects(STUDIO_ID)
    print(f"DEBUG: 6. Fetched projects count: {len(current_projects) if current_projects else 'None'}")
    
    if not current_projects:
        print("Failed to fetch studio projects.")
        return

    is_first_run = len(tracked_projects) == 0
    print(f"Checking {len(current_projects)} projects for Studio {STUDIO_ID}...")

    changes_detected = False

    for proj in current_projects:
        p_id = str(proj['id'])
        p_title = proj['title']
        details = get_project_details(p_id)
        
        if details:
            current_modified = details.get('history', {}).get('modified')
            
            if p_id in tracked_projects:
                if tracked_projects[p_id] != current_modified:
                    msg = f"🔔 **ALERT:** '{p_title}' (ID: {p_id}) was updated at {current_modified}!"
                    print(msg)
                    send_webhook(msg)
                    tracked_projects[p_id] = current_modified
                    changes_detected = True
            else:
                if not is_first_run:
                    msg = f"✨ **NEW ADDITION:** '{p_title}' was added to the studio."
                    print(msg)
                    send_webhook(msg)
                    changes_detected = True
                tracked_projects[p_id] = current_modified
                
        time.sleep(0.15)

    save_state(tracked_projects)

    # Send a status message if no updates occurred (skipping the very first run)
    if not changes_detected and not is_first_run:
        send_webhook("🔍 **Status Check:** Scanned studio. No new updates or additions found.")

    print("Check completed and state saved.")
if __name__ == "__main__":
    try:
        print("DEBUG: Calling main()")
        main()
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()
