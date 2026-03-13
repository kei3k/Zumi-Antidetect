import sqlite3

conn = sqlite3.connect(r"D:\K\CHAPALL\Chapall.dist\chapall.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM profiles LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(dict(r))
conn.close()

# Also check Hidemium's AppData
import os, json, glob

# Hidemium stores config in AppData
appdata = os.environ.get("LOCALAPPDATA", "")
hidemium_paths = [
    os.path.join(appdata, "Hidemium"),
    os.path.join(appdata, "hidemium"),
    os.path.join(os.environ.get("APPDATA", ""), "Hidemium"),
    os.path.join(os.environ.get("APPDATA", ""), "hidemium"),
]
print("\n--- Searching Hidemium AppData ---")
for p in hidemium_paths:
    if os.path.exists(p):
        print(f"FOUND: {p}")
        for item in os.listdir(p):
            full = os.path.join(p, item)
            sz = os.path.getsize(full) if os.path.isfile(full) else "DIR"
            print(f"  {item} ({sz})")
    else:
        print(f"NOT FOUND: {p}")

# Also check if Hidemium runs local API
import socket
print("\n--- Checking Hidemium local ports ---")
for port in [50325, 36422, 8585, 9222, 18585, 19222, 50200]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex(("127.0.0.1", port))
        if result == 0:
            print(f"  PORT {port}: OPEN")
        s.close()
    except:
        pass
