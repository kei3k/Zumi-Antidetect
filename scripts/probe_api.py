"""Fetch ALL profiles from Hidemium API and compare UUIDs with local folders."""
import urllib.request
import json
import os

API = "http://127.0.0.1:2222"
PROFILES_ROOT = r"D:\K\HIDEMIUM_4\ProfilesData\2236226b-3617-47ec-a77e-5fa031f16782"

def post(endpoint, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(f"{API}{endpoint}", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req, timeout=10)
    return json.loads(r.read().decode())

# Fetch all cloud profiles (paginate)
all_profiles = []
page = 1
while True:
    result = post("/v1/browser/list", {"is_local": False, "page": page, "limit": 50})
    data = result.get("data", {})
    profiles = data.get("content", data.get("data", []))
    if not profiles:
        break
    all_profiles.extend(profiles)
    if len(profiles) < 50:
        break
    page += 1

print(f"Total from API: {len(all_profiles)}")

# Local folders
local_folders = set(os.listdir(PROFILES_ROOT))
print(f"Total local folders: {len(local_folders)}")

# Match
api_uuids = {p["uuid"] for p in all_profiles}
matched = api_uuids & local_folders
unmatched_api = api_uuids - local_folders
unmatched_local = local_folders - api_uuids

print(f"\nMatched: {len(matched)}")
print(f"API only (not in local): {len(unmatched_api)}")
print(f"Local only (not in API): {len(unmatched_local)}")

if matched:
    print("\nSample matched profiles:")
    for uuid in list(matched)[:5]:
        p = next((x for x in all_profiles if x["uuid"] == uuid), None)
        if p:
            print(f"  {uuid[:8]}... -> name={p.get('name')}, proxy={p.get('proxy')}, note={p.get('note')}, last_open={p.get('last_open')}")

if unmatched_local:
    print(f"\nSample local-only UUIDs (first 5):")
    for u in list(unmatched_local)[:5]:
        print(f"  {u}")

if unmatched_api:
    print(f"\nSample API-only UUIDs (first 5):")
    for u in list(unmatched_api)[:5]:
        p = next((x for x in all_profiles if x["uuid"] == u), None)
        if p:
            print(f"  {u[:8]}... -> name={p.get('name')}")
