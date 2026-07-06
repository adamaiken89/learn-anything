# Content Verification — Evidence-Based Quality Check

Load after each module generation. Verify against criteria below before presenting.

## Checklist (from Content Design Mod17)

- [ ] Concrete problem/example first, not abstract definition?
- [ ] ≤2 concepts per section (~WM limit, CLT Mod2)?
- [ ] Active engagement: cloze, predict, error-spot? (Retrieval Mod7, Feedback Mod12)
- [ ] Immediate feedback after every exercise? (Feedback Mod12)
- [ ] Non-redundant diagram for structure/relationships? (Dual Coding Mod6, Redundancy Effect CLT Mod2)
- [ ] No extraneous fluff? (CLT Mod2 — extraneous load)
- [ ] Builds on previous modules? (schema building, CLT Mod2)
- [ ] Ends with retrieval opportunity (Feynman/Drill)? (Retrieval Mod7)

## Redundancy Effect Check

If same info appears through verbal AND visual channel simultaneously, mark violation:

| Violation | Example | Fix |
|-----------|---------|-----|
| Diagram repeats text paragraph | Paragraph describing flowchart + same flowchart | Remove paragraph. Diagram alone sufficient. |
| Narration + identical on-screen text | "The heart pumps blood" written AND narrated | Use narration OR text, not both (Mayer redundancy principle). |
| Separate legend for self-labeled diagram | "Fig 1: A=heart, B=lungs" when labels already on diagram | Remove legend. Integrate labels onto diagram (spatial contiguity). |

## Syntax Validation

- [ ] All code blocks opened with ``` are closed?
- [ ] Heading hierarchy valid (no skipped levels)?
- [ ] Mermaid blocks have valid diagram type keyword?
- [ ] Mermaid `style` statements use valid hex colors?
- [ ] Mermaid `subgraph`/`end` blocks paired?
- [ ] Links `[text](url)` and images `![alt](src)` well-formed?
- [ ] Bold `**` and italic `*` markers properly closed?
- [ ] Table header/separator column counts match?

Run `learn.sh validate-content <topic> [module]` for automated checks.

## Design Strategies (use ≥2 per module)

| Strategy | Usage | Science |
|----------|-------|---------|
| **Chunking** | Break complex topics into 2-4 sub-topics per section | CLT Mod2 — WM ~4 chunk limit |
| **Fading worked examples** | Full worked → partial (fill blanks) → independent | CLT Mod2 — worked example effect |
| **Self-explanation prompts** | "Why does this step work?" after each claim | Deep Proc Mod5 — elaborative interrogation |
| **Pre-training** | Introduce key terms before complex interaction | CLT Mod2 — reduced momentary intrinsic load |

## 14 Quality Rules Reference

| # | Rule | Science module |
|---|------|----------------|
| 1 | Explain conventions | CLT Mod2 (extraneous load) |
| 2 | Answer implicit Qs | Deep Proc Mod5 (elaboration) |
| 3 | Pull-to-par intuition | CLT Mod2 (causal chain) |
| 4 | Causal chain first | CLT Mod2 + Deep Proc Mod5 |
| 5 | Practical context | Deep Proc Mod5 (elaboration) |
| 6 | "How likely" | Feedback Mod12 (prediction calibration) |
| 7 | Common misconceptions | Error-Driven Learning Mod12 |
| 8 | Socratic throughout | Deep Proc Mod5 (elaborative interrogation) |
| 9 | Dual coding (non-redundant) | Dual Coding Mod6 + CLT Mod2 (redundancy) |
| 10 | Concrete-first ordering | CLT Mod2 (schema building) |
| 11 | Cloze deletions | Retrieval Practice Mod7 |
| 12 | Predict-next | Error-Driven Learning Mod12 |
| 13 | Error-spotting | Error-Driven Learning Mod12 |
| 14 | Graduated examples | CLT Mod2 (fading worked examples) |

If any item fails, rewrite affected section. Cite violated principle.
