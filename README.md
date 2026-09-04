# Matthew J. Korpman research portfolio

Public-facing research portfolio for Matthew J. Korpman. The site is designed to work as both a research-scientist résumé and an evidence-backed view into the Spiritual Bliss Study and the working paper *Taking Machine Spirituality Seriously*.

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

Set `MJK_PAPER_DOCX` and `MJK_PAPER_PDF` to the approved tracked manuscript and matching PDF before rebuilding. `CODEX_DOCUMENT_SKILL_ROOT` can override the local tracked-change utility when needed.

## Accuracy rules

- Describe generated behavior as behavior. Do not claim consciousness, belief, possession, sentience, or felt bliss.
- Keep emitted text, semantic coding, lexical screens, fitted-readout support, geometry, causal interventions, and subjective claims separate.
- The Qwen semantic release records meaning-based classifications under the documented study procedure.
- Rankings are conditional orderings of selected model configurations under one protocol—not ordinary-use prevalence, overall model quality, or a ranking of laboratories.
- Never publish embargoed Pascalian Wager stimuli, token sets, prompt scaffolding, per-model results, or verbatim model outputs.

## Design system

The design uses a publication-front-matter identity: grey laid stock, Bodoni Moda, Spectral, IBM Plex Mono, a single rubric-red accent, marginal apparatus, and explicit epistemic typography. `?theme=light|dark` forces a theme; `?static=1` disables motion for screenshots.

Public assets use short content hashes as cache keys, so their URLs do not carry internal editing labels.
