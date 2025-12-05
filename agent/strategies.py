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
    """
    Chain-of-Thought strategy. Ask the model to think step-by-step,
    then return only the final answer.
    """

    # Tell the model to think step-by-step but finish with a single "FINAL ANSWER:" line
    system_msg = (
        "You are a careful problem solver.\n"
        "You MUST output your final answer in the form:\n"
        "FINAL ANSWER: <answer>\n\n"
        "Do NOT include explanation after the final answer.\n"
        "Keep reasoning concise and place it BEFORE the FINAL ANSWER line."
        "Your final answer must be short — a word, phrase, number, or name."
    )

    # Call the model once
    result = call_model(
        question,
        system=system_msg,
        temperature=0.0,
    )

    # If the call failed, return a simple error marker
    if not result.get("ok"):
        return "ERROR"

    # Clean up the text
    text = (result.get("text") or "").strip()
    if not text:
        return "ERROR"

    return extract_final_answer(text)



def run_self_critique(question: str, domain: str | None = None) -> str:
    """
    Self-Critique: I get an initial answer, then ask the model to verify and correct it.
    """
    # First: get the initial answer
    initial = run_cot(question, domain)
    if not initial or initial == "ERROR":
        return initial

    system_msg = (
        "You will see a question and a proposed answer.\n"
        "Evaluate whether the answer is correct.\n"
        "If it is wrong, compute the correct answer.\n"
        "Think step by step, but end with a single line starting with "
        "'FINAL ANSWER:' followed by the corrected or confirmed answer."
    )

    prompt = (
        f"Question:\n{question}\n\n"
        f"Proposed Answer:\n{initial}\n\n"
        "If the proposed answer is correct, repeat it. "
        "If incorrect, provide the correct one."
    )

    result = call_model(prompt, system=system_msg, temperature=0.0)

    if not result.get("ok"):
        return initial  # Safe fallback

    text = (result.get("text") or "").strip()
    if not text:
        return initial

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

