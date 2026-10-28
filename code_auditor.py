import re

def audit_app_source(filename="app.py"):
    print("=" * 50)
    print("⚡ GARFIELD LOCAL SOURCE CODE AUDITOR v1.0")
    print(f"📂 Membaca file: {filename}")
    print("=" * 50 + "\n")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()

        # Mencari pola rute URL di Flask/FastAPI (cth: @app.route('/...'))
        routes = re.findall(r'@\w+\.route\([\'"]([^\'"]+)[\'"]', code)
        
        print(f"[*] Ditemukan {len(routes)} rute/endpoint terdaftar di dalam kode:")
        for route in routes:
            print(f"    -> {route}")

        print("\n[*] Mencari konfigurasi atau fungsi sensitif...")
        if "sqlite" in code.lower() or "sql" in code.lower():
            print("    [i] Terdeteksi interaksi database di dalam kode.")
        if "debug" in code.lower():
            print("    [i] Periksa konfigurasi mode debug.")

    except FileNotFoundError:
        print(f"[X] File {filename} tidak ditemukan di direktori ini.")
    except Exception as e:
        print(f"[X] Terjadi kesalahan: {e}")

    print("\n" + "=" * 50)
    print("[✓] Audit Kode Selesai.")
    print("=" * 50)

if __name__ == "__main__":
    audit_app_source()
