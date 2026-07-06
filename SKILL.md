---
name: learn-something
description: >
    Structured learning framework for any subject from text. Create syllabus +
    lessons + MCQ quizzes interactively with LLM. Study via CLI with spaced
    repetition (FSRS-5). Three-theory pedagogy: Marva Collins' Way (repetition,
    reframing, high expectations), Feynman Technique (explain-simply, find gaps),
    Desirable Difficulties (spaced/MCQ/retrieval). Cost-effective: content
    creation ~$0.10 per course; per-session cost = $0.
    Trigger: "I want to learn [topic]", "build curriculum for [subject]",
    "create learning module", "help me study [topic]", "/learn [topic]"
---

# Learn Something Framework

Turn subject into structured curriculum via interactive LLM session.
Study via CLI: read lessons, explain-back, drill MCQs, spaced repetition.

## 1. Pedagogy

Three theories fused:

| Theory                     | AI role                                                           | Problem solved                       |
| -------------------------- | ----------------------------------------------------------------- | ------------------------------------ |
| **Marva Collins**          | Socratic tutor. Rigorous Q&A, high expectations, endless patience | Needs great teacher. AI never tires. |
| **Feynman Technique**      | Gap detector. Learner explains simply → AI finds holes            | Illusion of understanding            |
| **Desirable Difficulties** | Spaced scheduler. FSRS retrieval + interleaved practice           | Passive re-reading                   |

### Session phase → theory mapping

| Phase       | Theory            | Learner                | AI/CLI                                 |
| ----------- | ----------------- | ---------------------- | -------------------------------------- |
| **Read**    | Marva             | Study lesson           | Write clear content                    |
| **Explain** | Feynman           | Explain concept simply | Probe: "you said X, but Y — reconcile" |
| **Drill**   | Marva + Desirable | Answer MCQs, justify   | Grade, explain distractors             |
| **Judge**   | Marva             | Critique, form opinion | Socratic follow-up                     |
| **Review**  | Desirable         | Active recall via FSRS | Schedule optimal intervals             |

### Time budget

- Subject: **40h max** (13 wk × 3h/wk)
- Module: 1.5-3h, ~15-20 per subject
- SRS review: ~10-15 min daily

## 2. Content Structure

```
<topic>/
├── syllabus.yaml             # Course spec
├── modules/
│   ├── NN-name/
│   │   ├── lesson.md         # Core content + exercises
│   │   ├── quiz.yaml         # 8-10 MCQs
│   │   └── cloze.yaml        # 8-10 cloze questions
│   └── ...
└── srs/
    ├── deck.json             # FSRS-5 cards
    └── stats.json            # History
```

Full templates in `templates/`. Key: syllabus.yaml (20-module skeleton), module.md (lesson structure), quiz.yaml (4-option MCQ format).

## 3. Content Creation Protocol

### Workflow

1. **Scope** (5 min): Ask domain/level/time budget/lang/use case. Propose syllabus.
2. **Outline stage**: Verify module DAG + prerequisite chain. Check time budget.
3. **Per module** (10 min): Create module with `learn.sh create-module <topic> NN-name`. Zero-padded two-digit number + kebab-case name (e.g., `01-intro`, `02-core-concepts`). Write lesson.md + quiz.yaml. Apply 15 quality rules inline. User reviews. Proceed.
   3.5. **Validate syntax**: Run `learn.sh validate-content <topic> [module]`. Fix all markdown + mermaid errors before proceeding.
4. **Pre-publication**: Load `content-verify.md`. Run checklist. Fix violations.
5. **Compile SRS** (2 min): Extract MCQs → FSRS-5 deck.
6. **Cumulative quizzes**: After every 3-5 modules, generate `cumulative_quiz.yaml` in subject root. 8-10 questions mixing cloze, MCQ, T/F. Each tagged with `source_modules`. Answers distributed across A-D.

### Content principles

