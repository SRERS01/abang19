import math
from collections import Counter

def calculate_shannon_entropy(token_string):
    """Calculates the thermodynamic entropy density of a target data string."""
    # 1. Count the frequency of each distinct character in the sequence
    total_chars = len(token_string)
    if total_chars == 0:
        return 0.0
        
    char_counts = Counter(token_string)
    
    # 2. Information Theory Engine: Sum over -p(x) * log2(p(x))
    entropy_bits = 0.0
    for count in char_counts.values():
        probability = count / total_chars
        entropy_bits -= probability * math.log2(probability)
        
    return entropy_bits

def audit_session_tokens():
    print("[*] Advanced Math Module: Information Theory & Shannon Entropy")
    
    # Target Token Database Matrix gathered during your endpoint crawl
    token_audit_matrix = {
        "Secure_JWT_Token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.S2ZsZWRyM3M0",
        "Cloudflare_Session": "cf_8a7fd853ac1d4ac7b9dabf17bbbfdf0a26e7a7fd",
        "Weak_Custom_Cookie": "admin_user_session_1786362319_00014421_session"
    }
    
    print("=" * 60)
    print("🎯 ENTROPY DENSITY ANALYSIS REPORT:")
    print("=" * 60)
    for label, token in token_audit_matrix.items():
        entropy_score = calculate_shannon_entropy(token)
        
        # Security Boundary Logic
        if entropy_score < 4.2:
            status = "🚨 VULNERABLE: Low Entropy / Predictable Code Sequence"
        else:
            status = "✅ SECURE: High Entropy Cryptographic Randomness"
            
        print(f" -> [{label:<18}] Score: {entropy_score:.3f} bits/char")
        print(f"    Verdict: {status}\n")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    audit_session_tokens()
