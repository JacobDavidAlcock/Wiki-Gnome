"""Run the Wiki-Gnome documentation benchmark with headless Claude Code sessions.

Example:
    python bench/run.py --name pilot --tasks readme,docstrings,changelog --runs 2
"""

import argparse
import hashlib
import json
import sys
import tempfile
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import BENCH_DIR, SKILL_DIR, checks, judge, reader, report, workspace  # noqa: E402
from harness.claude import UsageLimitReached, run_claude  # noqa: E402
from harness.tasks import TASKS, load_conditions  # noqa: E402

STAGES = ("generate", "read", "judge", "report")

WRITER_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill"]
WRITER_ALLOWED = [
    "Read", "Write", "Edit", "Glob", "Grep", "Skill",
    # Models often prefix commands with `cd <workspace> &&`, so cd and echo must be allowed for the rest to run.
    "Bash(cd:*)", "Bash(echo:*)",
    "Bash(ls:*)", "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)", "Bash(git status:*)",
    "Bash(git tag:*)", "Bash(python -m pantry:*)", "Bash(python -m unittest:*)",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="Results folder name under bench/results/.")
    parser.add_argument("--tasks", default=",".join(TASKS), help="Comma-separated task IDs. Default: all.")
    parser.add_argument("--conditions", default="none,oneline,prompt,skill", help="Comma-separated condition IDs.")
    parser.add_argument("--models", default="haiku", help="Comma-separated writer models. Default: haiku.")
    parser.add_argument("--runs", type=int, default=3, help="Runs per task, condition and model. Default: 3.")
    parser.add_argument("--reader-model", default="haiku", help="Model for reader tests. Default: haiku.")
    parser.add_argument("--judge-model", default="sonnet", help="Model for blind ranking. Default: sonnet.")
    parser.add_argument("--shuffles", type=int, default=2, help="Judge passes per task and run. Default: 2.")
    parser.add_argument("--parallel", type=int, default=3, help="Sessions at once. Default: 3.")
    parser.add_argument("--stages", default=",".join(STAGES), help="Comma-separated stages to run.")
    parser.add_argument("--clean", action="store_true", help="Delete the temporary workspaces when finished.")
    args = parser.parse_args()

    conditions = load_conditions()
    args.task_list = [TASKS[t] for t in _split(args.tasks, TASKS)]
    args.condition_list = [conditions[c] for c in _split(args.conditions, conditions)]
    args.model_list = _split(args.models)
    args.stage_list = _split(args.stages, STAGES)
    return args


def _split(value: str, valid=None) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if valid is not None:
        unknown = [item for item in items if item not in valid]
        if unknown:
            sys.exit(f"Unknown value(s): {', '.join(unknown)}. Choose from: {', '.join(valid)}")
    return items


def condition_fingerprint(condition) -> str | None:
    if condition.append_system_prompt:
        return hashlib.sha256(condition.append_system_prompt.encode("utf-8")).hexdigest()[:12]
    if condition.skill_dir:
        return hashlib.sha256((condition.skill_dir / "SKILL.md").read_bytes()).hexdigest()[:12]
    return None


