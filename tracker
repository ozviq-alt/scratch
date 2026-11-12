from curl_cffi import requests
import time
import json
import os

STUDIO_ID = 51744069
STATE_FILE = "tracked_projects.json"

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
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def main():
    tracked_projects = load_state()
    current_projects = get_all_studio_projects(STUDIO_ID)
    
    if not current_projects:
        print("Failed to fetch studio projects.")
        return

    is_first_run = len(tracked_projects) == 0
    print(f"Checking {len(current_projects)} projects for Studio {STUDIO_ID}...")

    for proj in current_projects:
        p_id = str(proj['id'])
        p_title = proj['title']
        details = get_project_details(p_id)
        
        if details:
            current_modified = details.get('history', {}).get('modified')
            
            if p_id in tracked_projects:
                if tracked_projects[p_id] != current_modified:
                    print(f"ALERT: '{p_title}' (ID: {p_id}) was updated at {current_modified}!")
                    tracked_projects[p_id] = current_modified
            else:
                if not is_first_run:
                    print(f"NEW ADDITION: '{p_title}' was added to the studio.")
                tracked_projects[p_id] = current_modified
                
        time.sleep(0.15)

    save_state(tracked_projects)
    print("Check completed and state saved.")

if __name__ == "__main__":
    main()
