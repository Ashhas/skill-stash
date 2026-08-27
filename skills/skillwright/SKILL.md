---
name: skillwright
description: Write or restructure an agent skill (SKILL.md). Use when creating a new skill, reviewing an existing one, or deciding whether something should be a skill at all. Covers naming, the description line, layout, formatting for agent readers, and the pre-publish checklist.
---

# Skillwright

Guide the writing of a skill that an agent can read cheaply, navigate reliably, and execute without guessing.

## Non-negotiables

1. **Frontmatter is `name` and `description` only.** Extra fields break portability across SKILL.md-aware tools.
2. **Write tool-agnostic.** "Search the codebase for X", not a specific tool name. The skill must work in Claude Code, Codex, and whatever comes next.
3. **The name must not collide** with well-known skills (check before writing, see step 2).
4. **Adapted content keeps its attribution.** A footer line naming the source and license; never copy text from unlicensed sources, rewrite the ideas instead.
5. **The prose passes unslop.** No em dashes, sentence-case headings, no decorative emojis, no filler.

## Step 1: Confirm it should be a skill

| It is a… | When | Lives in |
|----------|------|----------|
| Instruction file entry | The rule applies to every message (style, standing constraints) | `CLAUDE.md` / `AGENTS.md` |
| Skill | Reusable procedure for a recurring *kind* of task | `skills/<name>/SKILL.md` |
| Spec | Describes one deliverable for one project | The project, not a skills repo |

If the content is a standing rule, stop here and put it in the instruction file. A skill that should fire on all writing can do both: a normal skill plus an `@`-import of its file from the instruction file for a guaranteed always-on path.

## Step 2: Name it

- Short, kebab-case, says what it does or is memorably coined. Verb-first names ("prep-commit") read well for workflows.
- Check for collisions before committing to it: `ls ~/.claude/skills/`, the well-known skill repos (anthropics/skills, superpowers, pstack, android/skills), and a GitHub name search. Generic names ("code-review", "skill-creator") are guaranteed collisions; avoid them.

## Step 3: Write the description

The description is the only part loaded in every session, and it alone decides whether the skill fires. Include, in one or two sentences:

- What the skill does (the imperative core).
- When to use it, including literal trigger phrases users say ("update dependencies", "bump versions").
- For an always-on skill, end with "Must always apply." so the ever-present description nudges invocation.

## Step 4: Choose the layout

| Level | Loaded | Budget |
|-------|--------|--------|
| description | always | one or two sentences; spend them on triggers |
| SKILL.md body | every invocation | small; workflow, invariants, decision rules |
| `references/*.md` | on demand, per section of work | can be large; one file per ecosystem/topic |

Getting this split right saves more context than any formatting choice inside a file. If the body explains one ecosystem or scenario for more than ~30 lines, that content wants to be a reference file. Give sibling reference files an identical section skeleton so an agent that learned one can navigate the others blind. Executable helpers go in a `scripts/` directory next to the SKILL.md.

## Step 5: Write the body

Open with the workflow in one line. When the skill has invariants that hold across steps, put them in a numbered non-negotiables block right after it: attention is strongest at the start, and later text can cite "non-negotiable 3" instead of restating it. A small single-purpose skill needs no such block. Number sections (§2.2 style) when references cross-link them; anchors act as pointers and cut repetition.

Match the form of each chunk to the shape of its content:

| Content shape | Form | Why |
|---------------|------|-----|
| Sequential procedure | numbered steps or STEP headings | Order is load-bearing, and numbers make steps citable |
| Executable | fenced code block with `<placeholders>` | The agent runs it instead of reconstructing it |
| Relational facts (X couples to Y, error → fix) | table | Encodes relations with no connective-tissue tokens |
| Parallel, order-independent items | bullets | The only case plain bullets win |
| Causal or conditional logic | one tight sentence | "A → B because C unless D" dies when fragmented |
| Expected output | literal template, exact strings to say | The agent copies instead of improvising |

Rules of thumb while writing:

- State each rule once. The exception is guardrails ("never hand-edit the lockfile"): repeat those in every section where they bite, so a partial read still contains them.
- Give a non-obvious rule a one-clause why. Reasoned rules get better compliance and generalize to cases the rule didn't anticipate.
- Mark provenance when it differs: rules learned from real project history versus rules assembled from public docs. Readers calibrate trust differently.
- Delegate instead of duplicating: when an official skill or document owns a topic (an upgrade guide, a vendor skill), point at it, resolved dynamically (by target version or by lookup), never by a pinned name that rots.
- End with a verification checklist. Agents turn checklists into todos.

Anti-patterns, all of which cost tokens or reliability:

- Motivational repetition (persuasion is for humans; an agent needs the rule once).
- Vague adverbs ("carefully", "appropriately"): not executable, replace with the concrete action.
- Over-fragmentation: forty ungrouped one-liners lose addressability just like a wall of prose; group under headings.
- Describing an output format in prose when a template would show it.
- A "When to use" body section that restates the description. The description already routed the invocation; the body is only read after that decision.

## Step 6: Verify before publishing

- [ ] Frontmatter has `name` and `description` only; description carries trigger phrases
- [ ] Name collision-checked against installed skills and the well-known repos
- [ ] Body opens with the workflow; cross-step invariants, if any, sit in a non-negotiables block
- [ ] Every chunk's form matches its content shape (table above)
- [ ] Heavy per-topic detail split into `references/` with a shared skeleton
- [ ] Guardrails repeated where they bite; everything else stated once
- [ ] Adapted content attributed; provenance marked where rules aren't battle-tested
- [ ] Prose passes unslop (no em dashes, sentence-case headings, no decorative emojis)
- [ ] Tested: invoke the skill on a real case and watch where it hesitates; that's the next edit
