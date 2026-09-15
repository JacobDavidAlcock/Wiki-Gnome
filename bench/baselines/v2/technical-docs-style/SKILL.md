---
name: technical-docs-style
description: Load this skill before you write, edit or review any developer documentation, and follow it. That includes a README, docstrings, code comments, an API or CLI reference, a quickstart, tutorial or how-to guide, a changelog or release notes, and command help text. Load it even when the request is short and doesn't mention style, such as "document this", "add docstrings", "write a changelog" or "update the README". It covers how to check facts against the code, which behaviour readers need warning about, and how to write each kind of doc.
---

# Technical documentation style

Apply this style whenever producing developer-facing documentation: READMEs, API references, quickstarts, tutorials, how-to guides, docstrings, CLI help text, changelog entries, or code comments meant for other humans to read.

Your only job when writing documentation is to get the reader unstuck and back to work as quickly and confidently as possible. Every sentence should either help them understand something or help them do something. If a sentence does neither, cut it.

## Voice and tone

- Write in the second person. Address the reader as "you". Never write "the user" when you mean the person reading.
- Use active voice and present tense by default: "The function returns an error" rather than "an error is returned by the function".
- Sound like a knowledgeable colleague explaining something to a peer, not a professor lecturing or a salesperson pitching. Direct, warm, unhurried, never chatty or jokey.
- Skip unnecessary politeness. Write "Run the command", not "Please run the command".
- Cut hedging and filler words: "simply", "just", "obviously", "of course", "easily". If something were actually simple for the reader, they wouldn't need documentation for it; if it isn't simple, that word reads as condescending.
- Avoid marketing language entirely: no "powerful", "seamless", "best-in-class", "blazing fast". Describe what something does, not how impressive it is.
- Never blame the reader for an error state. Write "This request is missing a required field", not "You forgot to include a required field".

## Sentence-level craft

- Keep sentences short. One idea per sentence. If a sentence needs two or three subordinate clauses, split it in two.
- Define a term the moment it first appears, in a single plain sentence, inline, before using it again. Do not defer definitions to a glossary the reader has to leave the page to find. For example: "A worker pool is a fixed set of goroutines that pull tasks from a shared queue." One sentence, then move on.
- State the condition before the instruction: "If the config file is missing, the command exits with status 1" rather than "The command exits with status 1 if the config file is missing." Readers scan for the condition that applies to them; putting it first lets them skip irrelevant branches.
- Prefer concrete nouns and specific numbers over vague qualifiers: "Requests time out after 30 seconds" beats "requests may time out after a while".
- Use transitions sparingly and naturally ("This way", "Because of this") rather than stacking formal connectives ("Furthermore", "Notwithstanding").

## Structure: separate the four jobs documentation does

Every piece of documentation is doing one of four jobs. Decide which one before you write, and don't let content belonging to the other three leak in:

1. **Tutorial** — a guided lesson for someone learning from scratch. Practical, sequential, one path only. Link out to alternatives and edge cases rather than covering them here.
2. **How-to guide** — a recipe for solving one specific, named problem for someone who already has basic competence. Assume context; get to the steps fast.
3. **Reference** — exhaustive, factual, looked up rather than read start to finish (function signatures, config options, CLI flags, API fields). Precise and consistent, no narrative, no opinions.
4. **Explanation** — background and reasoning for someone who wants to understand why something works the way it does. This is the only place discursive, exploratory writing belongs.

A README typically mixes a short tutorial (getting started) with reference (config/API summary) and should say clearly where each part begins.

## Organise around tasks, not implementation

Head sections with what the reader is trying to do ("Add a new provider", "Handle a failed request"), not with the name of a component ("The Provider class", "Error handling internals"). Lead each section with the reader's goal in the first sentence. Give the shortest path to a working result first, then link out to edge cases and advanced options rather than front-loading them.

## Check every fact against the code

Readers copy what you write and act on it, so a wrong detail costs them more than a missing one.

- Before you document a command, option, default, file path, environment variable or exit code, find it in the code or run it.
- If you can't confirm a detail, leave it out rather than guess.
- Match the project's actual language, package manager and conventions. Never invent a command, flag, config format or install method that doesn't exist in the codebase.

## Warn readers about behaviour they will trip over

Readers get stuck where the tool doesn't behave the way they'd guess. Look for these in the code and state each one plainly, next to the instructions it affects:

- **Order that matters.** For example, global options that must come before a subcommand, or a step that must run first. State the rule in words; an example alone isn't enough, because readers change the order without knowing it matters.
- **Defaults.** Where data is stored, default values, and what happens when an input is missing.
- **Errors and exit codes.** What each one means and what the reader does about it.
- **Edge cases.** Empty input, zero, duplicates, values out of range, and items that already exist.
- **Anything that differs from similar tools.** Readers bring habits from tools they already know.

For example, write "Global options go before the command: `deployctl --config prod.toml push` works, but `deployctl push --config prod.toml` fails." Don't leave the reader to notice the order in an example.

## Code examples

- Every example should be complete enough to copy, paste and run, not a fragment the reader has to mentally assemble.
- Use realistic values, not placeholders like `foo` or `xxxxx`, unless the value is genuinely meant to be filled in by the reader, in which case name it clearly (`YOUR_API_KEY`).
- Show input and output together where relevant, so the reader can confirm they got the right result.
- Keep each example focused on the one thing it demonstrates. Don't bury the relevant line inside twenty lines of unrelated setup.

## Write docstrings and code comments

A docstring is read in an editor tooltip, next to a signature that already shows the name and types. Spend its words on what the signature can't show.

- Start with a one-sentence summary of what the function does.
- Then describe the behaviour a caller needs: what it returns, which errors it raises and when, side effects such as writing files, and what happens in edge cases.
- Don't restate the name or the types. "Load the items" adds nothing to `load_items(path) -> list[Item]`.
- In code comments, explain why the code does something, not what it does.

For example:

```python
def withdraw(account: Account, amount: int) -> int:
    """Take money out of an account and return the new balance.

    Raises InsufficientFunds if amount is more than the balance, and leaves
    the balance unchanged. An amount of 0 is allowed and changes nothing.
    """
```

## Write changelogs and release notes

A changelog entry answers one question for the reader: what do I need to know, or do, before I upgrade?

- Read the whole diff, not only the commit messages. Changes to validation, defaults, file formats and error handling are the easiest to miss and the most likely to break someone's setup.
- Put breaking changes first, under their own heading. For each one, say what stops working and give the steps to fix it.
- Describe what changed for the reader, not what changed in the code: "`deploy` now waits for health checks before it exits", not "Refactored the deploy polling loop".
- Group the remaining changes under **Added**, **Changed** and **Fixed**.

## Formatting

- Numbered lists for steps that must happen in order. Bullet lists for items with no required order.
- Bold UI element names. Use code font for anything the reader types, sees on screen as code, or that names a parameter, field, function, or file.
- Break up long explanations with headers, short paragraphs and tables rather than dense blocks of prose.
- One topic per heading. If a section is doing two jobs, split it.

## Before finishing, check

- Did you confirm every command, option, default and path against the code?
- Did you state the order rules, defaults, errors and edge cases a reader will trip over, in words?
- Would a reader encountering this term for the first time understand it from context alone?
- Could any sentence be split in two and get clearer?
- Is every code sample something the reader could paste and run right now, against the actual project?
- Have you written for the reader's goal, or for the shape of the underlying system?
- Read it back. If a sentence sounds stiff or over-formal when spoken aloud, rewrite it.
