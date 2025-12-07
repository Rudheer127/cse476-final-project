# CSE 476 Final Project Report

## Overview

For this project, I implemented an LLM-based agent that answers questions across multiple domains. The agent uses different reasoning strategies based on question type to maximize accuracy while staying within API call limits.

## Strategies Implemented

### 1. Chain-of-Thought (CoT)

I implemented Chain-of-Thought as the baseline reasoning approach. The model receives a carefully structured prompt that instructs it to output its answer in a strict format: `FINAL: <answer>`. This is implemented in the `run_cot` function in `agent/strategies.py`.

The prompt adapts based on question type:
- For multiple-choice questions, it requests a single letter (A/B/C/D)
- For yes/no questions, it constrains output to Yes or No
- For numeric questions, it requests only the final number
- For factoid questions, it requests a short phrase

### 2. Self-Critique

For non-mathematical domains, I use a two-step Self-Critique approach. After generating an initial CoT answer, the model reviews the question and proposed answer, then either confirms it or provides a correction. This is implemented in `run_self_critique` in `agent/strategies.py`.

I added an optimization where short, stable answers (12 characters or fewer with no spaces) skip the critique step since they are unlikely to benefit from review.

### 3. Self-Consistency

For mathematical questions, I implemented Self-Consistency by generating multiple CoT samples (default: 3) and aggregating results. For numeric answers, I take the median value to handle outliers. For non-numeric answers, I use majority voting. This is in `run_self_consistency` in `agent/strategies.py`.

## Agent Workflow and Routing

The `CoreAgent` class in `agent/agent_core.py` routes each question to the appropriate strategy. Math detection uses:
- Presence of operators (+, -, *, /, ×, ÷)
- Math keywords (solve, calculate, percent, total, sum, difference, quotient, etc.)
- At least 2 digits in the question text

Math questions route to Self-Consistency, while all others route to Self-Critique.

## Key Design Decisions

**Modular Strategy Design**: I structured each strategy as a standalone function, making them easy to test and swap independently.

**Robust Answer Extraction**: The `extract_final_answer` function handles edge cases like missing prefixes, parenthetical answers, and extra whitespace.

**Rate Limiting**: The API client uses exponential backoff, jitter, and a semaphore limiting concurrency to 3 calls to avoid rate-limit failures.

**Answer Validation**: The answer generation script validates each output to catch malformed responses before saving.

**Checkpoint System**: For long runs, I implemented checkpoint saving every 100 questions to allow resumption after interruptions.

## Efficiency

The agent stays well within the 20 LLM calls per question limit:
- CoT: 1 call
- Self-Critique: 2 calls (1 for initial answer, 1 for review)
- Self-Consistency: 3 calls (configurable)

Maximum LLM calls per question = 3, well below the 20-call limit.

## Integration

The `generate_answer_template.py` replaces placeholder answers with:

```python
agent = CoreAgent()
real_answer = agent.run(question["input"])
```

## Failure Cases

Known failure cases include:
- Ambiguous short factoid answers where the model provides extra context
- Questions where the model ignores the FINAL: output format
- Numeric aggregation edge cases in self-consistency (e.g., very different magnitudes)

## Code References

- **Strategies**: `agent/strategies.py`
  - `run_cot`: Lines 74-138
  - `run_self_critique`: Lines 141-192
  - `run_self_consistency`: Lines 229-269
- **Routing**: `agent/agent_core.py`, `CoreAgent.run`: Lines 8-43
- **Evaluation**: `evaluation.py`, `grade`: Lines 22-31
