import numpy as np
from scipy.special import softmax

class IBClusterer:
    def __init__(self, beta=1.0, tau=0.05):
        """Information Bottleneck based clusterer.
        beta: tradeoff between compression and relevance.
        tau: temperature for soft assignment.
        """
        self.beta = beta
        self.tau = tau
        
    def compute_assignment(self, embedding, cluster_centers):
        """Compute soft assignment of an embedding to existing clusters.
        embedding: (D,)
        cluster_centers: (K, D)
        Returns: (K,) assignment probabilities.
        """
        if len(cluster_centers) == 0:
            return np.array([])
            
        # Euclidean distance as a proxy for mutual information in this simplified version
        dists = np.linalg.norm(cluster_centers - embedding, axis=1)
        
        # Softmax over negative distances
        probs = softmax(-dists / self.tau)
        return probs

    def update_center(self, old_center, new_embedding, alpha=0.1):
        """Moving average update for cluster centers."""
        return (1 - alpha) * old_center + alpha * new_embedding
