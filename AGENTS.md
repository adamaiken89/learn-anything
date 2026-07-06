# Learn Something — Agent Modification Guide

## Skill Structure

```
learn-something/
├── SKILL.md           # Frontmatter metadata + main instruction body
├── study-protocol.md  # Learner-facing protocol reference
├── README.md          # General documentation
├── LICENSE            # MIT
├── AGENTS.md          # This file — agent modification guide
├── learn-something-schema/  # Shared JSON schemas (Phase 1)
│   ├── package.json
│   ├── schemas/       # JSON Schema files (deck, card, quiz, question, cloze_question, cloze_quiz, cumulative_question, cumulative_quiz, syllabus, stats, feedback)
│   ├── types/         # TypeScript type definitions
│   └── validate/      # Python + TypeScript validators
├── scripts/
│   ├── learn.sh       # Thin bash wrapper → delegates to learn.py
│   ├── learn.py       # Python CLI (FSRS, quiz engine, all commands)
│   ├── sm2.py         # FSRS-5 algorithm (replaces SM-2)
│   ├── enrich.py      # LLM-based lesson enrichment (cloze/predict/error/diagram/mindmap)
│   ├── render_diagrams.py  # Mermaid → PNG renderer (mmdc CLI or mermaid.ink API)
│   ├── epub.py        # EPUB 3 generator (zero-dep + optional extras)
│   └── pdf.py         # PDF generator (zero-dep + optional engines)
└── templates/
    ├── syllabus.yaml  # 20-module course skeleton
    ├── module.md      # Lesson structure (concrete-first, cloze/predict/error/diagram/mindmap)
    ├── quiz.yaml      # MCQ template (4 options, difficulty 1-3)
    └── cloze.yaml     # Cloze template (fill-in-blank, difficulty 1-3)
```

## Key Modification Points

### SKILL.md frontmatter

```yaml
---
name: learn-something
description: >
  Structured learning framework...
  Trigger: "I want to learn [topic]", ...
---
```

- `name`: must match directory name (`learn-something`)
- `description`: first sentence is summary. Remaining lines = trigger phrases.
- Trigger phrases: space-separated quotes. Each trigger activates skill.

### SKILL.md body

Contains sections: Pedagogy, Content Structure, Content Creation Protocol, Study Protocol, CLI, Cost Model, Integration, Trigger Behavior.

- **Section 3 (Content Creation Protocol)**: defines LLM behavior during course creation. Modify if changing AI creation flow. Includes 15 content quality rules now: concrete-first, cloze, predict, error-spotting, dual coding, mindmap, etc.
- **Section 4 (Study Protocol)**: defines session types and FSRS rules. Mirror changes into `study-protocol.md`.
- **Section 8 (Trigger Behavior)**: defines first-response behavior. Modify if changing entry flow.

### study-protocol.md

Learner-facing subset of SKILL.md Section 4. Keep in sync — this is the quick reference learners use during study sessions.

### scripts/learn.sh

Thin bash wrapper (9 lines). Delegates all logic to `learn.py`.

### scripts/learn.py

Python CLI. Key subsystems:

