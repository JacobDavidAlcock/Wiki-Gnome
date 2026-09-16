# Pooled comparison

Runs pooled: useful-v5. Writer models: sonnet.

## Reader success

Share of reader jobs that worked, pooled across runs, with a 95% bootstrap interval. `n` is the number of docs.

| Version | `pantry/changelog` | `pantry/docstrings` | `pantry/readme` | `tally/changelog` | `tally/docstrings` | `tally/readme` | `all` |
|---|---|---|---|---|---|---|---|
| `none` | 83% (83–83), n=3 | 42% (12–62), n=3 | 60% (40–100), n=3 | 81% (71–100), n=3 | 74% (67–78), n=3 | 89% (67–100), n=3 | 71% (59–80), n=18 |
| `oneline` | 83% (83–83), n=3 | 50% (38–62), n=3 | 80% (40–100), n=3 | 67% (57–71), n=3 | 33% (33–33), n=3 | 83% (83–83), n=3 | 63% (52–73), n=18 |
| `prompt-v5` | 94% (83–100), n=3 | 88% (75–100), n=3 | 93% (80–100), n=3 | 76% (57–100), n=3 | 100% (100–100), n=3 | 100% (100–100), n=3 | 92% (85–98), n=18 |

## Head-to-head in the blind ranking

Each cell shows how often the row version was ranked above the column version, when the judge saw both.

### `pantry/changelog`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 0% of 6 | 0% of 6 |
| `oneline` | 100% of 6 |  | 33% of 6 |
| `prompt-v5` | 100% of 6 | 67% of 6 |  |

### `pantry/docstrings`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 83% of 6 | 0% of 6 |
| `oneline` | 17% of 6 |  | 0% of 6 |
| `prompt-v5` | 100% of 6 | 100% of 6 |  |

### `pantry/readme`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 33% of 6 | 0% of 6 |
| `oneline` | 67% of 6 |  | 0% of 6 |
| `prompt-v5` | 100% of 6 | 100% of 6 |  |

### `tally/changelog`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 100% of 6 | 67% of 6 |
| `oneline` | 0% of 6 |  | 33% of 6 |
| `prompt-v5` | 33% of 6 | 67% of 6 |  |

### `tally/docstrings`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 100% of 6 | 0% of 6 |
| `oneline` | 0% of 6 |  | 0% of 6 |
| `prompt-v5` | 100% of 6 | 100% of 6 |  |

### `tally/readme`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 67% of 6 | 0% of 6 |
| `oneline` | 33% of 6 |  | 0% of 6 |
| `prompt-v5` | 100% of 6 | 100% of 6 |  |

### `all`

| | `none` | `oneline` | `prompt-v5` |
|---|---|---|---|
| `none` |  | 64% of 36 | 11% of 36 |
| `oneline` | 36% of 36 |  | 11% of 36 |
| `prompt-v5` | 89% of 36 | 89% of 36 |  |

