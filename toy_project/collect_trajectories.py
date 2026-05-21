import json
from pathlib import Path

from tools import dumps_action, execute_action
from verifier import load_tasks, verify_answer


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "trajectories_raw.jsonl"


def _good_final(task, search_result):
    snippets = " ".join(item["text"] for item in search_result[:2])
    return f"{task['prompt']} 答案：{snippets}"


def _bad_final(task):
    return f"{task['prompt']} 答案：这个问题需要进一步检查。"


def make_trajectory(task, variant):
    steps = []

    search_action = {"action": "search_text", "arguments": {"query": task["query"]}}
    search_result = execute_action(search_action)
    steps.append({"assistant": search_action, "tool": search_result})

    if variant == "good" and search_result:
        read_action = {"action": "read_file", "arguments": {"path": search_result[0]["path"]}}
        read_result = execute_action(read_action)
        steps.append({"assistant": read_action, "tool": read_result})
        final = _good_final(task, search_result)
    else:
        final = _bad_final(task)

    score = verify_answer(task, final)
    return {
        "task_id": task["task_id"],
        "task": task["prompt"],
        "variant": variant,
        "steps": steps,
        "final": final,
        "score": score,
        "final_status": "success" if score == 1.0 else "failure",
    }


def collect():
    trajectories = []
    for task in load_tasks():
        trajectories.append(make_trajectory(task, "good"))
        trajectories.append(make_trajectory(task, "bad"))
    return trajectories


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for trajectory in collect():
            fh.write(json.dumps(trajectory, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

