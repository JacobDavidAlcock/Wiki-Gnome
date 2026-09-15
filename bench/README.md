# Wiki-Gnome benchmark

This benchmark measures whether Wiki-Gnome makes AI agents write documentation that works for readers. It runs the same writing tasks with and without Wiki-Gnome, then tests each doc on a fresh session that has only the doc to go on.

Every session runs through Claude Code's non-interactive mode (`claude -p`), so the benchmark uses your Claude subscription, not an API key.

## Run the benchmark

You need:

- Claude Code, signed in to a Claude subscription. Run `claude` once to check.
- Python 3.10 or later.
- Git. On Windows, the Git Bash that ships with Git for Windows.
- Network access once, to download `setuptools` and `wheel` for the offline reader sandbox.

1. Run a pilot from the repository root. This one covers 2 tasks in each project, 4 conditions and 2 runs:

   ```sh
   python bench/run.py --name pilot --tasks readme,docstrings --runs 2
   ```

   The script prints each finished job, then the path to the report:

   ```text
   [32/32] generate tally/docstrings/skill/haiku/run2: ok (41s)
   ...
   Report: bench/results/pilot/report.md
   ```

2. Read `bench/results/pilot/report.md`.

3. If the pilot looks right, run every task in every project:

   ```sh
   python bench/run.py --name full --runs 3
   ```

If a run stops because you hit your plan's usage limit, run the same command again after the limit resets. Finished jobs are skipped, so the benchmark resumes where it stopped.

## Options

| Option | Default | Description |
|---|---|---|
| `--name` | Required | Folder name under `bench/results/`. |
| `--projects` | All projects | Comma-separated project IDs: `pantry`, `tally`. |
| `--tasks` | Every task | Comma-separated task IDs. A task ID runs in every selected project that has it. |
| `--conditions` | `none,oneline,prompt,skill` | Comma-separated condition IDs. |
| `--models` | `haiku` | Writer models, as Claude Code model names or aliases. |
| `--runs` | `3` | Runs per task, condition and model. |
| `--reader-model` | `haiku` | Model for reader tests. |
| `--judge-model` | `sonnet` | Model for the blind ranking. |
| `--shuffles` | `2` | Judge passes per task and run. The second pass shows the docs in reverse order. |
| `--parallel` | `3` | Sessions running at once. Lower it if you hit usage limits quickly. |
| `--stages` | `generate,read,judge,report` | Stages to run. Use `report` alone to rebuild a report. |
| `--clean` | Off | Delete each workspace once its doc is saved, and every temporary folder at the end. |

## What gets compared

| Condition | What the writing session gets |
|---|---|
| `none` | No documentation guidance |
| `oneline` | One appended instruction: "When you write documentation, write clear docs like Stripe's." |
| `prompt` | [`prompt.md`](../prompt.md), appended to the system prompt |
| `skill` | The [`technical-docs-style`](../.claude/skills/technical-docs-style/SKILL.md) skill, installed in the project. The session decides whether to load it. |
| `skill-forced` | The same skill, plus an instruction to load it before starting. |

The `oneline` condition checks whether Wiki-Gnome's full rules beat a one-sentence request for good docs.

`skill` and `skill-forced` answer different questions. `skill` measures what users get, including whether the model loads the skill at all. Claude Haiku 4.5 didn't load it in any of 15 runs. `skill-forced` measures whether the skill's content helps once it's loaded.

## Test projects

Each project in [`projects/`](projects/) is a small codebase built for this benchmark, with no docs and several behaviours a doc must get right.

| Project | What it is | Readers write | Traps a doc must cover |
|---|---|---|---|
| [`pantry`](projects/pantry/) | A command-line tool that tracks food and warns before it expires | Shell commands | `--file` must come before the command; `expiring --check` exits with status 3; the default file is in the working directory |
| [`tally`](projects/tally/) | A Python library that splits shared expenses | Python scripts | Amounts are whole pence, not floats; members must be added first; a positive balance means the member is owed; `Ledger.load` is a class method |

