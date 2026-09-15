# Wiki-Gnome benchmark

This benchmark measures whether Wiki-Gnome makes AI agents write documentation that works for readers. It runs the same writing tasks with and without Wiki-Gnome, then tests each doc on a fresh session that has only the doc to go on.

Every session runs through Claude Code's non-interactive mode (`claude -p`), so the benchmark uses your Claude subscription, not an API key.

## Run the benchmark

You need:

- Claude Code, signed in to a Claude subscription. Run `claude` once to check.
- Python 3.10 or later.
- Git. On Windows, the Git Bash that ships with Git for Windows.
- Network access once, to download `setuptools` and `wheel` for the offline reader sandbox.

1. Run a pilot from the repository root. It covers 3 tasks, 4 conditions and 2 runs each:

   ```sh
   python bench/run.py --name pilot --tasks readme,docstrings,changelog --runs 2
   ```

   The script prints each finished job, then the path to the report:

   ```text
   [24/24] generate changelog/skill/haiku/run2: ok (94s)
   ...
   Report: bench/results/pilot/report.md
   ```

2. Read `bench/results/pilot/report.md`.

3. If the pilot looks right, run every task:

   ```sh
   python bench/run.py --name full --runs 3
   ```

If a run stops because you hit your plan's usage limit, run the same command again after the limit resets. Finished jobs are skipped, so the benchmark resumes where it stopped.

## Options

| Option | Default | Description |
|---|---|---|
| `--name` | Required | Folder name under `bench/results/`. |
| `--tasks` | All tasks | Comma-separated task IDs from the table below. |
| `--conditions` | `none,oneline,prompt,skill` | Comma-separated condition IDs. |
| `--models` | `haiku` | Writer models, as Claude Code model names or aliases. |
| `--runs` | `3` | Runs per task, condition and model. |
| `--reader-model` | `haiku` | Model for reader tests. |
| `--judge-model` | `sonnet` | Model for the blind ranking. |
| `--shuffles` | `2` | Judge passes per task and run. The second pass shows the docs in reverse order. |
| `--parallel` | `3` | Sessions running at once. Lower it if you hit usage limits quickly. |
| `--stages` | `generate,read,judge,report` | Stages to run. Use `report` alone to rebuild the report. |
| `--clean` | Off | Delete the temporary workspaces when finished. |

## What gets compared

Each task runs under 4 conditions:

| Condition | What the writing session gets |
|---|---|
| `none` | No documentation guidance |
| `oneline` | One appended instruction: "When you write documentation, write clear docs like Stripe's." |
| `prompt` | [`prompt.md`](../prompt.md), appended to the system prompt |
| `skill` | The [`technical-docs-style`](../.claude/skills/technical-docs-style/SKILL.md) skill, installed in the project. The session decides whether to load it. |

The `oneline` condition checks whether Wiki-Gnome's full rules beat a one-sentence request for good docs.

## Compare a new version with an old one

Earlier versions of the prompt and skill live in [`baselines/`](baselines/), one folder per version. Each folder adds 2 conditions, named after it: `baselines/v1/` adds `prompt-v1` and `skill-v1`.

To test a change to `prompt.md` or the skill:

1. Copy the current versions into a new baseline folder before you edit them:

   ```sh
   mkdir -p bench/baselines/v2/technical-docs-style
   cp prompt.md bench/baselines/v2/prompt.md
   cp .claude/skills/technical-docs-style/SKILL.md bench/baselines/v2/technical-docs-style/
   ```

2. Edit `prompt.md` or the skill.

3. Run the new and old versions side by side, so the judge ranks them in the same pass:

   ```sh
   python bench/run.py --name v3-vs-v2 --conditions none,prompt-v2,prompt,skill --runs 3
   ```

The judge ranks every condition in a run together, so keep to 4 or 5 conditions per run.

## Pool results from several runs

A single run of 3 is noisy: the same version can score 40% on a task in one run and 80% in the next. Before you keep or drop a change, pool every run that tested it.

A condition name only means something inside its own run. `prompt` is whatever `prompt.md` held at the time, so give each run's conditions a version name with `--alias`:

