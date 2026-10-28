import requests
import re
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_apis(target_url):
    print("=" * 50)
    print("⚡ GARFIELD API & SCRIPT EXTRACTOR v1.0")
    print(f"🎯 Target: {target_url}")
    print("=" * 50 + "\n")

    try:
        response = requests.get(target_url, timeout=5)
        if response.status_code != 200:
            print(f"[X] Gagal mengakses target. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Mencari semua link eksternal atau file JavaScript yang dimuat
        scripts = soup.find_all('script')
        print(f"[*] Ditemukan {len(scripts)} blok/file <script> di halaman.")

        internal_links = set()
        
        # Regex sederhana untuk mencari pola URL/path API (misal: /api/..., /v1/..., dll)
        api_pattern = re.compile(r'[\"\'](/?[a-zA-Z0-9_\-/]*(?:api|v1|v2|status|metrics|data|vm|host)[a-zA-Z0-9_\-/]*)[\"\']')

        for idx, script in enumerate(scripts):
            script_content = script.string if script.string else ""
            src = script.get('src')
            
            if src:
                full_script_url = urljoin(target_url, src)
                print(halaman := f"    [i] Memuat file script eksternal: {src}")
                try:
                    js_resp = requests.get(full_script_url, timeout=3)
                    script_content = js_resp.text
                except:
                    pass

            # Cari kecocokan pola endpoint API di dalam teks JavaScript atau HTML
            matches = api_pattern.findall(script_content + response.text)
            for match in matches:
                if len(match) > 1 and not match.endswith('.js') and not match.endswith('.css'):
                    internal_links.add(match)

        print("\n[*] Potensi Endpoint API / Path Tersembunyi yang Ditemukan:")
        if internal_links:
            for link in sorted(internal_links):
                full_endpoint = urljoin(target_url, link)
                print(f"    -> {full_endpoint}")
                
                # Uji coba cepat apakah endpoint API tersebut merespons
                try:
                    api_test = requests.get(full_endpoint, timeout=3)
                    print(halaman := f"       [Status: {api_test.status_code}] - Panjang Konten: {len(api_test.content)} bytes")
                    if api_test.status_code == 200 and len(api_test.text) < 500:
                        print(f"       [Preview Data]: {api_test.text[:150]}")
                except:
                    pass
        else:
            print("    [-] Tidak ada pola endpoint API spesifik yang otomatis terdeteksi.")

    except Exception as e:
        print(f"[X] Terjadi kesalahan: {e}")

    print("\n" + "=" * 50)
    print("[✓] Ekstraksi API Selesai.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API & Script Extractor")
    parser.add_argument("-u", "--url", required=True, help="URL target (cth: http://127.0.0.1:8080/dashboard)")
    args = parser.parse_args()
    
    extract_apis(args.url)
