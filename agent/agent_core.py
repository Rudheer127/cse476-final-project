from agent.api_client import call_model
from agent.strategies import (run_cot,run_cot_with_critique,run_self_consistency,)

class CoreAgent:
    def __init__(self):
        pass

    def run(self, question: str, domain: str | None = None) -> str:
        if domain and "math" in domain:
            return run_self_consistency(question, domain)
        
        # Default to CoT + Critique for other domains (or if domain is None)
        return run_cot_with_critique(question, domain)
