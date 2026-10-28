import requests
import argparse
from bs4 import BeautifulSoup

def inspect_endpoint(target_url):
    print("=" * 50)
    print("⚡ GARFIELD ENDPOINT DEEP INSPECTOR v1.0")
    print(f"🎯 Target: {target_url}")
    print("=" * 50 + "\n")

    try:
        print("[*] Mengirim HTTP GET request...")
        response = requests.get(target_url, timeout=5)
        
        print(f"[+] Status Code : {response.status_code}")
        print(f"[+] Content-Type: {response.headers.get('Content-Type', 'Tidak diketahui')}")
        print(f"[+] Ukuran Data : {len(response.text)} bytes\n")

        if response.status_code == 200:
            print("--- [ Preview Konten / Teks Halaman ] ---")
            # Tampilkan 400 karakter pertama agar tidak terlalu panjang
            print(response.text[:400] if response.text else "[Kosong]")
            print("-----------------------------------------")

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Periksa apakah ada form input
            forms = soup.find_all('form')
            if forms:
                print(f"\n[!] Ditemukan {len(forms)} Form pada halaman ini:")
                for i, f in enumerate(forms):
                    action = f.get('action', '#')
                    method = f.get('method', 'GET').upper()
                    print(halaman := f"    - Form #{i+1} | Method: {method} | Action: {action}")
                    inputs = f.find_all(['input', 'select', 'textarea'])
                    for inp in inputs:
                        name = inp.get('name', 'tanpa_nama')
                        itype = inp.get('type', 'text')
                        print(halaman := f"      * Input field -> Name: '{name}' (Type: {itype})")
            else:
                print("\n[-] Tidak ada form HTML interaktif di halaman ini.")
        elif response.status_code in [301, 302]:
            print(f"[+] Halaman melakukan Redirect ke: {response.headers.get('Location')}")
        else:
            print(f"[-] Halaman mengembalikan respons khusus: {response.status_code}")

    except Exception as e:
        print(f"[X] Gagal mengakses target: {e}")

    print("\n" + "=" * 50)
    print("[✓] Inspeksi Selesai.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Endpoint Deep Inspector")
    parser.add_argument("-u", "--url", required=True, help="URL target lengkap (cth: http://127.0.0.1:8080/bank-transfer)")
    args = parser.parse_args()
    
    inspect_endpoint(args.url)
