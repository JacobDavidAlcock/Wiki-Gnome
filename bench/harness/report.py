"""Summarises a results folder into report.md and summary.json."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

CONDITION_ORDER = ["none", "oneline", "prompt-v1", "prompt", "skill-v1", "skill", "skill-forced"]
# Runs from before the benchmark had several projects all used pantry.
DEFAULT_PROJECT = "pantry"


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _avg(values) -> float | None:
    values = [v for v in values if v is not None]
    return mean(values) if values else None


def _fmt(value, kind="num") -> str:
    if value is None:
        return "–"
    if kind == "pct":
        return f"{value * 100:.0f}%"
    if kind == "rank":
        return f"{value:.2f}"
    return f"{value:.1f}" if isinstance(value, float) else str(value)


def collect(results: Path) -> dict:
    """Load every doc and verdict in a results folder.

    Reads the raw runs/ and judge/ folders when they exist, and the committed docs.jsonl and
    verdicts.jsonl otherwise, so reports and comparisons also work on a fresh clone.
    """
    runs = []
    for gen_path in sorted((results / "runs").rglob("generate.json")):
        gen = _load(gen_path)
        if gen:
            gen.setdefault("project", DEFAULT_PROJECT)
            gen["reader"] = _load(gen_path.with_name("reader.json"))
            runs.append(gen)
    if not runs:
        runs = _load_jsonl(results / "docs.jsonl")

    verdicts = []
    judge_dir = results / "judge"
    for judge_path in sorted(judge_dir.rglob("judge.json")):
        verdict = _load(judge_path)
        if not verdict:
            continue
        parts = judge_path.relative_to(judge_dir).parts[:-1]
        # New layout: project/task/model/runN/passN. Older runs: task/model/runN/passN.
        if len(parts) == 4:
            parts = (DEFAULT_PROJECT, *parts)
        identity = dict(zip(("project", "task", "model", "run", "pass"), parts))
        verdicts.append({**identity, **verdict})
    if not verdicts:
        verdicts = _load_jsonl(results / "verdicts.jsonl")

    for item in runs + verdicts:
        item["key"] = f"{item['project']}/{item['task']}"
    return {"runs": runs, "verdicts": verdicts}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compact(data: dict) -> tuple[list[dict], list[dict]]:
    """Strip docs and verdicts down to what reports and comparisons need, without transcripts."""
    docs = []
    for r in data["runs"]:
        reader = r.get("reader") or {}
        docs.append({
            "project": r["project"], "task": r["task"], "condition": r["condition"], "model": r["model"],
            "run": r["run"], "doc_written": r["doc_written"], "skill_loaded": r["skill_loaded"],
            "invented": [{"id": f["id"]} for f in r["invented"]],
            "checks": {"code_edits": r["checks"]["code_edits"], "tests_pass": r["checks"]["tests_pass"]},
            "style": {k: r["style"][k] for k in ("words", "banned_per_1000_words", "avg_sentence_words",
                                                  "filler_headings")},
            "session": {k: r["session"][k] for k in ("ok", "num_turns", "duration_ms")},
            "reader": {
                "score": reader.get("score"), "passed": reader.get("passed"), "total": reader.get("total"),
                "steps": {job: {"passed": step["passed"]} for job, step in (reader.get("steps") or {}).items()},
                "questions": reader.get("questions") or {},
            } if reader else None,
        })
    verdicts = [
        {k: v[k] for k in ("project", "task", "model", "run", "pass", "valid", "ranking", "factual_errors")}
        for v in data["verdicts"]
    ]
    return docs, verdicts


def summarise(data: dict) -> dict:
    runs, verdicts = data["runs"], data["verdicts"]
    conditions = [c for c in CONDITION_ORDER if any(r["condition"] == c for r in runs)]
    conditions += sorted({r["condition"] for r in runs} - set(conditions))
    tasks = sorted({r["key"] for r in runs})

    ranks, firsts, judged_errors = defaultdict(list), defaultdict(list), defaultdict(list)
    task_ranks = defaultdict(list)
    for verdict in verdicts:
        if not verdict.get("valid"):
            continue
        for position, condition in enumerate(verdict["ranking"], start=1):
            ranks[condition].append(position)
            firsts[condition].append(1.0 if position == 1 else 0.0)
            task_ranks[(verdict["key"], condition)].append(position)
            judged_errors[condition].append(len(verdict.get("factual_errors", {}).get(condition, [])))

    overall = {}
    for condition in conditions:
        rows = [r for r in runs if r["condition"] == condition]
        reader_scores = [r["reader"]["score"] for r in rows if r.get("reader")]
        overall[condition] = {
            "runs": len(rows),
            "docs_written": _avg([1.0 if r["doc_written"] else 0.0 for r in rows]),
            "reader_score": _avg(reader_scores),
            "mean_rank": _avg(ranks[condition]),
            "first_place": _avg(firsts[condition]),
            "judged_errors": _avg(judged_errors[condition]),
            "invented_patterns": _avg([len(r["invented"]) for r in rows]),
            "code_broken": sum(1 for r in rows if r["checks"]["code_edits"] or not r["checks"]["tests_pass"]),
            "skill_loaded": _avg([1.0 if r["skill_loaded"] else 0.0 for r in rows]),
            "words": _avg([r["style"]["words"] for r in rows if r["doc_written"]]),
            "banned_per_1000_words": _avg([r["style"]["banned_per_1000_words"] for r in rows if r["doc_written"]]),
            "avg_sentence_words": _avg([r["style"]["avg_sentence_words"] for r in rows if r["doc_written"]]),
            "filler_headings": _avg([r["style"]["filler_headings"] for r in rows if r["doc_written"]]),
            "writer_turns": _avg([r["session"]["num_turns"] for r in rows]),
            "writer_minutes": _avg([r["session"]["duration_ms"] / 60000 for r in rows]),
            "session_errors": sum(1 for r in rows if not r["session"]["ok"]),
        }

    per_task = {}
    for task in tasks:
        per_task[task] = {}
        for condition in conditions:
            rows = [r for r in runs if r["key"] == task and r["condition"] == condition]
            per_task[task][condition] = {
                "runs": len(rows),
                "reader_score": _avg([r["reader"]["score"] for r in rows if r.get("reader")]),
                "mean_rank": _avg(task_ranks[(task, condition)]),
                "invented_patterns": _avg([len(r["invented"]) for r in rows]),
            }

    step_rates = defaultdict(lambda: defaultdict(list))
    for r in runs:
        reader = r.get("reader") or {}
        for step, result in (reader.get("steps") or {}).items():
            step_rates[f"{r['project']}/{step}"][r["condition"]].append(1.0 if result["passed"] else 0.0)

    invented_counts = defaultdict(lambda: defaultdict(int))
    for r in runs:
        for finding in r["invented"]:
            invented_counts[finding["id"]][r["condition"]] += 1

    return {
        "conditions": conditions,
        "tasks": tasks,
        "overall": overall,
        "per_task": per_task,
        "exec_steps": {step: {c: _avg(v) for c, v in rates.items()} for step, rates in step_rates.items()},
        "invented_by_pattern": {k: dict(v) for k, v in invented_counts.items()},
        "judge_verdicts": len(verdicts),
        "invalid_verdicts": sum(1 for v in verdicts if not v.get("valid")),
    }


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def render(summary: dict, config: dict) -> str:
    conditions = summary["conditions"]
    names = config.get("conditions", {})
    label = lambda c: f"`{c}` ({names.get(c, c)})"  # noqa: E731
    o = summary["overall"]

    out = [
        "# Benchmark report",
        "",
        f"Writer models: {', '.join(config.get('models', []))}. Runs per task and condition: {config.get('runs')}. "
        f"Reader model: {config.get('reader_model')}. Judge model: {config.get('judge_model')}, "
        f"{config.get('judge_passes')} passes per task and run.",
        "",
        "## Headline results",
        "",
        "Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.",
        "",
        _table(
            ["Condition", "Runs", "Reader success", "Mean rank", "First place", "Judged errors per doc",
             "Invented-fact patterns per doc", "Broken code"],
            [[label(c), str(o[c]["runs"]), _fmt(o[c]["reader_score"], "pct"), _fmt(o[c]["mean_rank"], "rank"),
              _fmt(o[c]["first_place"], "pct"), _fmt(o[c]["judged_errors"]), _fmt(o[c]["invented_patterns"]),
              str(o[c]["code_broken"])] for c in conditions],
        ),
        "",
        "- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. "
        "Commands were run for real; quiz answers were marked against the answer key.",
        f"- **Mean rank:** average position in the blind ranking, where 1 is best and {len(conditions)} is worst.",
        "- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.",
        "- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.",
        "- **Broken code:** runs where the writer changed code or the tests stopped passing.",
        "",
        "## Results by task",
        "",
        "Each cell shows reader success, then mean rank.",
        "",
        _table(
            ["Task"] + [f"`{c}`" for c in conditions],
            [[f"`{task}`"] + [
                f"{_fmt(cells[c]['reader_score'], 'pct')}, {_fmt(cells[c]['mean_rank'], 'rank')}"
                for c in conditions
            ] for task, cells in summary["per_task"].items()],
        ),
        "",
    ]

    if summary["exec_steps"]:
        out += [
            "## Reader jobs that worked",
            "",
            "Share of runs where the reader's commands for each job produced the right result.",
            "",
            _table(
                ["Job"] + [f"`{c}`" for c in conditions],
                [[f"`{step}`"] + [_fmt(rates.get(c), "pct") for c in conditions]
                 for step, rates in summary["exec_steps"].items()],
            ),
            "",
        ]

    if summary["invented_by_pattern"]:
        out += [
            "## Invented facts found automatically",
            "",
            "Number of docs matching each pattern.",
            "",
            _table(
                ["Pattern"] + [f"`{c}`" for c in conditions],
                [[f"`{pattern}`"] + [str(counts.get(c, 0)) for c in conditions]
                 for pattern, counts in sorted(summary["invented_by_pattern"].items())],
            ),
            "",
        ]

    out += [
        "## Style and cost",
        "",
        "These show whether the style rules were followed. They don't show whether docs got better.",
        "",
        _table(
            ["Condition", "Skill loaded", "Words", "Banned words per 1,000", "Words per sentence",
             "Filler headings", "Writer turns", "Writer minutes", "Session errors"],
            [[f"`{c}`", _fmt(o[c]["skill_loaded"], "pct"), _fmt(o[c]["words"]),
              _fmt(o[c]["banned_per_1000_words"]), _fmt(o[c]["avg_sentence_words"]),
              _fmt(o[c]["filler_headings"]), _fmt(o[c]["writer_turns"]), _fmt(o[c]["writer_minutes"]),
              str(o[c]["session_errors"])] for c in conditions],
        ),
        "",
    ]
    if summary["invalid_verdicts"]:
        out += [f"{summary['invalid_verdicts']} of {summary['judge_verdicts']} judge verdicts couldn't be parsed "
                "and are left out of the rankings.", ""]
    return "\n".join(out)


def write_report(results: Path) -> Path:
    config = _load(results / "config.json") or {}
    data = collect(results)
    if (results / "runs").exists():
        docs, verdicts = compact(data)
        (results / "docs.jsonl").write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
        (results / "verdicts.jsonl").write_text("".join(json.dumps(v) + "\n" for v in verdicts), encoding="utf-8")
    summary = summarise(data)
    (results / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    path = results / "report.md"
    path.write_text(render(summary, config), encoding="utf-8")
    return path
