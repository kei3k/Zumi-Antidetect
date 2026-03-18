# -*- coding: utf-8 -*-
"""
+=====================================================+
|  ZUMI ANTIDETECT BROWSER MANAGER v3.0               |
|  Desktop Edition — Hidemium-Style UI                 |
|  CustomTkinter | Dark Theme | Neon Accents           |
+=====================================================+
"""

import os
import sys
import time
import json
import socket
import subprocess
import threading
import datetime
import urllib.request
from pathlib import Path
from typing import Optional, Dict, List

import customtkinter as ctk

# ══════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════

APP_DATA_DIR     = os.path.dirname(os.path.abspath(__file__))
PROFILES_ROOT    = r"D:\K\HIDEMIUM_4\ProfilesData\2236226b-3617-47ec-a77e-5fa031f16782"
NOTES_FILE       = os.path.join(APP_DATA_DIR, "profile_notes.json")
PROXY_FILE       = os.path.join(APP_DATA_DIR, "profile_proxies.json")
TAGS_FILE        = os.path.join(APP_DATA_DIR, "profile_tags.json")
NAMES_FILE       = os.path.join(APP_DATA_DIR, "profile_names.json")
BOOKMARKS_FILE   = os.path.join(APP_DATA_DIR, "bookmarks.json")
HIDEMIUM_CACHE   = os.path.join(APP_DATA_DIR, "hidemium_cache.json")
HIDEMIUM_API_URL = "http://127.0.0.1:2222"

# ══════════════════════════════════════════════════════
#  HIDEMIUM-STYLE COLOR PALETTE
# ══════════════════════════════════════════════════════

class C:
    """Colors — Dark theme inspired by Hidemium."""
    # Backgrounds
    BG_SIDEBAR    = "#13161d"
    BG_MAIN       = "#181b24"
    BG_HEADER     = "#1e2230"
    BG_ROW        = "#1a1e28"
    BG_ROW_ALT    = "#161a23"
    BG_ROW_HOVER  = "#252a38"
    BG_INPUT      = "#12151d"
    BG_TABLE_HEAD = "#14171f"
    BG_POPUP      = "#1e2230"

    # Borders
    BORDER        = "#2a2f3d"
    BORDER_FOCUS  = "#3b82f6"

    # Accents
    GREEN         = "#22c55e"      # Ready / Start / Running
    GREEN_HOVER   = "#16a34a"
    GREEN_DIM     = "#15382a"
    BLUE          = "#3b82f6"      # Buttons / Links
    BLUE_HOVER    = "#2563eb"
    BLUE_DIM      = "#1e3a5f"
    RED           = "#ef4444"      # Stop / Error
    RED_HOVER     = "#dc2626"
    RED_DIM       = "#3f1515"
    YELLOW        = "#eab308"      # Warning / Proxy test
    YELLOW_DIM    = "#3d3108"
    CYAN          = "#06b6d4"      # Highlight
    ORANGE        = "#f97316"      # Tag badge
    PURPLE        = "#a855f7"

    # Text
    TEXT          = "#e2e8f0"
    TEXT_SEC      = "#94a3b8"
    TEXT_DIM      = "#475569"
    TEXT_DARK     = "#0f172a"
    WHITE         = "#ffffff"


# ══════════════════════════════════════════════════════
#  HIDEMIUM API CLIENT
# ══════════════════════════════════════════════════════