class Benchmark:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.results = BENCH_DIR / "results" / args.name
        self.work = Path(tempfile.gettempdir()) / "wiki-gnome-bench" / args.name
        self.stop = threading.Event()
        self.print_lock = threading.Lock()
        self.failures: list[str] = []

    # Paths -----------------------------------------------------------------

    def run_dir(self, task, condition, model, run) -> Path:
        return self.results / "runs" / task.id / condition.id / model / f"run{run}"

    def work_dir(self, kind, task, condition, model, run) -> Path:
        return self.work / kind / task.id / condition.id / model / f"run{run}"

    def combos(self):
        for task in self.args.task_list:
            for model in self.args.model_list:
                for run in range(1, self.args.runs + 1):
                    for condition in self.args.condition_list:
                        yield task, condition, model, run

    # Stages ----------------------------------------------------------------

    def generate(self, task, condition, model, run) -> str:
        out = self.run_dir(task, condition, model, run)
        if (out / "generate.json").exists():
            return "cached"
        ws = self.work_dir("workspaces", task, condition, model, run)
        workspace.create_workspace(ws, task, condition)
        session = run_claude(
            task.prompt, cwd=ws, model=model, transcript=out / "writer-transcript.jsonl",
            tools=WRITER_TOOLS, allowed_tools=WRITER_ALLOWED,
            append_system_prompt=condition.append_system_prompt,
        )

        ws_checks = checks.workspace_checks(ws)
        doc_file = ws / task.doc_path
        doc_written = doc_file.exists() and task.doc_path in ws_checks["changed_files"]
        doc_text = doc_file.read_text(encoding="utf-8", errors="replace") if doc_written else ""
        (out / "doc").mkdir(parents=True, exist_ok=True)
        if doc_written:
            (out / "doc" / Path(task.doc_path).name).write_text(doc_text, encoding="utf-8")
            view = checks.reader_text(task, ws)
            if view:
                (out / "reader-view.txt").write_text(view, encoding="utf-8")
        (out / "changes.patch").write_text(workspace.diff(ws), encoding="utf-8")

        measured = checks.docstrings_only(doc_text) if task.id == "docstrings" else doc_text
        meta = {
            "task": task.id, "condition": condition.id, "model": model, "run": run,
            "session": session.to_json(),
            "skill_loaded": session.skill_loaded(SKILL_DIR.name),
            "doc_written": doc_written,
            "checks": ws_checks,
            "invented": checks.invented_facts(measured),
            "style": checks.style_metrics(measured),
        }
        if task.id == "docstrings" and doc_written:
            meta["docstring_coverage"] = checks.docstring_coverage(doc_text)
        (out / "generate.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return "ok" if session.ok else f"session error: {session.error}"

    def read(self, task, condition, model, run) -> str:
        out = self.run_dir(task, condition, model, run)
        if (out / "reader.json").exists():
            return "cached"
        if not (out / "generate.json").exists():
            return "skipped: not generated yet"
        view = out / "reader-view.txt"
        if view.exists():
            result = reader.run_reader(
                task, view.read_text(encoding="utf-8"), model=self.args.reader_model, out_dir=out,
                sandbox_root=self.work_dir("sandboxes", task, condition, model, run),
                venvs_dir=self.work / "venvs",
            )
        else:
            total = len(task.exec_steps) if task.reader == "exec" else len(task.questions)
            result = {"type": task.reader, "skipped": "no document", "passed": 0, "total": total, "score": 0.0}
        (out / "reader.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return f"{result['passed']}/{result['total']}"

    def judge(self, task, model, run, shuffle) -> str:
        out = self.results / "judge" / task.id / model / f"run{run}" / f"pass{shuffle + 1}"
        if (out / "judge.json").exists():
            if json.loads((out / "judge.json").read_text(encoding="utf-8")).get("valid"):
                return "cached"
            rebuilt = judge.reinterpret(out)
            if rebuilt and rebuilt["valid"]:
                return "rebuilt from transcript: " + " > ".join(rebuilt["ranking"])
        docs = {}
        for condition in self.args.condition_list:
            run_out = self.run_dir(task, condition, model, run)
            if not (run_out / "generate.json").exists():
                return "skipped: not all conditions generated"
            doc = run_out / "doc" / Path(task.doc_path).name
            docs[condition.id] = doc.read_text(encoding="utf-8") if doc.exists() else None
        result = judge.run_judge(
            task, docs, model=self.args.judge_model, seed=f"{task.id}/{model}/run{run}",
            reverse=shuffle % 2 == 1, out_dir=out, cwd=self.work / "judge",
        )
        return " > ".join(result["ranking"]) if result["valid"] else "invalid verdict"

    # Orchestration ---------------------------------------------------------

    def run_jobs(self, stage: str, jobs: list[tuple[str, callable]]) -> None:
        total = len(jobs)
        if not total:
            return
        self.log(f"\n== {stage}: {total} job(s), {self.args.parallel} at a time ==")
        done = 0
        with ThreadPoolExecutor(max_workers=self.args.parallel) as pool:
            futures = {pool.submit(self._guarded, label, fn): label for label, fn in jobs}
            for future in as_completed(futures):
                done += 1
                label = futures[future]
                status, seconds = future.result()
                self.log(f"[{done}/{total}] {stage} {label}: {status} ({seconds:.0f}s)")

    def _guarded(self, label: str, fn) -> tuple[str, float]:
        start = time.monotonic()
        if self.stop.is_set():
            return "not started: usage limit reached", 0.0
        try:
            return fn(), time.monotonic() - start
        except UsageLimitReached as exc:
            self.stop.set()
            return f"usage limit reached ({exc}); re-run the same command later to resume", time.monotonic() - start
        except Exception:
            self.failures.append(label)
            return "failed:\n" + traceback.format_exc(), time.monotonic() - start

    def log(self, message: str) -> None:
        with self.print_lock:
            print(message, flush=True)

    def main(self) -> int:
        self.results.mkdir(parents=True, exist_ok=True)
        config = {
            "tasks": [t.id for t in self.args.task_list],
            "conditions": {c.id: c.description for c in self.args.condition_list},
            # Fingerprints of each condition's prompt or skill, so pooled comparisons can tell versions apart.
            "condition_sha256": {c.id: condition_fingerprint(c) for c in self.args.condition_list},
            "models": self.args.model_list,
            "runs": self.args.runs,
            "reader_model": self.args.reader_model,
            "judge_model": self.args.judge_model,
            "judge_passes": self.args.shuffles,
        }
        (self.results / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.log(f"Results: {self.results}\nWorkspaces: {self.work}")

        combos = list(self.combos())
        if "generate" in self.args.stage_list:
            self.run_jobs("generate", [
                (f"{t.id}/{c.id}/{m}/run{r}", lambda t=t, c=c, m=m, r=r: self.generate(t, c, m, r))
                for t, c, m, r in combos
            ])
        if "read" in self.args.stage_list and not self.stop.is_set():
            if any(t.reader == "exec" for t in self.args.task_list):
                self.log("Preparing an offline virtual environment with pantry installed...")
                wheels = reader.download_build_wheels(self.work / "venvs" / "wheels")
                reader.make_venv(self.work / "venvs" / "installed", install_pantry=True, wheels=wheels)
            self.run_jobs("read", [
                (f"{t.id}/{c.id}/{m}/run{r}", lambda t=t, c=c, m=m, r=r: self.read(t, c, m, r))
                for t, c, m, r in combos
            ])
        if "judge" in self.args.stage_list and not self.stop.is_set():
            self.run_jobs("judge", [
                (f"{t.id}/{m}/run{r}/pass{s + 1}", lambda t=t, m=m, r=r, s=s: self.judge(t, m, r, s))
                for t in self.args.task_list for m in self.args.model_list
                for r in range(1, self.args.runs + 1) for s in range(self.args.shuffles)
            ])
        if "report" in self.args.stage_list:
            path = report.write_report(self.results)
            self.log(f"\nReport: {path}")

        if self.args.clean and not self.stop.is_set():
            workspace.remove_tree(self.work)
        if self.stop.is_set():
            self.log("\nStopped early because the usage limit was reached. Run the same command again to resume.")
            return 2
        if self.failures:
            self.log(f"\n{len(self.failures)} job(s) failed: {', '.join(self.failures)}")
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(Benchmark(parse_args()).main())