- **CILO alignment**: Every module serves ≥1 learning objective. No filler.
- **Language**: All content in syllabus.yaml language (`en`/`zh`/`yue`).
- **Practical first**: Start with concrete example before abstract definition.
- **Domain-relevant**: Scenarios from learner's industry.
- **Cloze deletions**: Every module gets 3-5 cloze blanks (`{term}`). Learner fills before proceeding. Forces retrieval during reading.
- **Predict-next**: Every causal chain gets 2-3 predict blocks. Learner commits to outcome before reveal.
- **Error-spotting**: Every module gets 1-2 "Spot the Mistake" exercises. Error-driven learning builds diagnostic skill.
- **Dual coding**: Every concept gets a diagram (Mermaid, ascii, or structured hierarchy).
- **MCQ diversity**: 40% recall, 40% application, 20% multi-step.
- **Feynman prompt**: Every lesson ends with explanation task + AI gap probe.
- **Desirable difficulty**: Same concept tested at different angles across modules.
- **Time budget**: Module ≤3h. Subject ≤40h.
- **Progression**: Build on prerequisites. Earlier modules foundational.
- **Skip permitted**: Learner gives sparse input? Generate content anyway with sensible defaults. Do not block.
- **Socratic throughout**: Every major concept is followed by a question that makes learner stop and think — not at end of module only, but inline after each new idea. Question → brief answer/explanation immediately after so learner can self-check. Pattern: state concept → ask "why?" or "what if?" → answer.
- **Mermaid diagrams**: For concepts with branching logic, state machines, workflows, or causal chains: generate Mermaid flowchart/sequence/state diagram. Theme auto-injects `neutral` for dark/light compatibility. Use muted earth-tone palette for `style` fills — visible in both dark and light themes. Palette: blue `#5c7a99`, green `#5c8a6a`, orange `#b8924a`, red `#b86a4a`, purple `#7a5a8a`, gray `#888`. Strokes: use darker shade of fill or `#333`. Example: `style A fill:#5c7a99,stroke:#333`. Place after concept explanation, before **Think** question.
- **Module mindmap**: Every module gets a Mermaid mindmap at top of lesson.md (after metadata, before Learning Objectives). Shows knowledge hierarchy: central concept → key topics → sub-concepts. Use `mindmap` syntax. Max 3 levels deep.
- **Answer distribution**: MCQ answer keys must be distributed across A/B/C/D. No more than 2 consecutive questions share same answer letter. Template shows B as example — rotate during generation.
- **Cumulative quizzes**: After every 3-5 modules, generate `cumulative_quiz.yaml` in subject root. 8-10 questions mixing cloze, MCQ, T/F. Each question tagged with `source_modules`. Answers distributed across A-D.

### Content quality rules (15)

