import json
from pathlib import Path

def build_bank():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    explanations_file = data_dir / "explanations.json"
    concepts_file = data_dir / "concepts.json"
    questions_file = data_dir / "questions.json"

    print("Verifying data assets...")
    with open(concepts_file, "r", encoding="utf-8") as f:
        concepts = json.load(f)
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(explanations_file, "r", encoding="utf-8") as f:
        explanations = json.load(f)

    print(f"Loaded {len(concepts)} concepts, {len(questions)} questions, and {len(explanations)} precomputed explanation clusters.")

    # Validate each concept has an explanation entry or fallback
    missing = []
    for c in concepts:
        cid = c["id"]
        if cid not in explanations:
            missing.append(cid)

    if missing:
        print(f"Warning: concepts missing dedicated offline cluster: {missing} (will use robust fallback)")
    else:
        print("All target concepts have dedicated offline clusters verified!")

    print("Offline bank validation complete.")

if __name__ == "__main__":
    build_bank()
