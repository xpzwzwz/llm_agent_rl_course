import json
from collections import defaultdict
from pathlib import Path

from build_sft_dataset import load_trajectories


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "dpo.jsonl"


def render_trajectory(trajectory):
    messages = []
    for index, step in enumerate(trajectory["steps"]):
        tool_call_id = f"call_{index + 1}"
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": step["assistant"]["action"],
                            "arguments": json.dumps(step["assistant"].get("arguments", {}), ensure_ascii=False),
                        },
                    }
                ],
            }
        )
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(step["tool"], ensure_ascii=False),
            }
        )
    messages.append({"role": "assistant", "content": trajectory["final"]})
    return messages


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
