from agent.api_client import call_model
from agent.strategies import run_cot
class CoreAgent:
    def __init__(self):
        pass

    def run(self, question: str, domain: str | None = None) -> str:
        # For now, everything goes through the CoT strategy
        return run_cot(question, domain)