"""Read main cookies from Default/Network/Cookies SQLite."""
import sqlite3, os

PROFILES_ROOT = r"D:\K\HIDEMIUM_4\ProfilesData\2236226b-3617-47ec-a77e-5fa031f16782"

# Check how many profiles have Network/Cookies
count = 0
for pid in sorted(os.listdir(PROFILES_ROOT)):
    p = os.path.join(PROFILES_ROOT, pid, "Default", "Network", "Cookies")
    if os.path.exists(p):
        count += 1

print(f"Profiles with Default/Network/Cookies: {count}/{len(os.listdir(PROFILES_ROOT))}")

# Read first profile with cookies
for pid in sorted(os.listdir(PROFILES_ROOT)):
    p = os.path.join(PROFILES_ROOT, pid, "Default", "Network", "Cookies")
    if not os.path.exists(p):
        continue
    
    print(f"\nProfile: {pid[:12]}... ({os.path.getsize(p):,} bytes)")
    
    conn = sqlite3.connect(p)
    cursor = conn.cursor()
    
    # Schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    cursor.execute("PRAGMA table_info(cookies)")
    cols = [r[1] for r in cursor.fetchall()]
    print(f"Columns: {cols}")
    
    cursor.execute("SELECT COUNT(*) FROM cookies")
    total = cursor.fetchone()[0]
    print(f"Total cookies: {total}")
    
    # Check encryption
    cursor.execute("SELECT host_key, name, value, encrypted_value, path FROM cookies LIMIT 5")
    for r in cursor.fetchall():
        host, name, val, enc_val, path = r
        enc_info = ""
        if enc_val:
            if isinstance(enc_val, bytes) and len(enc_val) > 3:
                prefix = enc_val[:3]
                if prefix == b'v10' or prefix == b'v20':
                    enc_info = f"AES-GCM encrypted ({len(enc_val)} bytes)"
                elif prefix[:1] == b'\x01':
                    enc_info = f"DPAPI encrypted ({len(enc_val)} bytes)"
                else:
                    enc_info = f"plaintext ({len(enc_val)} bytes)"
            else:
                enc_info = f"short ({len(enc_val) if enc_val else 0} bytes)"
        print(f"  {host} | {name} | value='{val[:20] if val else ''}' | enc={enc_info}")
    
    # Show unique domains
    cursor.execute("SELECT DISTINCT host_key FROM cookies ORDER BY host_key")
    domains = [r[0] for r in cursor.fetchall()]
    print(f"\nUnique domains ({len(domains)}):")
    for d in domains[:20]:
        cursor.execute("SELECT COUNT(*) FROM cookies WHERE host_key=?", (d,))
        cnt = cursor.fetchone()[0]
        print(f"  {d} ({cnt} cookies)")
    if len(domains) > 20:
        print(f"  ... and {len(domains)-20} more")
    
    conn.close()
    break
