import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COURSE_ROOT = ROOT.parent
TOY_ROOT = COURSE_ROOT / "toy_project"
sys.path.insert(0, str(TOY_ROOT))

from tools import execute_action
from verifier import load_tasks, verify_answer


@dataclass
class ParsedOutput:
    kind: str
    name: str | None = None
    arguments: dict | None = None
    final: str | None = None


def extract_action(text):
    stripped = text.strip()
    if stripped.startswith("Final:"):
        return ParsedOutput(kind="final", final=stripped[len("Final:") :].strip())
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        return ParsedOutput(kind="parse_error")
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return ParsedOutput(kind="parse_error")
    action = obj.get("action")
    arguments = obj.get("arguments", {})
    if not isinstance(action, str) or not isinstance(arguments, dict):
        return ParsedOutput(kind="parse_error")
    return ParsedOutput(kind="action", name=action, arguments=arguments)


def _make_final(task, search_result):
    snippets = " ".join(item["text"] for item in search_result[:2])
    return f"{task['prompt']} 答案：{snippets}"


def run_rule_based_agent(task, max_steps=4):
    trajectory = []
    parse_errors = 0
    invalid_actions = 0
    premature_final = 0

    search_action = {"action": "search_text", "arguments": {"query": task["query"]}}
    search_result = execute_action(search_action)
    trajectory.append({"assistant": search_action, "tool": search_result})

    if search_result:
        read_action = {"action": "read_file", "arguments": {"path": search_result[0]["path"]}}
        read_result = execute_action(read_action)
        trajectory.append({"assistant": read_action, "tool": read_result})
        final = _make_final(task, search_result)
    else:
        premature_final = 1
        final = f"{task['prompt']} 答案：没有找到足够信息。"

    score = verify_answer(task, final)
    return {
        "task_id": task["task_id"],
        "score": score,
        "final_status": "success" if score == 1.0 else "failure",
        "final": final,
        "steps": len(trajectory),
        "parse_errors": parse_errors,
        "invalid_actions": invalid_actions,
        "premature_final": premature_final,
        "trajectory": trajectory,
    }


def build_prompt(task, history):
    lines = [
        "你是文档检索 agent。可用工具：",
        '- search_text: {"action":"search_text","arguments":{"query":"..."}}',
        '- read_file: {"action":"read_file","arguments":{"path":"..."}}',
        "每次只能输出一个 JSON action，完成时输出 Final: ...",
        f"任务：{task['prompt']}",
    ]
    for item in history:
        lines.append(f"Assistant: {json.dumps(item['assistant'], ensure_ascii=False)}")
        lines.append(f"Tool: {json.dumps(item['tool'], ensure_ascii=False)}")
    return "\n".join(lines)


def load_model(model_name):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", trust_remote_code=True)
    return tokenizer, model


def generate_text(tokenizer, model, prompt, max_new_tokens=128):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True)


def run_model_agent(task, tokenizer, model, max_steps=4):
    history = []
    parse_errors = 0
    invalid_actions = 0
    premature_final = 0
    final = ""

    for step_index in range(max_steps):
        prompt = build_prompt(task, history)
        text = generate_text(tokenizer, model, prompt)
        parsed = extract_action(text)
        if parsed.kind == "parse_error":
            parse_errors += 1
            final = text.strip()
            break
        if parsed.kind == "final":
            final = parsed.final or ""
            if step_index == 0:
                premature_final = 1
            break
        try:
            result = execute_action({"action": parsed.name, "arguments": parsed.arguments or {}})
        except Exception as exc:
            invalid_actions += 1
            result = {"error": str(exc)}
        history.append({"assistant": {"action": parsed.name, "arguments": parsed.arguments or {}}, "tool": result})
    else:
        final = "未在步数限制内完成。"

    score = verify_answer(task, final)
    return {
        "task_id": task["task_id"],
        "score": score,
        "final_status": "success" if score == 1.0 else "failure",
        "final": final,
        "steps": len(history),
        "parse_errors": parse_errors,
        "invalid_actions": invalid_actions,
        "premature_final": premature_final,
        "trajectory": history,
    }


def summarize(results, model_name):
    total = len(results)
    successes = sum(1 for item in results if item["score"] == 1.0)
    return {
        "model": model_name,
        "num_tasks": total,
        "success_rate": successes / total if total else 0.0,
        "invalid_action_rate": sum(item["invalid_actions"] for item in results) / total if total else 0.0,
        "avg_steps": sum(item["steps"] for item in results) / total if total else 0.0,
        "premature_final_rate": sum(item["premature_final"] for item in results) / total if total else 0.0,
        "parse_error_rate": sum(1 for item in results if item["parse_errors"] > 0) / total if total else 0.0,
        "examples_failed": [item["task_id"] for item in results if item["score"] < 1.0][:5],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="rule", help="'rule' for smoke test, or HF model/checkpoint path")
    parser.add_argument("--tasks_path", default=str(ROOT / "data" / "eval_tasks.jsonl"))
    parser.add_argument("--max_steps", type=int, default=4)
    parser.add_argument("--output_path", default=str(ROOT / "outputs" / "eval_results.json"))
    args = parser.parse_args()

    tasks_path = Path(args.tasks_path)
    tasks = load_tasks(tasks_path if tasks_path.exists() else TOY_ROOT / "data" / "tasks.jsonl")
    if args.model == "rule":
        results = [run_rule_based_agent(task, max_steps=args.max_steps) for task in tasks]
    else:
        tokenizer, model = load_model(args.model)
        results = [run_model_agent(task, tokenizer, model, max_steps=args.max_steps) for task in tasks]

    summary = summarize(results, args.model)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()

