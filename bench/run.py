"""Run the Wiki-Gnome documentation benchmark with headless Claude Code sessions.

Example:
    python bench/run.py --name pilot --projects tally --tasks readme,docstrings --runs 2
"""

import argparse
import json
import sys
import tempfile
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import BENCH_DIR, SKILL_DIR, checks, judge, reader, report, sandbox, workspace  # noqa: E402
from harness.claude import UsageLimitReached, run_claude  # noqa: E402
from harness.conditions import fingerprint, load_conditions  # noqa: E402
from harness.projects import load_projects  # noqa: E402

STAGES = ("generate", "read", "judge", "report")

WRITER_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill"]
WRITER_ALLOWED = [
    "Read", "Write", "Edit", "Glob", "Grep", "Skill",
    # Models often prefix commands with `cd <workspace> &&`, so cd and echo must be allowed for the rest to run.
    "Bash(cd:*)", "Bash(echo:*)",
    "Bash(ls:*)", "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)", "Bash(git status:*)", "Bash(git tag:*)",
]
# Deny rules win over allow rules, so a project can allow `python` without allowing installs into the host.
WRITER_DISALLOWED = ["Bash(python -m pip:*)", "Bash(pip:*)", "Bash(pip3:*)", "Bash(git commit:*)", "Bash(git push:*)"]


def parse_args() -> argparse.Namespace:
    projects = load_projects()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="Results folder name under bench/results/.")
    parser.add_argument("--projects", default=",".join(projects), help="Comma-separated project IDs. Default: all.")
    parser.add_argument("--tasks", default="", help="Comma-separated task IDs. Default: every task in each project.")
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
    args.project_list = [projects[p] for p in _split(args.projects, projects)]
    wanted = _split(args.tasks)
    all_task_ids = {t for p in args.project_list for t in p.tasks}
    unknown = [t for t in wanted if t not in all_task_ids]
    if unknown:
        sys.exit(f"Unknown task(s): {', '.join(unknown)}. Choose from: {', '.join(sorted(all_task_ids))}")
    args.task_list = [(p, t) for p in args.project_list for t in p.tasks.values() if not wanted or t.id in wanted]
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


