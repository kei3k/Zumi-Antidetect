# ⚡ Zumi Antidetect Browser Manager v3.0

A desktop antidetect browser manager built with **Python** + **CustomTkinter** + **Camoufox**.

Manage multiple browser profiles with unique fingerprints, persistent sessions, proxy support, and Hidemium data sync.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Camoufox](https://img.shields.io/badge/Engine-Camoufox-orange)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Profile Management** | Manage 90+ browser profiles from one dashboard |
| **Persistent Fingerprints** | Each profile gets a unique Firefox fingerprint, saved permanently |
| **Persistent Sessions** | Cookies, bookmarks, history saved between sessions |
| **Proxy Management** | Set/edit/test proxies per profile with latency check |
| **Hidemium Sync** | Import profiles + cookies from Hidemium Browser |
| **Bookmark Bar** | Built-in bookmark bar with click-to-copy |
| **Dark Theme UI** | Hidemium-inspired cyberpunk dark theme |

## 🚀 Quick Start

### 1. Clone
```bash
git clone https://github.com/kei3k/Zumi-Antidetect.git
cd Zumi-Antidetect
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Camoufox Browser
```bash
python -m camoufox fetch
```

### 4. Configure Profile Path
Edit `main_app.py` line 28 — set `PROFILES_ROOT` to your Hidemium profiles folder:
```python
PROFILES_ROOT = r"D:\Your\Path\To\ProfilesData\your-uuid"
```

### 5. Run
```bash
python main_app.py
```
Or double-click `start.bat`.

## 📸 Screenshots

*Coming soon*

## 🏗️ Architecture

```
Zumi-Antidetect/
├── main_app.py          ← Core app (UI + Profile Manager + Camoufox launcher)
├── start.bat            ← One-click launcher (auto-installs deps)
├── requirements.txt     ← Python dependencies
├── scripts/
│   ├── api_server.py    ← FastAPI backend (optional)
│   ├── explore_hidemium.py
│   ├── inspect_cookies.py
│   ├── inspect_db.py
│   ├── migrate_himenium.py
│   └── probe_api.py
└── (auto-generated at runtime)
    ├── hidemium_cache.json
    ├── profile_proxies.json
    ├── bookmarks.json
    └── fingerprint.json (per profile)
```

## 🔧 How It Works

### Fingerprint Persistence
- First launch: generates a **unique Firefox fingerprint** via `browserforge`
- Saved as `fingerprint.json` inside each profile folder
- All future launches use the **same fingerprint** — websites see the same "device"

### Persistent Browser Sessions
- Uses Camoufox `persistent_context` with dedicated `browser_data/` per profile
- Cookies, localStorage, bookmarks, history — all saved to disk
- Second launch = **instant session restore** (no re-login needed)

### Hidemium Integration
- Syncs profile names, proxies, notes from Hidemium API (port 2222)
- Imports cookies from Hidemium's SQLite databases
- Falls back to cached data when Hidemium is offline

## 📋 Requirements

- **Python** 3.10+
- **Windows** 10/11
- **Camoufox** (auto-installed via pip)
- **Hidemium** (optional, for profile sync)

## 🎮 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Close browser | Click **Stop** in Zumi app or `Alt+F4` |
| Minimize | `Alt+Space` → `N` |
| Copy bookmark URL | Click bookmark pill in bar |
| Delete bookmark | Right-click bookmark pill |

## 📄 License

MIT License — feel free to use and modify.

---
*Built with ❤️ by Zumi Team*
