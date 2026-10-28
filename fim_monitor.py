import os
import hashlib
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("OWNER_ID")

# Direktori dan file yang ingin dipantau integritasnya
TARGET_DIR = "/home/ubuntu/sec-monitor"
HASH_STORE = "file_hashes.json"
MONITOR_EXTENSIONS = (".py", ".env", ".sh", ".json")

def send_telegram_alert(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram token belum dikonfigurasi.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[X] Gagal kirim alert FIM: {e}")

def calculate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def scan_files():
    file_hashes = {}
    for root, dirs, files in os.walk(TARGET_DIR):
        # Lewati folder venv atau git agar tidak membebani
        if "venv" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(MONITOR_EXTENSIONS):
                full_path = os.path.join(root, file)
                file_hash = calculate_file_hash(full_path)
                if file_hash:
                    file_hashes[full_path] = file_hash
    return file_hashes

def check_integrity():
    print("=" * 50)
    print("⚡ GARFIELD FILE INTEGRITY MONITOR (FIM)")
    print("=" * 50 + "\n")

    current_hashes = scan_files()

    if not os.path.exists(HASH_STORE):
        print("[*] Baseline hash belum ada. Membuat baseline awal...")
        with open(HASH_STORE, "w") as f:
            json.dump(current_hashes, f, indent=4)
        print(f"[+] Baseline berhasil dibuat dengan {len(current_hashes)} file terpantau.")
        return

    # Muat baseline sebelumnya
    with open(HASH_STORE, "r") as f:
        baseline_hashes = json.load(f)

    modified = []
    added = []
    deleted = []

    # Cek perubahan dan penambahan
    for filepath, current_hash in current_hashes.items():
        if filepath not in baseline_hashes:
            added.append(filepath)
        elif baseline_hashes[filepath] != current_hash:
            modified.append(filepath)

    # Cek penghapusan
    for filepath in baseline_hashes:
        if filepath not in current_hashes:
            deleted.append(filepath)

    if modified or added or deleted:
        alert_msg = (
            f"🚨 <b>PERINGATAN INTEGRITAS FILE (FIM)</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>Perubahan kode sistem terdeteksi!</b>\n"
        )
        if modified:
            alert_msg += f"📝 <b>Dimodifikasi:</b>\n" + "\n".join([f"• <code>{f}</code>" for f in modified]) + "\n"
        if added:
            alert_msg += f"➕ <b>File Baru Ditambahkan:</b>\n" + "\n".join([f"• <code>{f}</code>" for f in added]) + "\n"
        if deleted:
            alert_msg += f"🗑 <b>File Dihapus:</b>\n" + "\n".join([f"• <code>{f}</code>" for f in deleted]) + "\n"
        alert_msg += f"━━━━━━━━━━━━━━━━━━━"
        
        print(alert_msg)
        send_telegram_alert(alert_msg)
        
        # Perbarui baseline ke kondisi sekarang (atau biarkan manual demi keamanan)
        with open(HASH_STORE, "w") as f:
            json.dump(current_hashes, f, indent=4)
    else:
        print("[+] Integritas file aman. Tidak ada perubahan kode yang mencurigakan.")

if __name__ == "__main__":
    check_integrity()
