import sys
import os
import subprocess

if len(sys.argv) < 3:
    print("\033[1;31m[-] Error: Missing arguments.\033[0m")
    print("Usage: python3 matrix_verifier01.py <target-domain> <path_list_file.txt>")
    sys.exit(1)

# Fix the array index mapping definitions explicitly
TARGET_DOMAIN = sys.argv[1]
log_file = sys.argv[2]

print("==================================================")
print("    AUTOMATED LIVE MATRIX VERIFICATION ENGINE    ")
print(f"    Target Domain: {TARGET_DOMAIN}")
print(f"    Processing Log: {log_file}")
print("==================================================")

if not os.path.exists(log_file):
    print(f"\033[1;31m[-] Error: File '{log_file}' not found.\033[0m")
    sys.exit(1)

with open(log_file, "r") as f:
    paths = [line.strip() for line in f if line.strip()]

critical_signatures = [".env", ".git", "backup", "config", "admin", "secret", ".sql"]

for path in set(paths):
    if not path.startswith("/"):
        path = "/" + path
        
    low_path = path.lower()
    if any(sig in low_path for sig in critical_signatures):
        url = f"https://{TARGET_DOMAIN}{path}"
        print(f"\n[*] Probing Node: {path}")
        
        # Execute live curl check automatically following redirects
        cmd = f"curl -i -s -L -k -m 10 \"{url}\""
        try:
            output = subprocess.check_output(cmd, shell=True, text=True)
            
            # Split the response content cleanly by lines
            lines = output.splitlines()
            status_code = "Unknown"
            
            # Read backwards to find the last valid HTTP response line from the final redirected server hop
            for line in lines:
                if line.startswith("HTTP/"):
                    parts = line.split()
                    if len(parts) > 1:
                        status_code = parts[1]
            
            # Check content characteristics
            is_html = "<html" in output.lower() or "<doctype" in output.lower()
            
            print(f"  └── Final Destination HTTP Status: {status_code}")
            
            if status_code == "200" and not is_html:
                print(f"  └── \033[1;41m[CRITICAL FINDING]\033[0m Raw configuration data exposed! Document instantly.")
            elif status_code == "200" and is_html and (".env" in low_path or ".sql" in low_path or "backup" in low_path):
                print(f"  └── \033[1;33m[-] Mitigated (Soft 404):\033[0m Returned HTML main application landing page instead of a raw configuration file. False Positive.")
            elif status_code == "404":
                print(f"  └── [-] Secure: Path does not exist on server (404).")
            else:
                print(f"  └── [-] Handled / Closed Response (Status: {status_code})")
                
        except Exception as e:
            print(f"  └── [-] Verification Probe Exception Error: {str(e)}")

print("\n==================================================\n")