class Benchmark:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.results = BENCH_DIR / "results" / args.name
        self.work = Path(tempfile.gettempdir()) / "wiki-gnome-bench" / args.name
        self.stop = threading.Event()
        self.print_lock = threading.Lock()
        self.failures: list[str] = []

    # Paths -----------------------------------------------------------------

    def run_dir(self, project, task, condition, model, run) -> Path:
        return self.results / "runs" / project.id / task.id / condition.id / model / f"run{run}"

    def work_dir(self, kind, project, task, condition, model, run) -> Path:
        return self.work / kind / project.id / task.id / condition.id / model / f"run{run}"

    def combos(self):
        for project, task in self.args.task_list:
            for model in self.args.model_list:
                for run in range(1, self.args.runs + 1):
                    for condition in self.args.condition_list:
                        yield project, task, condition, model, run

    # Stages ----------------------------------------------------------------

    def generate(self, project, task, condition, model, run) -> str:
        out = self.run_dir(project, task, condition, model, run)
        if (out / "generate.json").exists():
            return "cached"
        ws = self.work_dir("workspaces", project, task, condition, model, run)
        workspace.create_workspace(ws, project, task, condition)
        session = run_claude(
            condition.prompt_prefix + task.prompt, cwd=ws, model=model, transcript=out / "writer-transcript.jsonl",
            tools=WRITER_TOOLS, allowed_tools=WRITER_ALLOWED + project.writer_allowed,
            disallowed_tools=WRITER_DISALLOWED + project.writer_disallowed,
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

        measured = checks.docstrings_only(doc_text) if task.code_doc else doc_text
        meta = {
            "project": project.id, "task": task.id, "condition": condition.id, "model": model, "run": run,
            "session": session.to_json(),
            "skill_loaded": session.skill_loaded(SKILL_DIR.name),
            "doc_written": doc_written,
            "checks": ws_checks,
            "invented": checks.invented_facts(measured, project.invented_patterns, task.id),
            "style": checks.style_metrics(measured),
        }
        if task.code_doc and doc_written:
            meta["docstring_coverage"] = checks.docstring_coverage(doc_text)
        (out / "generate.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if self.args.clean:
            workspace.remove_tree(ws)
        return "ok" if session.ok else f"session error: {session.error}"

    def read(self, project, task, condition, model, run) -> str:
        out = self.run_dir(project, task, condition, model, run)
        if (out / "reader.json").exists():
            return "cached"
        if not (out / "generate.json").exists():
            return "skipped: not generated yet"
        view = out / "reader-view.txt"
        if view.exists():
            result = reader.run_reader(
                project, task, view.read_text(encoding="utf-8"), model=self.args.reader_model, out_dir=out,
                sandbox_root=self.work_dir("sandboxes", project, task, condition, model, run),
                venvs_dir=self.work / "venvs",
            )
        else:
            total = len(task.jobs) if task.reader == "exec" else len(task.questions)
            result = {"type": task.reader, "skipped": "no document", "passed": 0, "total": total, "score": 0.0}
        (out / "reader.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return f"{result['passed']}/{result['total']}"

    def judge(self, project, task, model, run, shuffle) -> str:
        out = self.results / "judge" / project.id / task.id / model / f"run{run}" / f"pass{shuffle + 1}"
        if (out / "judge.json").exists():
            if json.loads((out / "judge.json").read_text(encoding="utf-8")).get("valid"):
                return "cached"
            rebuilt = judge.reinterpret(out)
            if rebuilt and rebuilt["valid"]:
                return "rebuilt from transcript: " + " > ".join(rebuilt["ranking"])
        docs = {}
        for condition in self.args.condition_list:
            run_out = self.run_dir(project, task, condition, model, run)
            if not (run_out / "generate.json").exists():
                return "skipped: not all conditions generated"
            doc = run_out / "doc" / Path(task.doc_path).name
            docs[condition.id] = doc.read_text(encoding="utf-8") if doc.exists() else None
        identity = {"project": project.id, "task": task.id, "model": model, "run": f"run{run}",
                    "pass": f"pass{shuffle + 1}"}
        out.mkdir(parents=True, exist_ok=True)
        result = judge.run_judge(
            project, task, docs, model=self.args.judge_model, seed=f"{task.id}/{model}/run{run}",
            reverse=shuffle % 2 == 1, out_dir=out, cwd=self.work / "judge", identity=identity,
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

    def write_config(self) -> None:
        config = {
            "projects": [p.id for p in self.args.project_list],
            "tasks": [f"{p.id}/{t.id}" for p, t in self.args.task_list],
            "conditions": {c.id: c.description for c in self.args.condition_list},
            # Fingerprints of each condition's prompt or skill, so pooled comparisons can tell versions apart.
            "condition_sha256": {c.id: fingerprint(c) for c in self.args.condition_list},
            "models": self.args.model_list,
            "runs": self.args.runs,
            "reader_model": self.args.reader_model,
            "judge_model": self.args.judge_model,
            "judge_passes": self.args.shuffles,
        }
        (self.results / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    def main(self) -> int:
        self.results.mkdir(parents=True, exist_ok=True)
        # Only a run that writes docs defines the config, so rebuilding a report can't overwrite it.
        if "generate" in self.args.stage_list or not (self.results / "config.json").exists():
            self.write_config()
        self.log(f"Results: {self.results}\nWorkspaces: {self.work}")

        combos = list(self.combos())
        label = lambda p, t, c, m, r: f"{p.id}/{t.id}/{c.id}/{m}/run{r}"  # noqa: E731
        if "generate" in self.args.stage_list:
            self.run_jobs("generate", [
                (label(*combo), lambda combo=combo: self.generate(*combo)) for combo in combos
            ])
        if "read" in self.args.stage_list and not self.stop.is_set():
            venvs = self.work / "venvs"
            exec_projects = {p.id: p for p, t in self.args.task_list if t.reader == "exec"}
            if exec_projects:
                self.log("Preparing offline virtual environments with each project installed...")
                sandbox.download_build_wheels(venvs / "wheels")
                for project in exec_projects.values():
                    reader.installed_venv(project, venvs)
            self.run_jobs("read", [
                (label(*combo), lambda combo=combo: self.read(*combo)) for combo in combos
            ])
        if "judge" in self.args.stage_list and not self.stop.is_set():
            self.run_jobs("judge", [
                (f"{p.id}/{t.id}/{m}/run{r}/pass{s + 1}", lambda p=p, t=t, m=m, r=r, s=s: self.judge(p, t, m, r, s))
                for p, t in self.args.task_list for m in self.args.model_list
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
