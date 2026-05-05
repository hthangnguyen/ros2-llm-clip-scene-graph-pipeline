import numpy as np

class CTMCModel:
    def __init__(self, num_states: int):
        self.num_states = num_states
        # Q matrix (transition rates)
        # q_ij >= 0 for i != j
        # q_ii = -sum(q_ij)
        self.Q = np.zeros((num_states, num_states))
        
    def set_rates(self, rates_matrix: np.ndarray):
        """Set the transition rates and update diagonal."""
        self.Q = rates_matrix.copy()
        for i in range(self.num_states):
            self.Q[i, i] = 0.0 # Clear diagonal
            self.Q[i, i] = -np.sum(self.Q[i, :])
            
    def compute_transition_probs(self, dt: float) -> np.ndarray:
        """Compute the transition probability matrix P(t) = exp(Q * t)."""
        from scipy.linalg import expm
        return expm(self.Q * dt)

def compute_compatibility(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Cosine similarity between two CLIP embeddings."""
    # Already normalized in CLIPEncoder, so just dot product
    return float(np.dot(emb1, emb2))
