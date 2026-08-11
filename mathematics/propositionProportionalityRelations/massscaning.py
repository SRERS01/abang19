import requests
import sys
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_headers(url):
    headers = {"User-Agent": "Mozilla/5.0 Mass-Header-Auditor/1.0"}
    try:
        # Use HEAD requests to scan fast without downloading full web pages
        resp = requests.head(url, headers=headers, timeout=5, verify=False, allow_redirects=True)
        
        server_header = resp.headers.get("Server", "Unknown")
        powered_by = resp.headers.get("X-Powered-By", "Unknown")
        
        return url, resp.status_code, server_header, powered_by
    except Exception:
        return url, "OFFLINE", None, None

def run_mass_scan(subdomain_file, max_threads=50):
    print(r'''
    [*] Running Multi-Threaded Target Version Harvester...
    ''')
    
    try:
        with open(subdomain_file, "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[-] Error: Could not locate domain target file: {subdomain_file}")
        sys.exit(1)
        
    print(f"[*] File parsed successfully. Loaded {len(targets)} active domains.")
    print(f"[*] Deploying {max_threads} execution channels. Commencing sweep...\n")
    
    vulnerable_candidates = []
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(check_headers, target): target for target in targets}
        
        for future in as_completed(futures):
            url, status, server, php_version = future.result()
            
            if status != "OFFLINE":
                # Check for legacy, unpatched version configurations (e.g., PHP 8.2.16, 8.1.20)
                # This isolates targets from fully updated servers running safe releases like PHP 8.2.32
                if "PHP/8.2." in php_version or "PHP/8.1." in php_version:
                    # Filter out known safe patch levels to avoid false positives
                    if not any(patched in php_version for patched in ["8.2.20", "8.2.32", "8.1.29"]):
                        print(f"[POTENTIAL TARGET ISOLATED] -> {url} | Version: {php_version} | Server: {server}")
                        vulnerable_candidates.append(f"{url} ({php_version})")
                        
    print("\n" + "="*50)
    print(f"[*] Mass Audit complete. Total domains evaluated: {len(targets)}")
    print(f"[*] Total isolated targets matching old version patterns: {len(vulnerable_candidates)}")
    
    if vulnerable_candidates:
        print("\n[+] Actionable Targets to exploit using your specialized tools (like 52331.py):")
        for item in vulnerable_candidates:
            print(f"    -> {item}")
    else:
        print("[-] Scan complete. Zero legacy version signatures found across the target file infrastructure.")
    print("="*50)

if __name__ == "__main__":
    # Create a local file named 'subdomains.txt' with your testing domains before running
    # Example format inside the file:
    # http://192.168.0.10:8080
    # https://testing-sandbox.local
    run_mass_scan("subdomains.txt", max_threads=40)
