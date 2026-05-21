import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "env" / "corpus"


def list_files(path="."):
    if path != ".":
        raise ValueError("toy project only allows listing the corpus root")
    return sorted(p.name for p in CORPUS_DIR.glob("*.md"))


def _safe_path(path):
    candidate = (CORPUS_DIR / path).resolve()
    if CORPUS_DIR.resolve() not in candidate.parents and candidate != CORPUS_DIR.resolve():
        raise ValueError("path escapes corpus directory")
    if candidate.suffix != ".md":
        raise ValueError("only markdown files are readable")
    return candidate


def read_file(path, max_chars=3000):
    return _safe_path(path).read_text(encoding="utf-8")[:max_chars]


def search_text(query, max_matches=10):
    query_lower = query.lower()
    matches = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if query_lower in line.lower():
                matches.append({"path": path.name, "line": line_no, "text": line.strip()})
                if len(matches) >= max_matches:
                    return matches
    return matches


def execute_action(action):
    name = action["action"]
    args = action.get("arguments", {})
    if name == "list_files":
        return list_files(**args)
    if name == "read_file":
        return read_file(**args)
    if name == "search_text":
        return search_text(**args)
    raise ValueError(f"unknown action: {name}")


def dumps_action(name, arguments):
    return json.dumps({"action": name, "arguments": arguments}, ensure_ascii=False)

