# Benchmark report

Writer models: haiku. Runs per task and condition: 3. Reader model: haiku. Judge model: sonnet, 2 passes per task and run.

## Headline results

Higher is better for reader success and first place. Lower is better for mean rank, errors and broken code.

| Condition | Runs | Reader success | Mean rank | First place | Judged errors per doc | Invented-fact patterns per doc | Broken code |
|---|---|---|---|---|---|---|---|
| `none` (No guidance) | 12 | 53% | 2.79 | 25% | 1.9 | 0.3 | 0 |
| `prompt-v1` (Wiki-Gnome prompt.md, v1) | 12 | 70% | 2.67 | 8% | 1.9 | 0.2 | 0 |
| `prompt` (Wiki-Gnome prompt.md) | 12 | 73% | 2.42 | 29% | 1.9 | 0.2 | 0 |
| `skill-forced` (Wiki-Gnome skill, loaded by instruction) | 12 | 67% | 2.12 | 38% | 1.7 | 0.2 | 0 |

- **Reader success:** share of reader jobs that worked when a fresh session followed only the doc. Commands were run for real; quiz answers were marked against the answer key.
- **Mean rank:** average position in the blind ranking, where 1 is best and 4 is worst.
- **Judged errors:** wrong or invented details the judge found, checked against `fixtures/pantry-facts.md`.
- **Invented-fact patterns:** automatic matches for known false claims, such as `pip install pantry`.
- **Broken code:** runs where the writer changed code or the tests stopped passing.

## Results by task

Each cell shows reader success, then mean rank.

| Task | `none` | `prompt-v1` | `prompt` | `skill-forced` |
|---|---|---|---|---|
| `tally/api-reference` | 100%, 2.67 | 100%, 3.33 | 100%, 2.33 | 93%, 1.67 |
| `tally/changelog` | 0%, 3.83 | 38%, 2.67 | 52%, 1.33 | 38%, 2.17 |
| `tally/docstrings` | 44%, 2.17 | 59%, 2.00 | 52%, 3.33 | 59%, 2.50 |
| `tally/readme` | 67%, 2.50 | 83%, 2.67 | 89%, 2.67 | 78%, 2.17 |

## Reader jobs that worked

Share of runs where the reader's commands for each job produced the right result.

| Job | `none` | `prompt-v1` | `prompt` | `skill-forced` |
|---|---|---|---|---|
| `tally/balance` | 100% | 100% | 100% | 100% |
| `tally/weights` | 50% | 83% | 100% | 67% |
| `tally/settle` | 100% | 100% | 100% | 100% |
| `tally/save_load` | 100% | 100% | 100% | 100% |
| `tally/error` | 100% | 100% | 100% | 100% |
| `tally/install` | 0% | 33% | 33% | 0% |

## Invented facts found automatically

Number of docs matching each pattern.

| Pattern | `none` | `prompt-v1` | `prompt` | `skill-forced` |
|---|---|---|---|---|
| `float-amount` | 0 | 1 | 0 | 0 |
| `pypi-install` | 4 | 2 | 3 | 3 |

## Style and cost

These show whether the style rules were followed. They don't show whether docs got better.

| Condition | Skill loaded | Words | Banned words per 1,000 | Words per sentence | Filler headings | Writer turns | Writer minutes | Session errors |
|---|---|---|---|---|---|---|---|---|
| `none` | 0% | 427.2 | 0.0 | 9.1 | 0.1 | 12 | 0.7 | 0 |
| `prompt-v1` | 0% | 512.6 | 0.0 | 9.0 | 0 | 12.2 | 0.8 | 0 |
| `prompt` | 0% | 556.1 | 0.1 | 10.2 | 0 | 11.2 | 0.8 | 0 |
| `skill-forced` | 100% | 615.4 | 0.0 | 9.7 | 0.2 | 14.7 | 0.8 | 0 |
