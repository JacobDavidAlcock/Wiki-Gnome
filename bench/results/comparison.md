# Pooled comparison

Runs pooled: pilot, v2-vs-v1, v3-vs-v2, v4-vs-v3, readme-v4-vs-v3, tally-v4, v5-vs-v4, v6-vs-v5.

## Reader success

Share of reader jobs that worked, pooled across runs, with a 95% bootstrap interval. `n` is the number of docs.

| Version | `pantry/changelog` | `pantry/docstrings` | `pantry/readme` | `tally/api-reference` | `tally/changelog` | `tally/docstrings` | `tally/readme` | `all` |
|---|---|---|---|---|---|---|---|---|
| `none` | 56% (49–62), n=17 | 33% (25–43), n=17 | 84% (73–94), n=22 | 100% (100–100), n=3 | 16% (3–33), n=9 | 46% (37–54), n=9 | 76% (69–83), n=9 | 53% (47–60), n=86 |
| `oneline` | 67% (67–67), n=2 | 31% (25–38), n=2 | 100% (100–100), n=2 | – | – | – | – | 61% (40–88), n=6 |
| `prompt-v1` | 58% (52–64), n=11 | 64% (52–75), n=11 | 78% (62–95), n=11 | 100% (100–100), n=3 | 38% (29–57), n=3 | 59% (56–67), n=3 | 83% (67–100), n=3 | 66% (60–72), n=45 |
| `prompt-v2` | 78% (72–83), n=6 | 81% (77–85), n=6 | 60% (40–80), n=6 | – | – | – | – | 75% (66–82), n=18 |
| `prompt-v3` | 75% (69–81), n=6 | 69% (54–79), n=6 | 84% (67–100), n=11 | – | – | – | – | 76% (68–84), n=23 |
| `prompt-v4` | 74% (69–80), n=9 | 74% (69–78), n=9 | 80% (66–93), n=14 | 100% (100–100), n=3 | 48% (35–57), n=9 | 48% (42–56), n=9 | 87% (78–94), n=9 | 68% (63–74), n=62 |
| `prompt-v5` | 72% (67–78), n=6 | 85% (79–92), n=6 | 63% (43–83), n=6 | – | 52% (36–67), n=6 | 56% (48–63), n=6 | 83% (72–94), n=6 | 68% (62–74), n=36 |
| `prompt-v6` | 67% (50–83), n=3 | 88% (88–88), n=3 | 93% (80–100), n=3 | – | 43% (43–43), n=3 | 56% (56–56), n=3 | 72% (67–83), n=3 | 68% (60–77), n=18 |
| `skill-forced-v4` | – | – | – | 93% (80–100), n=3 | 38% (14–57), n=3 | 59% (56–67), n=3 | 78% (67–83), n=3 | 64% (52–77), n=12 |
| `skill-v1` | 67% (67–67), n=2 | 31% (25–38), n=2 | 100% (100–100), n=2 | – | – | – | – | 61% (40–88), n=6 |
| `skill-v2` | 56% (33–67), n=3 | 46% (25–75), n=3 | 100% (100–100), n=3 | – | – | – | – | 63% (46–81), n=9 |

## Head-to-head in the blind ranking

Each cell shows how often the row version was ranked above the column version, when the judge saw both.

### `pantry/changelog`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` |  | 50% of 4 | 50% of 22 | 17% of 12 | 33% of 12 | 56% of 18 | 25% of 12 | 0% of 6 | 50% of 4 | 67% of 6 |
| `oneline` | 50% of 4 |  | 50% of 4 | – | – | – | – | – | 50% of 4 | – |
| `prompt-v1` | 50% of 22 | 50% of 4 |  | 17% of 12 | 25% of 12 | 33% of 6 | – | – | 50% of 4 | 67% of 6 |
| `prompt-v2` | 83% of 12 | – | 83% of 12 |  | 67% of 6 | – | – | – | – | 67% of 6 |
| `prompt-v3` | 67% of 12 | – | 75% of 12 | 33% of 6 |  | 50% of 6 | – | – | – | – |
| `prompt-v4` | 44% of 18 | – | 67% of 6 | – | 50% of 6 |  | 25% of 12 | 17% of 6 | – | – |
| `prompt-v5` | 75% of 12 | – | – | – | – | 75% of 12 |  | 33% of 6 | – | – |
| `prompt-v6` | 100% of 6 | – | – | – | – | 83% of 6 | 67% of 6 |  | – | – |
| `skill-v1` | 50% of 4 | 50% of 4 | 50% of 4 | – | – | – | – | – |  | – |
| `skill-v2` | 33% of 6 | – | 33% of 6 | 33% of 6 | – | – | – | – | – |  |

