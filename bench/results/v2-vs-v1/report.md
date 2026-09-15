# Benchmark report

Writer models: haiku. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 9 | 70% | 2.67 | 17% | 0.9 | 0 | 0 |
| `prompt-v1` (Wiki-Gnome prompt.md, v1) | 9 | 77% | 1.78 | 50% | 0.8 | 0 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 9 | 66% | 2.61 | 22% | 0.8 | 0.2 | 0 |
| `skill` (Wiki-Gnome skill) | 9 | 67% | 2.94 | 11% | 1.1 | 0 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 4 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt-v1` | `prompt` | `skill` |
|---|---|---|---|---|
| `pantry/changelog` | 61%, 2.33 | 67%, 2.67 | 83%, 2.00 | 56%, 3.00 |
| `pantry/docstrings` | 50%, 3.17 | 83%, 1.00 | 75%, 2.33 | 46%, 3.50 |
| `pantry/readme` | 100%, 2.50 | 80%, 1.67 | 40%, 3.50 | 100%, 2.33 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt-v1` | `prompt` | `skill` |
|---|---|---|---|---|
| `pantry/install` | 100% | 100% | 100% | 100% |
| `pantry/add` | 100% | 67% | 0% | 100% |
| `pantry/check` | 100% | 67% | 0% | 100% |
| `pantry/env` | 100% | 100% | 100% | 100% |
| `pantry/use` | 100% | 67% | 0% | 100% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `prompt-v1` | `prompt` | `skill` |
|---|---|---|---|---|
| `file-after-command` | 0 | 0 | 2 | 0 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 169.3 | 0.0 | 9.3 | 0 | 10.1 | 0.5 | 0 |
| `prompt-v1` | 0% | 201.2 | 0.6 | 9.8 | 0 | 10 | 0.6 | 0 |
| `prompt` | 0% | 223.3 | 0.6 | 10.5 | 0 | 9.3 | 0.6 | 0 |
| `skill` | 0% | 193.6 | 0.0 | 9.1 | 0 | 9.2 | 0.5 | 0 |
