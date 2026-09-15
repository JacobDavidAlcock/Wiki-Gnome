# Benchmark report

Writer models: haiku. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 18 | 60% | 2.19 | 19% | 2.0 | 0.2 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 18 | 66% | 1.64 | 58% | 1.6 | 0.1 | 0 |
| `prompt-v4` (Wiki-Gnome prompt.md, v4) | 18 | 70% | 2.17 | 22% | 1.8 | 0.2 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 3 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt` | `prompt-v4` |
|---|---|---|---|
| `pantry/changelog` | 56%, 1.83 | 78%, 1.17 | 78%, 3.00 |
| `pantry/docstrings` | 33%, 2.67 | 83%, 1.00 | 71%, 2.33 |
| `pantry/readme` | 100%, 2.50 | 47%, 1.83 | 87%, 1.67 |
| `tally/changelog` | 38%, 2.50 | 62%, 1.67 | 48%, 1.83 |
| `tally/docstrings` | 44%, 1.83 | 56%, 1.67 | 56%, 2.50 |
| `tally/readme` | 89%, 1.83 | 72%, 2.50 | 83%, 1.67 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt` | `prompt-v4` |
|---|---|---|---|
| `pantry/install` | 100% | 100% | 100% |
| `pantry/add` | 100% | 0% | 67% |
| `pantry/check` | 100% | 33% | 100% |
| `pantry/env` | 100% | 100% | 100% |
| `pantry/use` | 100% | 0% | 67% |
| `tally/install` | 33% | 33% | 33% |
| `tally/balance` | 100% | 100% | 100% |
| `tally/weights` | 100% | 33% | 67% |
| `tally/settle` | 100% | 67% | 100% |
| `tally/save_load` | 100% | 100% | 100% |
| `tally/error` | 100% | 100% | 100% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `prompt` | `prompt-v4` |
|---|---|---|---|
| `pypi-install` | 3 | 2 | 3 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 221.4 | 0.0 | 8.6 | 0 | 11.1 | 0.6 | 0 |
| `prompt` | 0% | 272.5 | 0.2 | 9.4 | 0 | 10 | 0.6 | 0 |
| `prompt-v4` | 0% | 278.3 | 0.2 | 10.3 | 0.1 | 11.1 | 0.6 | 0 |
