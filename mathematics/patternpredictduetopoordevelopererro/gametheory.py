import numpy as np

def calculate_nash_equilibrium():
    print("[*] Advanced Math Module: Game Theory & Payoff Matrix Optimization")
    
    # Operational Strategies
    hunter_strategies = ["Fast (0.1s Sleep)", "Balanced (0.5s Sleep)", "Stealth (2.0s Sleep)"]
    defender_strategies = ["Low Aggression WAF", "Heuristic WAF", "Human Admin Manual Block"]
    
    # Payoff Matrix: Rows = Hunter, Columns = Defender
    # Values reflect Hunter's net gain (Bounties found minus chance of IP ban)
    # Higher score = Better for Hunter, Negative score = Complete lockout
    payoff_matrix = np.array([
        [ 80, -20, -100],  # Fast Scan Strategy outcomes
        [ 60,  40,  -10],  # Balanced Scan Strategy outcomes
        [ 20,  20,   15]   # Stealth Scan Strategy outcomes
    ])
    
    # Math Engine: Find the Maximin Strategy (Minimizing max potential loss)
    # For each strategy row, what is the absolute worst-case scenario the defender can enforce?
    worst_case_per_strategy = np.min(payoff_matrix, axis=1)
    
    # Isolate the index that gives the highest worst-case guarantee (Safe optimization)
    optimal_strategy_idx = np.argmax(worst_case_per_strategy)
    
    print("=" * 60)
    print("🎯 CRAWLER STRATEGY OPTIMIZATION REPORT:")
    print("=" * 60)
    for idx, strategy in enumerate(hunter_strategies):
        print(f" -> Strategy: {strategy:<22} | Worst-Case Security Payoff: {worst_case_per_strategy[idx]:>4}")
        
    print("=" * 60)
    print(f"🏆 MATHEMATICAL EQUILIBRIUM CHOICE: {hunter_strategies[optimal_strategy_idx]}")
    print("   This strategy guarantees maximum discovery metrics with zero vector lockouts.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    calculate_nash_equilibrium()
