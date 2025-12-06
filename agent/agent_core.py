from agent.strategies import run_cot, run_self_critique, run_self_consistency

class CoreAgent:
    def __init__(self):
        pass

    def run(self, question: str, domain: str | None = None) -> str:
        q = (question or "").strip()

        is_math = any(char.isdigit() for char in q) and any(op in q for op in "+-*/")

        if is_math:
            answer = run_self_consistency(q)
        else:
            answer = run_self_critique(q)

        if not answer:
            return "ERROR"

        return answer.strip()

