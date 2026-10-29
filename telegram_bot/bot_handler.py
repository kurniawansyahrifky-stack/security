import os
import time
import sqlite3
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("OWNER_ID")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../security_logs.db"))
BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backups"))
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "telegram_error.log"))

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount('https://', adapter)

def answer_callback(callback_query_id, text=None):
    if not BOT_TOKEN: return
    try:
        session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text or ""},
            timeout=10
        )
    except:
        pass

def send_reply(text, reply_markup=None):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": str(CHAT_ID), "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    try:
        session.post(url, json=payload, timeout=25)
    except Exception as e:
        print(f"[X] Gagal kirim pesan: {e}")

def edit_message(chat_id, message_id, text, reply_markup=None):
    if not BOT_TOKEN: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    try:
        session.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"[X] Gagal edit pesan: {e}")

def get_main_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📦 Menu Backup", "callback_data": "menu_backup"},
                {"text": "♻️ Restore Database", "callback_data": "menu_restore"}
            ],
            [
                {"text": "🌐 List Target Web", "callback_data": "btn_list_clients"},
                {"text": "🛡️ Whitelist Admin", "callback_data": "btn_list_admins"}
            ],
            [
                {"text": "🚨 Cloudflare Failover", "callback_data": "btn_cf_confirm"},
                {"text": "🔄 Refresh", "callback_data": "btn_main_menu"}
            ]
        ]
    }