class HidemiumAPI:
    """Fetch profile data from Hidemium's local API (port 2222)."""

    def __init__(self):
        self._cache: Dict[str, dict] = {}  # uuid -> profile data
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(HIDEMIUM_CACHE):
            try:
                with open(HIDEMIUM_CACHE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self):
        try:
            with open(HIDEMIUM_CACHE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def fetch_all(self) -> Dict[str, dict]:
        """Fetch all profiles from Hidemium API. Returns uuid->data dict."""
        all_profiles = []
        page = 1
        while True:
            try:
                body = json.dumps({"is_local": False, "page": page, "limit": 50}).encode()
                req = urllib.request.Request(
                    f"{HIDEMIUM_API_URL}/v1/browser/list",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                resp = urllib.request.urlopen(req, timeout=8)
                result = json.loads(resp.read().decode())
                data = result.get("data", {})
                profiles = data.get("content", data.get("data", []))
                if not profiles or not isinstance(profiles, list):
                    break
                all_profiles.extend(profiles)
                if len(profiles) < 50:
                    break
                page += 1
            except Exception as e:
                print(f"[Hidemium API] page {page} error: {e}")
                break

        # Build uuid -> data lookup
        lookup = {}
        for p in all_profiles:
            uuid = p.get("uuid", "")
            if not uuid:
                continue
            # Format proxy: extract IP:port from proxy dict or string
            proxy_raw = p.get("proxy", "")
            proxy_str = ""
            if isinstance(proxy_raw, dict):
                ip = proxy_raw.get("ip", "")
                port = proxy_raw.get("port", "")
                user = proxy_raw.get("user", "")
                pwd = proxy_raw.get("pass", "")
                ptype = proxy_raw.get("type", "HTTP").lower()
                if ip and port:
                    if user:
                        proxy_str = f"{ptype}://{user}:{pwd}@{ip}:{port}"
                    else:
                        proxy_str = f"{ptype}://{ip}:{port}"
            elif isinstance(proxy_raw, str):
                proxy_str = proxy_raw

            lookup[uuid] = {
                "name":      p.get("name", ""),
                "note":      p.get("note", ""),
                "proxy":     proxy_str,
                "last_open": p.get("last_open", ""),
                "folder_id": p.get("folder_id", ""),
                "version":   p.get("version", ""),
                "os":        p.get("os", ""),
                "status":    p.get("status", ""),
            }

        if lookup:
            self._cache = lookup
            self._save_cache()
            print(f"[Hidemium API] Synced {len(lookup)} profiles")
        else:
            print(f"[Hidemium API] No data from API, using cache ({len(self._cache)} profiles)")

        return self._cache

    def get(self, uuid: str) -> dict:
        return self._cache.get(uuid, {})


# ══════════════════════════════════════════════════════
#  PROFILE MANAGER — Backend Logic
# ══════════════════════════════════════════════════════

class ProfileManager:
    """Scan profiles, launch/stop via Camoufox. Hidemium sync optional."""

    def __init__(self):
        self._running: set = set()  # Set of running profile UUIDs
        self._browsers: Dict[str, dict] = {}  # uuid -> {camoufox, browser, page}
        self._notes:   Dict[str, str] = {}
        self._proxies: Dict[str, str] = {}
        self._tags:    Dict[str, str] = {}
        self._names:   Dict[str, str] = {}  # Local profile names
        self._hidemium = HidemiumAPI()
        self._api_data: Dict[str, dict] = {}  # uuid -> API data (optional)
        os.makedirs(PROFILES_ROOT, exist_ok=True)
        self._load_json()

    # --- JSON persistence ---------------------------------------------------
    def _load_json(self):
        for attr, path in [("_notes", NOTES_FILE), ("_proxies", PROXY_FILE), ("_tags", TAGS_FILE), ("_names", NAMES_FILE)]:
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        setattr(self, attr, json.load(f))
            except Exception:
                setattr(self, attr, {})

    def _save(self, attr, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(getattr(self, attr), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def save_notes(self):   self._save("_notes",   NOTES_FILE)
    def save_proxies(self): self._save("_proxies", PROXY_FILE)
    def save_tags(self):    self._save("_tags",    TAGS_FILE)
    def _save_names(self):  self._save("_names",   NAMES_FILE)

    # --- Setters -------------------------------------------------------------
    def set_note(self, pid, v):  self._notes[pid]=v;   self.save_notes()
    def set_proxy(self, pid, v): self._proxies[pid]=v;  self.save_proxies()
    def set_tag(self, pid, v):   self._tags[pid]=v;     self.save_tags()
    def set_name(self, pid, v):  self._names[pid]=v;    self._save_names()

    # --- Hidemium API sync ---------------------------------------------------
    def sync_from_hidemium(self):
        """Fetch profile data from Hidemium API and merge into local data."""
        self._api_data = self._hidemium.fetch_all()
        return len(self._api_data)

    # --- Profile scan --------------------------------------------------------
    def scan_profiles(self) -> List[dict]:
        profiles = []
        if not os.path.exists(PROFILES_ROOT):
            return profiles

        # Use cached API data (optional — may be empty)
        api = self._api_data or self._hidemium._cache

        for pid in sorted(os.listdir(PROFILES_ROOT)):
            p_path = os.path.join(PROFILES_ROOT, pid)
            if not os.path.isdir(p_path):
                continue

            is_running = pid in self._running

            # Merge: local name > API data > defaults
            api_info = api.get(pid, {})

            # Name: local _name file > API name > fallback
            name = self._names.get(pid) or api_info.get("name") or f"Profile-{pid[:8]}"

            # Proxy: local override > API > default
            proxy = self._proxies.get(pid) or api_info.get("proxy") or "Direct"

            # Notes: local override > API note > empty
            notes = self._notes.get(pid) or api_info.get("note") or ""

            # Tags: local > empty
            tag = self._tags.get(pid, "")

            # Last open: API > Local State > folder mtime
            last_open = api_info.get("last_open", "")
            if not last_open:
                local_state = os.path.join(p_path, "Local State")
                if os.path.exists(local_state):
                    try:
                        with open(local_state, "r", encoding="utf-8") as f:
                            ls = json.load(f)
                        at = ls.get("profile",{}).get("info_cache",{}).get("Default",{}).get("active_time", 0)
                        if at and at > 1000000000:
                            dt = datetime.datetime.fromtimestamp(at)
                            last_open = dt.strftime("%d-%m-%Y %H:%M")
                    except Exception:
                        pass
            if not last_open:
                try:
                    mtime = os.path.getmtime(p_path)
                    dt = datetime.datetime.fromtimestamp(mtime)
                    last_open = dt.strftime("%d-%m-%Y %H:%M")
                except Exception:
                    last_open = "Unknown"

            profiles.append({
                "id":        pid,
                "name":      name,
                "proxy":     proxy,
                "tag":       tag,
                "notes":     notes,
                "last_open": last_open,
                "is_running": is_running,
            })

        return profiles

    # --- Launch / Stop via Camoufox (Free, Open-Source) -----------------------
    def _read_hidemium_cookies(self, profile_id: str) -> list:
        """Read cookies from Hidemium profile if available (optional)."""
        cookies = []
        profile_dir = os.path.join(PROFILES_ROOT, profile_id)

        # Hidemium (Chromium) cookie files — skip if not present
        cookie_files = [
            os.path.join(profile_dir, "Default", "Network", "Cookies"),             # Main login cookies
            os.path.join(profile_dir, "Default", "Extension Cookies"),               # Extension cookies
            os.path.join(profile_dir, "Default", "Safe Browsing Network", "Safe Browsing Cookies"),
        ]

        seen = set()  # Deduplicate by (domain, name, path)

        for cookie_path in cookie_files:
            if not os.path.exists(cookie_path):
                continue
            try:
                import sqlite3 as _sql
                conn = _sql.connect(cookie_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT host_key, name, encrypted_value, path, expires_utc, "
                    "is_secure, is_httponly, samesite FROM cookies"
                )
                for row in cursor.fetchall():
                    host, name, value, path, expires, secure, httponly, samesite = row
                    if not name or not value:
                        continue

                    # Skip Chrome extension internal cookies (fake domains without dots)
                    clean_host = host.lstrip(".")
                    if "." not in clean_host:
                        continue

                    # Deduplicate
                    key = (host, name, path or "/")
                    if key in seen:
                        continue
                    seen.add(key)

                    # Convert Chrome timestamp (microseconds since 1601-01-01) to Unix epoch
                    expires_unix = -1
                    if expires and expires > 0:
                        expires_unix = (expires / 1_000_000) - 11644473600
                        if expires_unix < 0:
                            expires_unix = -1

                    # Map samesite: 0=None, 1=Lax, 2=Strict
                    sameSite_map = {0: "None", 1: "Lax", 2: "Strict"}
                    val_str = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)

                    cookie = {
                        "name": name,
                        "value": val_str,
                        "domain": host,
                        "path": path or "/",
                        "secure": bool(secure),
                        "httpOnly": bool(httponly),
                        "sameSite": sameSite_map.get(samesite, "Lax"),
                    }
                    if expires_unix > 0:
                        cookie["expires"] = expires_unix
                    cookies.append(cookie)
                conn.close()
            except Exception as e:
                print(f"[Cookie Read] Error reading {os.path.basename(cookie_path)} for {profile_id[:8]}: {e}")

        print(f"[Cookie Read] {profile_id[:8]}: {len(cookies)} cookies from {len([f for f in cookie_files if os.path.exists(f)])} files")
        return cookies

    def _load_or_create_fingerprint(self, profile_id: str):
        """Load saved fingerprint or generate + save a new one (Firefox only!)."""
        from browserforge.fingerprints import FingerprintGenerator, Fingerprint
        from browserforge.fingerprints import ScreenFingerprint, NavigatorFingerprint, VideoCard
        from dataclasses import asdict

        profile_dir = os.path.join(PROFILES_ROOT, profile_id)
        fp_path = os.path.join(profile_dir, "fingerprint.json")

        # Try to load existing fingerprint
        if os.path.exists(fp_path):
            try:
                with open(fp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate: must be Firefox fingerprint (Camoufox rejects others)
                ua = data.get("navigator", {}).get("userAgent", "")
                if "Firefox" not in ua:
                    print(f"[Fingerprint] Saved fingerprint is non-Firefox ({ua[:40]}), regenerating...")
                    os.remove(fp_path)
                else:
                    fp = Fingerprint(
                        screen=ScreenFingerprint(**data["screen"]),
                        navigator=NavigatorFingerprint(**data["navigator"]),
                        headers=data["headers"],
                        videoCodecs=data["videoCodecs"],
                        audioCodecs=data["audioCodecs"],
                        pluginsData=data["pluginsData"],
                        battery=data.get("battery"),
                        videoCard=VideoCard(**data["videoCard"]) if data.get("videoCard") else None,
                        multimediaDevices=data["multimediaDevices"],
                        fonts=data["fonts"],
                        mockWebRTC=data.get("mockWebRTC"),
                        slim=data.get("slim"),
                    )
                    print(f"[Fingerprint] Loaded saved Firefox fingerprint for {profile_id[:8]}")
                    return fp
            except Exception as e:
                print(f"[Fingerprint] Load error, regenerating: {e}")

        # Generate new Firefox-only fingerprint
        fg = FingerprintGenerator(browser='firefox', mock_webrtc=True)
        fp = fg.generate()

        # Save to disk
        try:
            os.makedirs(profile_dir, exist_ok=True)
            with open(fp_path, "w", encoding="utf-8") as f:
                json.dump(asdict(fp), f, indent=2, ensure_ascii=False)
            print(f"[Fingerprint] Generated & saved new Firefox fingerprint for {profile_id[:8]}")
        except Exception as e:
            print(f"[Fingerprint] Save error: {e}")

        return fp

    def launch_profile(self, profile_id: str) -> dict:
        """Open a profile browser via Camoufox with Hidemium cookies."""
        if profile_id in self._running:
            return {"ok": False, "msg": "Already running"}

        try:
            from camoufox.sync_api import Camoufox

            # Read cookies from Hidemium profile
            cookies = self._read_hidemium_cookies(profile_id)

            # Build proxy config for camoufox
            proxy_str = self._proxies.get(profile_id, "")
            proxy_cfg = None
            if proxy_str and proxy_str not in ("Direct", "No Proxy", ""):
                proxy_cfg = {"server": proxy_str}

            # Load or generate persistent fingerprint
            fingerprint = self._load_or_create_fingerprint(profile_id)

            # Set up persistent user data dir for this profile
            browser_data_dir = os.path.join(PROFILES_ROOT, profile_id, "browser_data")
            first_launch = not os.path.exists(browser_data_dir)
            os.makedirs(browser_data_dir, exist_ok=True)

            def _launch():
                try:
                    camoufox = Camoufox(
                        headless=False,
                        proxy=proxy_cfg,
                        humanize=True,
                        window=(1860, 900),
                        fingerprint=fingerprint,
                        i_know_what_im_doing=True,
                        persistent_context=True,
                        user_data_dir=browser_data_dir,
                        firefox_user_prefs={
                            "browser.toolbars.bookmarks.visibility": "always",
                            "browser.startup.page": 3,
                        },
                    )
                    # persistent_context returns BrowserContext directly
                    context = camoufox.__enter__()

                    # Get existing page or create new one
                    if context.pages:
                        page = context.pages[0]
                    else:
                        page = context.new_page()

                    # Only inject Hidemium cookies on first launch
                    if first_launch and cookies:
                        ok_count = 0
                        for c in cookies:
                            try:
                                context.add_cookies([c])
                                ok_count += 1
                            except Exception:
                                pass
                        print(f"[Camoufox] First launch — injected {ok_count}/{len(cookies)} cookies for {profile_id[:8]}")
                    elif not first_launch:
                        print(f"[Camoufox] Persistent session loaded for {profile_id[:8]}")

                    page.goto("https://www.google.com", timeout=15000)

                    # Store references for cleanup
                    self._browsers[profile_id] = {
                        "camoufox": camoufox,
                        "browser": context,
                        "page": page,
                    }
                    self._running.add(profile_id)
                    print(f"[Camoufox] Profile {profile_id[:8]} launched (persistent)")
                except Exception as e:
                    self._running.discard(profile_id)
                    print(f"[Camoufox] Launch error: {e}")

            self._running.add(profile_id)
            threading.Thread(target=_launch, daemon=True).start()
            msg = f"First launch, injecting {len(cookies)} cookies..." if first_launch else "Loading saved session..."
            return {"ok": True, "msg": msg}

        except ImportError:
            return {"ok": False, "msg": "camoufox not installed. Run: pip install camoufox"}
        except Exception as e:
            self._running.discard(profile_id)
            return {"ok": False, "msg": str(e)[:60]}

    def stop_profile(self, pid: str) -> dict:
        """Close a Camoufox browser instance."""
        if pid not in self._browsers:
            self._running.discard(pid)
            return {"ok": False, "msg": "Not running"}

        try:
            info = self._browsers.pop(pid)
            camoufox = info.get("camoufox")
            if camoufox:
                try:
                    camoufox.__exit__(None, None, None)
                except Exception:
                    pass
            self._running.discard(pid)
            return {"ok": True, "msg": "Stopped"}
        except Exception as e:
            self._running.discard(pid)
            return {"ok": False, "msg": str(e)[:60]}

    # --- Create new profile ---------------------------------------------------
    def create_profile(self, name: str = "", proxy: str = "", notes: str = "") -> dict:
        """Create a new empty Camoufox profile folder."""
        import uuid as _uuid
        new_id = str(_uuid.uuid4())
        profile_dir = os.path.join(PROFILES_ROOT, new_id)
        os.makedirs(os.path.join(profile_dir, "Default", "Network"), exist_ok=True)

        # Save metadata
        if name:
            self._tags[new_id] = ""
            self.save_tags()
        if proxy and proxy not in ("Direct", "No Proxy", ""):
            self._proxies[new_id] = proxy
            self.save_proxies()
        if notes:
            self._notes[new_id] = notes
            self.save_notes()

        # Save name locally
        self._names[new_id] = name or f"Profile-{new_id[:8]}"
        self._save_names()

        return {"ok": True, "id": new_id, "msg": f"Created: {name or new_id[:8]}"}

    # --- Proxy test ----------------------------------------------------------
    def test_proxy(self, proxy_str: str) -> dict:
        if not proxy_str or proxy_str in ("Direct", "No Proxy"):
            return {"ok": False, "ms": 0, "msg": "No proxy"}
        try:
            proxy = proxy_str
            for pfx in ("socks5://","socks4://","http://","https://"):
                if proxy.startswith(pfx): proxy = proxy[len(pfx):]; break
            if "@" in proxy: proxy = proxy.split("@",1)[1]
            host, port = (proxy.rsplit(":",1) + ["1080"])[:2]
            port = int(port)
            t0 = time.time()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            ms = int((time.time()-t0)*1000)
            s.close()
            return {"ok": True, "ms": ms, "msg": f"{ms}ms"}
        except Exception as e:
            return {"ok": False, "ms": 0, "msg": str(e)[:30]}

    def running_count(self) -> int:
        dead = [k for k,v in self._running.items() if v.poll() is not None]
        for k in dead: del self._running[k]
        return len(self._running)


# ══════════════════════════════════════════════════════
#  PROFILE ROW WIDGET
# ══════════════════════════════════════════════════════

class ProfileRow(ctk.CTkFrame):
    """One row in the profile table."""

    def __init__(self, master, idx: int, data: dict, mgr: ProfileManager,
                 on_change=None, **kw):
        bg = C.BG_ROW if idx % 2 == 0 else C.BG_ROW_ALT
        super().__init__(master, fg_color=bg, corner_radius=0, height=44, **kw)
        self.pack_propagate(False)
        self.d = data
        self.mgr = mgr
        self.on_change = on_change
        self._bg = bg

        # Column widths (proportional to Hidemium)
        self.grid_columnconfigure(0, weight=0, minsize=42)   # checkbox/index
        self.grid_columnconfigure(1, weight=2, minsize=160)  # Name
        self.grid_columnconfigure(2, weight=0, minsize=70)   # Tag
        self.grid_columnconfigure(3, weight=3, minsize=220)  # Proxy
        self.grid_columnconfigure(4, weight=1, minsize=140)  # Last Open
        self.grid_columnconfigure(5, weight=0, minsize=80)   # Status
        self.grid_columnconfigure(6, weight=2, minsize=160)  # Notes
        self.grid_columnconfigure(7, weight=0, minsize=150)  # Action

        px = {"padx": 5, "pady": 6}

        # 0 — Index
        ctk.CTkLabel(self, text=str(idx+1), font=("Segoe UI",11),
                     text_color=C.TEXT_DIM, width=36, anchor="center"
                     ).grid(row=0, column=0, **px)

        # 1 — Name (short id)
        ctk.CTkLabel(self, text=data["name"], font=("Segoe UI",12,"bold"),
                     text_color=C.TEXT, anchor="w"
                     ).grid(row=0, column=1, **px, sticky="w")

        # 2 — Tag (editable)
        self.tag_var = ctk.StringVar(value=data["tag"])
        tag_entry = ctk.CTkEntry(self, textvariable=self.tag_var,
                                 font=("Segoe UI",11), width=58, height=26,
                                 fg_color=C.BG_INPUT, border_color=C.BORDER,
                                 text_color=C.ORANGE, border_width=1,
                                 corner_radius=4, justify="center")
        tag_entry.grid(row=0, column=2, **px)
        tag_entry.bind("<FocusOut>", lambda e: self.mgr.set_tag(data["id"], self.tag_var.get().strip()))

        # 3 — Proxy (editable inline)
        self.proxy_var = ctk.StringVar(value=data["proxy"])
        proxy_frame = ctk.CTkFrame(self, fg_color="transparent")
        proxy_frame.grid(row=0, column=3, **px, sticky="ew")
        proxy_frame.grid_columnconfigure(0, weight=1)

        self.proxy_entry = ctk.CTkEntry(
            proxy_frame, textvariable=self.proxy_var, font=("Consolas",11),
            fg_color=C.BG_INPUT, border_color=C.BORDER, text_color=C.TEXT_SEC,
            border_width=1, height=26, corner_radius=4
        )
        self.proxy_entry.grid(row=0, column=0, sticky="ew", padx=(0,4))
        self.proxy_entry.bind("<FocusOut>", self._save_proxy)
        self.proxy_entry.bind("<Return>", self._save_proxy)

        # Test button (inline, small)
        self.test_btn = ctk.CTkButton(
            proxy_frame, text="Test", font=("Segoe UI",10,"bold"),
            fg_color=C.BLUE_DIM, hover_color=C.BLUE, text_color=C.CYAN,
            width=42, height=24, corner_radius=4,
            command=self._test_proxy
        )
        self.test_btn.grid(row=0, column=1)

        # 4 — Last Open
        ctk.CTkLabel(self, text=data["last_open"], font=("Segoe UI",11),
                     text_color=C.TEXT_DIM, anchor="w"
                     ).grid(row=0, column=4, **px, sticky="w")

        # 5 — Status badge
        self.status_lbl = ctk.CTkLabel(self, text="", font=("Segoe UI",10,"bold"),
                                       width=70, height=24, corner_radius=12)
        self.status_lbl.grid(row=0, column=5, **px)
        self._set_status(data["is_running"])

        # 6 — Notes
        self.notes_var = ctk.StringVar(value=data["notes"])
        notes_entry = ctk.CTkEntry(self, textvariable=self.notes_var,
                                   font=("Segoe UI",11), height=26,
                                   fg_color=C.BG_INPUT, border_color=C.BORDER,
                                   text_color=C.TEXT_SEC, border_width=1,
                                   corner_radius=4, placeholder_text="Note...")
        notes_entry.grid(row=0, column=6, **px, sticky="ew")
        notes_entry.bind("<FocusOut>", lambda e: self.mgr.set_note(data["id"], self.notes_var.get().strip()))

        # 7 — Action buttons
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=7, **px)

        self.start_btn = ctk.CTkButton(
            action_frame, text="", font=("Segoe UI",11,"bold"),
            width=80, height=28, corner_radius=6,
            command=self._toggle_launch
        )
        self.start_btn.pack(side="left", padx=2)
        self._set_btn(data["is_running"])

        # More menu button
        ctk.CTkButton(
            action_frame, text="⋮", font=("Segoe UI",14),
            fg_color="transparent", hover_color=C.BG_ROW_HOVER,
            text_color=C.TEXT_DIM, width=28, height=28,
            command=self._show_menu
        ).pack(side="left", padx=2)

        # Hover
        self.bind("<Enter>", lambda e: self.configure(fg_color=C.BG_ROW_HOVER))
        self.bind("<Leave>", lambda e: self.configure(fg_color=self._bg))

    def _set_status(self, running: bool):
        if running:
            self.status_lbl.configure(text="Running", fg_color=C.GREEN_DIM, text_color=C.GREEN)
        else:
            self.status_lbl.configure(text="Ready", fg_color=C.GREEN_DIM, text_color=C.GREEN)

    def _set_btn(self, running: bool):
        if running:
            self.start_btn.configure(text="Stop", fg_color=C.RED, hover_color=C.RED_HOVER, text_color=C.WHITE)
        else:
            self.start_btn.configure(text="Start", fg_color=C.GREEN, hover_color=C.GREEN_HOVER, text_color=C.TEXT_DARK)

    def _save_proxy(self, e=None):
        v = self.proxy_var.get().strip() or "Direct"
        self.mgr.set_proxy(self.d["id"], v)

    def _test_proxy(self):
        self.test_btn.configure(text="...", state="disabled")
        def run():
            r = self.mgr.test_proxy(self.proxy_var.get().strip())
            self.after(0, lambda: self._show_test(r))
        threading.Thread(target=run, daemon=True).start()

    def _show_test(self, r):
        if r["ok"]:
            self.test_btn.configure(text=f'{r["ms"]}ms', text_color=C.GREEN, state="normal")
        else:
            self.test_btn.configure(text="Fail", text_color=C.RED, state="normal")
        self.after(3000, lambda: self.test_btn.configure(text="Test", text_color=C.CYAN, state="normal"))

    def _toggle_launch(self):
        pid = self.d["id"]
        running = pid in self.mgr._running
        self.start_btn.configure(state="disabled", text="...")

        def run():
            if running:
                res = self.mgr.stop_profile(pid)
                new = False
            else:
                res = self.mgr.launch_profile(pid)
                new = res["ok"]
            self.after(0, lambda: self._done_launch(new, res))
        threading.Thread(target=run, daemon=True).start()

    def _done_launch(self, running, res):
        self._set_status(running)
        self._set_btn(running)
        self.start_btn.configure(state="normal")
        self.d["is_running"] = running
        if self.on_change: self.on_change()
        if not res["ok"]:
            ErrorPopup(self, res["msg"])

    def _show_menu(self):
        menu = ctk.CTkToplevel(self)
        menu.title("")
        menu.geometry("180x240")
        menu.configure(fg_color=C.BG_POPUP)
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)

        # Position near the button
        x = self.winfo_rootx() + self.winfo_width() - 200
        y = self.winfo_rooty() + 10
        menu.geometry(f"+{x}+{y}")

        items = [
            ("Edit Proxy",        lambda: (menu.destroy(), self.proxy_entry.focus_set())),
            ("Edit Notes",        lambda: (menu.destroy())),
            ("Copy Profile ID",   lambda: (self.clipboard_clear(), self.clipboard_append(self.d["id"]), menu.destroy())),
            ("Open Folder",       lambda: (os.startfile(os.path.join(PROFILES_ROOT, self.d["id"])), menu.destroy())),
            ("Test Proxy",        lambda: (menu.destroy(), self._test_proxy())),
        ]

        for text, cmd in items:
            btn = ctk.CTkButton(
                menu, text=text, font=("Segoe UI",12),
                fg_color="transparent", hover_color=C.BG_ROW_HOVER,
                text_color=C.TEXT, anchor="w", height=36, corner_radius=0,
                command=cmd
            )
            btn.pack(fill="x", padx=4, pady=1)

        # Separator
        ctk.CTkFrame(menu, fg_color=C.BORDER, height=1).pack(fill="x", padx=8, pady=4)

        # Delete note/proxy
        ctk.CTkButton(
            menu, text="Clear Data", font=("Segoe UI",12),
            fg_color="transparent", hover_color=C.RED_DIM,
            text_color=C.RED, anchor="w", height=36, corner_radius=0,
            command=lambda: (self.mgr.set_note(self.d["id"],""), self.mgr.set_proxy(self.d["id"],"Direct"),
                             self.proxy_var.set("Direct"), self.notes_var.set(""), menu.destroy())
        ).pack(fill="x", padx=4, pady=1)

        menu.bind("<FocusOut>", lambda e: menu.destroy())
        menu.focus_set()


# ══════════════════════════════════════════════════════
#  ERROR POPUP
# ══════════════════════════════════════════════════════

class ErrorPopup(ctk.CTkToplevel):
    def __init__(self, parent, msg):
        super().__init__(parent)
        self.title("Error")
        self.geometry("380x120")
        self.configure(fg_color=C.BG_POPUP)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        ctk.CTkLabel(self, text=msg, font=("Segoe UI",12), text_color=C.RED,
                     wraplength=340).pack(pady=(20,10), padx=16)
        ctk.CTkButton(self, text="OK", width=80, fg_color=C.RED, hover_color=C.RED_HOVER,
                      text_color=C.WHITE, command=self.destroy).pack(pady=(0,12))


class NewProfileDialog(ctk.CTkToplevel):
    """Dialog to create a new profile."""
    def __init__(self, parent, mgr, on_created=None):
        super().__init__(parent)
        self.title("New Profile")
        self.geometry("460x340")
        self.configure(fg_color=C.BG_POPUP)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.mgr = mgr
        self.on_created = on_created

        ctk.CTkLabel(self, text="➕ Create New Profile", font=("Segoe UI",18,"bold"),
                     text_color=C.GREEN).pack(pady=(20,16))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=30)

        # Name
        ctk.CTkLabel(form, text="Profile Name", font=("Segoe UI",12), text_color=C.TEXT_SEC).pack(anchor="w")
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.name_var, font=("Segoe UI",13),
                     fg_color=C.BG_INPUT, border_color=C.BORDER, text_color=C.TEXT,
                     height=36, corner_radius=8, placeholder_text="e.g. My Account 01"
                     ).pack(fill="x", pady=(4,12))

        # Proxy
        ctk.CTkLabel(form, text="Proxy (optional)", font=("Segoe UI",12), text_color=C.TEXT_SEC).pack(anchor="w")
        self.proxy_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.proxy_var, font=("Segoe UI",13),
                     fg_color=C.BG_INPUT, border_color=C.BORDER, text_color=C.TEXT,
                     height=36, corner_radius=8, placeholder_text="socks5://user:pass@host:port"
                     ).pack(fill="x", pady=(4,12))

        # Notes
        ctk.CTkLabel(form, text="Notes (optional)", font=("Segoe UI",12), text_color=C.TEXT_SEC).pack(anchor="w")
        self.notes_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.notes_var, font=("Segoe UI",13),
                     fg_color=C.BG_INPUT, border_color=C.BORDER, text_color=C.TEXT,
                     height=36, corner_radius=8, placeholder_text="Any notes..."
                     ).pack(fill="x", pady=(4,16))

        # Buttons
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=(0,20))
        ctk.CTkButton(btn_f, text="Cancel", width=100, fg_color=C.BG_HEADER,
                      hover_color=C.BG_ROW_HOVER, text_color=C.TEXT_SEC,
                      border_color=C.BORDER, border_width=1, corner_radius=8,
                      command=self.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_f, text="✓ Create", width=120, fg_color=C.GREEN,
                      hover_color=C.GREEN_HOVER, text_color=C.TEXT_DARK,
                      font=("Segoe UI",13,"bold"), corner_radius=8,
                      command=self._create).pack(side="left", padx=6)

    def _create(self):
        name = self.name_var.get().strip()
        proxy = self.proxy_var.get().strip()
        notes = self.notes_var.get().strip()
        if not name:
            ErrorPopup(self, "Profile name is required")
            return
        res = self.mgr.create_profile(name, proxy, notes)
        if res["ok"]:
            self.destroy()
            if self.on_created:
                self.on_created()
        else:
            ErrorPopup(self, res["msg"])


