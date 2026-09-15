# Benchmark report

Writer models: haiku. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 9 | 55% | 3.33 | 11% | 1.3 | 0 | 0 |
| `prompt-v1` (Wiki-Gnome prompt.md, v1) | 9 | 65% | 2.44 | 17% | 0.2 | 0 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 9 | 78% | 2.33 | 39% | 0.9 | 0 | 0 |
| `prompt-v3` (Wiki-Gnome prompt.md, v3) | 9 | 82% | 1.89 | 33% | 0.7 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 4 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt-v1` | `prompt` | `prompt-v3` |
|---|---|---|---|---|
| `changelog` | 56%, 3.00 | 56%, 2.83 | 78%, 2.17 | 72%, 2.00 |
| `docstrings` | 29%, 3.67 | 58%, 3.00 | 75%, 1.50 | 75%, 1.83 |
| `readme` | 80%, 3.33 | 80%, 1.50 | 80%, 3.33 | 100%, 1.83 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt-v1` | `prompt` | `prompt-v3` |
|---|---|---|---|---|
| `install` | 100% | 100% | 100% | 100% |
| `add` | 67% | 67% | 67% | 100% |
| `check` | 67% | 67% | 67% | 100% |
| `env` | 100% | 100% | 100% | 100% |
| `use` | 67% | 67% | 67% | 100% |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 177 | 0.0 | 8.9 | 0 | 10 | 0.6 | 0 |
| `prompt-v1` | 0% | 171.9 | 0.0 | 9.1 | 0 | 10.2 | 0.6 | 0 |
| `prompt` | 0% | 242.8 | 0.5 | 10.9 | 0 | 9.3 | 0.6 | 0 |
| `prompt-v3` | 0% | 197.7 | 0.5 | 10.3 | 0 | 10.1 | 0.6 | 0 |
