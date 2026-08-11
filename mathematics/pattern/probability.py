import numpy as np

def predict_markov_state():
    print("[*] Math Module: Probability & Stochastic Markov Processes")
    
    # Define state indices
    states = {0: "Unpatched (Vulnerable)", 1: "Testing Patch", 2: "Fully Patched (Safe)"}
    
    # Transition Probability Matrix (P)
    # P[i][j] represents the probability of moving from state i to state j over a 30-day cycle
    # Row 0: If unpatched, 10% stay unpatched, 60% move to testing, 30% patch instantly.
    P = np.array([
        [0.10, 0.60, 0.30],
        [0.00, 0.20, 0.80],
        [0.00, 0.00, 1.00] # Patched state is an absorbing state (stays 100% patched)
    ])
    
    # Current vector state: 100% chance a newly discovered system is currently State 0
    current_state_vector = np.array([1.0, 0.0, 0.0])
    
    # Matrix Multiplication over 3 development cycles (P cubed: P^3)
    three_cycle_matrix = np.linalg.matrix_power(P, 3)
    future_prediction = current_state_vector.dot(three_cycle_matrix)
    
    print("=" * 55)
    print("🎯 90-DAY INFRASTRUCTURE STATE PREDICTIONS:")
    print("=" * 55)
    for idx, prob in enumerate(future_prediction):
        print(f" -> System Transitioning To [{states[idx]:<21}]: {prob * 100:.2f}% Probability")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    predict_markov_state()
