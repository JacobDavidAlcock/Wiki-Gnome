<p align="center">
  <img src="assets/gnome.png" alt="A grumpy gnome with folded arms sitting on a stack of books, one labelled Glossary" width="240">
</p>

<h1 align="center">Wiki-Gnome</h1>

<p align="center"><em>Wiki-Gnome <del>simply and seamlessly</del> fixes your docs.</em></p>

Wiki-Gnome makes AI agents write documentation like the best developer docs, such as Stripe's and Google's. The rules come from an agent that read a large set of well-regarded technical docs and worked out what they have in common: second person, one idea per sentence, conditions before instructions, and runnable code examples.

Wiki-Gnome comes in two versions with the same rules:

| Version | File | Use it when |
|---|---|---|
| Skill | [`.claude/skills/technical-docs-style/SKILL.md`](.claude/skills/technical-docs-style/SKILL.md) | Your agent supports skills, like Claude Code, and you use a model that loads them reliably. |
| Prompt | [`prompt.md`](prompt.md) | Your tool doesn't support skills, or you use a smaller model. Paste it in as a system prompt or custom instructions. |

A skill is a folder of instructions an agent loads on its own when a task matches the skill's description. The model decides whether to load it. In the [benchmark](#benchmark-results), Claude Sonnet 5 loaded the skill in 2 of 2 runs and Claude Haiku 4.5 in 0 of 15, so use the prompt with Haiku.

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
| Docstrings | Describe what the signature can't show: return values, errors and when they're raised, side effects and edge cases. |
| Changelogs | Put breaking changes first, each with the steps to upgrade. Describe what changed for the reader, not in the code. |
| Formatting | Numbered lists for ordered steps, bullets otherwise. Bold for UI elements, code font for identifiers. |

## Benchmark results

The [`bench/`](bench/) folder tests whether Wiki-Gnome helps readers. Claude Haiku 4.5 writes docs for a small command-line tool with and without Wiki-Gnome. A fresh session then follows each doc: its commands are run for real, or it answers questions marked against an answer key. Claude Sonnet 5 also ranks the docs blind.

Results for the current `prompt.md`, pooled across runs:

| Task | Reader success without Wiki-Gnome | Reader success with `prompt.md` |
|---|---|---|
| Changelog | 58% (11 docs) | 78% (3 docs) |
| Docstrings | 35% (11 docs) | 75% (3 docs) |
| README | 81% (16 docs) | 78% (8 docs) |
| All three | 57% (38 docs) | 77% (14 docs) |

In the blind ranking, the judge put docs written with `prompt.md` above docs written without it in 75% of 28 comparisons.

These are early results from one test project and small samples. READMEs don't improve yet: most README failures come from one detail, an option that must come before the command, and no version of the prompt has fixed it. See [`bench/results/comparison.md`](bench/results/comparison.md) for every version tested, and [`bench/README.md`](bench/README.md) to run the benchmark yourself.
