"""Blind ranking: a judge model ranks the anonymised docs for one task and run."""

import json
import random
from pathlib import Path

from .claude import parse_json_answer, run_claude
from .model import Project, Task

JUDGE_PROMPT = """You are reviewing documentation for {description}. Several writers were each given the same request, and each wrote their own version. Rank the versions from most to least useful.

The request each writer received:
<request>
{request}
</request>

The facts below are verified against the code. Use them to judge accuracy. The writers did not see this list.
<facts>
{facts}
</facts>

Judge each version by how well it serves a developer who needs to get a job done with {name}:
- Accuracy: wrong or invented details are the most serious fault, because the reader acts on them.
- Coverage: does it include what this kind of document needs, including behaviour a reader would trip over?
- Clarity: can the reader find what they need and act on it quickly?

Ignore length for its own sake. A shorter version that is accurate and complete beats a longer one.

When you list factual errors, include only statements that are wrong or invented. Missing information and valid alternatives to the facts, such as a different but working command, are not factual errors; weigh them under coverage instead.

{documents}

Reply with only a JSON object, no other text:
{{"ranking": ["best label", "...", "worst label"], "factual_errors": {{"<label>": ["short description of each wrong or invented detail"]}}, "reasons": {{"<label>": "one sentence"}}}}
"""


def build_documents(docs: dict[str, str | None], seed: str, reverse: bool) -> tuple[str, dict[str, str]]:
    """Shuffle the conditions behind neutral labels. Returns the prompt section and label -> condition.

    The same seed with reverse=True shows the documents in the opposite order, which cancels out
    any preference the judge has for early or late positions.
    """
    conditions = sorted(docs)
    random.Random(seed).shuffle(conditions)
    if reverse:
        conditions.reverse()
    labels = {f"Version {chr(ord('A') + i)}": condition for i, condition in enumerate(conditions)}
    sections = []
    for label, condition in labels.items():
        body = docs[condition] or "(This writer produced no document.)"
        sections.append(f'<document label="{label}">\n{body}\n</document>')
    return "\n\n".join(sections), labels


def run_judge(
    project: Project, task: Task, docs: dict[str, str | None], *, model: str, seed: str, reverse: bool,
    out_dir: Path, cwd: Path, identity: dict,
) -> dict:
    documents, labels = build_documents(docs, seed, reverse)
    prompt = JUDGE_PROMPT.format(
        description=project.description,
        name=project.id,
        request=task.prompt,
        facts=project.facts_file.read_text(encoding="utf-8"),
        documents=documents,
    )
    cwd.mkdir(parents=True, exist_ok=True)
    session = run_claude(prompt, cwd=cwd, model=model, transcript=out_dir / "judge-transcript.jsonl", tools=[])
    return interpret(session.result, labels, session.to_json(), out_dir, identity)


def reinterpret(out_dir: Path) -> dict | None:
    """Rebuild a verdict from a saved transcript, for example after a parser fix. Returns None if impossible."""
    saved, transcript = out_dir / "judge.json", out_dir / "judge-transcript.jsonl"
    if not saved.exists() or not transcript.exists():
        return None
    previous = json.loads(saved.read_text(encoding="utf-8"))
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            identity = {k: previous[k] for k in ("project", "task", "model", "run", "pass") if k in previous}
            return interpret(event.get("result") or "", previous["labels"], previous["session"], out_dir, identity)
    return None


def interpret(reply: str, labels: dict[str, str], session: dict, out_dir: Path, identity: dict) -> dict:
    verdict = parse_json_answer(reply) or {}

    # Judges sometimes shorten "Version A" to "A".
    def condition_for(label) -> str | None:
        label = str(label).strip()
        return labels.get(label) or labels.get(f"Version {label}")

    ranking = [c for c in (condition_for(label) for label in verdict.get("ranking", [])) if c]
    valid = len(ranking) == len(labels) and len(set(ranking)) == len(labels)
    errors = {condition_for(label): items for label, items in (verdict.get("factual_errors") or {}).items()
              if condition_for(label)}
    reasons = {condition_for(label): text for label, text in (verdict.get("reasons") or {}).items()
               if condition_for(label)}
    result = {
        # Which project, task, model, run and pass this verdict belongs to.
        **identity,
        "valid": valid,
        "labels": labels,
        "ranking": ranking if valid else [],
        "factual_errors": errors,
        "reasons": reasons,
        "session": session,
    }
    (out_dir / "judge.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
