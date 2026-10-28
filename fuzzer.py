import os
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor
import requests
from dotenv import load_dotenv

# Load kredensial dari .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("OWNER_ID")

# Header penyamaran agar request tidak langsung diblokir WAF sederhana
HEADERS = {
    "User-Agent": "GarfieldSecurityScanner/1.0 (Auditing Tool)"
}

# Daftar endpoint bawaan jika user tidak menyertakan file wordlist sendiri
DEFAULT_WORDLIST = [
    "admin", "login", "bank-transfer", "dashboard", "api", 
    ".env", "config", "config.json", "backup", "backup.sql",
    "robots.txt", "upload", "uploads", "portal", "secret",
    "db", "test", "server-status", "phpmyadmin", "console"
]

def send_telegram_alert(target_url, status_code, path):
    """Mengirim hasil temuan sensitif ke Bot Telegram Anda."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    msg = (
        f"🎯 <b>ENDPOINT DITEMUKAN!</b> 🎯\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>Target:</b> <code>{target_url}</code>\n"
        f"📂 <b>Path:</b> <code>/{path}</code>\n"
        f"📊 <b>Status Code:</b> <b>{status_code}</b>\n"
        f"🔗 <b>Full URL:</b> {target_url}/{path}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def scan_path(target, path):
    """Fungsi pekerja untuk memeriksa satu path URL."""
    url = f"{target.rstrip('/')}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=4, allow_redirects=False)
        code = resp.status_code

        # Kode 200 = Ditemukan dan Terbuka
        if code == 200:
            print(f"\033[92m[+] [200 OK]        -> {url}\033[0m")
            send_telegram_alert(target, code, path)
        # Kode 301/302 = Ada Redirect (seringkali halaman login/admin terproteksi)
        elif code in [301, 302]:
            redirect_to = resp.headers.get("Location", "")
            print(f"\033[93m[*] [{code} REDIRECT]  -> {url} => {redirect_to}\033[0m")
            send_telegram_alert(target, f"{code} Redirect to {redirect_to}", path)
        # Kode 401/403 = Halaman ada tapi butuh login/rahasia
        elif code in [401, 403]:
            print(f"\033[94m[!] [{code} FORBIDDEN] -> {url} (Ada tapi terproteksi)\033[0m")
            send_telegram_alert(target, f"{code} Protected", path)
        elif code == 404:
            # 404 = Tidak ada (abaikan agar tampilan terminal rapi)
            pass
        else:
            print(f"[-] [{code}]           -> {url}")
            
    except requests.exceptions.RequestException:
        pass

def main():
    parser = argparse.ArgumentParser(description="Garfield Custom Directory & Endpoint Scanner")
    parser.add_argument("-u", "--url", required=True, help="URL target (Contoh: http://fakebank.thm atau http://localhost:8080)")
    parser.add_argument("-w", "--wordlist", help="Path ke file wordlist kustom (opsional)")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Jumlah thread paralel (default: 10)")
    args = parser.parse_args()

    target = args.url
    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://" + target

    # Tentukan wordlist yang dipakai
    words = DEFAULT_WORDLIST
    if args.wordlist and os.path.exists(args.wordlist):
        with open(args.wordlist, "r", encoding="utf-8", errors="ignore") as f:
            words = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print("\033[96m" + "="*50)
    print(f"⚡ GARFIELD DIRECTORY SCANNER v1.0")
    print(f"🎯 Target    : {target}")
    print(f"📋 Total Path: {len(words)} kata")
    print(f"🚀 Threads   : {args.threads} paralel")
    print(f"📲 Telegram  : Alert Aktif ke ID {TELEGRAM_CHAT_ID}")
    print("="*50 + "\033[0m\n")

    # Jalankan pemindaian dengan multi-threading paralel
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for word in words:
            executor.submit(scan_path, target, word)

    print("\n\033[92m[✓] Pemindaian selesai!\033[0m")

if __name__ == "__main__":
    main()
