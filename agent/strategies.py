from agent.api_client import call_model

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
        "You are a careful problem solver. "
        "Think step by step, but end with a line that starts with "
        "'FINAL ANSWER:' followed by the final answer only."
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

    # Look for the explicit FINAL ANSWER line
    lines = text.splitlines()
    prefix = "FINAL ANSWER:"

    for raw_line in lines:
        line = raw_line.strip()
        if prefix in line:
            # Take whatever comes after the prefix
            _, after = line.split(prefix, 1)
            answer = after.strip()
            if answer:
                return answer

    # If the model didn't follow instructions, use the last non-empty line
    for raw_line in reversed(lines):
        line = raw_line.strip()
        if line:
            return line

    # Last fallback: return the whole text
    return text

def run_cot_with_critique(question: str, domain: str | None = None) -> str:
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
    answers = []

    for _ in range(num_samples):
        ans = run_cot(question, domain)
        if ans:
            answers.append(ans)

    if not answers:
        return "ERROR"

    # If numeric domain, try numeric majority/median
    nums = []
    for a in answers:
        n = extract_number(a)
        if n is not None:
            nums.append(float(n))

    if len(nums) >= 2:
        # Use median value
        nums.sort()
        mid = nums[len(nums)//2]
        return str(int(mid)) if mid.is_integer() else str(mid)

    # Otherwise majority vote on strings
    counts = {}
    for a in answers:
        counts[a] = counts.get(a, 0) + 1

    best = max(counts.items(), key=lambda x: x[1])[0]
    return best

