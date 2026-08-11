import networkx as nx
import numpy as np

def predict_crawler_flow():
    print("[*] Math Module: Graph Theory & Directed Endorelations")
    
    # Create a directed network graph representing website routing links
    G = nx.DiGraph()
    
    # Relations: (Page_A, Page_B) means Page A links directly to Page B
    web_relations = [
        ("/", "/login.php"),
        ("/", "/blogs"),
        ("/blogs", "/blogs/page-1"),
        ("/blogs/page-1", "/"),
        ("/login.php", "/dashboard/"),
        ("/dashboard/", "/admin/"),
        ("/dashboard/", "/logout")
    ]
    G.add_edges_from(web_relations)
    
    # Calculate adjacency matrix to check structural boundaries
    adj_matrix = nx.to_numpy_array(G)
    print(f"[+] Structural Adjacency Matrix Shapes calculated:\n{adj_matrix}\n")
    
    # Math Engine: Stationary distribution via PageRank (Eigenvector Centrality)
    # Predicts the statistical steady-state probability of a visitor landing on any node
    predictions = nx.pagerank(G, alpha=0.85)
    
    print("=" * 55)
    print("🎯 PREDICTED CRAWL PROBABILITIES (Ranked Highest to Lowest):")
    print("=" * 55)
    for node, prob in sorted(predictions.items(), key=lambda x: x[1], reverse=True):
        print(f" -> Path: {node:<20} | Probability of Next Hit: {prob * 100:.2f}%")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    predict_crawler_flow()
