"""Re-run the invented-fact checks on saved docs, then rebuild each run's report.

Use this after changing a project's invented-fact patterns, so earlier runs are scored the same way
as new ones. It needs each run's raw runs/ folder, which git doesn't keep.

Example:
    python bench/recheck.py pilot v5-vs-v4 useful-v5
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import BENCH_DIR, checks, report  # noqa: E402
from harness.projects import load_projects  # noqa: E402
from harness.report import DEFAULT_PROJECT  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="Results folder names under bench/results/.")
    args = parser.parse_args()
    projects = load_projects()

    for run in args.runs:
        folder = BENCH_DIR / "results" / run
        gen_paths = sorted((folder / "runs").rglob("generate.json"))
        if not gen_paths:
            print(f"{run}: skipped, no raw runs/ folder on this machine")
            continue
        changed = 0
        for gen_path in gen_paths:
            meta = json.loads(gen_path.read_text(encoding="utf-8"))
            project = projects[meta.get("project", DEFAULT_PROJECT)]
            task = project.tasks[meta["task"]]
            doc_path = gen_path.parent / "doc" / Path(task.doc_path).name
            text = doc_path.read_text(encoding="utf-8") if meta["doc_written"] and doc_path.exists() else ""
            measured = checks.docstrings_only(text) if task.code_doc else text
            invented = checks.invented_facts(measured, project.invented_patterns, task.id)
            if invented != meta["invented"]:
                meta["invented"] = invented
                gen_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                changed += 1
        report.write_report(folder)
        print(f"{run}: rechecked {len(gen_paths)} docs, {changed} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
