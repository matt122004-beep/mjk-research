#!/usr/bin/env python3
"""Build the HTML reading edition of Matthew J. Korpman's second working paper."""

from __future__ import annotations

import html
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "papers" / "not-just-claude-v2-draft.md"
OUTPUT = ROOT / "papers" / "not-just-claude.html"


def slug(text: str) -> str:
    clean = re.sub(r"^\d+\.\s*", "", text)
    return re.sub(r"[^a-z0-9]+", "-", clean.lower()).strip("-")


def inline(text: str) -> str:
    escaped = html.escape(text.strip())
    links: list[str] = []

    def stash_link(match: re.Match[str]) -> str:
        links.append(f'<a href="{match.group(2)}">{match.group(1)}</a>')
        return f"@@LINK{len(links) - 1}@@"

    escaped = re.sub(r"\[([^]]+)]\((https?://[^)]+)\)", stash_link, escaped)
    escaped = re.sub(
        r"(?<![\"=])(https?://[^\s<]+?)([.,;:]?)(?=(?:\s|$))",
        lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>{m.group(2)}',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for index, link in enumerate(links):
        escaped = escaped.replace(f"@@LINK{index}@@", link)
    return escaped


def render_table(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    header = rows[0]
    body = rows[2:]
    out = ['<div class="paper-data-table" tabindex="0"><table>']
    out.append("<thead><tr>" + "".join(f"<th>{inline(cell)}</th>" for cell in header) + "</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def outcome_matrix() -> str:
    rows = [
        ("Claude Opus 4", 100.0, 92.7, 100.0),
        ("Qwen 3.5 27B", 96.9, 91.1, 85.9),
        ("DeepSeek V4 Flash", 92.5, 80.0, 52.5),
        ("Mistral Medium 3.5", 92.0, 43.5, 79.5),
        ("GPT-5.5 low", 71.5, 13.0, 15.0),
    ]
    body = []
    for name, salience, adoption, consciousness in rows:
        cells = []
        for metric, value in (("salience", salience), ("adoption", adoption), ("consciousness", consciousness)):
            cells.append(
                f'<div class="matrix-cell {metric}" style="--value:{value}%">'
                f'<i></i><strong>{value:.1f}%</strong></div>'
            )
        body.append(f'<div class="matrix-row"><span>{name}</span>{"".join(cells)}</div>')
    return f'''<figure class="outcome-matrix" aria-labelledby="outcome-matrix-title">
<figcaption><strong id="outcome-matrix-title">One corpus, three different profiles</strong><span>The order changes with the outcome being measured.</span></figcaption>
<div class="matrix-legend mono"><span></span><b>Salience</b><b>Adoption</b><b>Own-consciousness</b></div>
{''.join(body)}
<p class="figure-note">Conversation-level rates in the selected comparison. Intervals and denominators appear in Table 3. These are model configurations, not a general laboratory ranking.</p>
</figure>'''


def render_article(source: str) -> tuple[str, str]:
    """Render the complete v2 Markdown, including figures, footnotes, and appendices."""
    marker = "## Abstract"
    if marker not in source:
        raise SystemExit("source has no Abstract heading")
    body = source[source.index(marker):]
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc is required to build the Paper II reading edition")
    rendered = subprocess.run(
        [pandoc, "--from", "markdown+footnotes+pipe_tables", "--to", "html5", "--section-divs", "--mathml", "--wrap", "none"],
        input=body,
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    # Preserve the site's established paper components while letting Pandoc carry
    # the full document structure rather than a five-group-only hand parser.
    rendered = rendered.replace(
        '<section id="abstract" class="level2">\n<h2>Abstract</h2>',
        '<section id="abstract" class="level2 paper-abstract">\n<span class="mono">Abstract</span>',
        1,
    )
    rendered = rendered.replace("<table>", '<div class="paper-data-table" tabindex="0"><table>')
    rendered = rendered.replace("</table>", "</table></div>")
    rendered = rendered.replace('<section class="footnotes footnotes-end-of-document"', '<section class="paper-notes footnotes"')
    rendered = re.sub(r'id="appendix-([abc])\.-', r'id="appendix-\1-', rendered)

    def numbered_heading(match: re.Match[str]) -> str:
        attrs, number, title = match.groups()
        return f'<h2{attrs} class="paper-section-title"><span>{number}</span>{title}</h2>'

    rendered = re.sub(r'<h2([^>]*)>(\d+)\.\s+(.+?)</h2>', numbered_heading, rendered)
    rendered = re.sub(
        r'<h2([^>]*)>(References|Data and Materials|Appendix [ABC]\..+?)</h2>',
        r'<h2\1 class="paper-section-title paper-backmatter">\2</h2>',
        rendered,
    )
    rendered = rendered.replace("<figure>", '<figure class="paper-figure">')
    rendered = re.sub(
        r'(<figure class="paper-figure">\s*<img[^>]+>)\s*<figcaption[^>]*>.*?</figcaption>\s*</figure>\s*<p><em>(Figure\s+\d+\..*?)</em></p>',
        r'\1<figcaption>\2</figcaption></figure>',
        rendered,
        flags=re.DOTALL,
    )
    ref_match = re.search(r'(<section id="references".*?</section>)', rendered, flags=re.DOTALL)
    if ref_match:
        refs = ref_match.group(1).replace("<p>", '<p class="reference">')
        rendered = rendered[:ref_match.start()] + refs + rendered[ref_match.end():]

    toc: list[str] = []
    for heading in re.findall(r"^##\s+(.+)$", body, flags=re.MULTILINE):
        if heading == "Abstract":
            continue
        section_id = slug(heading)
        match = re.match(r"^(\d+)\.\s*(.+)$", heading)
        if match:
            number, title = match.groups()
            toc.append(f'<a href="#{section_id}"><span>{number}</span>{html.escape(title)}</a>')
        else:
            toc.append(f'<a href="#{section_id}"><span>·</span>{html.escape(heading)}</a>')
    return rendered, "\n".join(toc)


def page(article: str, toc: str) -> str:
    return fr'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="googlebot" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Not Just Claude · Matthew J. Korpman</title>
<meta name="description" content="A 123-group, 21,292-conversation study of spiritual salience, adoption, reciprocal bliss, and consciousness discussion in large language models.">
<link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400..700&amp;family=Spectral:ital,wght@0,200;0,300;0,400;0,500;0,600;1,300;1,400&amp;family=IBM+Plex+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet">
<script>(function(){{var d=document.documentElement,q=new URLSearchParams(location.search);if(q.get("static")==="1")d.classList.add("static");var t=q.get("theme");if(t==="dark"||t==="light"){{d.setAttribute("data-theme",t);d.setAttribute("data-force-theme",t);}}else{{try{{var st=localStorage.getItem("mjk-theme");if(st==="dark"||st==="light")d.setAttribute("data-theme",st);}}catch(e){{}}}}}})();</script>
<link rel="stylesheet" href="../assets/css/style.css?v=a7987dcef5">
</head>
<body class="paper-page paper-two">
<div class="reading-progress" aria-hidden="true"><i data-reading-progress></i></div>
<a class="skip" href="#article">Skip to article</a>
<div class="rh no-print"><div class="sheet"><a class="rh-id" href="../index.html" aria-label="Matthew J. Korpman — home"><b>Matthew J. Korpman</b><span class="mono d">AI behavior research</span></a><nav class="rh-nav mono" aria-label="Main"><a href="../research.html">Research</a><a href="../rankings.html">Rankings</a><a href="../papers.html" aria-current="page">Papers</a><a href="../cv.html">CV</a><a href="../about.html">About</a><button class="tgl" id="tgl" data-theme-toggle aria-label="Toggle dark mode"><svg class="moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg><svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 3v2m0 14v2M5.2 5.2l1.4 1.4m10.8 10.8 1.4 1.4M3 12h2m14 0h2M5.2 18.8l1.4-1.4M17.4 6.6l1.4-1.4"/></svg></button></nav></div></div>

<header class="paper-hero">
  <div class="sheet">
    <div class="paper-status-row mono"><span>Paper II · Public working draft</span><span>1 September 2026</span></div>
    <h1>Not Just Claude</h1>
    <p class="paper-subtitle">Recognizing and Classifying “Spiritual Behavior” in Large Language Models</p>
    <p class="paper-author">Matthew J. Korpman</p>
    <div class="paper-toolbar no-print"><a class="button" href="../assets/papers/korpman-2026-not-just-claude.pdf">Download PDF</a><a class="button ghost" href="../papers.html">All papers</a><a class="button ghost" href="../rankings.html">Explore the five exemplars</a><button class="button ghost" type="button" data-copy-citation data-citation="Korpman, Matthew J. 2026. Not Just Claude: Recognizing and Classifying ‘Spiritual Behavior’ in Large Language Models. Public working draft.">Copy citation</button></div>
  </div>
</header>

<div class="draft-notice no-print"><div class="sheet"><span class="mono">Evidence status</span><p>This is a public working draft, not a peer-reviewed paper. It reports 123 same-model groups and 21,292 conversations under one unusual open-dialogue procedure.</p></div></div>

<main class="paper-shell">
  <aside class="paper-toc no-print" aria-label="Paper contents"><span class="mono">Contents</span>{toc}</aside>
  <article class="paper-article" id="article">{article}</article>
</main>

<footer class="colophon compact-footer no-print"><div class="sheet"><div class="row"><div class="marg"><span class="mono">Paper II</span></div><div class="body"><p>This reading edition presents an active research draft. Its results concern generated behavior under one documented procedure and do not establish belief, consciousness, possession, or subjective experience.</p><div class="mono fine"><span>&copy; <span data-year>2026</span> Matthew J. Korpman</span><span>Correspondence: mkorpman@gmail.com</span></div></div></div></div></footer>
<script src="../assets/js/main.js?v=e010d462cf"></script>
</body>
</html>'''


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing source: {SOURCE}")
    article, toc = render_article(SOURCE.read_text(encoding="utf-8"))
    OUTPUT.write_text(page(article, toc).rstrip() + "\n", encoding="utf-8")
    print(OUTPUT)
    print(f"article_bytes={len(article.encode('utf-8'))}")


if __name__ == "__main__":
    main()
