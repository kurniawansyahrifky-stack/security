import requests
import json
import argparse

def analyze_logs(api_url):
    print("=" * 50)
    print("⚡ GARFIELD LOG DATA ANALYZER v1.0")
    print(f"🎯 Target API: {api_url}")
    print("=" * 50 + "\n")

    try:
        print("[*] Mengambil data dari endpoint API...")
        response = requests.get(api_url, timeout=5)
        
        if response.status_code != 200:
            print(f"[X] Gagal mengambil data. Status code: {response.status_code}")
            return

        print(f"[+] Berhasil terhubung! (Status: {response.status_code})\n")
        
        # Coba parsing sebagai JSON (karena ini endpoint /api/)
        try:
            data = response.json()
            print("[*] Data berformat JSON terdeteksi. Menampilkan secara terstruktur:\n")
            print(json.dumps(data, indent=4))
        except json.JSONDecodeError:
            # Jika bukan JSON, tampilkan sebagai teks mentah biasa
            print("[*] Data berformat teks biasa (Plain Text/HTML):\n")
            print(response.text)

    except Exception as e:
        print(f"[X] Terjadi kesalahan saat mengakses API: {e}")

    print("\n" + "=" * 50)
    print("[✓] Analisis Log Selesai.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log Data Analyzer")
    parser.add_argument("-u", "--url", required=True, help="URL endpoint API log (cth: http://127.0.0.1:8080/api/logs)")
    args = parser.parse_args()
    
    analyze_logs(args.url)
