import json
from pathlib import Path

TOTAL_QUESTIONS = 6208
START_IDX = 0000
END_IDX = 6208 # Inclusive? Let's assume inclusive of the range provided by user. 
# Prompt: "run from questions 4000 to 5208"
# Python slice: [4000:5209]

CHECKPOINT_PATH = Path("cse_476_final_project_answers.checkpoint.json")
BACKUP_PATH = CHECKPOINT_PATH.with_suffix('.checkpoint.json.bak')

def main():
    # Load original if exists to verify or just overwrite logic
    if CHECKPOINT_PATH.exists():
        print(f"Backing up {CHECKPOINT_PATH} to {BACKUP_PATH}")
        data = json.loads(CHECKPOINT_PATH.read_text(encoding='utf-8'))
        BACKUP_PATH.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    # Create new structure
    # We want 0-3999 SKIPPED
    # 4000-5208 PENDING (None)
    # 5209-6207 SKIPPED
    
    new_data = []
    for i in range(TOTAL_QUESTIONS):
        if 0000 <= i <= 6208:
            new_data.append(None) # Pending
        else:
            new_data.append({"output": "SKIPPED"})
            
    # Write back
    print(f"Writing new checkpoint with {new_data.count(None)} pending questions (indices {START_IDX}-{END_IDX})")
    CHECKPOINT_PATH.write_text(json.dumps(new_data, indent=2, ensure_ascii=False), encoding='utf-8')
    print("Done.")

if __name__ == "__main__":
    main()

