import requests
import argparse

def check_access_control(target_url):
    print("=" * 50)
    print("⚡ GARFIELD ACCESS CONTROL AUDITOR v1.0")
    print(f"🎯 Target Endpoint: {target_url}")
    print("=" * 50 + "\n")

    # Skenario 1: Mengakses tanpa cookie / tanpa login sama sekali
    print("[*] Menguji akses tanpa autentikasi (Anonymous Request)...")
    try:
        response = requests.get(target_url, allow_redirects=False, timeout=5)
        print(f"    Status Code Tanpa Login: {response.status_code}")
        
        if response.status_code == 200:
            print("[!] [BAHAYA] Broken Access Control! Halaman sensitif bisa diakses TANPA LOGIN!")
        elif response.status_code in [301, 302, 303]:
            print("[+] Aman: Server mengalihkan (redirect) user yang tidak login ke halaman login.")
        elif response.status_code == 401 or response.status_code == 403:
            print("[+] Aman: Server menolak akses (Unauthorized/Forbidden).")
        else:
            print(f"[-] Status code tidak biasa: {response.status_code}")
    except Exception as e:
        print(f"[X] Gagal terhubung: {e}")

    # Skenario 2: Memeriksa Information Disclosure pada Header HTTP
    print("\n[*] Menganalisis Security Headers Server...")
    try:
        response = requests.get(target_url, timeout=5)
        headers = response.headers
        
        security_headers = [
            'Server', 'X-Powered-By', 'X-Content-Type-Options', 
            'X-Frame-Options', 'Content-Security-Policy'
        ]
        
        for h in security_headers:
            if h in headers:
                print(f"    [i] {h}: {headers[h]}")
            else:
                print(f"    [-] Header '{h}' tidak ditemukan (Potensi Kurang Pengamanan)")
                
    except Exception as e:
        print(f"[X] Gagal membaca header: {e}")
    
    print("\n" + "=" * 50)
    print("[✓] Audit Access Control Selesai.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Access Control & Header Auditor")
    parser.add_argument("-u", "--url", required=True, help="URL target (cth: http://127.0.0.1:8080/dashboard)")
    args = parser.parse_args()
    
    check_access_control(args.url)
