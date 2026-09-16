<p align="center">
  <img src="assets/gnome.png" alt="A grumpy gnome with folded arms sitting on a stack of books, one labelled Glossary" width="240">
</p>

<h1 align="center">Wiki-Gnome</h1>

<p align="center"><em>Wiki-Gnome <del>simply and seamlessly</del> fixes your docs.</em></p>

Wiki-Gnome makes AI agents write documentation that readers can follow. Its rules come from an agent that read a large set of well-regarded technical docs, such as Stripe's and Google's, and worked out what they have in common: second person, one idea per sentence, conditions before instructions, and runnable code examples.

It works. In the [benchmark](#benchmark-results), docs written with Wiki-Gnome got readers through 70% of their jobs with Claude Haiku 4.5 and 92% with Claude Sonnet 5, against 52% and 71% for the same models without it.

Wiki-Gnome comes in two versions with the same rules:

| Version | File | Use it when |
|---|---|---|
| Skill | [`.claude/skills/technical-docs-style/SKILL.md`](.claude/skills/technical-docs-style/SKILL.md) | Your agent supports skills, like Claude Code. |
| Prompt | [`prompt.md`](prompt.md) | Your tool doesn't support skills. Paste it in as a system prompt or custom instructions. |

A skill is a folder of instructions an agent loads on its own when a task matches the skill's description. Claude Sonnet 5 loads this one on its own. Claude Haiku 4.5 doesn't, so with Haiku either use [`prompt.md`](prompt.md) or ask for the skill by name.

## Install the skill

These steps set up Wiki-Gnome in Claude Code.

1. Clone the repository:

   ```sh
   git clone https://github.com/JacobDavidAlcock/Wiki-Gnome.git
   ```

2. Copy the skill folder into your skills directory. If you want the skill in every project, copy it to `~/.claude/skills`:

   ```sh
   mkdir -p ~/.claude/skills
   cp -r Wiki-Gnome/.claude/skills/technical-docs-style ~/.claude/skills/
   ```

   On Windows, run this in PowerShell instead:

   ```powershell
   New-Item -ItemType Directory -Force "$HOME\.claude\skills"
   Copy-Item -Recurse Wiki-Gnome\.claude\skills\technical-docs-style "$HOME\.claude\skills\"
   ```

   If you want the skill in only one project, copy the folder into that project's `.claude/skills` directory instead.

3. Start a new Claude Code session and ask for documentation:

   ```text
   Write a README for this project
   ```

   Claude loads `technical-docs-style` before writing if the model picks it up. If it doesn't, type `/technical-docs-style` to load it by hand.

## Use the prompt

If your tool doesn't support skills, copy the full contents of [`prompt.md`](prompt.md) into its system prompt, custom instructions or project rules. The rules match the skill, but the examples use APIs and payments instead of general codebases.

## See what changes

Here is one sentence from a typical README, before and after Wiki-Gnome:

**Before**

> Please note that the config file will simply be loaded automatically, and an error will be thrown if it can't be found.

**After**

> If `config.yaml` is missing, the CLI exits with status 1.

The rewrite drops "please" and "simply", switches to active voice, puts the condition first and names the actual file and exit code.

## What the style enforces

This is a summary. The full rules are in [`SKILL.md`](.claude/skills/technical-docs-style/SKILL.md).

| Area | Rule |
|---|---|
| Voice | Address the reader as "you". Use active voice and present tense. No marketing words, filler words or blaming the reader. |
| Sentences | One idea per sentence. Define each term inline the first time it appears. Put the condition before the instruction. Use specific numbers. |
| Structure | Each page does one of four jobs, from the [Diátaxis](https://diataxis.fr/) framework: tutorial, how-to guide, reference or explanation. |
| Headings | Name sections after what the reader is trying to do, not after components. |
| Code | Run every command example before including it. Examples are complete, use realistic values and show input and output together. |
| Install | Only document an install method the repository supports. A package name in `pyproject.toml` doesn't mean it's published. |
| Docstrings | Use the project's docstring format, or the language's standard one. Give each parameter's valid values and units, and name every exception the code raises. |
| Changelogs | Put breaking changes first, each with the steps to upgrade. Describe what changed for the reader, not in the code. |
| Formatting | Numbered lists for ordered steps, bullets otherwise. Bold for UI elements, code font for identifiers. |

## Benchmark results

The [`bench/`](bench/) folder tests whether Wiki-Gnome helps readers. An AI model writes docs for two small test projects: `pantry`, a command-line tool, and `tally`, a Python library. A fresh session then follows each doc: its commands and scripts are run for real, or it answers questions marked against an answer key. Claude Sonnet 5 also ranks the docs blind, against a verified list of facts.

Each doc was written three ways: with no guidance, with a one-line request ("When you write documentation, write clear docs like Stripe's"), and with the current `prompt.md`.

Share of reader jobs that worked, across README, docstring and changelog tasks on both projects:

| Writer model | No guidance | One-line request | `prompt.md` |
|---|---|---|---|
| Claude Haiku 4.5 | 52% (104 docs) | 48% (24 docs) | **70%** (54 docs) |
| Claude Sonnet 5 | 71% (18 docs) | 63% (18 docs) | **92%** (18 docs) |

In the blind ranking, the judge put docs written with `prompt.md` above docs with no guidance in 79% of comparisons for Haiku and 89% for Sonnet. It put them above the one-line request in 75% of comparisons for Haiku and 89% for Sonnet.

Asking for good docs isn't enough: the one-line request did no better than no guidance overall, and made docstrings worse in 3 of the 4 model and project combinations.

By task, for docs written with `prompt.md`:

| Task | Haiku, no guidance | Haiku, `prompt.md` | Sonnet, no guidance | Sonnet, `prompt.md` |
|---|---|---|---|---|
| pantry changelog | 57% | 72% | 83% | 94% |
| pantry docstrings | 34% | 88% | 42% | 88% |
| pantry README | 83% | 67% | 60% | 93% |
| tally changelog | 13% | 51% | 81% | 76% |
| tally docstrings | 41% | 60% | 74% | 100% |
| tally README | 78% | 87% | 89% | 100% |

- **Docstrings improve the most**, for both models. With `prompt.md`, docstrings describe valid values and name the exact exceptions a function raises.
- **Changelogs improve for Haiku,** from 13% to 51% on tally. Without guidance, changelogs describe code changes instead of telling readers what to do before they upgrade.
- **READMEs improve for Sonnet,** which reached 93% on pantry and 100% on tally.

Every number above comes from docs written, read and ranked by the benchmark in this repository.

See [`bench/results/comparison.md`](bench/results/comparison.md) for every version tested with Haiku, [`bench/results/comparison-sonnet.md`](bench/results/comparison-sonnet.md) for Sonnet, and [`bench/README.md`](bench/README.md) to run the benchmark yourself.
