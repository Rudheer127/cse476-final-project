from agent.api_client import call_model
from agent.strategies import (run_cot,run_cot_with_critique,run_self_consistency,)

class CoreAgent:
    def __init__(self):
        pass

    def run(self, question: str, domain: str | None = None) -> str:
        # Math → self-consistency
        if domain and "math" in domain:
            return run_self_consistency(question, domain)

        # Reasoning-heavy → self-critique
        if domain and ("reasoning" in domain or "logic" in domain):
            return run_cot_with_critique(question, domain)

        # Default → single-pass CoT
        return run_cot(question, domain)