### `pantry/docstrings`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` |  | 75% of 4 | 18% of 22 | 8% of 12 | 8% of 12 | 11% of 18 | 0% of 12 | 0% of 6 | 50% of 4 | 67% of 6 |
| `oneline` | 25% of 4 |  | 0% of 4 | – | – | – | – | – | 75% of 4 | – |
| `prompt-v1` | 82% of 22 | 100% of 4 |  | 50% of 12 | 33% of 12 | 17% of 6 | – | – | 100% of 4 | 100% of 6 |
| `prompt-v2` | 92% of 12 | – | 50% of 12 |  | 100% of 6 | – | – | – | – | 83% of 6 |
| `prompt-v3` | 92% of 12 | – | 67% of 12 | 0% of 6 |  | 33% of 6 | – | – | – | – |
| `prompt-v4` | 89% of 18 | – | 83% of 6 | – | 67% of 6 |  | 0% of 12 | 0% of 6 | – | – |
| `prompt-v5` | 100% of 12 | – | – | – | – | 100% of 12 |  | 33% of 6 | – | – |
| `prompt-v6` | 100% of 6 | – | – | – | – | 100% of 6 | 67% of 6 |  | – | – |
| `skill-v1` | 50% of 4 | 25% of 4 | 0% of 4 | – | – | – | – | – |  | – |
| `skill-v2` | 33% of 6 | – | 0% of 6 | 17% of 6 | – | – | – | – | – |  |

### `pantry/readme`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` |  | 25% of 4 | 27% of 22 | 67% of 12 | 18% of 22 | 29% of 28 | 33% of 12 | 50% of 6 | 0% of 4 | 50% of 6 |
| `oneline` | 75% of 4 |  | 50% of 4 | – | – | – | – | – | 50% of 4 | – |
| `prompt-v1` | 73% of 22 | 50% of 4 |  | 83% of 12 | 33% of 12 | 100% of 6 | – | – | 75% of 4 | 67% of 6 |
| `prompt-v2` | 33% of 12 | – | 17% of 12 |  | 33% of 6 | – | – | – | – | 17% of 6 |
| `prompt-v3` | 82% of 22 | – | 67% of 12 | 67% of 6 |  | 62% of 16 | – | – | – | – |
| `prompt-v4` | 71% of 28 | – | 0% of 6 | – | 38% of 16 |  | 42% of 12 | 67% of 6 | – | – |
| `prompt-v5` | 67% of 12 | – | – | – | – | 58% of 12 |  | 67% of 6 | – | – |
| `prompt-v6` | 50% of 6 | – | – | – | – | 33% of 6 | 33% of 6 |  | – | – |
| `skill-v1` | 100% of 4 | 50% of 4 | 25% of 4 | – | – | – | – | – |  | – |
| `skill-v2` | 50% of 6 | – | 33% of 6 | 83% of 6 | – | – | – | – | – |  |

### `tally/api-reference`

| | `none` | `prompt-v1` | `prompt-v4` | `skill-forced-v4` |
|---|---|---|---|---|
| `none` |  | 67% of 6 | 33% of 6 | 33% of 6 |
| `prompt-v1` | 33% of 6 |  | 33% of 6 | 0% of 6 |
| `prompt-v4` | 67% of 6 | 67% of 6 |  | 33% of 6 |
| `skill-forced-v4` | 67% of 6 | 100% of 6 | 67% of 6 |  |

### `tally/changelog`

