# Benchmark report

Writer models: haiku, sonnet. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 36 | 60% | 2.28 | 11% | 1.2 | 0.1 | 0 |
| `oneline` (One-line prompt) | 36 | 58% | 2.39 | 11% | 1.3 | 0.2 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 36 | 83% | 1.33 | 78% | 1.1 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 3 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `oneline` | `prompt` |
|---|---|---|---|
| `pantry/changelog` | 72%, 2.75 | 75%, 1.75 | 83%, 1.50 |
| `pantry/docstrings` | 42%, 2.00 | 33%, 2.83 | 90%, 1.17 |
| `pantry/readme` | 70%, 2.25 | 90%, 2.17 | 83%, 1.58 |
| `tally/changelog` | 43%, 2.00 | 43%, 2.33 | 62%, 1.67 |
| `tally/docstrings` | 50%, 2.08 | 22%, 2.92 | 85%, 1.00 |
| `tally/readme` | 86%, 2.58 | 86%, 2.33 | 97%, 1.08 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `oneline` | `prompt` |
|---|---|---|---|
| `pantry/install` | 100% | 100% | 100% |
| `pantry/add` | 50% | 83% | 67% |
| `pantry/check` | 50% | 83% | 67% |
| `pantry/env` | 100% | 100% | 100% |
| `pantry/use` | 50% | 83% | 83% |
| `tally/install` | 33% | 33% | 100% |
| `tally/balance` | 100% | 100% | 100% |
| `tally/weights` | 83% | 83% | 83% |
| `tally/settle` | 100% | 100% | 100% |
| `tally/save_load` | 100% | 100% | 100% |
| `tally/error` | 100% | 100% | 100% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `oneline` | `prompt` |
|---|---|---|---|
| `pypi-install` | 4 | 6 | 0 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 219.0 | 0.2 | 10.8 | 0 | 10.8 | 0.6 | 0 |
| `oneline` | 0% | 214.5 | 0.1 | 11.0 | 0 | 11.0 | 0.6 | 0 |
| `prompt` | 0% | 314.2 | 0.6 | 11.6 | 0.0 | 12.3 | 0.9 | 0 |