| Function               | Purpose                                                                                                                            |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `sm2_update()`         | FSRS-5 algorithm: stability, difficulty, lapses, state                                                                             |
| `cmd_init`             | Create subject directory, copy syllabus template. Flags: `--depth survey                                                           | standard            | deep`, `--pretest` |
| `cmd_start`            | Show subject overview + module list                                                                                                |
| `cmd_create_module`    | Create module from template. Flag: `--name`. module_id must match NN-name (e.g., 01-intro)                                           |
| `cmd_create_cloze`     | Create cloze.yaml from template for a module                                                                                       |
| `cmd_quiz`             | Parse YAML, shuffle, display MCQs, update SRS deck. Flags: `--adaptive`, `--weak-only`                                             |
| `cmd_cloze`            | Cloze (fill-in-blank) quiz. Parse cloze.yaml, display prompts, update SRS deck. Flags: `--adaptive`, `--weak-only`                |
| `cmd_cumulative_quiz`  | Cross-module quiz: 8-10 questions (MCQ/cloze/T/F). Flag: `--modules X-Y`                                                           |
| `cmd_explain`          | Feynman technique prompt with gap detection guide                                                                                  |
| `cmd_review`           | FSRS review: due cards, scoring, interval calc                                                                                     |
| `cmd_blurting`         | Brain-dump before review. Compares user recall to lesson key terms                                                                 |
| `cmd_enrich`           | Add cloze/predict/error/diagram/mindmap/cloze-quiz enrichments to existing lessons via LLM. Flags: `--types`, `--dry-run`, `--render-mode api | local               | off`               |
| `cmd_fsrs_predict`     | Show avg stability, difficulty, retention per topic                                                                                |
| `cmd_stats`            | Card counts, due today, mastery rate, avg ease, session history                                                                    |
| `cmd_export`           | Export deck to CSV for Anki import                                                                                                 |
| `cmd_rate`             | Rate module clarity (1-5 stars), save to feedback.json. Flag: `--comment`                                                          |
| `cmd_flag`             | Report content error (wrong/outdated/confusing). Flag: `--detail`                                                                  |
| `cmd_feedback`         | Aggregate feedback: avg ratings, flag counts, suggest modules                                                                      |
| `cmd_analytics`        | Retention analytics: mastery breakdown, session history, weak modules                                                              |
| `cmd_forecast`         | Forgetting forecast: cards due now/week/month                                                                                      |
| `cmd_study_plan`       | Optimal study session: due + weak cards, skip mastered                                                                             |
| `cmd_epub`             | Generate EPUB book from all modules + quizzes. Flags: `--mermaid`, `--description`                                                 |
| `cmd_epub_regen`       | Regenerate EPUB from cached `book.md`. Flags: `--mermaid`, `--description`                                                         |
| `cmd_epub_verify`      | Validate EPUB structure                                                                                                            |
| `cmd_epub_list_themes` | List available EPUB themes                                                                                                         |
| `cmd_pdf`              | Generate PDF from all modules + quizzes. Flags: `--engine`, `--title`, `--author`                                                  |
| `cmd_pdf_regen`        | Regenerate PDF from cached `book.md`. Flags: `--engine`, `--title`, `--author`                                                     |
| `cmd_sync`             | Export deck to Reader directory (~/.coursereader/subjects/). Flag: `--reader-path`                                                 |
| `cmd_sync_pull`        | Import deck from Reader directory. Flag: `--reader-path`                                                                           |
| `cmd_validate`         | Validate subject files against JSON schemas (deck, quiz, syllabus, feedback)                                                       |
| `cmd_render_diagrams`  | Render ```mermaid blocks in lesson.md to PNG. Flags: `--render-mode api                                                            | local`, `--scale N` |
| `cmd_mindmap`          | Generate/regenerate Mermaid mindmap for a module via LLM                                                                           |
| `cmd_validate_content` | Validate markdown + mermaid syntax in lesson files. Uses pymarkdownlnt + mmdc if available, falls back to basic checks             |

#### FSRS-5 Algorithm (`sm2_update()`)

- Replaces SM-2. Uses 21-parameter model from py-fsrs v6.
- Quality >= 4 (correct) → rating=Good(3). Quality < 3 (wrong) → rating=Again(1). Quality=3 → rating=Hard(2).
- Initial stability S0 = W[rating-1], difficulty D0 = W[4] - exp(W[5] * (rating - 1)) + 1
- Retrievability: R = (1 + FACTOR * t / S) ^ DECAY
- Short-term (elapsed < 1d) vs long-term (elapsed >= 1d) stability updates
- Old SM-2 cards auto-migrate via `_migrate_sm2_card()` on update
- See `sm2.py` for full parameter constants W[0..20]

#### Quiz Engine (`cmd_quiz`)

- Uses Python3 with `yaml` library.
- Options shuffled per question, keys remapped (A-D → a-d).
- Each quiz attempt updates SRS deck with FSRS-5 intervals.
- Falls back to raw display if `yaml` unavailable.
- Adaptive mode: weighted by ease, difficulty ramp, streak skip.

### templates/

| Template        | Purpose                    | Key constraints                                                                                                                                                                                                                    |
| --------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `syllabus.yaml` | 20-module default skeleton | time_hours per module ≤ 3, prerequisites form DAG                                                                                                                                                                                  |
| `module.md`     | Lesson structure           | Must include: Real-World Example → Core Content (with **Think**, **Cloze**, **Predict**, Mermaid per section) → Why This Matters → Key Takeaways → Common Misconception → **Spot the Mistake** → Feynman Explain → Reframe → Drill |
| `quiz.yaml`     | MCQ format                 | 4 options, 1 correct, difficulty 1-3, tags per category                                                                                                                                                                            |

## Content Quality Rules

SKILL.md §3 now includes 15 mandatory content quality rules:

| Rule                     | What it prevents                                         | Example fix                                                                                                    |
| ------------------------ | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1. Explain conventions   | Stating "price quoted as 95" without "why"               | "95 = 95% of $1,000 par. Enables comparison across bonds with different face values."                          |
| 2. Answer implicit Qs    | Learner wonders "does coupon ever change?" — text silent | Add Q&A: "Fixed-rate bonds: coupon never changes. FRNs: resets periodically."                                  |
| 3. Pull-to-par intuition | Price convergence treated as mystery                     | "Premium bond falls toward par at maturity because only principal remains."                                    |
| 4. Causal chain first    | Formula without intuition                                | Explain opportunity cost before bond pricing formula.                                                          |
| 5. Practical context     | Numbers without meaning                                  | "Duration 7.5 = 7.5% price drop per 1% rate rise (small moves only)."                                          |
| 6. "How likely" answers  | Frequency uncertainty                                    | "Yield curve inverts rarely. ~8mo before recession typically."                                                 |
| 7. Common misconceptions | Persistent errors                                        | "Higher coupon ≠ better bond. Discount bonds have built-in price gain."                                        |
| 8. Socratic throughout   | Passive reading                                          | Every concept section embeds **Think**: question + answer. Forces stop-and-process.                            |
| 9. Dual coding           | Text-only explanations                                   | Every concept gets diagram (Mermaid, ascii, or structured hierarchy).                                          |
| 10. Concrete-first       | Abstract definition before example                       | Start with real-world scenario: "Your company needs $10M. Bank says 8%. Bond market says 6%. You issue bonds." |
| 11. Cloze deletions      | No retrieval during reading                              | `> **Cloze**: "A {bond} is a debt security..."` — learner fills blank.                                         |
| 12. Predict-next         | Passive outcome reveal                                   | `> **Predict**: What happens to price if rates rise?` → learner commits before reveal.                         |
| 13. Error-spotting       | Misconception not challenged                             | "Duration 7.5 means price rises 7.5% for 1% rate rise" → "Wrong: measures fall for rise."                      |
| 14. Graduated examples   | Formula without practice                                 | Full worked example → partial (learner fills) → independent problem.                                           |
| 15. Module mindmap       | No knowledge overview at module top                      | Add Mermaid mindmap showing concept hierarchy: central concept → topics → sub-concepts.                        |

Apply all 15 rules to every generated module. If content violates any rule, rewrite before presenting.

## Modification Rules

1. **Keep pedagogy alignment**: Any new feature must fit Marva Collins (rigor/repetition), Feynman (explain-simply), or Desirable Difficulties (spacing/interleaving). Tag new features with which theory they serve.
2. **Keep cost model**: Powered by DeepSeek V4 Flash. Content creation stays ~$0.10/course max. Study sessions stay $0.
3. **Keep time budgets**: Module ≤ 3h. Subject ≤ 40h.
4. **Keep FSRS-5 correct**: Stability/difficulty formulas match py-fsrs v6. Do not change W parameters without testing against known FSRS implementations.
5. **Keep trigger behavior**: On trigger, enter content creation mode immediately — never generate full course in one shot unless user explicitly asks.
6. **Keep template constraints**: MCQ = exactly 4 options, 1 correct. Module must include Feynman + Reframe sections.
7. **Keep sync**: Changes to study protocol in SKILL.md must be mirrored in `study-protocol.md`. Changes to deck schema must sync between CLI and Reader.
8. **Keep backward compat**: CLI flags and file structure (syllabus.yaml, modules/NN-name/lesson.md, modules/NN-name/quiz.yaml, srs/deck.json) are public API. Breaking changes need migration path.

## Adding Features

1. **CLI**: Add `cmd_<name>(topic: str, ...)` in `learn.py`, register via `app.command('name')(cmd_name)` (typer).
2. **Docs**: Update SKILL.md §5 (CLI) and AGENTS.md CLI table.
3. **Study flow**: If affected, update SKILL.md §4 + `study-protocol.md`.
4. **Content flow**: If affected, update SKILL.md §3.
5. **Cost**: If it adds API calls, verify < $0.10/course (SKILL.md §6).
6. **Schema**: If new data type, add JSON Schema to `learn-something-schema/schemas/`, TypeScript type to `types/`, validator to `validate/python/validate.py`.
7. **Tests**: Add 2+ tests in `tests/test_learn.py` (happy path + error case).

### Mermaid Diagram Support (added 2026-06)

- **epub.py**: `_mermaid_render()`, `_mermaid_render_local()`, `_mermaid_render_api()`, `_process_mermaid_blocks()`
- Default mode: `api` (mermaid.ink GET, zero deps). `local` mode calls `mmdc` CLI.
- Fallback chain: local → api → text fallback in `<figure>`.
- SVG files stored as separate EPUB items (`image/svg+xml`), referenced by `<img>` in XHTML.
- CLI flags: `--mermaid api|local|off` on `build`/`from-md` subcommands.
- learn.sh: `--local` flag passed through as `--mermaid local`.
- Content rules: Rule #9 added — Mermaid for complex concepts (branching, state, workflows).
- SKILL.md: §3 content principles + quality rules, §5 CLI, §7 Integration updated.
- module.md: optional ```mermaid slot after concept definition.