# ══════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════

class ZumiApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("ZUMI ANTIDETECT v3.0")
        self.geometry("1360x820")
        self.minsize(1080, 600)
        self.configure(fg_color=C.BG_MAIN)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.mgr = ProfileManager()
        self.profiles: List[dict] = []
        self.rows: List[ProfileRow] = []
        self._search_job = None

        # Root grid: sidebar | main
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()
        self._switch_view("Profiles")  # Set initial sidebar highlight

        # Auto-sync from Hidemium API on startup, then load profiles
        self.after(200, self._initial_sync)
        self._auto_refresh()

    # ─────────── SIDEBAR ───────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=C.BG_SIDEBAR, width=220, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent", height=60)
        logo_frame.pack(fill="x", padx=16, pady=(20,8))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(logo_frame, text="⚡", font=("Segoe UI Emoji",22),
                     text_color=C.GREEN).pack(side="left", padx=(0,6))
        ctk.CTkLabel(logo_frame, text="Zumi", font=("Segoe UI",20,"bold"),
                     text_color=C.WHITE).pack(side="left")
        ctk.CTkLabel(logo_frame, text="Antidetect", font=("Segoe UI",14),
                     text_color=C.TEXT_SEC).pack(side="left", padx=(4,0), pady=(4,0))

        # Divider
        ctk.CTkFrame(sb, fg_color=C.BORDER, height=1).pack(fill="x", padx=16, pady=8)

        # Nav items — clickable
        self._nav_buttons = {}
        nav_items = [
            ("📋", "Profiles"),
            ("🌐", "Proxy"),
            ("🔌", "Extensions"),
            ("⚙️", "Settings"),
        ]
        for icon, label in nav_items:
            f = ctk.CTkFrame(sb, fg_color="transparent", corner_radius=8, height=38, cursor="hand2")
            f.pack(fill="x", padx=12, pady=2)
            f.pack_propagate(False)
            lbl_icon = ctk.CTkLabel(f, text=icon, font=("Segoe UI Emoji",14), text_color=C.TEXT_SEC)
            lbl_icon.pack(side="left", padx=(12,8), pady=6)
            lbl_text = ctk.CTkLabel(f, text=label, font=("Segoe UI",13), text_color=C.TEXT_SEC)
            lbl_text.pack(side="left", pady=6)
            self._nav_buttons[label] = {"frame": f, "icon": lbl_icon, "text": lbl_text}
            # Click handler
            cmd = lambda e, l=label: self._switch_view(l)
            f.bind("<Button-1>", cmd)
            lbl_icon.bind("<Button-1>", cmd)
            lbl_text.bind("<Button-1>", cmd)

        self._current_view = "Profiles"

        # --- Bottom stats ---
        stats_frame = ctk.CTkFrame(sb, fg_color=C.BG_HEADER, corner_radius=10)
        stats_frame.pack(side="bottom", fill="x", padx=12, pady=16)

        ctk.CTkLabel(stats_frame, text="ZUMI-3K", font=("Consolas",13,"bold"),
                     text_color=C.GREEN).pack(anchor="w", padx=14, pady=(12,4))

        self.stat_total = ctk.CTkLabel(stats_frame, text="Profiles:  0",
                                       font=("Segoe UI",11), text_color=C.TEXT_SEC)
        self.stat_total.pack(anchor="w", padx=14, pady=1)

        self.stat_running = ctk.CTkLabel(stats_frame, text="Running:   0",
                                         font=("Segoe UI",11), text_color=C.GREEN)
        self.stat_running.pack(anchor="w", padx=14, pady=1)

        self.stat_stopped = ctk.CTkLabel(stats_frame, text="Stopped:   0",
                                         font=("Segoe UI",11), text_color=C.TEXT_DIM)
        self.stat_stopped.pack(anchor="w", padx=14, pady=(1,12))

    def _switch_view(self, view_name):
        """Switch sidebar highlighting and content panel."""
        self._current_view = view_name
        # Update sidebar highlights
        for name, parts in self._nav_buttons.items():
            if name == view_name:
                parts["frame"].configure(fg_color=C.BLUE_DIM)
                parts["icon"].configure(text_color=C.WHITE)
                parts["text"].configure(text_color=C.WHITE)
            else:
                parts["frame"].configure(fg_color="transparent")
                parts["icon"].configure(text_color=C.TEXT_SEC)
                parts["text"].configure(text_color=C.TEXT_SEC)

        # Show/hide content panels
        if view_name == "Profiles":
            self._profiles_panel.grid(row=0, column=1, sticky="nsew")
            for pname in ('_proxy_panel', '_ext_panel', '_settings_panel'):
                if hasattr(self, pname):
                    getattr(self, pname).grid_remove()
        elif view_name == "Proxy":
            self._profiles_panel.grid_remove()
            for pname in ('_ext_panel', '_settings_panel'):
                if hasattr(self, pname):
                    getattr(self, pname).grid_remove()
            self._show_proxy_panel()
        elif view_name == "Extensions":
            self._profiles_panel.grid_remove()
            for pname in ('_proxy_panel', '_settings_panel'):
                if hasattr(self, pname):
                    getattr(self, pname).grid_remove()
            self._show_extensions_panel()
        elif view_name == "Settings":
            self._profiles_panel.grid_remove()
            for pname in ('_proxy_panel', '_ext_panel'):
                if hasattr(self, pname):
                    getattr(self, pname).grid_remove()
            self._show_settings_panel()

    # ─────────── MAIN PANEL ───────────
    def _build_main_panel(self):
        main = ctk.CTkFrame(self, fg_color=C.BG_MAIN, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        self._profiles_panel = main
        main.grid_rowconfigure(3, weight=1)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=0)

        # --- Title Bar ---
        title_bar = ctk.CTkFrame(main, fg_color=C.BG_MAIN, height=50, corner_radius=0)
        title_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16,0))
        title_bar.pack_propagate(False)

        ctk.CTkLabel(title_bar, text="Profiles", font=("Segoe UI",22,"bold"),
                     text_color=C.TEXT).pack(side="left")

        self.total_badge = ctk.CTkLabel(title_bar, text="0",
                                        font=("Segoe UI",11,"bold"), text_color=C.TEXT_DARK,
                                        fg_color=C.GREEN, corner_radius=10,
                                        width=30, height=22)
        self.total_badge.pack(side="left", padx=(10,0), pady=(4,0))

        # --- Search + Actions Bar ---
        action_bar = ctk.CTkFrame(main, fg_color=C.BG_MAIN, height=46, corner_radius=0)
        action_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(12,0))

        # Search
        search_frame = ctk.CTkFrame(action_bar, fg_color=C.BG_INPUT, corner_radius=8,
                                    border_width=1, border_color=C.BORDER)
        search_frame.pack(side="left", fill="y", pady=2)

        ctk.CTkLabel(search_frame, text="🔍", font=("Segoe UI Emoji",13),
                     text_color=C.TEXT_DIM).pack(side="left", padx=(10,4))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var,
            placeholder_text="Search by name or proxy...",
            font=("Segoe UI",12), fg_color="transparent", border_width=0,
            text_color=C.TEXT, width=250, height=32
        )
        self.search_entry.pack(side="left", padx=(0,8))

        # Action buttons
        btn_frame = ctk.CTkFrame(action_bar, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="➕ New Profile", font=("Segoe UI",12,"bold"),
            fg_color=C.CYAN, hover_color="#0891b2",
            text_color=C.TEXT_DARK, width=126, height=34, corner_radius=8,
            command=self._new_profile
        ).pack(side="left", padx=4)

        self.sync_btn = ctk.CTkButton(
            btn_frame, text="🔄 Sync", font=("Segoe UI",12,"bold"),
            fg_color=C.PURPLE, hover_color="#9333ea",
            text_color=C.WHITE, width=90, height=34, corner_radius=8,
            command=self._sync_hidemium
        )
        self.sync_btn.pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="↻", font=("Segoe UI",14,"bold"),
            fg_color=C.BG_HEADER, hover_color=C.BG_ROW_HOVER,
            text_color=C.TEXT_SEC, border_color=C.BORDER, border_width=1,
            width=38, height=34, corner_radius=8,
            command=self._load_profiles
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="▶ Start All", font=("Segoe UI",12,"bold"),
            fg_color=C.GREEN, hover_color=C.GREEN_HOVER,
            text_color=C.TEXT_DARK, width=100, height=34, corner_radius=8,
            command=self._launch_all
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="■ Stop All", font=("Segoe UI",12,"bold"),
            fg_color=C.RED, hover_color=C.RED_HOVER,
            text_color=C.WHITE, width=100, height=34, corner_radius=8,
            command=self._stop_all
        ).pack(side="left", padx=4)

        # --- Table Header ---
        th = ctk.CTkFrame(main, fg_color=C.BG_TABLE_HEAD, height=38, corner_radius=0)
        th.grid(row=2, column=0, sticky="ew", padx=20, pady=(12,0))
        th.pack_propagate(False)

        th.grid_columnconfigure(0, weight=0, minsize=42)
        th.grid_columnconfigure(1, weight=2, minsize=160)
        th.grid_columnconfigure(2, weight=0, minsize=70)
        th.grid_columnconfigure(3, weight=3, minsize=220)
        th.grid_columnconfigure(4, weight=1, minsize=140)
        th.grid_columnconfigure(5, weight=0, minsize=80)
        th.grid_columnconfigure(6, weight=2, minsize=160)
        th.grid_columnconfigure(7, weight=0, minsize=150)

        cols = ["#", "Name", "Tags", "Proxy", "Last Open", "Status", "Notes", "Action"]
        for i, col in enumerate(cols):
            anch = "center" if i in (0,5) else "w"
            ctk.CTkLabel(th, text=col, font=("Segoe UI",11,"bold"),
                         text_color=C.TEXT_DIM, anchor=anch
                         ).grid(row=0, column=i, padx=5, pady=8, sticky="ew")

        # --- Table Body ---
        self.table = ctk.CTkScrollableFrame(
            main, fg_color=C.BG_MAIN, corner_radius=0,
            scrollbar_button_color=C.BORDER,
            scrollbar_button_hover_color=C.BLUE
        )
        self.table.grid(row=3, column=0, sticky="nsew", padx=20, pady=(2,0))

        # --- Bookmark Bar ---
        bm_bar = ctk.CTkFrame(main, fg_color=C.BG_HEADER, height=42, corner_radius=0)
        bm_bar.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        bm_bar.pack_propagate(False)
        self._bookmark_bar = bm_bar

        # Bookmark bar label
        ctk.CTkLabel(bm_bar, text="★", font=("Segoe UI",14),
                     text_color=C.YELLOW).pack(side="left", padx=(16,4), pady=4)
        ctk.CTkLabel(bm_bar, text="Bookmarks", font=("Segoe UI",11,"bold"),
                     text_color=C.TEXT_SEC).pack(side="left", padx=(0,8), pady=4)

        # Bookmark items container (scrollable horizontal)
        self._bm_container = ctk.CTkFrame(bm_bar, fg_color="transparent")
        self._bm_container.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        # Add bookmark button
        ctk.CTkButton(
            bm_bar, text="+", font=("Segoe UI",14,"bold"),
            fg_color=C.BORDER, hover_color=C.BLUE, text_color=C.WHITE,
            width=30, height=28, corner_radius=6,
            command=self._add_bookmark
        ).pack(side="right", padx=(4,16), pady=4)

        # Load and display bookmarks
        self._bookmarks = self._load_bookmarks()
        self._render_bookmarks()

        # --- Status Bar ---
        sbar = ctk.CTkFrame(main, fg_color=C.BG_SIDEBAR, height=32, corner_radius=0)
        sbar.grid(row=5, column=0, sticky="ew", padx=0, pady=0)
        sbar.pack_propagate(False)

        self.status_lbl = ctk.CTkLabel(sbar, text="Ready", font=("Consolas",10),
                                        text_color=C.TEXT_DIM, anchor="w")
        self.status_lbl.pack(side="left", padx=20, pady=4)

        ctk.CTkLabel(sbar, text=f"Source: {PROFILES_ROOT}", font=("Consolas",9),
                     text_color=C.TEXT_DIM, anchor="e").pack(side="right", padx=20, pady=4)

    # ─────────── BOOKMARKS ───────────
    def _load_bookmarks(self):
        """Load bookmarks from JSON file."""
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_bookmarks(self):
        """Save bookmarks to JSON file."""
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Bookmarks] Save error: {e}")

    def _render_bookmarks(self):
        """Render bookmark pills in the bookmark bar."""
        for w in self._bm_container.winfo_children():
            w.destroy()
        for i, bm in enumerate(self._bookmarks):
            name = bm.get("name", "?")
            url = bm.get("url", "")
            pill = ctk.CTkFrame(self._bm_container, fg_color=C.BG_INPUT,
                                corner_radius=6, cursor="hand2")
            pill.pack(side="left", padx=3, pady=2)

            lbl = ctk.CTkLabel(pill, text=f"🔗 {name}", font=("Segoe UI",11),
                               text_color=C.BLUE, cursor="hand2")
            lbl.pack(side="left", padx=(8,4), pady=4)

            # Click → copy URL to clipboard
            def _copy(e, u=url, n=name):
                self.clipboard_clear()
                self.clipboard_append(u)
                self._set_status(f"📋 Copied: {u}")
            pill.bind("<Button-1>", _copy)
            lbl.bind("<Button-1>", _copy)

            # Right-click → delete
            def _delete(e, idx=i):
                self._bookmarks.pop(idx)
                self._save_bookmarks()
                self._render_bookmarks()
                self._set_status("Bookmark removed")
            pill.bind("<Button-3>", _delete)
            lbl.bind("<Button-3>", _delete)

    def _add_bookmark(self):
        """Open dialog to add a new bookmark."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Bookmark")
        dialog.geometry("400x200")
        dialog.configure(fg_color=C.BG_MAIN)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Add Bookmark", font=("Segoe UI",16,"bold"),
                     text_color=C.WHITE).pack(pady=(16,12))

        # Name input
        name_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        name_frame.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(name_frame, text="Name:", font=("Segoe UI",12),
                     text_color=C.TEXT_SEC, width=50).pack(side="left")
        name_entry = ctk.CTkEntry(name_frame, fg_color=C.BG_INPUT,
                                   border_color=C.BORDER, text_color=C.WHITE,
                                   font=("Segoe UI",12), height=32)
        name_entry.pack(side="left", fill="x", expand=True, padx=(8,0))

        # URL input
        url_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        url_frame.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(url_frame, text="URL:", font=("Segoe UI",12),
                     text_color=C.TEXT_SEC, width=50).pack(side="left")
        url_entry = ctk.CTkEntry(url_frame, fg_color=C.BG_INPUT,
                                  border_color=C.BORDER, text_color=C.WHITE,
                                  font=("Segoe UI",12), height=32,
                                  placeholder_text="https://...")
        url_entry.pack(side="left", fill="x", expand=True, padx=(8,0))

        def _save():
            n = name_entry.get().strip()
            u = url_entry.get().strip()
            if n and u:
                self._bookmarks.append({"name": n, "url": u})
                self._save_bookmarks()
                self._render_bookmarks()
                self._set_status(f"Bookmark added: {n}")
                dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(12,8))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=C.BORDER,
                      hover_color=C.BG_TABLE_HEAD, text_color=C.WHITE,
                      width=80, height=32, corner_radius=8,
                      command=dialog.destroy).pack(side="right", padx=(8,0))
        ctk.CTkButton(btn_frame, text="Add", fg_color=C.GREEN,
                      hover_color=C.GREEN_HOVER, text_color=C.TEXT_DARK,
                      width=80, height=32, corner_radius=8,
                      command=_save).pack(side="right")

    # ─────────── DATA ───────────
    def _load_profiles(self):
        self._set_status("Scanning profiles...")
        def scan():
            data = self.mgr.scan_profiles()
            self.after(0, lambda: self._fill(data))
        threading.Thread(target=scan, daemon=True).start()

    def _fill(self, profiles):
        self.profiles = profiles
        for w in self.rows: w.destroy()
        self.rows.clear()

        q = self.search_var.get().strip().lower()
        filtered = profiles
        if q:
            filtered = [p for p in profiles
                        if q in p["id"].lower() or q in p["name"].lower()
                        or q in p["proxy"].lower() or q in p["notes"].lower()
                        or q in p["tag"].lower()]

        for i, p in enumerate(filtered):
            row = ProfileRow(self.table, i, p, self.mgr, on_change=self._update_stats)
            row.pack(fill="x", padx=0, pady=0)
            self.rows.append(row)

        self._update_stats()
        self._set_status(f"Loaded {len(filtered)}/{len(profiles)} profiles")

    def _update_stats(self):
        total = len(self.profiles)
        running = len(self.mgr._running)
        stopped = total - running
        self.stat_total.configure(text=f"Profiles:  {total}")
        self.stat_running.configure(text=f"Running:   {running}")
        self.stat_stopped.configure(text=f"Stopped:   {stopped}")
        self.total_badge.configure(text=str(total))

    def _set_status(self, t):
        self.status_lbl.configure(text=t)

    def _on_search(self, *a):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, lambda: self._fill(self.profiles))

    # ─────────── BULK ───────────
    def _launch_all(self):
        targets = [p for p in self.profiles if not p["is_running"]]
        if not targets: self._set_status("No profiles to start"); return
        self._set_status(f"Starting {len(targets)} profiles...")
        def run():
            for p in targets:
                self.mgr.launch_profile(p["id"]); time.sleep(0.3)
            self.after(0, self._load_profiles)
        threading.Thread(target=run, daemon=True).start()

    def _stop_all(self):
        targets = [p for p in self.profiles if p["is_running"]]
        if not targets: self._set_status("No running profiles"); return
        self._set_status(f"Stopping {len(targets)} profiles...")
        def run():
            for p in targets: self.mgr.stop_profile(p["id"])
            self.after(0, self._load_profiles)
        threading.Thread(target=run, daemon=True).start()

    def _initial_sync(self):
        """On startup: sync from Hidemium API then load profiles."""
        self._set_status("Syncing from Hidemium API...")
        def run():
            count = self.mgr.sync_from_hidemium()
            self.after(0, lambda: self._set_status(f"Synced {count} profiles from Hidemium"))
            profiles = self.mgr.scan_profiles()
            self.after(0, lambda: self._fill(profiles))
        threading.Thread(target=run, daemon=True).start()

    def _sync_hidemium(self):
        """Manual sync button handler."""
        self.sync_btn.configure(state="disabled", text="Syncing...")
        self._set_status("Syncing from Hidemium API...")
        def run():
            count = self.mgr.sync_from_hidemium()
            profiles = self.mgr.scan_profiles()
            self.after(0, lambda: (
                self._fill(profiles),
                self._set_status(f"Synced {count} profiles from Hidemium"),
                self.sync_btn.configure(state="normal", text="🔄 Sync Hidemium")
            ))
        threading.Thread(target=run, daemon=True).start()

    def _auto_refresh(self):
        self._update_stats()
        self.after(5000, self._auto_refresh)

    def _new_profile(self):
        """Open the New Profile dialog."""
        NewProfileDialog(self, self.mgr, on_created=self._load_profiles)

    # ─────────── SECONDARY PANELS ───────────
    def _show_proxy_panel(self):
        """Show the Proxy management panel."""
        if hasattr(self, '_proxy_panel'):
            self._proxy_panel.grid(row=0, column=1, sticky="nsew")
            return

        panel = ctk.CTkFrame(self, fg_color=C.BG_MAIN, corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        self._proxy_panel = panel

        # Title
        ctk.CTkLabel(panel, text="🌐  Proxy Management", font=("Segoe UI",22,"bold"),
                     text_color=C.TEXT).grid(row=0, column=0, sticky="w", padx=24, pady=(20,4))
        ctk.CTkLabel(panel, text="View and edit proxies for all profiles",
                     font=("Segoe UI",12), text_color=C.TEXT_DIM
                     ).grid(row=1, column=0, sticky="w", padx=24, pady=(0,12))

        # Scrollable list
        scroll = ctk.CTkScrollableFrame(panel, fg_color=C.BG_MAIN,
                                         scrollbar_button_color=C.BORDER)
        scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,10))
        scroll.grid_columnconfigure(1, weight=1)

        for i, p in enumerate(self.profiles):
            bg = C.BG_ROW_ALT if i % 2 == 0 else C.BG_ROW
            row_f = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=6, height=40)
            row_f.pack(fill="x", pady=1)
            row_f.pack_propagate(False)

            ctk.CTkLabel(row_f, text=p["name"], font=("Segoe UI",12,"bold"),
                         text_color=C.TEXT, width=180, anchor="w"
                         ).pack(side="left", padx=(12,8))

            proxy_var = ctk.StringVar(value=p["proxy"])
            pid = p["id"]
            entry = ctk.CTkEntry(row_f, textvariable=proxy_var, font=("Segoe UI",11),
                                 fg_color=C.BG_INPUT, border_color=C.BORDER,
                                 text_color=C.CYAN, border_width=1, corner_radius=6,
                                 height=30)
            entry.pack(side="left", fill="x", expand=True, padx=4)
            entry.bind("<FocusOut>", lambda e, pid=pid, v=proxy_var: self.mgr.set_proxy(pid, v.get().strip()))

            def _test(btn, pv):
                btn.configure(text="...", state="disabled")
                def run():
                    r = self.mgr.test_proxy(pv.get().strip())
                    txt = f'{r["ms"]}ms' if r["ok"] else "Fail"
                    clr = C.GREEN if r["ok"] else C.RED
                    self.after(0, lambda: btn.configure(text=txt, text_color=clr, state="normal"))
                    self.after(3000, lambda: btn.configure(text="Test", text_color=C.CYAN, state="normal"))
                threading.Thread(target=run, daemon=True).start()

            test_btn = ctk.CTkButton(row_f, text="Test", width=55, height=28,
                                      font=("Segoe UI",10,"bold"), fg_color=C.BG_HEADER,
                                      hover_color=C.BG_ROW_HOVER, text_color=C.CYAN,
                                      border_color=C.CYAN, border_width=1, corner_radius=6)
            test_btn.configure(command=lambda b=test_btn, v=proxy_var: _test(b, v))
            test_btn.pack(side="right", padx=(4,12))

    def _show_extensions_panel(self):
        """Show Extensions info panel."""
        if hasattr(self, '_ext_panel'):
            self._ext_panel.grid(row=0, column=1, sticky="nsew")
            return

        panel = ctk.CTkFrame(self, fg_color=C.BG_MAIN, corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew")
        self._ext_panel = panel

        ctk.CTkLabel(panel, text="🔌  Extensions", font=("Segoe UI",22,"bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=24, pady=(20,4))
        ctk.CTkLabel(panel, text="Camoufox uses its own built-in antidetect extensions.\n"
                     "Custom extensions can be added via the addons parameter.",
                     font=("Segoe UI",13), text_color=C.TEXT_DIM, justify="left"
                     ).pack(anchor="w", padx=24, pady=(0,16))

        info_frame = ctk.CTkFrame(panel, fg_color=C.BG_HEADER, corner_radius=10)
        info_frame.pack(fill="x", padx=24, pady=8)
        for ext in ["🛡️ Anti-fingerprint (built-in)", "🌐 WebGL spoofing (built-in)",
                    "🔒 WebRTC leak protection (built-in)", "🎭 Canvas noise (built-in)"]:
            ctk.CTkLabel(info_frame, text=ext, font=("Segoe UI",12),
                         text_color=C.GREEN).pack(anchor="w", padx=16, pady=4)

    def _show_settings_panel(self):
        """Show Settings panel."""
        if hasattr(self, '_settings_panel'):
            self._settings_panel.grid(row=0, column=1, sticky="nsew")
            return

        panel = ctk.CTkFrame(self, fg_color=C.BG_MAIN, corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew")
        self._settings_panel = panel

        ctk.CTkLabel(panel, text="⚙️  Settings", font=("Segoe UI",22,"bold"),
                     text_color=C.TEXT).pack(anchor="w", padx=24, pady=(20,4))

        settings = [
            ("Profile Data Path", PROFILES_ROOT),
            ("Browser Engine", "Camoufox v135.0.1 (Firefox-based)"),
            ("Hidemium API", HIDEMIUM_API_URL),
            ("Cookie Source", "Default/Network/Cookies (auto-inject)"),
            ("Window Size", "1920 x 1080"),
        ]
        for label, value in settings:
            row = ctk.CTkFrame(panel, fg_color=C.BG_HEADER, corner_radius=8, height=44)
            row.pack(fill="x", padx=24, pady=4)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label, font=("Segoe UI",12,"bold"),
                         text_color=C.TEXT_SEC, width=180, anchor="w"
                         ).pack(side="left", padx=(16,8), pady=8)
            ctk.CTkLabel(row, text=value, font=("Consolas",11),
                         text_color=C.CYAN, anchor="w"
                         ).pack(side="left", fill="x", expand=True, pady=8)


# ══════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  ZUMI ANTIDETECT v3.0 - Desktop Edition")
    print(f"  Profiles: {PROFILES_ROOT}")
    print("=" * 60)
    app = ZumiApp()
    app.mainloop()
