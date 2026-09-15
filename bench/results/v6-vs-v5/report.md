# Benchmark report

Writer models: haiku. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 18 | 47% | 3.39 | 6% | 1.6 | 0.2 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 18 | 70% | 2.03 | 42% | 1.5 | 0.2 | 0 |
| `prompt-v4` (Wiki-Gnome prompt.md, v4) | 18 | 65% | 2.72 | 8% | 1.4 | 0.2 | 0 |
| `prompt-v5` (Wiki-Gnome prompt.md, v5) | 18 | 71% | 1.86 | 44% | 1 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 4 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt` | `prompt-v4` | `prompt-v5` |
|---|---|---|---|---|
| `pantry/changelog` | 50%, 3.33 | 67%, 1.50 | 67%, 2.67 | 67%, 2.50 |
| `pantry/docstrings` | 25%, 4.00 | 88%, 1.33 | 75%, 3.00 | 88%, 1.67 |
| `pantry/readme` | 80%, 2.83 | 93%, 2.83 | 80%, 2.33 | 80%, 2.00 |
| `tally/changelog` | 10%, 3.83 | 43%, 2.17 | 43%, 2.33 | 43%, 1.67 |
| `tally/docstrings` | 48%, 3.50 | 56%, 1.50 | 37%, 3.17 | 56%, 1.83 |
| `tally/readme` | 72%, 2.83 | 72%, 2.83 | 89%, 2.83 | 94%, 1.50 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt` | `prompt-v4` | `prompt-v5` |
|---|---|---|---|---|
| `pantry/install` | 100% | 67% | 100% | 100% |
| `pantry/add` | 67% | 100% | 67% | 67% |
| `pantry/check` | 67% | 100% | 67% | 67% |
| `pantry/env` | 100% | 100% | 100% | 100% |
| `pantry/use` | 67% | 100% | 67% | 67% |
| `tally/install` | 0% | 0% | 67% | 100% |
| `tally/balance` | 100% | 100% | 100% | 100% |
| `tally/weights` | 67% | 33% | 67% | 67% |
| `tally/settle` | 67% | 100% | 100% | 100% |
| `tally/save_load` | 100% | 100% | 100% | 100% |
| `tally/error` | 100% | 100% | 100% | 100% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `prompt` | `prompt-v4` | `prompt-v5` |
|---|---|---|---|---|
| `home-default-file` | 1 | 0 | 0 | 0 |
| `pypi-install` | 3 | 4 | 3 | 0 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 209 | 0.1 | 8.4 | 0.1 | 11.4 | 0.6 | 0 |
| `prompt` | 0% | 254.7 | 0.4 | 9.5 | 0 | 11.8 | 0.7 | 0 |
| `prompt-v4` | 0% | 293.4 | 0.4 | 10.3 | 0 | 11.2 | 0.8 | 0 |
| `prompt-v5` | 0% | 274.9 | 0.0 | 10.2 | 0 | 11.4 | 0.7 | 0 |
