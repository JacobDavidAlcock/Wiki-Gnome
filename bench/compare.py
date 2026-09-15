"""Pool several benchmark runs and compare prompt or skill versions across all of them.

A condition name only means something within one run: `prompt` is whatever prompt.md held at the time.
Use --alias to give each run's conditions a stable version name before pooling.

Example:
    python bench/compare.py pilot v2-vs-v1 v3-vs-v2 \\
        --alias pilot:prompt=prompt-v1 --alias v2-vs-v1:prompt=prompt-v2 --alias v3-vs-v2:prompt=prompt-v3
"""

import argparse
import itertools
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import BENCH_DIR  # noqa: E402
from harness.report import collect  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="Results folder names under bench/results/.")
    parser.add_argument("--alias", action="append", default=[], metavar="RUN:CONDITION=NAME",
                        help="Rename a condition in one run, e.g. v2-vs-v1:prompt=prompt-v2. Repeatable.")
    parser.add_argument("--out", help="Write the comparison to this Markdown file as well as printing it.")
    return parser.parse_args()


def parse_aliases(values: list[str]) -> dict[tuple[str, str], str]:
    aliases = {}
    for value in values:
        try:
            left, name = value.split("=", 1)
            run, condition = left.split(":", 1)
        except ValueError:
            sys.exit(f"Bad --alias {value!r}. Use RUN:CONDITION=NAME, e.g. v2-vs-v1:prompt=prompt-v2")
        aliases[(run, condition)] = name
    return aliases


def bootstrap_interval(groups: list[list[float]], samples: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% interval for the mean, resampling whole docs so a doc's reader jobs stay together."""
    if len(groups) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        picked = [rng.choice(groups) for _ in groups]
        flat = [v for group in picked for v in group]
        means.append(sum(flat) / len(flat))
    means.sort()
    return means[int(0.025 * samples)], means[int(0.975 * samples) - 1]


def main() -> None:
    args = parse_args()
    aliases = parse_aliases(args.alias)

    # Reader results: one list of per-job pass/fail values per doc.
    reader = defaultdict(list)          # (task, version) -> [[1.0, 0.0, ...], ...]
    wins = defaultdict(lambda: [0, 0])  # (task, a, b) -> [a ranked higher, comparisons]
    versions = set()
    tasks = set()

    for run in args.runs:
        folder = BENCH_DIR / "results" / run
        if not folder.is_dir():
            sys.exit(f"No results folder: {folder}")
        data = collect(folder)
        name = lambda condition: aliases.get((run, condition), condition)  # noqa: E731
        for row in data["runs"]:
            result = row.get("reader")
            if not result:
                continue
            version = name(row["condition"])
            versions.add(version)
            tasks.add(row["task"])
            if result.get("steps"):
                values = [1.0 if step["passed"] else 0.0 for step in result["steps"].values()]
            elif result.get("questions"):
                values = [1.0 if q["passed"] else 0.0 for q in result["questions"].values()]
            else:
                values = [0.0] * result.get("total", 1)
            reader[(row["task"], version)].append(values)
        for verdict in data["verdicts"]:
            if not verdict.get("valid"):
                continue
            ranking = [name(c) for c in verdict["ranking"]]
            for higher, lower in itertools.combinations(ranking, 2):
                for task in (verdict["task"], "all"):
                    wins[(task, higher, lower)][0] += 1
                    wins[(task, higher, lower)][1] += 1
                    wins[(task, lower, higher)][1] += 1

    order = sorted(versions, key=lambda v: (v != "none", v))
    task_list = sorted(tasks) + ["all"]
    lines = [
        "# Pooled comparison",
        "",
        f"Runs pooled: {', '.join(args.runs)}.",
        "",
        "## Reader success",
        "",
        "Share of reader jobs that worked, pooled across runs, with a 95% bootstrap interval. `n` is the number of docs.",
        "",
        "| Version | " + " | ".join(f"`{t}`" for t in task_list) + " |",
        "|---|" + "---|" * len(task_list),
    ]
    for version in order:
        cells = []
        for task in task_list:
            groups = [g for (t, v), gs in reader.items() if v == version and (task == "all" or t == task) for g in gs]
            if not groups:
                cells.append("–")
                continue
            flat = [x for g in groups for x in g]
            low, high = bootstrap_interval(groups)
            cells.append(f"{100 * sum(flat) / len(flat):.0f}% ({100 * low:.0f}–{100 * high:.0f}), n={len(groups)}")
        lines.append(f"| `{version}` | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Head-to-head in the blind ranking",
        "",
        "Each cell shows how often the row version was ranked above the column version, when the judge saw both.",
        "",
    ]
    for task in task_list:
        present = [v for v in order if any(wins[(task, v, o)][1] for o in order)]
        if len(present) < 2:
            continue
        lines += [f"### `{task}`", "", "| | " + " | ".join(f"`{v}`" for v in present) + " |",
                  "|---|" + "---|" * len(present)]
        for row in present:
            cells = []
            for col in present:
                won, total = wins[(task, row, col)]
                cells.append("" if row == col else (f"{100 * won / total:.0f}% of {total}" if total else "–"))
            lines.append(f"| `{row}` | " + " | ".join(cells) + " |")
        lines.append("")

    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
