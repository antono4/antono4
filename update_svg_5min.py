#!/usr/bin/env python3
"""
Script untuk memperbarui contrib-3d.svg setiap 5 menit
dan push ke GitHub repository
"""
import os
import sys
import time
import subprocess
from datetime import datetime, timezone
import requests

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

REPO = "antono4/antono4"
BRANCH = "main"
SVG_PATH = "assets/contrib-3d.svg"
WORK_DIR = "/workspace/project"
INTERVAL = 300  # 5 menit

def run_cmd(cmd, cwd=WORK_DIR):
    """Jalankan command shell"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("🔄 Memperbarui contrib-3d.svg setiap 5 menit...")
    print(f"📍 Repo: {REPO}")
    print(f"📍 Branch: {BRANCH}")
    print("=" * 50)
    
    count = 0
    
    while True:
        count += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        print(f"[{count}] {timestamp} - Mengunduh SVG terbaru...")
        
        # Download SVG dari GitHub raw
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{SVG_PATH}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                svg_content = response.content
                file_size = len(svg_content)
                
                # Simpan file
                svg_file = os.path.join(WORK_DIR, SVG_PATH)
                with open(svg_file, 'wb') as f:
                    f.write(svg_content)
                
                print(f"[{count}] ✓ Download berhasil, ukuran: {file_size} bytes")
                
                # Commit dan push
                run_cmd("git add assets/contrib-3d.svg", WORK_DIR)
                _, diff_out, _ = run_cmd("git diff --staged --quiet", WORK_DIR)
                
                if diff_out == "" and run_cmd("git diff --staged", WORK_DIR)[1] == "":
                    print(f"[{count}] Tidak ada perubahan")
                else:
                    commit_msg = f"chore: update contrib-3d.svg [{timestamp}] [skip ci]"
                    # Allow empty commit agar tetap push
                    run_cmd(f'git commit -m "{commit_msg}" --allow-empty', WORK_DIR)
                    code, out, err = run_cmd("git push", WORK_DIR)
                    if code == 0:
                        print(f"[{count}] ✓ Berhasil di-push!")
                    else:
                        print(f"[{count}] ✗ Push gagal: {err}")
            else:
                print(f"[{count}] ✗ Gagal mengunduh: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[{count}] ✗ Error: {e}")
        
        print("---")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
