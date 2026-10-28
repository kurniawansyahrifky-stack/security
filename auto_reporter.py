import sqlite3
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("OWNER_ID")
DB_PATH = "security_logs.db"

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Token atau Chat ID Telegram belum diset di .env")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
        print("[+] Laporan keamanan berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"[X] Gagal mengirim laporan: {e}")

def generate_security_report():
    print("=" * 50)
    print("⚡ GARFIELD AUTOMATED SECURITY REPORTER v1.1")
    print(f"📂 Working Directory: {os.getcwd()}")
    print("=" * 50 + "\n")

    # Auto-create database & table if it doesn't exist yet so it never fails
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip TEXT,
            method TEXT,
            path TEXT,
            is_threat INTEGER,
            threats TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            ip TEXT PRIMARY KEY,
            reason TEXT,
            blocked_at TEXT
        )
    """)
    conn.commit()

    # 1. Total Trafik & Ancaman
    cursor.execute("SELECT COUNT(*) FROM logs")
    total_logs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM logs WHERE is_threat = 1")
    total_threats = cursor.fetchone()[0]

    # 2. Daftar IP yang diblokir / terkena Honeypot
    cursor.execute("SELECT ip, reason, blocked_at FROM blocked_ips")
    blocked_ips = cursor.fetchall()

    conn.close()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Susun Pesan Laporan
    report_text = (
        f"📊 <b>LAPORAN KEAMANAN OTOMATIS</b> 📊\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Waktu Laporan:</b> {timestamp}\n"
        f"🌐 <b>Total Request Masuk:</b> {total_logs}\n"
        f"🚨 <b>Total Ancaman/Honeypot:</b> {total_threats}\n"
        f"🛡 <b>Total IP Diblokir:</b> {len(blocked_ips)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
    )

    if blocked_ips:
        report_text += "<b>Daftar IP Terekam/Diblokir:</b>\n"
        for ip, reason, b_time in blocked_ips[-5:]:
            report_text += f"• <code>{ip}</code> -> {reason} ({b_time})\n"
    else:
        report_text += "✅ Belum ada IP berbahaya yang diblokir.\n"

    print(report_text)
    send_telegram(report_text)

if __name__ == "__main__":
    generate_security_report()
