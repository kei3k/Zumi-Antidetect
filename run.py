import subprocess
import sys
import os
import threading

# Config paths
BACKEND_DIR = r"D:\K\Zumi-Antidetect\scripts"
FRONTEND_DIR = r"D:\K\Zumi-Antidetect\dashboard"

def run_backend():
    """Chạy Backend API Server"""
    os.chdir(BACKEND_DIR)
    subprocess.run([sys.executable, "api_server.py"], shell=True)

def run_frontend():
    """Chạy Frontend Dashboard"""
    os.chdir(FRONTEND_DIR)
    subprocess.run(["npm", "run", "dev"], shell=True)

if __name__ == "__main__":
    print("=" * 60)
    print("  ZUMI ANTIDECTECT DASHBOARD - STARTING")
    print("  Backend: http://localhost:8001")
    print("  Frontend: http://localhost:5173")
    print("=" * 60)
    
    # Chạy 2 thread song song
    t1 = threading.Thread(target=run_backend, daemon=True)
    t2 = threading.Thread(target=run_frontend, daemon=True)
    
    t1.start()
    t2.start()
    
    # Giữ cho program chạy
    t1.join()
    t2.join()
