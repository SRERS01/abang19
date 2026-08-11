import requests
import sys

# Equivalence Relation Mapping: Testing if User B can access User A's data class
def check_idor(base_url, user_a_token, user_b_token, resource_ids):
    print(r'''
    [*] Mapping Role Relations & IDOR Matrix...
    ''')
    
    # Establish a session representing User B (The Unauthorized Attacker role)
    session_b = requests.Session()
    session_b.headers.update({
        "Authorization": f"Bearer {user_b_token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QA-Validator/1.0"
    })

    for resource_id in resource_ids:
        # Construct the unique object endpoint path
        target_url = f"{base_url.rstrip('/')}/api/v1/users/account/{resource_id}"
        
        try:
            # Attempt to read User A's private resource using User B's authentication tokens
            resp = session_b.get(target_url, timeout=10, verify=False)
            
            print(f"[+] Testing Object Path: .../account/{resource_id}")
            print(f"[+] Status Code: {resp.status_code}")
            
            # If a separate user can successfully read or modify another user's restricted ID class
            if resp.status_code == 200 and "private_data" in resp.text:
                print(f"[CRITICAL VULNERABILITY CONFIRMED] IDOR found on resource: {resource_id}")
                print(f"[+] Leak Output:\n{resp.text}\n")
            elif resp.status_code in:
                print("[-] Access Denied. Object boundaries correctly enforced by the server.\n")
            else:
                print("[-] Status 200 received but no clear object leak detected.\n")
                
            print("-" * 50)
        except Exception as e:
            print(f"[-] Connection failed for resource {resource_id}: {e}")

if __name__ == "__main__":
    # Replace these placeholders with your authorized staging/lab headers
    TARGET_HOST = "https://your-authorized-target.com"
    TOKEN_A = "USER_A_JWT_TOKEN_HERE"
    TOKEN_B = "USER_B_JWT_TOKEN_HERE"
    OBJECT_LIST = ["10441", "10442", "10443", "10444"] # Harvested IDs belonging to User A
    
    check_idor(TARGET_HOST, TOKEN_A, TOKEN_B, OBJECT_LIST)
