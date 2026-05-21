import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def verify_answer(task, final_answer):
    text = final_answer.lower()
    for term in task.get("answer_contains", []):
        if term.lower() not in text:
            return 0.0
    return 1.0


def load_tasks(path=ROOT / "data" / "tasks.jsonl"):
    tasks = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                tasks.append(json.loads(line))
    return tasks