def get_clients_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT domain, backend_url, client_name, db_source_path, status FROM client_targets")
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def handle_callback_action(callback_data, callback_id, chat_id, message_id, perform_backup_func, failover_func, restore_func):
    answer_callback(callback_id)

    if callback_data == "btn_main_menu":
        msg = "🤖 <b>GARFIELD COMMAND CENTER</b> 🤖\nPilih menu operasional di bawah:"
        edit_message(chat_id, message_id, msg, get_main_keyboard())

    # --- MENU PILIHAN BACKUP ---
    elif callback_data == "menu_backup":
        clients = get_clients_from_db()
        keyboard = [
            [{"text": "🛡️ Full SOC Gateway (WAF+Logs+.env)", "callback_data": "do_backup_soc"}]
        ]
        if clients:
            for domain, _, name, _, _ in clients:
                keyboard.append([{"text": f"🌐 Backup {name} ({domain})", "callback_data": f"do_bkclient_{domain}"}])
        keyboard.append([{"text": "🔙 Kembali", "callback_data": "btn_main_menu"}])
        
        text = "📦 <b>PILIH TARGET YANG INGIN DIBACKUP:</b>\n━━━━━━━━━━━━━━━━━━━━\nPilih backup sistem pusat atau database spesifik klien:"
        edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})

    elif callback_data == "do_backup_soc":
        send_reply("🔄 <b>Sedang membuat backup Full SOC Gateway...</b>")
        success = perform_backup_func()
        if not success: send_reply("⚠️ Gagal mengeksekusi backup SOC.")

    elif callback_data.startswith("do_bkclient_"):
        domain = callback_data.replace("do_bkclient_", "")
        send_reply(f"🔄 <b>Sedang membackup data untuk:</b> <code>{domain}</code>...")
        success = perform_backup_func(target_domain=domain)
        if not success: send_reply(f"⚠️ Gagal mengeksekusi backup untuk {domain}.")

    # --- MENU FITUR RESTORE ---
    elif callback_data == "menu_restore":
        os.makedirs(BACKUP_DIR, exist_ok=True)
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")], reverse=True)
        if not files:
            text = "♻️ <b>RESTORE DATABASE</b>\n━━━━━━━━━━━━━━━━━━━━\n<i>Belum ada arsip zip backup yang tersimpan di folder backups/.</i>"
            kb = {"inline_keyboard": [[{"text": "🔙 Kembali", "callback_data": "btn_main_menu"}]]}
        else:
            text = f"♻️ <b>PILIH FILE RESTORE POINT ({len(files)} Tersedia):</b>\n━━━━━━━━━━━━━━━━━━━━\nPilih file backup yang ingin dipulihkan ke server:"
            keyboard = []
            for f in files[:8]: # Ambil 8 backup terbaru
                keyboard.append([{"text": f"📥 {f}", "callback_data": f"confirm_res_{f}"}])
            keyboard.append([{"text": "🔙 Menu Utama", "callback_data": "btn_main_menu"}])
            kb = {"inline_keyboard": keyboard}
        edit_message(chat_id, message_id, text, kb)

    elif callback_data.startswith("confirm_res_"):
        fname = callback_data.replace("confirm_res_", "")
        text = (
            f"⚠️ <b>KONFIRMASI RESTORE FILE:</b>\n<code>{fname}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tindakan ini akan menimpa database/file saat ini dengan isi arsip backup.\nLanjutkan?"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🔥 YA, RESTORE SEKARANG", "callback_data": f"do_restore_{fname}"}],
                [{"text": "❌ Batalkan", "callback_data": "menu_restore"}]
            ]
        }
        edit_message(chat_id, message_id, text, kb)

    elif callback_data.startswith("do_restore_"):
        fname = callback_data.replace("do_restore_", "")
        send_reply(f"🔄 <b>Sedang melakukan proses pemulihan (restore):</b> <code>{fname}</code>...")
        if restore_func:
            ok, msg_result = restore_func(fname)
            if ok:
                send_reply(f"✅ <b>Restore Berhasil!</b>\n{msg_result}")
            else:
                send_reply(f"❌ <b>Restore Gagal:</b> {msg_result}")
        else:
            send_reply("⚠️ Fungsi restore engine tidak terpasang.")

    # --- TARGET KLIEN & ADMIN ---
    elif callback_data == "btn_list_clients":
        clients = get_clients_from_db()
        keyboard = []
        if not clients:
            text = "🌐 <b>KLIEN TARGET WEB</b>\nBelum ada klien terdaftar."
        else:
            text = f"🌐 <b>STATUS KLIEN TERLINDUNGI ({len(clients)})</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            for domain, backend, name, db_path, status in clients:
                db_info = db_path if db_path else "<i>Belum diset</i>"
                text += f"🟢 <b>{name}</b>\n• Domain: <code>{domain}</code>\n• Backend: <code>{backend}</code>\n• DB Path: <code>{db_info}</code>\n\n"
                keyboard.append([
                    {"text": f"📦 Backup {name}", "callback_data": f"do_bkclient_{domain}"},
                    {"text": f"🗑️ Hapus", "callback_data": f"delcli_{domain}"}
                ])
        keyboard.append([{"text": "➕ Format Tambah Klien", "callback_data": "btn_help_addclient"}])
        keyboard.append([{"text": "🔙 Menu Utama", "callback_data": "btn_main_menu"}])
        edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})

    elif callback_data.startswith("delcli_"):
        target_domain = callback_data.replace("delcli_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM client_targets WHERE domain = ?", (target_domain,))
        conn.commit()
        conn.close()
        send_reply(f"🗑️ Klien <code>{target_domain}</code> berhasil dihapus.")
        handle_callback_action("btn_list_clients", callback_id, chat_id, message_id, perform_backup_func, failover_func, restore_func)

    elif callback_data == "btn_help_addclient":
        text = (
            "➕ <b>CARA MENDAFTARKAN KLIEN & DB TARGET:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Format:\n"
            "<code>/addclient [Nama] [Domain] [BackendURL] [PathDB]</code>\n\n"
            "<b>Contoh (dengan path DB spesifik):</b>\n"
            "<code>/addclient TokoKu store.devgarf.my.id http://127.0.0.1:5020 /var/www/toko/database.sqlite</code>\n\n"
            "<i>(Jika tidak menyertakan PathDB, default SOC metadata yang akan dibackup).</i>"
        )
        kb = {"inline_keyboard": [[{"text": "🔙 Kembali", "callback_data": "btn_list_clients"}]]}
        edit_message(chat_id, message_id, text, kb)

    elif callback_data == "btn_list_admins":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT ip, device_name FROM admin_whitelist")
        admins = c.fetchall()
        conn.close()
        text = f"🛡️ <b>ADMIN IP WHITELIST ({len(admins)})</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        keyboard = []
        for ip, dev in admins:
            text += f"• <code>{ip}</code> ({dev})\n"
            keyboard.append([{"text": f"🚫 Cabut {ip}", "callback_data": f"deladm_{ip}"}])
        keyboard.append([{"text": "🔙 Menu Utama", "callback_data": "btn_main_menu"}])
        edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})

    elif callback_data.startswith("deladm_"):
        target_ip = callback_data.replace("deladm_", "")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM admin_whitelist WHERE ip = ?", (target_ip,))
        conn.commit()
        conn.close()
        send_reply(f"🚫 IP <code>{target_ip}</code> dicabut.")
        handle_callback_action("btn_list_admins", callback_id, chat_id, message_id, perform_backup_func, failover_func, restore_func)

    elif callback_data == "btn_cf_confirm":
        text = "🚨 <b>KONFIRMASI DNS FAILOVER</b> 🚨\nAlihkan DNS Cloudflare ke backup server?"
        kb = {
            "inline_keyboard": [
                [{"text": "🔥 YA, EKSEKUSI", "callback_data": "btn_cf_execute"}],
                [{"text": "❌ Batalkan", "callback_data": "btn_main_menu"}]
            ]
        }
        edit_message(chat_id, message_id, text, kb)

    elif callback_data == "btn_cf_execute":
        send_reply("⚡ <b>Mengeksekusi Cloudflare Failover API...</b>")
        if failover_func():
            send_reply("✅ Failover berhasil dialihkan.")
        else:
            send_reply("⚠️ Gagal mengeksekusi failover.")