### SVG Cover Generation (added 2026-06)

- **epub.py**: `generate_cover_svg(title, author, description)` function (~100 lines)
- Zero dependencies — uses `hashlib`, `math`, `random` from stdlib.
- Deterministic from title: SHA256 hash → palette selection (8 dark-theme palettes), pattern type (4: circles, sine waves, radial, grid).
- Cover layout: 1264×1680 SVG (portrait, 3:4 ratio, matches Kobo Libra 2 / Kindle Oasis 7"), accent line, uppercase wrapped title, description (3 lines max, 70% opacity), author at bottom.
- Stored as `cover.svg` in EPUB with `image/svg+xml` media type.
- OPF: `<meta name="cover" content="cover-image"/>`.
- CLI flags: `--description` on `build`/`from-md` (epub.py) and `epub`/`epub-regen` (learn.py).
- learn.py passes `--description` through to epub.py subprocess.
- SKILL.md §5 documents flag. AGENTS.md documents here.

### Shared JSON Schema Package (added 2026-07)

- **learn-something-schema/**: Standalone package with JSON Schema definitions for all shared data types.
- Schemas: `deck.json`, `card.json`, `quiz.json`, `question.json`, `syllabus.json`, `stats.json`, `feedback.json`.
- TypeScript types in `types/` directory, Python validator in `validate/python/validate.py`.
- Both CLI and Desktop reader validate against these schemas.
- Key conventions: camelCase fields, card ID = `{courseId}-{moduleId}-{questionId}`, quiz keys = lowercase a-d, deck = `{cards: Record<string, Card>}`.
- Version: 1.0.0. Breaking changes bump major version.
- Usage: `python validate/python/validate.py deck path/to/deck.json`

### Format Alignment with Reader (added 2026-07)

- **Decision**: CLI deck format aligned to match [learn-something-reader](https://github.com/adamaiken89/learn-something-reader) desktop app.
- **Deck format**: `{cards: {"id": card}}` (Record<string, Card>), NOT array.
- **Card ID**: `{courseId}-{moduleId}-{questionId}` (e.g., `python-01-intro-1.1`).
- **Fields**: All camelCase — `easeFactor`, `nextReviewDate`, `lastReviewed`, `isStarred`, `questionId`, `moduleId`, `courseId`.
- **Answer format**: `{key}. {text}` (e.g., `a. A programming language`).
- **SM-2 in `sm2.py`**: Updated to use camelCase fields (easeFactor, nextReviewDate, lastReviewed).
- **Auto-migration**: `_load_deck()` detects old array-format decks and converts to new format via `_migrate_deck_array()`.
- **`_find_card()`**: Helper for flexible card lookup by questionId across different ID formats.
- **CLI commands updated**: quiz, review, stats, export, analytics, forecast, study-plan — all use dict-based deck and camelCase.

### Adaptive Quiz Engine (added 2026-07)

- `cmd_quiz` gained `--adaptive` and `--weak-only` flags.
- `--adaptive`: weighted sampling by easeFactor, difficulty ramp (easy→medium→hard), streak skip (3 correct → advance), anti-repeat per session.
- `--weak-only`: only quiz on cards with easeFactor < 2.0.
- Pedagogy: Desirable Difficulties (adaptive difficulty), Marva Collins (targeted repetition).

### Feedback Loop (added 2026-07)

- `cmd_rate <topic> <module> <1-5>`: learner rates module clarity, saved to `srs/feedback.json`.
- `cmd_flag <topic> <module> <type>`: report content error (wrong/outdated/confusing).
- `cmd_feedback <topic>`: aggregate ratings per module, flag counts, suggest modules to revisit.
- Pedagogy: Marva Collins (rigor through feedback), content quality improvement loop.

### Retention Analytics (added 2026-07)

- `cmd_analytics <topic>`: mastery breakdown (new/learning/mastered), session history, weak modules by ease factor.
- `cmd_forecast <topic>`: cards due now/this week/this month/later, grouped by module.
- `cmd_study_plan <topic>`: optimal session composition (due + weak, skip mastered, 15-25 card target).
- Pedagogy: Desirable Difficulties (spacing via forecast), Feynman (weak area identification).

### Cross-Tool Sync (added 2026-07)

- `cmd_sync <topic>`: export CLI deck + modules to Reader directory (`~/.coursereader/subjects/<topic>/`).
- `cmd_sync_pull <topic>`: import Reader deck to CLI format.
- Both commands validate format compatibility (already aligned via Phase 3).
- `--reader-path` flag to override default Reader location.
- Copies: deck.json, modules (lesson.md + quiz.yaml), syllabus.yaml.

### Dynamic Depth & Pre-test (added 2026-07)

- `cmd_init` gained `--depth` and `--pretest` flags.
- `--depth survey|standard|deep`: dynamically generates syllabus with different module counts.
  - `survey`: ~6 modules, ~12 hours. Quick overview.
  - `standard`: ~18 modules, ~40 hours. Default.
  - `deep`: ~28 modules, ~75 hours. Comprehensive.
- `--pretest`: after syllabus creation, asks 1 question per module to identify known content. Marks known modules for removal.
- `_generate_syllabus()`: builds skeleton YAML from preset (module count, time range, prerequisites DAG).
- `_run_pretest()`: interactive input loop, reports skip count.
- Pedagogy: Desirable Difficulties (right-sized challenge), Marva Collins (no wasted time on known material).

### Content Syntax Validation (added 2026-07)

- **`cmd_validate_content <topic> [module]`**: validates markdown + mermaid syntax in lesson.md files.
- **Markdown validation** (two-tier):
  - Primary: `pymarkdownlnt` (`pip install pymarkdownlnt`) — GFM-compliant linter with dozens of rules.
  - Fallback: Pure Python basic checks — code block closure, heading hierarchy, link/image syntax, table structure, bold/italic closure.
- **Mermaid validation** (two-tier):
  - Primary: `mmdc --dry-run` (`npm install -g @mermaid-js/mermaid-cli`) — full syntax validation.
  - Fallback: Pattern checks — diagram type keyword, arrow syntax, hex color validity, subgraph/end pairing.
- **Auto-triggered**: SKILL.md §3 workflow step 3.5 runs this after content generation.
- **Manual**: `learn.sh validate-content <topic> [module]` for re-checks.
- Both dependencies optional. System works without them — less thorough validation.
- Pedagogy: Marva Collins (rigor), content quality improvement loop.

### Diagram Rendering to PNG (added 2026-07)

- **render_diagrams.py**: New script. Scans ` ```mermaid ` blocks in lesson.md, renders each to PNG (via mmdc CLI or mermaid.ink/png API), saves `.mmd` source + `.png` in `modules/NN-name/diagrams/`, replaces fenced block with `![Diagram](diagrams/diagram_NNN.png)`.
- **Enrich auto-render**: When `enrich.py` runs with `--types diagram` (default), it auto-calls `render_lesson_diagrams()` after LLM enrichment. Controlled by `--render-mode api|local|off`.
- **CLI command**: `learn.py render-diagrams <topic> [module] [--render-mode api|local] [--scale 2]`. Runs on all modules or specific one.
- **EPUB integration**: `collect_subject_md()` now returns `(markdown_text, assets_dict)` tuple. PNG files are collected from `modules/*/diagrams/`, paths adjusted to EPUB-internal names, and included as `image/png` items in the EPUB manifest. SVG fallback kept for unprocessed modules.
- **module.md**: Added HTML comment about diagrams/ directory convention.
- **Cost**: $0 (local CLI or free mermaid.ink API).
- **Pedagogy**: Dual coding (Rule #9), Marva Collins (rigor).

### Module Mindmaps (added 2026-07)

- **Content**: Every module gets Mermaid mindmap at top of lesson.md (after metadata, before Learning Objectives). Shows knowledge hierarchy: central concept → key topics → sub-concepts.
- **SKILL.md**: §3 content principles + Rule #15 added. module.md template updated with Knowledge Map section.
- **enrich.py**: New `'mindmap'` type in `_DEFAULT_TYPES` and `_TYPE_PROMPTS`. Generates mindmap via LLM.
- **CLI command**: `learn.py mindmap <topic> <module>`. Generates/regenerates mindmap for specific module.
- **Cost**: ~$0.002 per module (LLM call).
- **Pedagogy**: Dual coding (Rule #15), Feynman (overview before detail).

### Cumulative Quizzes (added 2026-07)

- **Content**: After every 3-5 modules, generate `cumulative_quiz.yaml` in subject root. 8-10 questions mixing MCQ, cloze, T/F. Each question tagged with `source_modules`.
- **Schema**: New `cumulative_question.schema.json` (discriminated union: mcq/cloze/tf), `cumulative_quiz.schema.json` (array, 8-10 items).
- **Types**: New `cumulative_question.ts` with `CumulativeMCQ`, `CumulativeCloze`, `CumulativeTF` interfaces.
- **CLI command**: `learn.py cumulative-quiz <topic> [--modules X-Y]`. Filters by module range. Updates SRS deck.
- **Answer distribution**: MCQ answers rotated across A/B/C/D, no more than 2 consecutive same letter.
- **Pedagogy**: Desirable Difficulties (interleaving), Marva Collins (rigor through cross-module testing).

## Testing

```bash
# Create test directory
mkdir test-course && cd test-course

# Initialize
../scripts/learn.sh init python

# Create test module
../scripts/learn.sh create-module python 01-intro

# Run quiz
../scripts/learn.sh quiz python 01-intro

# Run review
../scripts/learn.sh review python

# Check stats (includes session history)
../scripts/learn.sh stats python

# Export to Anki CSV
../scripts/learn.sh export python

# Test diagram rendering
../scripts/learn.sh enrich python 01-intro --types diagram --render-mode off
../scripts/learn.sh render-diagrams python 01-intro --render-mode api

# Cleanup
cd .. && rm -rf test-course
```


