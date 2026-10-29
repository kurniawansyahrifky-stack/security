import re

with open("/home/ubuntu/sec-monitor/app.py", "r") as f:
    code = f.read()

full_listener_block = """def telegram_command_listener():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    offset = 0
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=10", timeout=15).json()
            for item in resp.get("result", []):
                offset = item["update_id"] + 1
                msg = item.get("message", {})
                if str(msg.get("chat", {}).get("id")) == str(TELEGRAM_CHAT_ID):
                    text = msg.get("text", "").strip()
                    
                    # 1. /backup
                    if text == "/backup": 
                        perform_system_backup(manual=True)
                        
                    # 2. /failover
                    elif text == "/failover": 
                        trigger_cloudflare_failover()
                        
                    # 3. /addadmin <IP> <Nama>
                    elif text.startswith("/addadmin"):
                        parts = text.split()
                        if len(parts) >= 2:
                            ip_to_add = parts[1]
                            dev_name = parts[2] if len(parts) > 2 else "Admin"
                            with db_lock:
                                import sqlite3
                                conn = sqlite3.connect(DB_PATH)
                                c = conn.cursor()
                                c.execute("INSERT OR REPLACE INTO admin_whitelist (ip, device_name, added_at) VALUES (?, ?, datetime('now'))", (ip_to_add, dev_name))
                                conn.commit()
                                conn.close()
                            send_telegram(f"🛡️ <b>Admin IP Terdaftar!</b>\\n• Device: {dev_name}\\n• IP: <code>{ip_to_add}</code>")
                        else:
                            send_telegram("⚠️ Format salah! Contoh: <code>/addadmin 192.168.1.50 LaptopUtama</code>")
                            
                    # 4. /deladmin <IP>
                    elif text.startswith("/deladmin"):
                        parts = text.split()
                        if len(parts) >= 2:
                            ip_to_del = parts[1]
                            with db_lock:
                                import sqlite3
                                conn = sqlite3.connect(DB_PATH)
                                c = conn.cursor()
                                c.execute("DELETE FROM admin_whitelist WHERE ip = ?", (ip_to_del,))
                                conn.commit()
                                conn.close()
                            send_telegram(f"🚫 <b>Akses Admin Dicabut!</b>\\n• IP: <code>{ip_to_del}</code>")
                        else:
                            send_telegram("⚠️ Format salah! Contoh: <code>/deladmin 192.168.1.50</code>")
                            
                    # 5. /addclient <Nama> <Domain> <BackendURL>
                    elif text.startswith("/addclient"):
                        parts = text.split()
                        if len(parts) >= 4:
                            c_name = parts[1]
                            c_domain = parts[2].lower()
                            c_backend = parts[3]
                            with db_lock:
                                import sqlite3
                                conn = sqlite3.connect(DB_PATH)
                                c = conn.cursor()
                                c.execute("INSERT OR REPLACE INTO client_targets (domain, backend_url, client_name, status, added_at) VALUES (?, ?, ?, 'ACTIVE', datetime('now'))", (c_domain, c_backend, c_name))
                                conn.commit()
                                conn.close()
                            send_telegram(f"🌐 <b>Klien Web Baru Didaftarkan!</b>\\n• Nama: {c_name}\\n• Domain: <code>{c_domain}</code>\\n• Backend: <code>{c_backend}</code>")
                        else:
                            send_telegram("⚠️ Format salah! Contoh:\\n<code>/addclient TokoKu store.devgarf.my.id http://127.0.0.1:5020</code>")
                            
                    # 6. /delclient <Domain>
                    elif text.startswith("/delclient"):
                        parts = text.split()
                        if len(parts) >= 2:
                            c_domain = parts[1].lower()
                            with db_lock:
                                import sqlite3
                                conn = sqlite3.connect(DB_PATH)
                                c = conn.cursor()
                                c.execute("DELETE FROM client_targets WHERE domain = ?", (c_domain,))
                                conn.commit()
                                conn.close()
                            send_telegram(f"🗑️ <b>Klien Web Dihapus!</b>\\n• Domain: <code>{c_domain}</code>")
                        else:
                            send_telegram("⚠️ Format salah! Contoh: <code>/delclient store.devgarf.my.id</code>")
                            
                    # 7. /help atau pesan umum
                    elif text == "/help" or text == "/start":
                        help_msg = (
                            "🤖 <b>GARFIELD SOC BOT COMMANDS</b> 🤖\\n"
                            "━━━━━━━━━━━━━━━━━━━\\n"
                            "📦 /backup - Kirim file zip cadangan database\\n"
                            "🚨 /failover - Eksekusi DNS failover Cloudflare\\n"
                            "🛡️ /addadmin [IP] [Nama] - Tambah IP whitelist admin\\n"
                            "🚫 /deladmin [IP] - Hapus IP whitelist admin\\n"
                            "🌐 /addclient [Nama] [Domain] [BackendURL] - Tambah web klien\\n"
                            "🗑️ /delclient [Domain] - Hapus web klien\\n"
                            "━━━━━━━━━━━━━━━━━━━"
                        )
                        send_telegram(help_msg)
        except Exception:
            pass
        time.sleep(1)"""

# Update fungsi listener di app.py
if "def telegram_command_listener" in code:
    code = re.sub(r"def telegram_command_listener\(\):.*?(?=\ndef [a-zA-Z_]|\Z)", full_listener_block + "\n\n", code, flags=re.DOTALL)
else:
    code += "\n\n" + full_listener_block

with open("/home/ubuntu/sec-monitor/app.py", "w") as f:
    f.write(code)

print("[+] Berhasil memperbarui seluruh command bot Telegram secara lengkap!")
