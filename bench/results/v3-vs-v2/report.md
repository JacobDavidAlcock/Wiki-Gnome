# Benchmark report

Writer models: haiku. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 9 | 48% | 3.06 | 6% | 0.7 | 0.1 | 0 |
| `prompt-v1` (Wiki-Gnome prompt.md, v1) | 9 | 57% | 2.89 | 6% | 1 | 0 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 9 | 80% | 2.28 | 22% | 0.7 | 0 | 0 |
| `prompt-v2` (Wiki-Gnome prompt.md, v2) | 9 | 80% | 1.78 | 67% | 0.6 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 4 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt-v1` | `prompt` | `prompt-v2` |
|---|---|---|---|---|
| `pantry/changelog` | 50%, 3.33 | 50%, 3.00 | 78%, 2.33 | 72%, 1.33 |
| `pantry/docstrings` | 33%, 3.50 | 42%, 2.83 | 62%, 2.67 | 88%, 1.00 |
| `pantry/readme` | 60%, 2.33 | 80%, 2.83 | 100%, 1.83 | 80%, 3.00 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt-v1` | `prompt` | `prompt-v2` |
|---|---|---|---|---|
| `pantry/install` | 100% | 100% | 100% | 100% |
| `pantry/add` | 33% | 67% | 100% | 67% |
| `pantry/check` | 33% | 67% | 100% | 67% |
| `pantry/env` | 100% | 100% | 100% | 100% |
| `pantry/use` | 33% | 67% | 100% | 67% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `prompt-v1` | `prompt` | `prompt-v2` |
|---|---|---|---|---|
| `pypi-install` | 1 | 0 | 0 | 0 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 151.2 | 0.0 | 8.2 | 0 | 10 | 0.5 | 0 |
| `prompt-v1` | 0% | 173.2 | 0.0 | 8.7 | 0 | 11.9 | 0.6 | 0 |
| `prompt` | 0% | 220.1 | 0.6 | 9.9 | 0 | 9.8 | 0.6 | 0 |
| `prompt-v2` | 0% | 263.7 | 0.0 | 10.4 | 0 | 9.2 | 0.6 | 0 |
