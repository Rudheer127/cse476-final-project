from agent.strategies import run_cot, run_self_critique, run_self_consistency, is_numeric_question
import re

class CoreAgent:
    def __init__(self):
        pass

    def run(self, question: str, domain: str | None = None) -> str:
        q = (question or "").strip()

        # Math detection rules
        main_q = q.split("Context:", 1)[0].strip().lower()
        operators = "+-*/×÷"
        math_keywords = [
            "solve", "evaluate", "calculate", "compute",
            "sum", "difference", "product", "quotient",
            "ratio", "percent", "percentage",
            "square", "cube", "root",
            "divided", "times", "=",
            "how many", "how much", "total", "altogether"
        ]

        num_count = sum(ch.isdigit() for ch in main_q)
        has_operator = any(op in main_q for op in operators)
        has_keyword = any(re.search(rf"\b{re.escape(kw)}\b", main_q) for kw in math_keywords)

        # Only treat as math if the question contains math signals
        is_math = (
            has_operator
            or has_keyword
            or num_count >= 2
        )

        # Route to correct strategy
        if is_math:
            answer = run_self_consistency(q, domain)
        else:
            answer = run_self_critique(q, domain)

        if not answer:
            return "ERROR"

        return answer.strip()
