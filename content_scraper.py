import requests
import re
import argparse
from bs4 import BeautifulSoup

def scrape_and_analyze(target_url):
    print("=" * 50)
    print("⚡ GARFIELD CONTENT SCRAPER & SENSITIVE DATA FINDER")
    print(f"🎯 Target: {target_url}")
    print("=" * 50 + "\n")

    try:
        response = requests.get(target_url, timeout=5)
        if response.status_code != 200:
            print(f"[X] Gagal mengakses halaman. Status code: {response.status_code}")
            return

        print("[*] Berhasil mengambil konten halaman. Menganalisis elemen HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Menampilkan judul halaman dan teks utama
        page_title = soup.title.string if soup.title else "Tidak ada judul"
        print(f"    [i] Judul Halaman: {page_title.strip()}")

        # 2. Mencari form tersembunyi atau input yang mungkin terlewat
        forms = soup.find_all('form')
        print(f"    [i] Ditemukan {len(forms)} buah Form HTML di halaman ini.")
        for idx, form in enumerate(forms):
            action = form.get('action', 'Tidak ada action')
            method = form.get('method', 'GET')
            print(f"        - Form #{idx+1} | Method: {method.upper()} | Action: {action}")

        # 3. Mencari pola teks sensitif menggunakan Regular Expression (Regex)
        print("\n[*] Memindai teks sensitif (Token, Password, Key, Secret)...")
        page_text = response.text
        
        # Pola pencarian kata kunci rahasia
        keywords = ['password', 'secret', 'api_key', 'token', 'admin', 'credential']
        found_sensitive_data = False

        for word in keywords:
            # Mencari baris yang mengandung keyword tersebut
            matches = re.findall(rf".{{0,30}}{word}.{{0,30}}", page_text, re.IGNORECASE)
            if matches:
                found_sensitive_data = True
                print(halaman := f"    [!] Kata kunci '{word}' ditemukan dalam teks:")
                for match in set(matches):
                    print(f"        -> ...{match.strip()}...")

        if not found_sensitive_data:
            print("    [-] Tidak ditemukan kata kunci sensitif yang mencolok secara pola teks.")

    except Exception as e:
        print(f"[X] Terjadi kesalahan saat scraping: {e}")

    print("\n" + "=" * 50)
    print("[✓] Analisis Konten Selesai.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Scraper & Sensitive Data Finder")
    parser.add_argument("-u", "--url", required=True, help="URL target (cth: http://127.0.0.1:8080/dashboard)")
    args = parser.parse_args()
    
    scrape_and_analyze(args.url)
