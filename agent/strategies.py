from agent.api_client import call_model
from evaluation import extract_number

def extract_final_answer(text: str) -> str:
    """
    Extracts the final answer from a model response.
    I first look for a 'FINAL ANSWER:' line; if I don't find it,
    I use the last non-empty line. Then I clean it up a bit.
    """
    if not text:
        return "ERROR"

    prefix = "FINAL ANSWER:"
    lines = text.strip().splitlines()

    answer = None

    for raw in lines:
        line = raw.strip()
        if prefix in line:
            _, after = line.split(prefix, 1)
            candidate = after.strip()
            if candidate:
                answer = candidate
                break

    if answer is None:
        for raw in reversed(lines):
            line = raw.strip()
            if line:
                answer = line
                break

    if answer is None:
        answer = text.strip()

    cleaned = answer.strip()

    cleaned = cleaned.strip('"').strip("'")

    if "FINAL ANSWER" in cleaned:
        cleaned = cleaned.split("FINAL ANSWER")[0].strip()

    core = cleaned.strip("()[] .")
    if len(cleaned) <= 4 and len(core) == 1 and core.upper() in "ABCD":
        cleaned = core.upper()

    if any(ord(c) > 127 for c in cleaned):
        num = extract_number(cleaned)
        if num is not None and str(num).strip() != "":
            cleaned = str(num).strip()
    return cleaned.strip()

def run_cot(question: str, domain: str | None = None) -> str:
    # I clean the question text first.
    q = (question or "").strip()

    # I detect if this looks like a multiple-choice question.
    is_mc = "Options:" in q and "(A" in q

    # I detect if this looks like a yes/no question.
    is_yesno = q.lower().startswith("is ") or q.lower().startswith("does ") or q.lower().startswith("do ")

    # I detect if this looks like a numeric / math question.
    has_digit = any(ch.isdigit() for ch in q)

    if is_mc:
        cot_prompt = (
            "You are answering a multiple-choice question.\n"
            "Choose the single best option from A, B, C, or D.\n"
            "Do NOT show any reasoning or explanation.\n"
            "Respond on one line in this exact format:\n"
            "FINAL ANSWER: <letter>\n\n"
            f"Question:\n{q}\n"
        )

    elif is_yesno:
        cot_prompt = (
            "Answer the following question with Yes or No only.\n"
            "Do NOT show any reasoning or explanation.\n"
            "Respond on one line, using exactly one of these two forms:\n"
            "FINAL ANSWER: Yes\nor\nFINAL ANSWER: No\n\n"
            f"Question:\n{q}\n"

        )

    elif has_digit:
        # For math questions I want the model to be extra careful,
        # but still only show the final answer.
        cot_prompt = (
            "Solve the following math question carefully.\n"
            "Do NOT show any reasoning or explanation.\n"
            "Respond on one line in this exact format:\n"
            "FINAL ANSWER: <answer>\n\n"
            f"Question:\n{q}\n"
        )

    else:
        # For general questions I just want a short final answer.
        cot_prompt = (
            "Answer the following question.\n"
            "Do NOT show any reasoning or explanation.\n"
            "Respond on one line in this exact format:\n"
            "FINAL ANSWER: <answer>\n\n"
            f"Question:\n{q}\n"
        )

    result = call_model(cot_prompt, temperature=0.0)
    if not result.get("ok"):
        return "ERROR"

    text = (result.get("text") or "").strip()
    if not text:
        return "ERROR"
    
    final = extract_final_answer(text)

    # If this was a multiple-choice question and the final answer isn't
    # a single letter, I try to salvage the first A/B/C/D from it.
    if is_mc:
        if final.upper() not in {"A", "B", "C", "D"}:
            for ch in final:
                if ch.upper() in {"A", "B", "C", "D"}:
                    final = ch.upper()
                    break
    return final

def run_self_critique(question: str, domain: str | None = None) -> str:
    """
    Self-critique strategy.
    First obtains an initial answer using run_cot, then asks the model to verify
    and, if needed, correct that answer while enforcing a clean FINAL ANSWER line.
    """
    # First obtain the initial answer using the CoT-style prompt.
    initial = run_cot(question, domain)
    if not initial or initial == "ERROR":
        return initial

    # If the initial answer is already short and clean, keep it to avoid extra calls.
    if "\n" not in initial and len(initial.strip()) < 40:
        return initial.strip()

    # For longer or messy answers, ask the model to confirm or correct them.
    critique_prompt = (
        "You will see a question and a proposed answer.\n"
        "Decide whether the proposed answer is correct.\n"
        "If it is wrong, provide the correct answer.\n"
        "Do NOT show any reasoning or explanation.\n"
        "Respond on one line in this exact format:\n"
        "FINAL ANSWER: <answer>\n\n"
        f"Question:\n{question}\n\n"
        f"Proposed answer:\n{initial}\n"
    )

    result = call_model(critique_prompt, temperature=0.0)
    if not result.get("ok"):
        # If the critique call fails, fall back to the initial answer.
        return initial.strip()

    text = (result.get("text") or "").strip()
    if not text:
        return initial.strip()

    final = extract_final_answer(text)
    return final or initial.strip()


def run_self_consistency(question: str, domain: str | None = None, num_samples: int = 3) -> str:
    answers = []
    for _ in range(num_samples):
        ans = run_cot(question, domain)
        if ans and ans != "ERROR":
            answers.append(ans.strip())

    if not answers:
        return "ERROR"

    nums = []
    for a in answers:
        n = extract_number(a)
        if n is not None:
            nums.append(float(n))

    if len(nums) >= 2:
        nums.sort()
        mid = nums[len(nums)//2]
        return str(int(mid)) if mid.is_integer() else str(mid)

    counts = {}
    for a in answers:
        counts[a] = counts.get(a, 0) + 1

    best = max(counts.items(), key=lambda x: x[1])[0]
    return best


