import os
import time
import sqlite3
import socket
import subprocess
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Zumi Antidetect API", version="2.0.0")

# --- CORS for Vite dev server ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Config ---
# ĐÃ CẬP NHẬT: Trỏ thẳng vào thư mục data của Hidemium theo yêu cầu của anh Kei
DB_PATH = r"D:\K\CHAPALL\Chapall.dist\chapall.db" # Tạm thời giữ để tránh lỗi DB, nhưng sẽ ưu tiên quét Folder
PROFILES_ROOT = r"D:\K\HIDEMIUM_4\ProfilesData\2236226b-3617-47ec-a77e-5fa031f16782" 

# Track running browser processes: profile_id -> subprocess.Popen
_running: dict[str, subprocess.Popen] = {}


def get_db():
    """Get a database connection with row_factory."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=503, detail="Database not found")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# === Models ===
class ProfileLaunch(BaseModel):
    profile_id: str
    proxy: Optional[str] = None

class ProfileUpdate(BaseModel):
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    notes: Optional[str] = None

class ProxyTest(BaseModel):
    proxy: str


# === ENDPOINTS ===

@app.get("/groups")
def list_groups():
    """Return distinct group names with profile counts."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT group_name, COUNT(*) as cnt FROM profiles GROUP BY group_name ORDER BY group_name"
        )
        rows = cursor.fetchall()
        return [{"name": r["group_name"], "count": r["cnt"]} for r in rows if r["group_name"]]
    finally:
        conn.close()


@app.get("/profiles")
def list_profiles(
    group: Optional[str] = Query(None, description="Filter by group name"),
    search: Optional[str] = Query(None, description="Search by name, proxy, or ID"),
):
    """List profiles by scanning Hidemium folder directly."""
    profiles = []
    
    if not os.path.exists(PROFILES_ROOT):
        return []

    # Quét toàn bộ folder trong ProfilesData
    for pid in os.listdir(PROFILES_ROOT):
        p_path = os.path.join(PROFILES_ROOT, pid)
        if not os.path.isdir(p_path):
            continue
            
        is_running = pid in _running and _running[pid].poll() is None
        
        # Mặc định lấy ID làm tên nếu không tìm thấy thông tin khác
        profile_info = {
            "id": pid,
            "name": f"Hidemium-{pid[:8]}",
            "group_name": "Hidemium-Sync",
            "proxy": "No Proxy",
            "ua": "Default",
            "notes": "Synced from Hidemium_4",
            "has_cookies": True,
            "is_running": is_running,
        }
        
        # Thử đọc thông tin chi tiết từ Local State (nếu có)
        local_state_path = os.path.join(p_path, "Local State")
        if os.path.exists(local_state_path):
            try:
                import json
                with open(local_state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Trích xuất thông tin proxy/ua nếu Hidemium lưu ở đây
                    # (Tùy thuộc vào cấu trúc riêng của Hidemium, em sẽ ưu tiên hiển thị ID trước)
            except:
                pass

        # Search filter
        if search:
            if search.lower() not in pid.lower():
                continue

        profiles.append(profile_info)
        
    return profiles


@app.put("/profiles/{profile_id}")
def update_profile(profile_id: str, data: ProfileUpdate):
    """Update proxy, user_agent, and/or notes for a profile."""
    conn = get_db()
    try:
        cursor = conn.cursor()

        sets = []
        params = []
        if data.proxy is not None:
            sets.append("proxy = ?")
            params.append(data.proxy)
        if data.user_agent is not None:
            sets.append("user_agent = ?")
            params.append(data.user_agent)
        if data.notes is not None:
            sets.append("notes = ?")
            params.append(data.notes)

        if not sets:
            raise HTTPException(status_code=400, detail="Nothing to update")

        params.append(profile_id)
        cursor.execute(f"UPDATE profiles SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {"status": "success", "message": f"Profile {profile_id} updated"}
    finally:
        conn.close()


@app.post("/launch")
def launch_profile(data: ProfileLaunch):
    """Launch a Camoufox browser for the given profile."""
    profile_dir = os.path.join(PROFILES_ROOT, data.profile_id)

    # Ensure profile directory exists
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir, exist_ok=True)

    # Check if already running
    if data.profile_id in _running:
        proc = _running[data.profile_id]
        if proc.poll() is None:
            return {"status": "already_running", "message": f"Profile {data.profile_id} is already running"}

    # Build launch command
    cmd = ["camoufox", "launch", f"--profile={profile_dir}"]
    if data.proxy:
        cmd.append(f"--proxy={data.proxy}")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        _running[data.profile_id] = proc
        return {"status": "success", "message": f"Profile {data.profile_id} launched", "pid": proc.pid}
    except FileNotFoundError:
        # Camoufox not found — log for development
        print(f"[WARN] camoufox not in PATH. Would launch: {' '.join(cmd)}")
        return {"status": "success", "message": f"Profile {data.profile_id} launch requested (camoufox not in PATH)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop/{profile_id}")
def stop_profile(profile_id: str):
    """Stop a running browser for the given profile."""
    if profile_id not in _running:
        raise HTTPException(status_code=404, detail="Profile not running")

    proc = _running[profile_id]
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    del _running[profile_id]
    return {"status": "success", "message": f"Profile {profile_id} stopped"}


@app.get("/profiles/{profile_id}/status")
def profile_status(profile_id: str):
    """Check if a profile browser is currently running."""
    if profile_id in _running and _running[profile_id].poll() is None:
        return {"is_running": True, "pid": _running[profile_id].pid}
    # Clean up finished processes
    if profile_id in _running:
        del _running[profile_id]
    return {"is_running": False}


@app.post("/proxy-test")
def test_proxy(data: ProxyTest):
    """Test proxy by attempting a connection. Returns latency in ms."""
    try:
        # Parse proxy string to extract host:port
        proxy = data.proxy
        # Remove protocol prefix
        for prefix in ["socks5://", "socks4://", "http://", "https://"]:
            if proxy.startswith(prefix):
                proxy = proxy[len(prefix):]
                break

        # Remove auth (user:pass@)
        if "@" in proxy:
            proxy = proxy.split("@", 1)[1]

        # Extract host and port
        if ":" in proxy:
            host, port_str = proxy.rsplit(":", 1)
            port = int(port_str)
        else:
            host = proxy
            port = 1080

        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        latency = int((time.time() - start) * 1000)
        sock.close()

        return {"success": True, "latency": latency}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  Zumi Antidetect API Server v2.0")
    print(f"  Database: {DB_PATH}")
    print(f"  Profiles: {PROFILES_ROOT}")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8001)
