# CSE 476 Final Project Report

**Project Repository**: https://github.com/Rudheer127/cse476-final-project

## Overview
I implemented an LLM-based agent that answers questions across multiple domains using different reasoning strategies based on question type to maximize accuracy while staying within API call limits.

## Strategies Implemented

**Chain-of-Thought (CoT)**: The baseline approach where the model outputs answers in a strict `FINAL: <answer>` format. The prompt adapts for MCQ (A/B/C/D), yes/no, numeric, or factoid questions. Implemented in `run_cot` in `agent/strategies.py`.

**Self-Critique**: A two-step approach for non-math domains. After generating an initial CoT answer, the model reviews and corrects if needed. Short stable answers (<=12 chars, no spaces) skip critique. Implemented in `run_self_critique`.

**Self-Consistency**: For math questions, generates 3 CoT samples and aggregates results using median (numeric) or majority vote (text). Implemented in `run_self_consistency`.

## Agent Workflow and Routing
The `CoreAgent` class routes questions based on math detection signals:
- Operators (+, -, *, /, ×, ÷) or math keywords (solve, calculate, percent, total, etc.)
- At least 2 digits in the question text

Math questions use Self-Consistency; others use Self-Critique.

## Key Design Decisions
- **Modular Strategies**: Each strategy is a standalone function for easy testing and swapping
- **Robust Answer Extraction**: Handles missing prefixes, parenthetical answers, extra whitespace
- **Rate Limiting**: API client uses exponential backoff, jitter, and semaphore (concurrency=3)
- **Checkpointing**: Saves progress every 100 questions for resumption after interruptions

## Efficiency
Maximum LLM calls per question = 3, well below the 20-call limit:
- CoT: 1 call | Self-Critique: 2 calls | Self-Consistency: 3 calls

## Integration
The `generate_answer_template.py` uses:
```python
agent = CoreAgent()
real_answer = agent.run(question["input"])
```

## Failure Cases
- Ambiguous factoid answers where the model provides extra context
- Questions where the model ignores the FINAL: format
- Numeric aggregation edge cases in self-consistency

## Code References
- `agent/strategies.py`: `run_cot` (74-138), `run_self_critique` (141-192), `run_self_consistency` (229-269)
- `agent/agent_core.py`: `CoreAgent.run` (8-43)
- `evaluation.py`: `grade` (22-31)
