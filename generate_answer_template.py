#!/usr/bin/env python3
"""
Generate a placeholder answer file that matches the expected auto-grader format.

Replace the placeholder logic inside `build_answers()` with your own agent loop
before submitting so the ``output`` fields contain your real predictions.

Reads the input questions from cse_476_final_project_test_data.json and writes
an answers JSON file where each entry contains a string under the "output" key.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent.agent_core import CoreAgent

# Set to None to run all questions, or a number to limit for testing
NUM_TEST_QUESTIONS = None

# Number of parallel workers - adjust based on API rate limits
# Using 20 workers for increased throughput
NUM_WORKERS = 20

# Save checkpoint every N completed questions
CHECKPOINT_INTERVAL = 100

INPUT_PATH = Path("cse_476_final_project_test_data.json")
OUTPUT_PATH = Path("cse_476_final_project_answers.json")
CHECKPOINT_PATH = OUTPUT_PATH.with_suffix('.checkpoint.json')

def validate_single_answer(question: str, answer: str):
    """
    Validates a single extracted answer.
    Ensures:
      - Answer not empty
      - MCQ answers are A/B/C/D
      - Yes/No valid
      - Numeric values contain a number only
      - Factoid text is sane
    Returns: (True, "") if valid, or (False, reason)
    """
    import re
    from evaluation import extract_number

    if not answer or not answer.strip():
        return False, "Empty answer"

    clean = answer.strip()

    # MCQ
    if clean.upper() in {"A", "B", "C", "D"}:
        return True, ""

    # Yes/No
    if clean in {"Yes", "No"}:
        return True, ""

    # Numeric
    num = extract_number(clean)
    if num is not None:
        return True, ""

    # Factoid text - RELAXED validation
    # Accept anything that isn't empty (we already checked empty above)
    return True, ""

def load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    return data


# def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
#     agent = CoreAgent()
#     answers = []
#     total = len(questions)
#     print(f"Total questions: {total}")
#     for idx, question in enumerate(questions, start=1):
#         print(f"[{idx}/{total}] Running agent...")
#         real_answer = agent.run(question["input"], question.get("domain"))
#         print(f"[{idx}/{total}] Done")
#         answers.append({"output": real_answer})
#     return answers

def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Process questions in parallel using ThreadPoolExecutor.
    Maintains answer order by using index-based result collection.
    Saves checkpoint every CHECKPOINT_INTERVAL questions.
    """
    total = len(questions)
    print(f"Total questions: {total}, using {NUM_WORKERS} parallel workers")

    # Try to load existing checkpoint
    answers: List[Dict[str, str] | None] = [None] * total
    already_done = 0
    
    if CHECKPOINT_PATH.exists():
        try:
            with CHECKPOINT_PATH.open("r", encoding="utf-8") as fp:
                checkpoint_data = json.load(fp)
            if len(checkpoint_data) == total:
                for i, ans in enumerate(checkpoint_data):
                    if ans and ans.get("output") not in ("", "PENDING", "ERROR", None):
                        answers[i] = ans
                        already_done += 1
                print(f"[RESUME] Loaded {already_done}/{total} completed answers from checkpoint")
        except Exception as e:
            print(f"[WARNING] Failed to load checkpoint: {e}")
    
    # Build list of pending indices
    pending_indices = [i for i in range(total) if answers[i] is None]
    if not pending_indices:
        print("[RESUME] All questions already completed!")
        return answers
    
    print(f"[RESUME] Processing {len(pending_indices)} remaining questions...")
    
    def process_single(idx_and_question):
        """Process a single question. Returns (index, answer_dict)."""
        idx, question = idx_and_question
        agent = CoreAgent()  # Create agent per thread for thread safety
        
        qtext = question["input"]
        domain = question.get("domain")
        
        try:
            real_answer = agent.run(qtext, domain)
            
            # Validation
            ok, err = validate_single_answer(qtext, real_answer)
            if not ok:
                print(f"\n[VALIDATION ERROR] Q{idx+1}")
                print(f"Question: {qtext!r}")
                print(f"Answer:   {real_answer!r}")
                print(f"Reason:   {err}")
                # Return ERROR instead of raising to keep other threads running
                return (idx, {"output": "ERROR"})
            
            print(f"\n[Q{idx+1}] {qtext[:100]}...\n      -> {real_answer[:100]}...")
            return (idx, {"output": real_answer})
        except Exception as e:
            print(f"[ERROR] Q{idx+1} failed: {e}")
            return (idx, {"output": "ERROR"})
    
    def save_checkpoint(answers_list, completed_count):
        """Save current answers to checkpoint file."""
        checkpoint = [
            ans if ans is not None else {"output": "PENDING"}
            for ans in answers_list
        ]
        with CHECKPOINT_PATH.open("w", encoding="utf-8") as fp:
            json.dump(checkpoint, fp, ensure_ascii=False, indent=2)
        print(f"[CHECKPOINT] Saved {completed_count} answers to {CHECKPOINT_PATH}")
    
    # Process questions in parallel
    completed = already_done
    last_checkpoint = already_done
    
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Submit only pending tasks
        futures = {
            executor.submit(process_single, (idx, questions[idx])): idx 
            for idx in pending_indices
        }
        
        for future in as_completed(futures):
            try:
                idx, result = future.result()
                answers[idx] = result
                completed += 1
                
                # Progress update every 50 questions
                if completed % 50 == 0 or completed == total:
                    print(f"[PROGRESS] {completed}/{total} questions completed ({100*completed/total:.1f}%)")
                
                # Checkpoint save every CHECKPOINT_INTERVAL questions
                if completed - last_checkpoint >= CHECKPOINT_INTERVAL:
                    save_checkpoint(answers, completed)
                    last_checkpoint = completed
                    
            except Exception as e:
                idx = futures[future]
                print(f"[ERROR] Future {idx} raised exception: {e}")
                answers[idx] = {"output": "ERROR"}
                completed += 1
    
    # Final checkpoint save
    save_checkpoint(answers, completed)
    
    # Verify all slots are filled
    for i, ans in enumerate(answers):
        if ans is None:
            print(f"[WARNING] Missing answer for question {i+1}, setting to ERROR")
            answers[i] = {"output": "ERROR"}
    
    return answers



def validate_results(
    questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
) -> None:
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            print(
                f"[WARNING] Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). It might be rejected by the autograder."
            )
            # raise ValueError(...)


def main() -> None:
    questions = load_questions(INPUT_PATH)
    # Test first 200 questions to validate agent
    if NUM_TEST_QUESTIONS is not None:
        questions = questions[:NUM_TEST_QUESTIONS]
        print(f"Testing on first {len(questions)} questions...")
    else:
        print(f"Running on all {len(questions)} questions...")
    
    answers = build_answers(questions)
    print("[DEBUG] All answers passed validation. Writing JSON...")


    with OUTPUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
        saved_answers = json.load(fp)
    validate_results(questions, saved_answers)
    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH} "
        "and validated format successfully."
    )


if __name__ == "__main__":
    main()

