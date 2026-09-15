# Benchmark report

Writer models: haiku. Runs per task and condition: 2. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 6 | 54% | 2.92 | 8% | 1.3 | 0 | 0 |
| `oneline` (One-line prompt) | 6 | 66% | 2.58 | 25% | 0.7 | 0 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 6 | 68% | 1.83 | 42% | 0.7 | 0 | 0 |
| `skill` (Wiki-Gnome skill) | 6 | 66% | 2.67 | 25% | 0.7 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 4 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `oneline` | `prompt` | `skill` |
|---|---|---|---|---|
| `changelog` | 67%, 2.25 | 67%, 2.50 | 58%, 2.75 | 67%, 2.50 |
| `docstrings` | 25%, 2.75 | 31%, 3.00 | 75%, 1.00 | 31%, 3.25 |
| `readme` | 70%, 3.75 | 100%, 2.25 | 70%, 1.75 | 100%, 2.25 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `oneline` | `prompt` | `skill` |
|---|---|---|---|---|
| `install` | 100% | 100% | 100% | 100% |
| `add` | 50% | 100% | 50% | 100% |
| `check` | 50% | 100% | 50% | 100% |
| `env` | 100% | 100% | 100% | 100% |
| `use` | 50% | 100% | 50% | 100% |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 204.7 | 0.0 | 9.6 | 0 | 9.5 | 0.5 | 0 |
| `oneline` | 0% | 173.2 | 0.0 | 8.4 | 0 | 9.3 | 0.5 | 0 |
| `prompt` | 0% | 209.8 | 0.7 | 9.6 | 0 | 10.5 | 0.6 | 0 |
| `skill` | 0% | 162 | 0.8 | 8.8 | 0 | 10 | 0.5 | 0 |