| #   | Rule                                  | What to do                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Bad example → Good example                                                                                                                     |
| --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Explain conventions                   | State why convention exists, not just what it is                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | "Price quoted 95" → "95 = 95% of $1,000 par. % convention enables comparison across bonds with different face values."                         |
| 2   | Answer implicit Qs                    | Anticipate 1-3 questions learner hasn't asked                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Silent on coupons → "Does coupon ever change? No for fixed-rate. Yes for FRNs (resets periodically)."                                          |
| 3   | Pull-to-par intuition                 | Explain price → face value at maturity is mechanical                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | "Price converges to par because time shrinks + remaining CFs' PV converges to principal. Not driven by rates."                                 |
| 4   | Causal chain first                    | Intuitive logic before formula                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Jump to bond pricing formula → "New bonds pay 6%. My bond pays 4%. Mine less valuable → price drops until yield matches."                      |
| 5   | Practical context                     | Every number gets real meaning                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | "Duration 7.5" → "1% rate rise → ~7.5% price drop (small moves only; convexity adjustment for large)."                                         |
| 6   | "How likely"                          | Tell normal vs rare frequencies                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Omit → "Yield curve inverts rarely. Each inversion preceded recession (~8mo). Not perfectly predictive."                                       |
| 7   | Common misconceptions                 | Flag 1-2 specific errors beginners hold                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | "Higher coupon = better bond" → "No. Discount bonds have built-in price gain at maturity (accretion)."                                         |
| 8   | Socratic throughout                   | Every concept section embeds **Think** question + immediate answer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Learner reads passively → forced to stop, process, self-check before proceeding                                                                |
| 9   | Dual coding WITH redundancy awareness | Every concept gets non-redundant diagram (Mermaid, ascii, hierarchy). Diagram ADDS info — structure, relationships, process flow — not duplicate text. Integrate labels on diagram (spatial contiguity). When diagram self-explanatory, skip redundant text paragraph. Channel split: verbal = sequential/abstract, visual = spatial/relational. Respects Baddeley WM model (phonological loop + visuospatial sketchpad) + redundancy effect (CLT). Mermaid: `neutral` theme, muted earth-tone palette `#5c7a99`/`#5c8a6a`/`#b8924a`/`#b86a4a`/`#7a5a8a`/`#888`, strokes `#333`. Minimum 1 per section. | Text-only amortization → Mermaid flowchart with cashflows on arrows. NOT: paragraph describing diagram + identical diagram.                    |
| 10  | Concrete-first ordering               | Start module with real-world example before abstract definition. Example → Explanation → Abstraction, not Definition → Example.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | "A bond is a debt security" → "Your company needs $10M. Bank says 8%. Bond market says 6%. You issue bonds."                                   |
| 11  | Cloze deletions                       | 3-5 per module. Key terms blanked as `{term}`. Learner fills before proceeding. Place after concept intro, before next section.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | No retrieval during reading → `> **Cloze**: "A \{bond\} is a debt security issued by..."`                                                      |
| 12  | Predict-next blocks                   | 2-3 per module. After causal chain explanation, before revealing outcome. Learner must commit to answer.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Learner reads outcome passively → `> **Predict**: What happens to price if rates rise?` → `> *Answer: Price falls*`                            |
| 13  | Error-spotting exercises              | 1-2 per module. Present plausible wrong solution. Learner identifies error.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | "Duration 7.5 means price rises 7.5% for 1% rate rise" → "Wrong. Duration measures price fall for rate rise, not rise for fall (small moves)." |
| 14  | Concrete example before abstraction   | Every formula/concept preceded by a worked example. Full worked → partial (learner fills) → independent.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Formula before example → "You issue $1M bonds at 5%. Here's the cashflow schedule. Now here's the PV formula."                                 |
| 15  | Module mindmap                        | No knowledge overview at module top                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | No mindmap → Add Mermaid mindmap showing concept hierarchy: central concept → topics → sub-concepts.                                           |

## 4. Study Protocol

### Session types

| Type        | Duration  | What to do                                                                       |
| ----------- | --------- | -------------------------------------------------------------------------------- |
| **LEARN**   | 45-60 min | `learn.sh start` → read lesson → reframe → `learn.sh quiz`                       |
| **EXPLAIN** | 15-20 min | Pick concept. Explain simply aloud/in writing. AI probes gaps. Loop until holds. |
| **BLURT**   | 10-15 min | `learn.sh blurting <topic> <module>` — brain-dump before review, AI shows gaps   |
| **REVIEW**  | 10-15 min | `learn.sh review` → due FSRS cards (interleaved across modules)                  |
| **MIXED**   | 30-45 min | BLURT (10min) → REVIEW (10min) → LEARN (20min) → EXPLAIN (5min)                  |

### FSRS rules

- Uses FSRS-5 algorithm (replaces SM-2). Cards tracked by: stability, difficulty, lapses, state.
- Correct (q≥4): stability grows with recall. Wrong (q<3): stability drops, difficulty rises.
- See `sm2.py` for full FSRS parameter set.
- `learn.sh fsrs-predict <topic>` shows avg stability/difficulty/retention per topic.
- Old SM-2 decks auto-migrate on first review after upgrade.

