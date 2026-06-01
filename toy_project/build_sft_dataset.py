import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "trajectories_raw.jsonl"
OUT = ROOT / "data" / "sft.jsonl"


def load_trajectories(path=RAW):
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def trajectory_to_sft(trajectory):
    messages = [{"role": "user", "content": trajectory["task"]}]
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
    return {"messages": messages}


def build_sft_samples(trajectories):
    return [trajectory_to_sft(item) for item in trajectories if item.get("score") == 1.0]


def main():
    samples = build_sft_samples(load_trajectories())
    with OUT.open("w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
