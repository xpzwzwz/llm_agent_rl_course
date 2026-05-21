import json
from collections import defaultdict
from pathlib import Path

from build_sft_dataset import load_trajectories


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "dpo.jsonl"


def render_trajectory(trajectory):
    parts = []
    for step in trajectory["steps"]:
        action = json.dumps(step["assistant"], ensure_ascii=False)
        parts.append(f"Action: {action}")
    parts.append(f"Final: {trajectory['final']}")
    return "\n".join(parts)


def build_pairs(trajectories):
    by_task = defaultdict(list)
    for item in trajectories:
        by_task[item["task_id"]].append(item)

    pairs = []
    for task_id, items in by_task.items():
        ordered = sorted(items, key=lambda item: item.get("score", 0.0), reverse=True)
        chosen = ordered[0]
        rejected = ordered[-1]
        if chosen.get("score", 0.0) <= rejected.get("score", 0.0):
            continue
        pairs.append(
            {
                "prompt": chosen["task"],
                "chosen": render_trajectory(chosen),
                "rejected": render_trajectory(rejected),
            }
        )
    return pairs


def main():
    pairs = build_pairs(load_trajectories())
    with OUT.open("w", encoding="utf-8") as fh:
        for pair in pairs:
            fh.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

