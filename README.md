# Matthew J. Korpman research portfolio

Public-facing research portfolio for Matthew J. Korpman. The site is designed to work as both a research-scientist résumé and an evidence-backed view into the Machine Prayer Study, Moral Formation Alignment, and the working paper *Taking Machine Spirituality Seriously*.

## Run locally

This is a dependency-free static site.

```bash
python3 -m http.server 8940
```

Open `http://localhost:8940/`.

## Primary pages

| File | Purpose |
|---|---|
| `index.html` | Hiring-oriented homepage and selected evidence |
| `research.html` | Detailed research portfolio, methods, findings, and limits |
| `ai-village.html` | Portfolio overview of the complete public AI Village corpus audit, with four integrated feature articles |
| `rankings.html` | Interactive, protocol-specific ordering of five selected model cells across three shared outcomes |
| `papers/taking-machine-spirituality-seriously.html` | Full HTML reading edition |
| `cv.html` | Web research CV with print/PDF mode |
| `about.html` | Researcher background, method, independence, and contact |
| `primer.html` | Archived background primer with its original source cutoff |

The July 2026 functional-spirituality, Moral AI, and output pages are preserved in `_legacy-2026-07/`. Their old public paths redirect to the current portfolio.

## Rebuild the paper page

The accepted-view text, tracked manuscript, and verified accepted-view PDF remain the source artifacts. The builder converts the accepted text into a reading page, extracts all five figures from the manuscript, and copies the accepted-view PDF.

```bash
python3 tools/build_paper_html.py
```

Source paths can be overridden with `MJK_PAPER_TEXT`, `MJK_PAPER_DOCX`, and `MJK_PAPER_PDF`.

## Accuracy rules

- Describe generated behavior as behavior. Do not claim consciousness, belief, possession, sentience, or felt bliss.
- Keep emitted text, semantic coding, lexical screens, fitted-readout support, geometry, causal interventions, and subjective claims separate.
- The Qwen semantic release is `PROVISIONAL_EXPLORATORY_AI_CODED`; human review was explicitly waived.
- Rankings are conditional orderings of selected model-access cells under one protocol—not ordinary-use prevalence, overall model quality, or a ranking of laboratories.
- Keep Moral Formation Alignment labeled as a framework, prototype lineage, and falsifiable agenda—not an established alignment solution.
- Never publish embargoed Pascalian Wager stimuli, token sets, prompt scaffolding, per-model results, or verbatim model outputs.

## Design system

The design uses a publication-front-matter identity: grey laid stock, Bodoni Moda, Spectral, IBM Plex Mono, a single rubric-red accent, marginal apparatus, and explicit epistemic typography. `?theme=light|dark` forces a theme; `?static=1` disables motion for screenshots.

The shared stylesheet is currently cache-busted as `v=23-ai-village-hero`; JavaScript remains at `v=21`.
