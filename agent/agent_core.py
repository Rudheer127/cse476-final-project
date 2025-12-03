from agent.api_client import call_model
class CoreAgent:
    def __init__(self):
        pass

    def run(self, question: str, domain: str | None = None) -> str:
            system_msg = "You are a helpful assistant. Answer concisely and correctly."
            result = call_model(question, system=system_msg, temperature=0.0)
            if not result["ok"]:
                return "ERROR"
            return (result["text"] or "").strip()