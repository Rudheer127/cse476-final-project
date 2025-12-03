import re
def normalize_text(s: str) -> str:
    # Treat None the same as an empty string
    if s is None:
        s = ""
    # Lowercase the text and trim whitespace on the ends
    s = s.lower().strip()
    # Collapse any extra spaces so everything is clean and uniform
    s = " ".join(s.split())
    return s

def extract_number(s: str) -> str | None:
    # If there's nothing to parse, there's no number to extract
    if s is None or s.strip() == "":
        return None
    # Look for the first integer or decimal number in the string
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    # Return the matched number text, or None if no match found
    return m.group(0) if m else None


def grade(expected: str, got: str, kind: str = "text") -> bool:
    # Numeric grading: pull out numbers and compare them directly
    if kind == "numeric":
        exp = extract_number(expected)
        pred = extract_number(got)
        # Only count as correct if the expected number exists and matches
        return exp is not None and pred == exp
    else:
        # Text grading: normalize both strings so small differences don't matter
        return normalize_text(expected) == normalize_text(got)


def evaluate_agent(agent, data, max_examples: int | None = None):
    # Figure out how many examples to actually evaluate
    n = len(data)
    if max_examples is not None and max_examples < n:
        n = max_examples

    total = 0
    num_correct = 0

    for i in range(n):
        item = data[i]
        q = item["input"]
        expected = item["output"]
        domain = item.get("domain")

        # Choose grading mode: numeric if the domain includes math
        kind = "numeric" if domain and "math" in domain else "text"

        # Get the model's prediction for this item
        pred = agent.run(q, domain)

        # Determine if the prediction matches the expected answer
        correct = grade(expected, pred, kind)

        total += 1
        num_correct += int(correct)

    # Print a simple summary of performance
    print(f"Score: {num_correct} / {total} correct")
