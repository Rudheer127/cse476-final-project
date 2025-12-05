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


import concurrent.futures

def evaluate_agent(agent, data, max_examples: int | None = None, num_workers: int = 1):
    # Figure out how many examples to actually evaluate
    n = len(data)
    if max_examples is not None and max_examples < n:
        n = max_examples
        data = data[:n]
    else:
        # If max_examples is None or >= len(data), use all data
        # We need to slice or ensure data is the right size if we iterate by range(n)
        # But for list processing, slicing is safer if we want to limit exactly.
        pass

    total = 0
    num_correct = 0

    print(f"Evaluating {n} examples using {num_workers} workers...")

    def process_item(item):
        q = item["input"]
        expected = item["output"]
        domain = item.get("domain")

        # Choose grading mode: numeric if the domain includes math
        kind = "numeric" if domain and "math" in domain else "text"

        # Get the model's prediction for this item
        # Note: agent.run might need to be thread-safe. 
        # Since it just makes API calls, it should be fine.
        pred = agent.run(q, domain)

        # Determine if the prediction matches the expected answer
        correct = grade(expected, pred, kind)
        return correct

    # Use ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_item, data))

    total = len(results)
    num_correct = sum(int(r) for r in results)

    # Print a simple summary of performance
    print(f"Score: {num_correct} / {total} correct")
