from agent.api_client import call_model
from evaluation import extract_number

def extract_final_answer(text: str) -> str:
    """
    Extracts the final answer from a model response.
    Looks for a 'FINAL ANSWER:' line; otherwise returns last non-empty line.
    """
    if not text:
        return "ERROR"

    prefix = "FINAL ANSWER:"
    lines = text.strip().splitlines()

    # Look for explicit FINAL ANSWER line
    for raw in lines:
        line = raw.strip()
        if prefix in line:
            _, after = line.split(prefix, 1)
            if after.strip():
                return after.strip()

    # Fallback: use last non-empty line
    for raw in reversed(lines):
        line = raw.strip()
        if line:
            return line

    return text.strip()


def run_cot(question: str, domain: str | None = None) -> str:
    # I ask the model to reason step-by-step using a simple prompt. 
    cot_prompt = (
        "Think step by step and solve the question.\n"
        "Question: " + question + "\n"
        "Give your reasoning first.\n"
        "Then write the final answer on a new line starting with: FINAL ANSWER:\n"
    )

    # I call the model with this reasoning prompt.
    result = call_model(cot_prompt, temperature=0.0)
    if not result.get("ok"):
        return "ERROR"

    reasoning_text = (result.get("text") or "").strip()
    if not reasoning_text:
        return "ERROR"

    # I extract only the final answer line.
    final = extract_final_answer(reasoning_text)
    return final


def run_self_critique(question: str, domain: str | None = None) -> str:
    """
    Self-Critique: I get an initial answer, then ask the model to verify and correct it.
    """
    # First: get the initial answer
    initial = run_cot(question, domain)
    if not initial or initial == "ERROR":
        return initial

    critique_prompt = (
        "I will show a question and a proposed answer.\n"
        "I think step by step and decide if the answer is correct.\n"
        "If it's wrong, I fix it.\n\n"
        "Question:\n" + question + "\n\n"
        "Proposed Answer:\n" + initial + "\n\n"
        "After thinking, I write the corrected final answer on a new line starting with FINAL ANSWER:\n"
    )

    result = call_model(critique_prompt, temperature=0.0)
    if not result.get("ok"):
        return initial

    text = (result.get("text") or "").strip()
    final = extract_final_answer(text)
    return final or initial

def run_self_consistency(question: str, domain: str | None = None, num_samples: int = 3) -> str:
    """
    Self-Consistency: I run CoT multiple times and take the most common answer.
    This filters out random errors by majority voting.
    """
    answers = []

    # Run CoT multiple times to get different attempts
    for _ in range(num_samples):
        ans = run_cot(question, domain)
        if ans:
            answers.append(ans)

    if not answers:
        return "ERROR"

    # For numeric answers, I use median to be robust against outliers
    nums = []
    for a in answers:
        n = extract_number(a)
        if n is not None:
            nums.append(float(n))

    if len(nums) >= 2:
        nums.sort()
        mid = nums[len(nums)//2]
        return str(int(mid)) if mid.is_integer() else str(mid)

    # For text answers, I use majority voting
    counts = {}
    for a in answers:
        counts[a] = counts.get(a, 0) + 1

    best = max(counts.items(), key=lambda x: x[1])[0]
    return best

