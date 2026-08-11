import numpy as np
from scipy.linalg import eigh

def detect_anomaly_pca():
    print("[*] Math Module: Linear Algebra (Covariance Matrix & Eigenvalues)")
    
    # Matrix Dataset: 5 sample connections with features [Response_Time_ms, Body_Size_bytes]
    # Row 4 simulates a malicious heavy exploit payload injection pattern
    traffic_matrix = np.array([,
 ,
 ,
 , # Extreme statistical anomaly (Exploit trace)
        [125, 480]
    ], dtype=float)
    
    # 1. Standardize the vector data (Mean centering)
    mean_vectors = np.mean(traffic_matrix, axis=0)
    centered_matrix = traffic_matrix - mean_vectors
    
    # 2. Compute the Covariance Matrix
    covariance_matrix = np.cov(centered_matrix, rowvar=False)
    
    # 3. Solve for Eigenvalues and Eigenvectors (Principal Axis Transformation)
    eigenvalues, eigenvectors = eigh(covariance_matrix)
    
    # Isolate the primary component (The Eigenvector with the maximum eigenvalue variance)
    primary_vector = eigenvectors[:, np.argmax(eigenvalues)]
    
    # Project data onto our mathematical pattern line to calculate anomaly scores
    pattern_projections = centered_matrix.dot(primary_vector)
    
    print("=" * 55)
    print("🎯 LINEAR ALGEBRA ANOMALY DETECTION SCORES:")
    print("=" * 55)
    for idx, score in enumerate(pattern_projections):
        status = "🚨 CRITICAL EXPLOIT PATTERN" if abs(score) > 1000 else "✅ Normal User Traffic"
        print(f" -> Connection Vector [{idx}]: Projection Score: {score:>8.2f} | {status}")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    detect_anomaly_pca()
