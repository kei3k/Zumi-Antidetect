# ⚡ Zumi Antidetect Browser Manager v3.0

A desktop antidetect browser manager built with **Python** + **CustomTkinter** + **Camoufox**.

Manage multiple browser profiles with unique fingerprints, persistent sessions, proxy support, and built-in bookmark bar.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Camoufox](https://img.shields.io/badge/Engine-Camoufox-orange)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Profile Management** | Create and manage unlimited browser profiles |
| **Persistent Fingerprints** | Each profile gets a unique Firefox fingerprint, saved permanently |
| **Persistent Sessions** | Cookies, bookmarks, history saved between sessions |
| **Proxy Management** | Set/edit/test proxies per profile with latency check |
| **Bookmark Bar** | Built-in bookmark bar — click to copy URL |
| **Hidemium Sync** | (Optional) Import profiles + cookies from Hidemium |
| **Dark Theme UI** | Premium cyberpunk dark theme |

---

## 🚀 Cài đặt mới (Fresh Install)

### Bước 1: Cài Python
Tải từ https://www.python.org/downloads/ → Cài đặt, **tick ✅ "Add to PATH"**

### Bước 2: Clone repo
```bash
git clone https://github.com/kei3k/Zumi-Antidetect.git
cd Zumi-Antidetect
```

### Bước 3: Cài dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cài Camoufox browser
```bash
python -m camoufox fetch
```

### Bước 5: Chạy
```bash
python main_app.py
```
Hoặc click đúp file **`start.bat`**

> ✅ Không cần cấu hình gì thêm. Profiles tự tạo trong thư mục `profiles/`.

---

## 🔄 Cập nhật (Update)

Khi có bản mới, chạy lệnh sau trong thư mục Zumi-Antidetect:

```bash
git pull origin main
```

Nếu có dependencies mới:
```bash
pip install -r requirements.txt
```

> ⚠️ Data profiles, bookmarks, proxies của anh **KHÔNG bị mất** khi update — chúng nằm trong `.gitignore`.

---

## 📸 Cách sử dụng

### Tạo Profile mới
1. Bấm **+ New Profile** trên thanh action
2. Nhập tên, proxy (tuỳ chọn), ghi chú → **Create**

### Mở Profile
- Bấm **Start** → Camoufox mở với fingerprint riêng
- Lần đầu: tạo fingerprint + browser data mới
- Lần sau: **load lại toàn bộ session** (cookies, login, history)

### Quản lý Proxy
- Click **Proxy** trên sidebar → chỉnh proxy cho từng profile
- Bấm **Test** để kiểm tra proxy sống/chết

### Bookmark Bar
- Bấm **+** trên thanh bookmark → thêm Name + URL
- **Click** bookmark → Copy URL vào clipboard → paste vào trình duyệt
- **Chuột phải** → xóa bookmark

### Đồng bộ Hidemium (Tuỳ chọn)
- Nếu có Hidemium đang chạy, bấm **Sync** để nhập profiles + cookies
- Không bắt buộc — tool hoạt động độc lập

---

## 🏗️ Cấu trúc

```
Zumi-Antidetect/
├── main_app.py          ← App chính
├── start.bat            ← Launcher (auto cài deps)
├── requirements.txt     ← Dependencies
├── scripts/             ← Utilities
└── profiles/            ← (auto tạo) Data profiles
    ├── <uuid>/
    │   ├── fingerprint.json    ← Fingerprint cố định
    │   └── browser_data/       ← Cookies, bookmarks, history
    └── ...
```

---

## 📋 Yêu cầu hệ thống

- **Python** 3.10+
- **Windows** 10/11
- **RAM** 4GB+
- **Camoufox** (tự cài qua pip)

## 📄 License

MIT License

---
*Built with ❤️ by Zumi Team*
