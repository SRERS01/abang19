import numpy as np

def optimize_resource_exhaustion():
    print("[*] Math Module: Differential Calculus & Curve Optimization")
    
    # Quadratic Resource Function modeling CPU usage curve: f(x) = 0.15*x^2 + 2*x + 5
    # where 'x' represents the number of concurrent multi-threaded exploit requests sent
    def cpu_load_function(x):
        return 0.15 * (x ** 2) + 2 * x + 5

    # Calculus Derivative: f'(x) = 0.3*x + 2 (Calculates instantaneous acceleration of load)
    def calculate_derivative(x):
        return 0.3 * x + 2

    # Predictive Analysis Loop
    thread_test_inputs = [5, 15, 30]
    
    print("=" * 55)
    print("🎯 CALCULUS RESOURCE ACCELERATION METRICS:")
    print("=" * 55)
    for threads in thread_test_inputs:
        current_load = cpu_load_function(threads)
        acceleration_rate = calculate_derivative(threads)
        
        # Predict threads needed to hit 100% crash limit based on derivative slope
        remaining_load = 100 - current_load
        predicted_threads_to_crash = threads + (remaining_load / acceleration_rate) if current_load < 100 else threads
        
        print(f" -> Active Load Threads: {threads:<2} | CPU: {current_load:>5.1f}% | Growth Slope: {acceleration_rate:.2f}")
        if current_load < 100:
            print(f"    [Calculus Prediction] System Exhaustion Limit Estimated At: {predicted_threads_to_crash:.1f} threads.")
        else:
            print("    [!] CRITICAL: Resource exhaustion point already breached.")
        print("-" * 55)

if __name__ == "__main__":
    optimize_resource_exhaustion()