Each project folder holds:

| Path | Contents |
|---|---|
| `current/` | The release the writer documents |
| `previous/` | The earlier release, for the changelog task |
| `facts.md` | The answer key. Writers never see it; the judge does. |
| `bad-doc.md` | A deliberately bad doc, for rewrite tasks. Only `pantry` has one. |
| `project.py` | The project's tasks, reader jobs, quiz questions and invented-fact patterns |

### Tasks

| Project | Task | Request given to the writer | Reader test |
|---|---|---|---|
| `pantry` | `readme` | Write a README.md for this project. | 5 command jobs |
| `pantry` | `cli-reference` | Write reference documentation for the CLI in docs/cli.md. | 4 command jobs |
| `pantry` | `howto-alerts` | Write a how-to guide for daily expiry warnings. | 1 command job |
| `pantry` | `docstrings` | Add docstrings to the functions in pantry/store.py. | 8 questions |
| `pantry` | `changelog` | Write a CHANGELOG.md entry for 0.2.0. | 6 questions |
| `pantry` | `rewrite` | Rewrite a deliberately bad docs/usage.md. | 4 command jobs |
| `tally` | `readme` | Write a README.md for this project. | 6 script jobs |
| `tally` | `api-reference` | Write API reference documentation in docs/api.md. | 5 script jobs |
| `tally` | `docstrings` | Add docstrings to the public classes and methods in tally/ledger.py. | 9 questions |
| `tally` | `changelog` | Write a CHANGELOG.md entry for 2.0.0. | 7 questions |

### Add a project

1. Create `bench/projects/<id>/` with `current/`, `facts.md` and `project.py`. Add `previous/` if it has a changelog task.
2. In `project.py`, define `build(project_dir)` returning a `Project` from [`harness/model.py`](harness/model.py). Use [`projects/tally/project.py`](projects/tally/project.py) as a starting point.
3. Add a known-good and a known-bad answer for every reader job to [`tests/test_harness.py`](tests/test_harness.py), then run the tests described below.

## How docs are scored

The benchmark runs in 4 stages.

1. **Generate.** A writing session runs in a fresh git repository containing the project. It can read and write files, run `git` commands, and run the project, but it can't install packages or commit. The harness then records whether the doc was written, whether existing code changed, and whether the project's tests still pass.
2. **Read.** A new session with no tools gets only the doc.
   - **Command and script jobs:** the reader writes shell commands or Python scripts for a set of jobs, such as installing the project or settling a group's debts. The harness runs them in a sandbox and checks the result against the known answer.
   - **Quiz:** the reader answers multiple-choice questions, with a "the documentation doesn't say" option. Answers are marked against the answer key.
3. **Judge.** A judge session sees every condition's doc for the same task and run, under shuffled labels, plus the project's `facts.md`. It ranks the docs and lists factual errors.
4. **Report.** The harness writes `report.md`, `summary.json`, `docs.jsonl` and `verdicts.jsonl`.

Reader success and factual errors are the main results. Style metrics such as banned-word counts are reported too. A doc written with Wiki-Gnome will score well on its own rules whether or not it helps readers, so those metrics don't show that docs improved.

## Compare a new version with an old one

Earlier versions of the prompt and skill live in [`baselines/`](baselines/), one folder per version. Each folder adds 3 conditions named after it: `baselines/v1/` adds `prompt-v1`, `skill-v1` and `skill-forced-v1`.

To test a change to `prompt.md` or the skill:

1. Check which saved version the current files match. For example, this prints nothing if `prompt.md` is version 5:

   ```sh
   cmp prompt.md bench/baselines/v5/prompt.md
   ```

   If the current files don't match any folder in `baselines/`, save them first under the next version number, such as `v7`:

   ```sh
   mkdir -p bench/baselines/v7/technical-docs-style
   cp prompt.md bench/baselines/v7/prompt.md
   cp .claude/skills/technical-docs-style/SKILL.md bench/baselines/v7/technical-docs-style/
   ```