### Desirable Difficulties in practice

- **Interleaved**: Review session mixes 3+ module tags.
- **Varied difficulty**: Easy recall day 1 → harder scenario variants at next interval.
- **Generation**: Type answer before seeing options (optional CLI mode).
- **Context variation**: Year 2 uses different scenarios than year 1.

## 5. CLI

````
# ── Content Creation ──────────────────────────────
learn.sh init <topic> [lang] [--depth survey|standard|deep] [--pretest]
                                         # Initialize topic dir with syllabus template
                                         # --depth: survey (~6 modules), standard (~18), deep (~28)
                                         # --pretest: test first, skip known content
learn.sh start <topic>                       # Overview + module list
learn.sh create-module <topic> <id>          # Create module from template
learn.sh create-cloze <topic> <module>      # Create cloze.yaml from template
learn.sh enrich <topic> [module|--all] [--types cloze,predict,error,diagram,cloze-quiz] [--dry-run] [--render-mode api|local|off]
                                         # Add cloze/predict/error/diagram to existing lessons
                                         # Uses DeepSeek API. Backup as .md.bak
                                         # --types: comma-separated subset of types (includes cloze-quiz for cloze.yaml generation)
                                         # --render-mode: auto-render diagrams to PNG (default: api)
learn.sh render-diagrams <topic> [module] [--render-mode api|local] [--scale N]
                                         # Render ```mermaid blocks to PNG in lesson.md
                                         # --render-mode: api (mermaid.ink) or local (mmdc CLI)
                                         # --scale: PNG scale factor (default 2 = 300dpi)
learn.sh mindmap <topic> <module>           # Generate/regenerate Mermaid mindmap for module

# ── Study ─────────────────────────────────────────
learn.sh quiz <topic> <module> [--adaptive] [--weak-only]
                                         # MCQ drill
                                         # --adaptive: weighted by ease, difficulty ramp, streak skip
                                         # --weak-only: only cards with ease < 2.0
learn.sh cloze <topic> <module> [--adaptive] [--weak-only]
                                         # Cloze (fill-in-blank) drill
                                         # --adaptive: weighted by ease, difficulty ramp, streak skip
                                         # --weak-only: only cards with ease < 2.0
learn.sh cumulative-quiz <topic> [--modules X-Y]
                                         # Cross-module quiz (8-10 questions, mix of MCQ/cloze/T/F)
                                         # --modules: filter to specific module range
learn.sh explain <topic> <module>            # Feynman prompt guide
learn.sh review <topic>                      # FSRS spaced repetition
learn.sh blurting <topic> <module>           # Brain-dump before review. AI compares to lesson

# ── Progress & Analytics ──────────────────────────
learn.sh stats <topic>                       # Progress + retention
learn.sh analytics <topic>                   # Mastery breakdown, weak modules, session history
learn.sh forecast <topic>                    # Cards due: now / week / month / later
learn.sh study-plan <topic>                  # Optimal session: due + weak, skip mastered
learn.sh fsrs-predict <topic>                # Avg stability, difficulty, retention per topic

# ── Feedback ──────────────────────────────────────
learn.sh rate <topic> <module> <1-5>         # Rate module clarity
learn.sh flag <topic> <module> <type>        # Report error (wrong/outdated/confusing)
learn.sh feedback <topic>                    # Aggregate ratings + flag counts

# ── Export ────────────────────────────────────────
learn.sh export <topic>                      # Anki CSV export
learn.sh epub <topic> [file] [--local] [--description TEXT]
                                         # Export to EPUB book
                                         # --local: use mmdc CLI for Mermaid
                                         # --description: cover page description
learn.sh epub-regen <topic> [file] [--local] [--description TEXT]
                                         # Regenerate EPUB from cached markdown
