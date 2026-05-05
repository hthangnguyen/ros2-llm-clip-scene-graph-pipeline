import torch
import open_clip
import numpy as np

class CLIPEncoder:
    def __init__(self, model_name="ViT-B-32", pretrained="laion2b_s34b_b79k"):
        """Initialize CLIP model. We use ViT-B-32 by default for speed/memory efficiency."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        
    def get_text_embedding(self, text: str) -> np.ndarray:
        """Generate 512-dim (for ViT-B-32) normalized embedding for a text label."""
        text_tokens = self.tokenizer([text]).to(self.device)
        with torch.no_grad(), torch.cuda.amp.autocast():
            text_features = self.model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        # Flatten to 1D array
        return text_features.cpu().numpy().flatten().astype(np.float32)

    def get_embedding_dim(self) -> int:
        """Returns the dimension of the embedding (e.g., 512 or 768)."""
        return self.model.visual.output_dim