2. Edit `prompt.md` or the skill.

3. Run the new version against the saved one, so the judge ranks them in the same pass. If the saved version is v5:

   ```sh
   python bench/run.py --name new-vs-v5 --conditions none,prompt-v5,prompt,skill-forced --runs 3
   ```

4. If the new version wins, save it under the next version number with the commands from step 1.

The judge ranks every condition in a run together, so keep to 4 or 5 conditions per run.

## Pool results from several runs

A single run of 3 is noisy: the same version can score 40% on a task in one run and 80% in the next. Before you keep or drop a change, pool every run that tested it:

```sh
python bench/compare.py v4-vs-v3 readme-v4-vs-v3 --out bench/results/comparison.md
```

`compare.py` names each condition after the baseline version it matches, using the `condition_sha256` fingerprints in each run's `config.json`. In the command above, `prompt` becomes `prompt-v4`. Runs from before fingerprints were recorded need `--alias`, such as `--alias v2-vs-v1:prompt=prompt-v2`.

The output has 2 tables:

- **Reader success** for each version and task, with a 95% bootstrap interval and the number of docs. If two versions' intervals overlap heavily, the difference could be noise.
- **Head-to-head** judge results: how often one version was ranked above another when the judge saw both.

## Test the harness

Run the fast tests from the repository root. They don't use Claude:

```sh
python -m unittest discover -s bench/tests -t bench
```

To also run every reader job in a real sandbox, with a known-good and a known-bad answer each, set `WIKI_GNOME_SLOW=1`. The first run builds virtual environments and downloads `setuptools` and `wheel`, and takes about 2 minutes:

```sh
WIKI_GNOME_SLOW=1 python -m unittest discover -s bench/tests -t bench
```

## Where results go

| Path | Contents | In git |
|---|---|---|
| `bench/results/<name>/report.md` | The report | Yes |
| `bench/results/<name>/summary.json` | The numbers behind the report | Yes |
| `bench/results/<name>/docs.jsonl` | One line per doc: scores, checks and style metrics, without transcripts | Yes |
| `bench/results/<name>/verdicts.jsonl` | One line per judge verdict | Yes |
| `bench/results/<name>/config.json` | The run's settings and condition fingerprints | Yes |
| `bench/results/<name>/runs/<project>/<task>/<condition>/<model>/run<n>/` | The doc, the full diff, both session transcripts, the reader's answers and scores | No |
| `bench/results/<name>/judge/<project>/<task>/<model>/run<n>/pass<n>/` | The judge's ranking and transcript | No |

Git ignores `runs/` and `judge/`, because their transcripts add up to megabytes per run. Reports and `compare.py` fall back to `docs.jsonl` and `verdicts.jsonl`, so they also work on a fresh clone.

Workspaces and sandboxes live in your system temp folder under `wiki-gnome-bench/<name>/`. Sandboxes are deleted after each reader job. Pass `--clean` to delete workspaces too.

## Safety

The reader stage runs commands and scripts that a model wrote. The harness limits what they can do:

- Shell jobs run only an allowlist of commands, such as `python`, `pip`, `export`, `mkdir` and the project's own CLI. A script with anything else fails that job without running.
- Python jobs may import only the project's package and a few standard modules such as `json` and `pathlib`. They can't call `open`, `eval`, `exec` or `__import__`, or use most double-underscore attributes.
- `pip` runs with no package index. It can install the project from its local folder, but can't download from PyPI. Options that name a remote source, such as `--index-url`, are refused.
- Everything runs in a throwaway folder with `HOME` pointed inside it.

Writing sessions can run the project and its tests in their workspace. For `tally`, that means any `python` command, because a library can only be tried out with Python code. They can't run `pip`, `git commit` or `git push`.

These limits reduce risk; they are not a full sandbox. Run the benchmark on a machine where that trade-off is acceptable.

Each session runs with `--setting-sources project`, so your personal Claude Code settings, memory and skills don't affect results. Sessions aren't saved to your history.