| | `none` | `prompt-v1` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-forced-v4` |
|---|---|---|---|---|---|---|
| `none` |  | 0% of 6 | 11% of 18 | 8% of 12 | 17% of 6 | 17% of 6 |
| `prompt-v1` | 100% of 6 |  | 0% of 6 | – | – | 33% of 6 |
| `prompt-v4` | 89% of 18 | 100% of 6 |  | 33% of 12 | 50% of 6 | 67% of 6 |
| `prompt-v5` | 92% of 12 | – | 67% of 12 |  | 50% of 6 | – |
| `prompt-v6` | 83% of 6 | – | 50% of 6 | 50% of 6 |  | – |
| `skill-forced-v4` | 83% of 6 | 67% of 6 | 33% of 6 | – | – |  |

### `tally/docstrings`

| | `none` | `prompt-v1` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-forced-v4` |
|---|---|---|---|---|---|---|
| `none` |  | 67% of 6 | 61% of 18 | 25% of 12 | 0% of 6 | 50% of 6 |
| `prompt-v1` | 33% of 6 |  | 100% of 6 | – | – | 67% of 6 |
| `prompt-v4` | 39% of 18 | 0% of 6 |  | 17% of 12 | 17% of 6 | 33% of 6 |
| `prompt-v5` | 75% of 12 | – | 83% of 12 |  | 33% of 6 | – |
| `prompt-v6` | 100% of 6 | – | 83% of 6 | 67% of 6 |  | – |
| `skill-forced-v4` | 50% of 6 | 33% of 6 | 67% of 6 | – | – |  |

### `tally/readme`

| | `none` | `prompt-v1` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-forced-v4` |
|---|---|---|---|---|---|---|
| `none` |  | 50% of 6 | 56% of 18 | 42% of 12 | 50% of 6 | 33% of 6 |
| `prompt-v1` | 50% of 6 |  | 33% of 6 | – | – | 50% of 6 |
| `prompt-v4` | 44% of 18 | 67% of 6 |  | 50% of 12 | 50% of 6 | 33% of 6 |
| `prompt-v5` | 58% of 12 | – | 50% of 12 |  | 83% of 6 | – |
| `prompt-v6` | 50% of 6 | – | 50% of 6 | 17% of 6 |  | – |
| `skill-forced-v4` | 67% of 6 | 50% of 6 | 67% of 6 | – | – |  |

### `all`

| | `none` | `oneline` | `prompt-v1` | `prompt-v2` | `prompt-v3` | `prompt-v4` | `prompt-v5` | `prompt-v6` | `skill-forced-v4` | `skill-v1` | `skill-v2` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `none` |  | 50% of 12 | 36% of 90 | 31% of 36 | 20% of 46 | 36% of 124 | 22% of 72 | 19% of 36 | 33% of 24 | 33% of 12 | 61% of 18 |
| `oneline` | 50% of 12 |  | 33% of 12 | – | – | – | – | – | – | 58% of 12 | – |
| `prompt-v1` | 64% of 90 | 67% of 12 |  | 50% of 36 | 31% of 36 | 45% of 42 | – | – | 38% of 24 | 75% of 12 | 78% of 18 |
| `prompt-v2` | 69% of 36 | – | 50% of 36 |  | 67% of 18 | – | – | – | – | – | 56% of 18 |
| `prompt-v3` | 80% of 46 | – | 69% of 36 | 33% of 18 |  | 54% of 28 | – | – | – | – | – |
| `prompt-v4` | 64% of 124 | – | 55% of 42 | – | 46% of 28 |  | 28% of 72 | 33% of 36 | 42% of 24 | – | – |
| `prompt-v5` | 78% of 72 | – | – | – | – | 72% of 72 |  | 50% of 36 | – | – | – |
| `prompt-v6` | 81% of 36 | – | – | – | – | 67% of 36 | 50% of 36 |  | – | – | – |
| `skill-forced-v4` | 67% of 24 | – | 62% of 24 | – | – | 58% of 24 | – | – |  | – | – |
| `skill-v1` | 67% of 12 | 42% of 12 | 25% of 12 | – | – | – | – | – | – |  | – |
| `skill-v2` | 39% of 18 | – | 22% of 18 | 44% of 18 | – | – | – | – | – | – |  |

