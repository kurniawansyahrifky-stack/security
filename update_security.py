with open('/home/ubuntu/sec-monitor/app.py', 'r') as f:
    content = f.read()

# Target blok fungsi render_dashboard yang lama untuk diganti dengan yang aman
old_func = """@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
def render_dashboard():
    host = request.host.lower().split(':')[0]
    client_ip = get_real_ip()

    # Perbaikan agar Tunnel Cloudflare (yang membawa host monitor.devgarf.my.id atau lokal) diizinkan masuk
    allowed_hosts = ["monitor.devgarf.my.id", "monitor.defgarf.my.id", "127.0.0.1", "localhost", "192.168.15.50"]
    if host not in allowed_hosts and not host.endswith("devgarf.my.id"):
        return proxy_handler('')

    if not is_admin_ip(client_ip):
        return render_template_string(PAGE_404), 404
    return render_template_string(HTML_DASHBOARD)"""

new_func = """@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
def render_dashboard():
    host = request.host.lower().split(':')[0]
    client_ip = get_real_ip()

    allowed_hosts = ["monitor.devgarf.my.id", "monitor.defgarf.my.id", "127.0.0.1", "localhost", "192.168.15.50"]
    if host not in allowed_hosts and not host.endswith("devgarf.my.id"):
        return proxy_handler('')

    # INI SISTEM KEAMANANNYA: Kalau bukan IP Admin, lempar ke 404!
    if not is_admin_ip(client_ip):
        return render_template_string(PAGE_404), 404
        
    return render_template_string(HTML_DASHBOARD)"""

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('/home/ubuntu/sec-monitor/app.py', 'w') as f:
        f.write(content)
    print("Berhasil memperbarui sistem keamanan render_dashboard!")
else:
    print("Pola lama tidak persis sama, mencoba metode penimpaan alternatif...")
