# Benchmark report

Writer models: haiku. Runs per task and condition: 5. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 5 | 88% | 2.70 | 10% | 1.9 | 0.6 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 5 | 76% | 1.70 | 30% | 1.4 | 0 | 0 |
| `prompt-v3` (Wiki-Gnome prompt.md, v3) | 5 | 64% | 1.60 | 60% | 0.5 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 3 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt` | `prompt-v3` |
|---|---|---|---|
| `pantry/readme` | 88%, 2.70 | 76%, 1.70 | 64%, 1.60 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt` | `prompt-v3` |
|---|---|---|---|
| `pantry/install` | 40% | 100% | 100% |
| `pantry/add` | 100% | 60% | 40% |
| `pantry/check` | 100% | 60% | 40% |
| `pantry/env` | 100% | 100% | 100% |
| `pantry/use` | 100% | 60% | 40% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `prompt` | `prompt-v3` |
|---|---|---|---|
| `pypi-install` | 3 | 0 | 0 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 187.2 | 0.0 | 7.5 | 0 | 8.8 | 0.4 | 0 |
| `prompt` | 0% | 282.2 | 0.0 | 8.0 | 0 | 8.8 | 0.5 | 0 |
| `prompt-v3` | 0% | 242.2 | 0.0 | 8.3 | 0 | 9.4 | 0.5 | 0 |