learn.sh epub-verify <topic> [file]          # Validate EPUB structure
learn.sh epub-list-themes                    # List available EPUB themes
learn.sh pdf <topic> [file] [--engine auto|weasyprint|pandoc|raw]
                                         # Export to PDF
learn.sh pdf-regen <topic> [file] [--engine] # Regenerate PDF from cached book.md

# ── Sync ──────────────────────────────────────────
learn.sh sync <topic>                        # Export to Reader dir (~/.coursereader/subjects/)
learn.sh sync-pull <topic>                   # Import deck from Reader dir

# ── Validation ──────────────────────────────────────
learn.sh validate <topic>                    # Validate files against JSON schemas
````

## 6. Cost Model (DeepSeek V4 Flash)

| Phase                           | Cost          |
| ------------------------------- | ------------- |
| Scope + syllabus                | ~$0.01        |
| Per module (~15K tokens out)    | ~$0.004       |
| Enrich per module (all 4 types) | ~$0.01        |
| Enrich per type (per module)    | ~$0.002-0.004 |
| Full course (20 modules)        | ~$0.08        |
| Full course + enrich            | ~$0.28        |
| Study session / SRS review      | $0            |

## 7. Integration

- **Anki**: `learn.sh export` → CSV/APKG
- **Obsidian/Notion**: Markdown imports directly
- **Print**: Print lesson.md or quiz.yaml
- **EPUB**: `learn.sh epub <subject>` generates EPUB 3 with hierarchical ToC, syntax highlighting, quizzes, Mermaid diagrams (mermaid.ink API by default, `--local` for offline mmdc CLI)
- **PDF**: `learn.sh pdf <subject>` generates PDF with zero-dep stdlib fallback or optional weasyprint/pandoc engine (`--engine weasyprint`)

### EPUB generation workflow

1. Content created → all modules complete
2. Run `learn.sh epub <subject>` or `learn.sh epub-regen <subject> [file]`
    - `epub`: assembles subject dir (lesson.md + quiz.yaml per module) → `book.md` → EPUB
    - `epub-regen`: rebuild EPUB from existing `book.md` (skip assembly, faster after edits)
    - `--description "text"` adds cover page description
3. Validate: `learn.sh epub-verify <subject> [file]`
4. Underlying script: `epub.py build <subject-dir> <output> [--title TITLE] [--author AUTHOR] [--description DESC]`
    - Also: `epub.py from-md <markdown-file> <output>` for custom markdown
    - Zero-dep fallback parser or optional `markdown` + `pygments` for GFM tables + syntax highlighting
    - Mermaid diagrams rendered to SVG via mermaid.ink API (default) or local mmdc CLI (`--mermaid local`)
    - Generates valid EPUB 3 (cover SVG, nav, spine, manifest, XHTML content, SVG diagrams)
    - Cover: procedural SVG generated from title hash (8 color palettes, 4 pattern types). Deterministic, zero-dep.

### PDF generation workflow

1. Content created → all modules complete
2. Run `learn.sh pdf <subject>` or `learn.sh pdf-regen <subject> [file]`
    - `pdf`: assembles subject dir (lesson.md + quiz.yaml per module) → `book.md` → PDF
    - `pdf-regen`: rebuild PDF from existing `book.md` (skip assembly, faster after edits)
3. Underlying script: `pdf.py build <subject-dir> <output> [--title TITLE] [--engine auto|weasyprint|pandoc|raw]`
    - Also: `pdf.py from-md <markdown-file> <output>` for custom markdown
    - Engine priority: weasyprint (best, pip install) → pandoc → stdlib-only text PDF (zero deps)
    - Default `--engine auto` picks best available engine

## 8. Trigger behavior

Enter content creation mode immediately:

1. Confirm scope iteratively.
2. Write module 1.
3. Proceed module by module — never full course in one shot unless asked.
