# CSE 476 Final Project - LLM Question Answering Agent

## Project Description

This project implements an LLM-based agent that answers questions across multiple domains including math, science, history, and general knowledge. The agent uses different reasoning strategies depending on question type to optimize accuracy.

## Setup

### Prerequisites
- Python 3.10+
- Access to the course LLM API endpoint

### Installation

```bash
pip install requests
```

### Environment Variables

Set the following environment variables to configure API access:

```bash
export OPENAI_API_KEY="cse476"
export API_BASE="http://10.4.58.53:41701/v1"
export MODEL_NAME="bens_model"
```

## Usage

### Generate Answers

Run the main answer generation script:

```bash
python generate_answer_template.py
```

This will:
1. Load questions from `cse_476_final_project_test_data.json`
2. Process each question using the agent
3. Save answers to `cse_476_final_project_answers.json`
4. Save checkpoints periodically to allow resumption

### Run Evaluation (Development)

For testing during development:

```bash
python run_test.py
```

## Project Structure

```
cse476-final-project/
├── agent/
│   ├── __init__.py
│   ├── agent_core.py      # Main agent with routing logic
│   ├── api_client.py      # API client with retry logic
│   └── strategies.py      # Reasoning strategies (CoT, etc.)
├── evaluation.py          # Grading and evaluation functions
├── generate_answer_template.py  # Main script for answer generation
├── run_test.py            # Development testing script
├── report.md              # Project report
├── README.md              # This file
└── cse_476_final_project_test_data.json  # Input questions
```

## Strategies

The agent implements three reasoning strategies:

1. **Chain-of-Thought (CoT)**: Baseline approach with structured output format
2. **Self-Critique**: Two-step process that reviews and corrects initial answers
3. **Self-Consistency**: Multiple samples with median/majority aggregation

Math questions use Self-Consistency, while other domains use Self-Critique.

## Configuration

Key parameters in `generate_answer_template.py`:
- `NUM_TEST_QUESTIONS`: Set to limit questions for testing (None for all)
- `NUM_WORKERS`: Parallel workers for processing (default: 8)
- `CHECKPOINT_INTERVAL`: Save checkpoint every N questions (default: 100)
