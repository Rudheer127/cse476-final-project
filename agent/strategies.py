from agent.api_client import call_model
from evaluation import extract_number

def extract_final_answer(text: str) -> str:
    """
    Robust final-answer extractor.
    Handles MCQ (A/B/C/D), Yes/No, numeric, and short factoid text.
    """
    import re
    if not text:
        return "ERROR"
    raw = text.strip()

    candidate = None

    m = re.search(r"\(([^()]+)\)", raw)
    if m:
        candidate = m.group(1).strip()
    else:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if lines:
            candidate = lines[-1]
        else:
            return "ERROR"

    cand = candidate.strip().strip('"').strip("'").strip()

    core = cand.upper().strip("()[] .")
    if core in {"A", "B", "C", "D"}:
        return core

    lower = core.lower()
    if lower == "yes":
        return "Yes"
    if lower == "no":
        return "No"

    num = extract_number(cand)
    if num is not None:
        return num
    return cand

def run_factoid(question: str, domain: str | None = None) -> str:
    """
    Strict short-answer mode for factoid questions.
    """
    q = (question or "").strip()

    prompt = (
        "Answer the question with ONLY the short final answer.\n"
        "No explanation. No reasoning. No chain of thought.\n"
        "If the answer is a number, output only the number.\n"
        "If the answer is a name, output only the name.\n"
        "If the answer is a single letter (A/B/C/D), output only that.\n"
        "Final answer only:\n\n"
        f"Question:\n{q}\n"
    )

    result = call_model(prompt, temperature=0.0)

    if not result.get("ok"):
        return "ERROR"

    text = (result.get("text") or "").strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    if not lines:
        return "ERROR"
    ans = lines[-1]

    return extract_final_answer(ans)


def run_cot(question: str, domain: str | None = None) -> str:
    """
    Unified prompting strategy. Forces model to output: FINAL: <answer>
    """
    q = (question or "").strip()

    is_mc = "Options:" in q and "(A" in q
    is_yesno = q.lower().startswith(("is ", "does ", "do "))
    has_digit = any(ch.isdigit() for ch in q)

    if is_mc:
        instruction = (
            "You are answering a multiple-choice question.\n"
            "Choose only one letter: A, B, C, or D.\n"
        )
    elif is_yesno:
        instruction = (
            "Answer the question with only Yes or No.\n"
        )
    elif has_digit:
        instruction = (
            "Solve the math question. Answer with only the final numeric value.\n"
        )
    else:
        instruction = (
            "Answer the question with a short factoid phrase.\n"
        )

    instruction += (
        "STRICT RULES:\n"
        "- Do NOT explain your reasoning.\n"
        "- Do NOT show any work or steps.\n"
        "- Do NOT write more than one line.\n"
        "- Respond with ONLY this format:\n"
        "FINAL: <answer>\n\n"
        f"Question:\n{q}\n"
    )

    result = call_model(instruction, temperature=0.0)

    if not result.get("ok"):
        return "MODEL_CALL_FAILED"

    text = (result.get("text") or "").strip()

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    final_candidates: list[str] = []

    for line in lines:
        if line.upper().startswith("FINAL:"):
            payload = line.split(":", 1)[1].strip()
            if payload and payload.lower() not in {"<answer>", "<final>", "answer"}:
                final_candidates.append(payload)

    # Take FIRST valid FINAL payload (avoids repetition loop issues)
    if final_candidates:
        chosen = final_candidates[0]
        return extract_final_answer(chosen)

    # Fallback if only placeholder FINAL lines
    if any(l.upper().startswith("FINAL:") for l in lines):
        return extract_final_answer(lines[-1])

    # Fallback if model ignored instruction
    return extract_final_answer(text)


def run_self_critique(question: str, domain: str | None = None) -> str:
    """
    Self-critique: get initial answer, then verify/correct it.
    """
    initial = run_cot(question, domain)
    clean_init = initial.strip()

    # Short stable answers don't need critique
    if clean_init and len(clean_init) <= 12 and " " not in clean_init:
        return clean_init

    critique_prompt = (
        "You will see a question and a proposed answer.\n"
        "Decide if the proposed answer is correct.\n"
        "If correct, repeat it. If incorrect, give the correct short final answer.\n"
        "STRICT RULE: Respond ONLY as:\n"
        "FINAL: <answer>\n"
        "Do NOT include explanations.\n"
        "Do NOT continue the sentence after the answer.\n"
        "The answer must be a COMPLETE standalone phrase.\n\n"
        f"Question:\n{question}\n\n"
        f"Proposed answer:\n{clean_init}\n"
    )

    result = call_model(critique_prompt, temperature=0.0)
    if not result.get("ok"):
        return clean_init

    raw = (result.get("text") or "").strip()

    extracted = None
    for line in raw.splitlines():
        s = line.strip()
        if s.upper().startswith("FINAL:"):
            extracted = s.split(":", 1)[1].strip()
            break

    if not extracted:
        extracted = extract_final_answer(raw)

    # Sanitize extracted answer
    bad_words = ["according", "because", "the question", "as the", "let's", "consider"]
    lower = extracted.lower()

    if "." in extracted:
        extracted = extracted.split(".")[0].strip()

    if any(bad in lower for bad in bad_words):
        tokens = extracted.split()
        extracted = " ".join(tokens[:3]).strip()

    return extract_final_answer(extracted)


def is_numeric_question(question: str) -> bool:
    """
    Heuristic to decide if a question expects a numeric answer.
    """
    if not question:
        return False

    q = question.lower()

    numeric_phrases = [
        "how many", "how much", "how long", "how far", "how old",
        "how big", "how tall", "how heavy", "how fast", "how often",
        "how many more", "how many fewer", "how many less", "how many left",
        "what is the total", "what is the sum", "what is the difference",
        "what is the product", "what is the quotient", "what is the value of",
        "what is the area", "what is the perimeter", "what is the volume",
        "what is the probability", "what percent", "what percentage",
        "what fraction", "what amount"
    ]

    if any(phrase in q for phrase in numeric_phrases):
        return True

    has_digit = any(ch.isdigit() for ch in q)
    has_op = any(op in q for op in "+-*/×÷=")
    if has_digit and has_op:
        return True

    if has_digit and any(word in q for word in ["total", "altogether", "remainder", "remain", "left"]):
        return True

    return False


def run_self_consistency(question: str, domain: str | None = None, num_samples: int = 3) -> str:
    """
    Self-consistency: run multiple samples and take median/majority.
    """
    q = (question or "").strip()

    raw_answers: list[str] = []
    numeric_values: list[float] = []

    for i in range(num_samples):
        ans = run_cot(q, domain)
        if not ans or ans == "ERROR":
            continue

        cleaned = extract_final_answer(ans)
        raw_answers.append(cleaned)

        n = extract_number(cleaned)
        if n is not None:
            try:
                numeric_values.append(float(n))
            except ValueError:
                pass

    if not raw_answers:
        return "ERROR"

    # Prefer numeric median if available
    if numeric_values:
        numeric_values.sort()
        mid = numeric_values[len(numeric_values) // 2]
        final_num = str(int(mid)) if mid.is_integer() else str(mid)
        return final_num

    # Fallback to majority vote
    counts: dict[str, int] = {}
    for a in raw_answers:
        counts[a] = counts.get(a, 0) + 1

    best_answer = max(counts.items(), key=lambda x: x[1])[0]
    return best_answer
