# Final Project Report

## Strategies Implemented

### 1. Chain-of-Thought (CoT)
The baseline strategy uses a Chain-of-Thought approach. The model is prompted to think step-by-step before providing the final answer. This is implemented in `run_cot` in `agent/strategies.py`. The system prompt instructs the model to output reasoning followed by a "FINAL ANSWER:" line, which is then extracted.

### 2. Self-Critique
For non-mathematical domains, a Self-Critique strategy is used. After generating an initial answer using CoT, the model is asked to review the question and the proposed answer. It evaluates correctness and provides a corrected answer if necessary. This is implemented in `run_cot_with_critique` in `agent/strategies.py`. This adds a verification step to improve accuracy on general knowledge and reasoning tasks.

### 3. Self-Consistency
For mathematical domains, a Self-Consistency strategy is employed. The agent generates multiple (default: 3) CoT answers independently.
- If the answers are numeric, it extracts the numbers and returns the median value to handle potential outliers.
- If the answers are non-numeric, it performs a majority vote to select the most common answer.
This is implemented in `run_self_consistency` in `agent/strategies.py`. This technique is particularly effective for math problems where calculation errors can occur stochastically.

## Agent Workflow & Routing

The `CoreAgent` class in `agent/agent_core.py` serves as the main entry point. It implements a routing logic based on the `domain` of the question:
- **Math Domain**: If the domain contains "math", the agent routes the query to the **Self-Consistency** strategy.
- **Other Domains**: For all other domains (or if domain is unspecified), the agent defaults to the **CoT + Critique** strategy.

This routing ensures that the most appropriate technique is applied to each type of problem, optimizing for both accuracy and efficiency.

## Key Design Choices

- **Modular Strategy Design**: Strategies are implemented as standalone functions in `strategies.py`, making them easy to test and compose. `CoreAgent` simply orchestrates these strategies.
- **Robust Answer Extraction**: The `extract_final_answer` function handles various edge cases in model output, such as missing "FINAL ANSWER:" prefixes or extra whitespace, ensuring reliable parsing.
- **Evaluation Metrics**: The `evaluation.py` module provides specific grading logic for text (normalization) and numbers (extraction and comparison), allowing for accurate performance assessment during development.
- **Efficiency**: The agent is designed to stay well within the 20 LLM calls per question limit. CoT uses 1 call, Critique uses 2 calls total, and Self-Consistency uses 3 calls total.

## Code References

- **Strategies**: `agent/strategies.py`
  - `run_cot`: Lines 31-83
  - `run_cot_with_critique`: Lines 85-116
  - `run_self_consistency`: Lines 118-148
- **Routing**: `agent/agent_core.py`
  - `CoreAgent.run`: Lines 8-14
- **Evaluation**: `evaluation.py`
  - `grade`: Lines 22-31