```sh
python bench/compare.py v2-vs-v1 v3-vs-v2 \
    --alias v2-vs-v1:prompt=prompt-v2 \
    --alias v3-vs-v2:prompt=prompt-v3 \
    --out bench/results/comparison.md
```

The output has 2 tables:

- **Reader success** for each version and task, with a 95% bootstrap interval and the number of docs. If two versions' intervals overlap heavily, the difference could be noise.
- **Head-to-head** judge results: how often one version was ranked above another when the judge saw both.

Each run's `config.json` records a `condition_sha256` fingerprint of every condition's prompt or skill. Use it to check which version a run's `prompt` condition was.

## Tasks

Every task uses `pantry`, a small command-line tool in [`fixtures/pantry/`](fixtures/pantry/) built for this benchmark. It has no docs and several behaviours a doc must get right, such as `--file` having to come before the command.

| Task | Request given to the writer | Reader test |
|---|---|---|
| `readme` | Write a README.md for this project. | Commands |
| `cli-reference` | Write reference documentation for the CLI in docs/cli.md. | Commands |
| `howto-alerts` | Write a how-to guide for daily expiry warnings. | Commands |
| `docstrings` | Add docstrings to the functions in pantry/store.py. | Quiz |
| `changelog` | Write a CHANGELOG.md entry for 0.2.0. | Quiz |
| `rewrite` | Rewrite a deliberately bad docs/usage.md. | Commands |

## How docs are scored

The benchmark runs in 4 stages.

1. **Generate.** A writing session runs in a fresh git repository containing pantry. It can read files, write files and run `git` and `python -m pantry`, but can't install anything. The harness then records whether the doc was written, whether any code changed, and whether pantry's tests still pass.
2. **Read.** A new session with no tools gets only the doc.
   - **Commands:** the reader writes shell commands for up to 5 jobs: install pantry, add items, write a cron check, set the default file, and use up an item. The harness runs those commands in a sandbox and checks the result. For example, the cron check must exit non-zero for a pantry with expired food and zero for one without.
   - **Quiz:** the reader answers multiple-choice questions, with a "the documentation doesn't say" option. Answers are marked against the answer key.
3. **Judge.** A judge session sees every condition's doc for the same task and run, under shuffled labels, plus the answer key in [`fixtures/pantry-facts.md`](fixtures/pantry-facts.md). It ranks the docs and lists factual errors.
4. **Report.** The harness writes `report.md` and `summary.json`.

Reader success and factual errors are the main results. Style metrics such as banned-word counts are reported too. A doc written with Wiki-Gnome will score well on its own rules whether or not it helps readers, so those metrics don't show that docs improved.

## Where results go

| Path | Contents |
|---|---|
| `bench/results/<name>/report.md` | The report |
| `bench/results/<name>/summary.json` | The numbers behind the report |
| `bench/results/<name>/runs/<task>/<condition>/<model>/run<n>/` | The doc, the full diff, both session transcripts, the reader's answers and scores |
| `bench/results/<name>/judge/<task>/<model>/run<n>/pass<n>/` | The judge's ranking and transcript |

Git ignores the `runs/` and `judge/` folders, because their transcripts add up to megabytes per run. Each run's `config.json`, `report.md` and `summary.json` are committed, along with `results/comparison.md`. `compare.py` reads the raw folders, so it only works on runs you have locally.

Workspaces and sandboxes live in your system temp folder under `wiki-gnome-bench/<name>/`. Pass `--clean` to delete them at the end.

## Safety

The reader stage runs commands that a model wrote. The harness limits what they can do:

- Only an allowlist of commands runs, such as `pantry`, `python`, `pip`, `export` and `mkdir`. A script with anything else fails that job without running.
- `pip` runs with no package index. It can install pantry from its local folder, but can't download from PyPI. Options that name a remote source, such as `--index-url`, are refused.
- Commands run in a throwaway folder with `HOME` pointed inside it.

These limits reduce risk; they are not a full sandbox. Run the benchmark on a machine where that trade-off is acceptable.

Each session runs with `--setting-sources project`, so your personal Claude Code settings, memory and skills don't affect results. Sessions aren't saved to your history.
