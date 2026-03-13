import os
import sqlite3
import json
import shutil
from pathlib import Path

# Cau hinh duong dan
HIMENIUM_DATA_PATH = r"D:\K\HIDEMIUM_4\ProfilesData\2236226b-3617-47ec-a77e-5fa031f16782"
ZUMI_PROFILES_PATH = r"D:\K\Zumi-Antidetect\profiles"

def get_himenium_profiles():
    """Lay danh sach cac thu muc profile tu Himenium"""
    if not os.path.exists(HIMENIUM_DATA_PATH):
        print(f"Loi: Khong tim thay duong dan {HIMENIUM_DATA_PATH}")
        return []
    return [d for d in os.listdir(HIMENIUM_DATA_PATH) if os.path.isdir(os.path.join(HIMENIUM_DATA_PATH, d))]

def migrate_cookies(profile_id):
    """
    Hanh dong di cu Cookies. 
    """
    source_profile = os.path.join(HIMENIUM_DATA_PATH, profile_id)
    target_profile = os.path.join(ZUMI_PROFILES_PATH, profile_id)
    
    if not os.path.exists(target_profile):
        os.makedirs(target_profile)
    
    # Tim file Cookies (Du doan vi tri trong nhan Chromium cua Himenium)
    possible_paths = [
        os.path.join(source_profile, "Default", "Network", "Cookies"),
        os.path.join(source_profile, "Network", "Cookies"),
        os.path.join(source_profile, "Cookies"),
        os.path.join(source_profile, "Default", "Cookies")
    ]
    
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            shutil.copy2(path, os.path.join(target_profile, "himenium_cookies.db"))
            print(f"OK: Found Cookies for {profile_id}")
            found = True
            break
            
    if not found:
        print(f"SKIP: No cookies found for {profile_id}")

def main():
    profiles = get_himenium_profiles()
    print(f"Starting migration for {len(profiles)} profiles...")
    
    for p_id in profiles:
        migrate_cookies(p_id)
    
    print("\nMigration preparation completed!")

if __name__ == "__main__":
    main()
