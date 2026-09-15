# Pooled comparison

Runs pooled: pilot, v2-vs-v1, v3-vs-v2, v4-vs-v3, readme-v4-vs-v3.

## Reader success

Share of reader jobs that worked, pooled across runs, with a 95% bootstrap interval. `n` is the number of docs.

| Version | `changelog` | `docstrings` | `readme` | `all` |
|---|---|---|---|---|
| `none` | 58% (47–67), n=11 | 35% (24–48), n=11 | 81% (68–92), n=16 | 57% (48–67), n=38 |
| `oneline` | 67% (67–67), n=2 | 31% (25–38), n=2 | 100% (100–100), n=2 | 61% (40–88), n=6 |
| `prompt-v1` | 58% (52–64), n=11 | 64% (52–75), n=11 | 78% (62–95), n=11 | 66% (58–73), n=33 |
| `prompt-v2` | 78% (72–83), n=6 | 81% (77–85), n=6 | 60% (40–80), n=6 | 75% (66–82), n=18 |
| `prompt-v3` | 75% (69–81), n=6 | 69% (54–79), n=6 | 84% (67–100), n=11 | 76% (68–84), n=23 |
| `prompt-v4` | 78% (67–83), n=3 | 75% (75–75), n=3 | 78% (55–100), n=8 | 77% (66–87), n=14 |
| `skill-v1` | 67% (67–67), n=2 | 31% (25–38), n=2 | 100% (100–100), n=2 | 61% (40–88), n=6 |
| `skill-v2` | 56% (33–67), n=3 | 46% (25–75), n=3 | 100% (100–100), n=3 | 63% (46–81), n=9 |

## Head-to-head in the blind ranking

Each cell shows how often the row version was ranked above the column version, when the judge saw both.

### `changelog`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|
| `none` |  | 50% of 4 | 50% of 22 | 17% of 12 | 33% of 12 | 33% of 6 | 50% of 4 | 67% of 6 |
| `oneline` | 50% of 4 |  | 50% of 4 | – | – | – | 50% of 4 | – |
| `prompt-v1` | 50% of 22 | 50% of 4 |  | 17% of 12 | 25% of 12 | 33% of 6 | 50% of 4 | 67% of 6 |
| `prompt-v2` | 83% of 12 | – | 83% of 12 |  | 67% of 6 | – | – | 67% of 6 |
| `prompt-v3` | 67% of 12 | – | 75% of 12 | 33% of 6 |  | 50% of 6 | – | – |
| `prompt-v4` | 67% of 6 | – | 67% of 6 | – | 50% of 6 |  | – | – |
| `skill-v1` | 50% of 4 | 50% of 4 | 50% of 4 | – | – | – |  | – |
| `skill-v2` | 33% of 6 | – | 33% of 6 | 33% of 6 | – | – | – |  |

### `docstrings`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|
| `none` |  | 75% of 4 | 18% of 22 | 8% of 12 | 8% of 12 | 0% of 6 | 50% of 4 | 67% of 6 |
| `oneline` | 25% of 4 |  | 0% of 4 | – | – | – | 75% of 4 | – |
| `prompt-v1` | 82% of 22 | 100% of 4 |  | 50% of 12 | 33% of 12 | 17% of 6 | 100% of 4 | 100% of 6 |
| `prompt-v2` | 92% of 12 | – | 50% of 12 |  | 100% of 6 | – | – | 83% of 6 |
| `prompt-v3` | 92% of 12 | – | 67% of 12 | 0% of 6 |  | 33% of 6 | – | – |
| `prompt-v4` | 100% of 6 | – | 83% of 6 | – | 67% of 6 |  | – | – |
| `skill-v1` | 50% of 4 | 25% of 4 | 0% of 4 | – | – | – |  | – |
| `skill-v2` | 33% of 6 | – | 0% of 6 | 17% of 6 | – | – | – |  |

### `readme`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|
| `none` |  | 25% of 4 | 27% of 22 | 67% of 12 | 18% of 22 | 31% of 16 | 0% of 4 | 50% of 6 |
| `oneline` | 75% of 4 |  | 50% of 4 | – | – | – | 50% of 4 | – |
| `prompt-v1` | 73% of 22 | 50% of 4 |  | 83% of 12 | 33% of 12 | 100% of 6 | 75% of 4 | 67% of 6 |
| `prompt-v2` | 33% of 12 | – | 17% of 12 |  | 33% of 6 | – | – | 17% of 6 |
| `prompt-v3` | 82% of 22 | – | 67% of 12 | 67% of 6 |  | 62% of 16 | – | – |
| `prompt-v4` | 69% of 16 | – | 0% of 6 | – | 38% of 16 |  | – | – |
| `skill-v1` | 100% of 4 | 50% of 4 | 25% of 4 | – | – | – |  | – |
| `skill-v2` | 50% of 6 | – | 33% of 6 | 83% of 6 | – | – | – |  |

### `all`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|
| `none` |  | 50% of 12 | 32% of 66 | 31% of 36 | 20% of 46 | 25% of 28 | 33% of 12 | 61% of 18 |
| `oneline` | 50% of 12 |  | 33% of 12 | – | – | – | 58% of 12 | – |
| `prompt-v1` | 68% of 66 | 67% of 12 |  | 50% of 36 | 31% of 36 | 50% of 18 | 75% of 12 | 78% of 18 |
| `prompt-v2` | 69% of 36 | – | 50% of 36 |  | 67% of 18 | – | – | 56% of 18 |
| `prompt-v3` | 80% of 46 | – | 69% of 36 | 33% of 18 |  | 54% of 28 | – | – |
| `prompt-v4` | 75% of 28 | – | 50% of 18 | – | 46% of 28 |  | – | – |
| `skill-v1` | 67% of 12 | 42% of 12 | 25% of 12 | – | – | – |  | – |
| `skill-v2` | 39% of 18 | – | 22% of 18 | 44% of 18 | – | – | – |  |

