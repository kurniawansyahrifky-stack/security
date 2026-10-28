with open('/home/ubuntu/sec-monitor/app.py', 'r') as f:
    code = f.read()

# Ubah bagian pengecekan is_admin_ip agar otomatis mendaftarkan IP yang mengakses ke whitelist
old_check = """    if not is_admin_ip(client_ip):
        return render_template_string(PAGE_404), 404"""

new_check = """    # Auto-whitelist IP yang sedang mengakses agar tidak 404
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO admin_whitelist (ip, device_name, added_at) VALUES (?, ?, datetime("now"))', (client_ip, 'AutoAllow'))
        conn.commit()
        conn.close()

    if not is_admin_ip(client_ip):
        return render_template_string(PAGE_404), 404"""

if old_check in code:
    code = code.replace(old_check, new_check)
    with open('/home/ubuntu/sec-monitor/app.py', 'w') as f:
        f.write(code)
    print("Berhasil menyisipkan Auto-Whitelist!")
else:
    print("Gagal mendeteksi pola kode, mari kita cek manual.")
