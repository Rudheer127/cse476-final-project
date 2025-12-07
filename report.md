# CSE 476 Final Project Report - LLM Question Answering Agent
**Author**: Rudheer | **Repository**: [github.com/Rudheer127/cse476-final-project](https://github.com/Rudheer127/cse476-final-project)

## Project Overview
An LLM-based agent that answers questions across multiple domains (math, science, history, general knowledge) using adaptive reasoning strategies to maximize accuracy while staying within API constraints (max 20 calls/question).

## Architecture
| Component | File | Purpose |
|-----------|------|---------|
| Core Agent | `agent/agent_core.py` | Question routing and strategy selection based on math detection |
| Strategies | `agent/strategies.py` | CoT, Self-Critique, Self-Consistency implementations |
| API Client | `agent/api_client.py` | Rate-limited API calls with exponential backoff and jitter |
| Evaluation | `evaluation.py` | Text/numeric grading with normalization |
| Runner | `generate_answer_template.py` | Parallel processing with checkpointing |

## Reasoning Strategies
**Chain-of-Thought (CoT)** - 1 API call: Base strategy forcing strict `FINAL: <answer>` output format. Adapts prompts for MCQ (A/B/C/D), yes/no, numeric, or factoid questions.
**Self-Critique** - 2 API calls: Two-step process for non-math domains. Generates initial CoT answer, then asks model to verify/correct. Short stable answers (<=12 chars, no spaces) skip critique for efficiency.
**Self-Consistency** - 3 API calls: For math questions. Generates 3 CoT samples, aggregates using median (numeric) or majority vote (text) to improve reliability.
## Question Routing Logic
Math detection triggers Self-Consistency when any of these conditions are met:
- Contains operators: `+ - * / × ÷`
- Contains math keywords: solve, calculate, percent, total, how many, how much, etc.
- Contains 2+ digits in question text
All other questions use Self-Critique.
## Key Design Decisions
- **Modular Design**: Each strategy is a standalone function for testing and extensibility
- **Robust Answer Extraction**: Handles missing FINAL: prefix, parenthetical answers, extra whitespace, MCQ letters
- **Rate Limiting**: API client uses exponential backoff, jitter, and semaphore (concurrency=3)
- **Checkpointing**: Saves progress every 100 questions for resumption after interruptions
- **Single-Threaded LLM Inference**: Prevents context bleed/KV cache corruption

## Efficiency & Constraints
| Strategy | Max API Calls | Use Case |
|----------|---------------|----------|
| CoT | 1 | Baseline |
| Self-Critique | 2 | Non-math domains |
| Self-Consistency | 3 | Math questions |
All strategies stay well below the 20-call limit.

## Integration Example
```python
from agent.agent_core import CoreAgent
agent = CoreAgent()
answer = agent.run(question["input"])  # Returns extracted final answer
```
## Known Failure Cases
- Ambiguous factoid answers where model provides extra context
- Questions where model ignores the FINAL: format instruction
- Numeric aggregation edge cases in self-consistency (median selection)
- Very long or complex multi-step reasoning questions
## Files & Structure
```
cse476-final-project/
├── agent/                     # Core agent module
│   ├── agent_core.py          # CoreAgent class with routing logic
│   ├── api_client.py          # Rate-limited API client
│   └── strategies.py          # CoT, Self-Critique, Self-Consistency
├── evaluation.py              # Grading functions
├── generate_answer_template.py # Main runner with checkpointing
├── run_test.py                # Development testing
├── cse_476_final_project_test_data.json  # Test questions
└── cse_476_final_project_answers.json    # Generated answers
```
