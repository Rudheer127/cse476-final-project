from agent.api_client import call_model


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