def handle_command(text, perform_backup_func, failover_func, restore_func):
    try:
        print(f"[BOT] Memproses perintah: {text}")
        if text in ["/start", "/help", "/menu"]:
            msg = "🤖 <b>GARFIELD SOC COMMAND CENTER</b> 🤖\nPilih menu tindakan di bawah:"
            send_reply(msg, get_main_keyboard())

        elif text.startswith("/addclient"):
            parts = text.split()
            if len(parts) >= 4:
                c_name = parts[1]
                c_domain = parts[2].lower()
                c_backend = parts[3]
                c_db = parts[4] if len(parts) >= 5 else ""
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""INSERT OR REPLACE INTO client_targets 
                             (domain, backend_url, client_name, db_source_path, status, added_at) 
                             VALUES (?, ?, ?, ?, 'ACTIVE', datetime('now'))""", 
                          (c_domain, c_backend, c_name, c_db))
                conn.commit()
                conn.close()
                send_reply(f"🌐 <b>Klien Web Baru Didaftarkan!</b>\n• Nama: {c_name}\n• Domain: <code>{c_domain}</code>\n• Backend: <code>{c_backend}</code>\n• Path DB: <code>{c_db or 'Default'}</code>")
            else:
                send_reply("⚠️ Format salah!\nContoh: <code>/addclient TokoKu store.devgarf.my.id http://127.0.0.1:5020 /var/www/store/db.sqlite</code>")

        elif text.startswith("/addadmin"):
            parts = text.split()
            if len(parts) >= 2:
                ip_to_add = parts[1]
                dev_name = parts[2] if len(parts) > 2 else "Admin"
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO admin_whitelist (ip, device_name, added_at) VALUES (?, ?, datetime('now'))", (ip_to_add, dev_name))
                conn.commit()
                conn.close()
                send_reply(f"🛡️ <b>Admin IP Terdaftar!</b>\n• Device: {dev_name}\n• IP: <code>{ip_to_add}</code>")
            else:
                send_reply("⚠️ Format salah! Contoh: <code>/addadmin 192.168.1.50 LaptopUtama</code>")

        elif text == "/backup":
            handle_callback_action("menu_backup", "", str(CHAT_ID), None, perform_backup_func, failover_func, restore_func)

        elif text == "/restore":
            handle_callback_action("menu_restore", "", str(CHAT_ID), None, perform_backup_func, failover_func, restore_func)

    except Exception as e:
        send_reply(f"❌ <b>Error:</b> <code>{text}</code>\n{e}")

def start_telegram_listener(perform_backup_func, failover_func, restore_func=None):
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] Token Bot Telegram atau Chat ID belum dikonfigurasi.")
        return

    print(f"[+] Telegram Bot Interactive Listener Aktif untuk Owner ID: {CHAT_ID}")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=15"
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("result", []):
                    offset = item["update_id"] + 1

                    if "message" in item:
                        msg = item["message"]
                        sender_id = str(msg.get("chat", {}).get("id", ""))
                        if sender_id == str(CHAT_ID):
                            text = msg.get("text", "").strip()
                            handle_command(text, perform_backup_func, failover_func, restore_func)

                    elif "callback_query" in item:
                        cb = item["callback_query"]
                        cb_id = cb["id"]
                        cb_data = cb.get("data", "")
                        cb_sender_id = str(cb.get("from", {}).get("id", ""))
                        msg_data = cb.get("message", {})
                        chat_id = msg_data.get("chat", {}).get("id")
                        msg_id = msg_data.get("message_id")

                        if cb_sender_id == str(CHAT_ID):
                            handle_callback_action(cb_data, cb_id, chat_id, msg_id, perform_backup_func, failover_func, restore_func)

            elif resp.status_code == 409:
                print("[!] Conflict 409: polling lain aktif. Tunggu...")
                time.sleep(5)
        except Exception as e:
            time.sleep(2)
        time.sleep(0.5)
