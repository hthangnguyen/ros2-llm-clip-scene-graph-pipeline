import requests
import json
import re
import os

class LLMInterface:
    def __init__(self, model="gemma4:e4b", url="http://localhost:11435/api/generate"):
        self.model = model
        self.url = url
        self.log_file = "logs/llm_debug.log"
        os.makedirs("logs", exist_ok=True)
        
    def _log(self, msg):
        with open(self.log_file, "a") as f:
            f.write(msg + "\n")

    def rank_next_objects(self, current_obj, candidates):
        candidate_str = ", ".join(candidates)
        prompt = f"""
        Current object: {current_obj}
        Candidate next objects: {candidate_str}
        
        Task: Provide a probability score (0.0 to 1.0) for each candidate based on how likely the agent is to visit it next.
        Format: Return ONLY a comma-separated list of {len(candidates)} floats.
        Example: 0.1, 0.5, 0.2, ...
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            # Increased timeout for larger model
            response = requests.post(self.url, json=payload, timeout=25.0)
            if response.status_code == 200:
                raw_text = response.json().get('response', '').strip()
                self._log(f"RAW [{current_obj}]: {raw_text}")
                
                # More robust regex for finding floats
                nums = re.findall(r"0\.\d+|1\.0|1|0", raw_text)
                scores = [float(s) for s in nums]
                
                # If the model gives too many or too few, handle it
                if len(scores) >= len(candidates):
                    return scores[:len(candidates)]
                    
                self._log(f"WARNING: Got {len(scores)} scores for {len(candidates)} candidates.")
            return [1.0/len(candidates)] * len(candidates)
        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            return [1.0/len(candidates)] * len(candidates)
