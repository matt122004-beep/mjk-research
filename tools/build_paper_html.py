#!/usr/bin/env python3
"""Update the public paper page from the accepted view of the tracked Word file.

The surrounding website markup is preserved. Only the paper hero, contents,
article, figures, notes, and linked PDF are rebuilt from the current sources.
"""

from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree, html as lhtml


ROOT = Path(__file__).resolve().parents[1]


def environment_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else None


SOURCE_DOCX = environment_path("MJK_PAPER_DOCX")
OUTPUT_HTML = ROOT / "papers" / "taking-machine-spirituality-seriously.html"
IMAGE_DIR = ROOT / "assets" / "img" / "paper"
PDF_OUT = ROOT / "assets" / "papers" / "korpman-2026-taking-machine-spirituality-seriously.pdf"
SOURCE_PDF = environment_path("MJK_PAPER_PDF")

PYTHON = Path(os.environ.get("CODEX_BUNDLED_PYTHON", sys.executable))
PANDOC = Path(os.environ.get("PANDOC", shutil.which("pandoc") or "/opt/homebrew/bin/pandoc"))

configured_document_skill = environment_path("CODEX_DOCUMENT_SKILL_ROOT")
installed_document_skills = sorted(
    (Path.home() / ".codex" / "plugins" / "cache" / "openai-primary-runtime" / "documents").glob(
        "*/skills/documents"
    )
)
DOCUMENT_SKILL_ROOT = configured_document_skill or (
    installed_document_skills[-1] if installed_document_skills else ROOT / "__missing_document_skill__"
)
ACCEPT_CHANGES = DOCUMENT_SKILL_ROOT / "scripts" / "accept_tracked_changes.py"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W_ID = f"{{{NS['w']}}}id"
FIGURE_NAMES = [f"figure{index}.png" for index in range(1, 6)]
URL_RE = re.compile(r"https?://[^\s<>()]+")


AUTHOR_DECISIONS = (
    (
        "Anthropic’s complete historical set of instructions also remains unavailable, and outside human readers have not independently reviewed the primary classifications.",
        "Anthropic’s complete historical set of instructions also remains unavailable.",
    ),
    (
        "Because the two readers are versions of one model family, their agreement limits coder drift but does not substitute for an independent check, and no outside human readers reviewed and resolved the classifications under blinded conditions in the present set of results.",
        "Because the two readers are versions of one model family, their agreement limits one kind of coder drift.",
    ),
    (
        ", and the primary judgments have not yet been checked by human readers who do not know which model produced each conversation",
        "",
    ),
    (
        ", check the judges against samples coded by humans,",
        ",",
    ),
    (
        "Human readers who were unaware of which model produced each conversation have not yet judged the same sample independently. ",
        "",
    ),
)


def run(*args: str | Path) -> None:
    subprocess.run([str(arg) for arg in args], check=True)


def apply_author_decisions(fragment_html: str) -> str:
    for old, new in AUTHOR_DECISIONS:
        count = fragment_html.count(old)
        if count != 1:
            raise RuntimeError(f"expected one author-decision passage, found {count}: {old[:72]}")
        fragment_html = fragment_html.replace(old, new)
    fragment_html = fragment_html.replace(
        "https://matt122004-beep.github.io/mjk-research/papers/not-just-claude.html",
        "https://mkorpman.com/papers/not-just-claude.html",
    )
    return fragment_html


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def paragraph_style(paragraph: etree._Element) -> str:
    values = paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)
    return values[0] if values else ""


def read_frontmatter(docx: Path) -> dict[str, str]:
    with zipfile.ZipFile(docx) as archive:
        document = etree.fromstring(archive.read("word/document.xml"))
        footnotes = etree.fromstring(archive.read("word/footnotes.xml"))

    values: dict[str, str] = {}
    abstract_paragraphs: list[str] = []
    for paragraph in document.xpath(".//w:body/w:p", namespaces=NS):
        style = paragraph_style(paragraph)
        text = paragraph_text(paragraph)
        if style == "Title":
            values["title"] = text
        elif style == "Author":
            values["author"] = text
        elif style == "Abstract" and text and text != "Abstract":
            abstract_paragraphs.append(text)
        elif text.startswith("Keywords:"):
            values["keywords"] = text
        if style == "Heading1":
            break
    values["abstract"] = " ".join(abstract_paragraphs)

    for footnote in footnotes.xpath(".//w:footnote", namespaces=NS):
        if footnote.get(W_ID) == "1":
            values["author_note"] = paragraph_text(footnote)
            break

    required = ("title", "author", "abstract", "keywords", "author_note")
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise RuntimeError(f"missing Word front matter: {', '.join(missing)}")
    return values


def copy_figures(docx: Path) -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx) as archive:
        for index, filename in enumerate(FIGURE_NAMES, start=1):
            source_name = f"word/media/image{index}.png"
            with archive.open(source_name) as source, (IMAGE_DIR / filename).open("wb") as target:
                shutil.copyfileobj(source, target)


def add_classes(element: etree._Element, *names: str) -> None:
    current = element.get("class", "").split()
    for name in names:
        if name not in current:
            current.append(name)
    element.set("class", " ".join(current))


def clean_url(url: str) -> tuple[str, str]:
    trailing = ""
    while url and url[-1] in ".,;:":
        trailing = url[-1] + trailing
        url = url[:-1]
    return url, trailing


def linkify_element_text(element: etree._Element) -> None:
    text = element.text or ""
    matches = list(URL_RE.finditer(text))
    if not matches:
        return
    element.text = text[: matches[0].start()]
    insert_at = 0
    for index, match in enumerate(matches):
        url, trailing = clean_url(match.group(0))
        anchor = etree.Element("a", href=url)
        anchor.text = url
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        anchor.tail = trailing + text[match.end() : next_start]
        element.insert(insert_at, anchor)
        insert_at += 1


def linkify_tail(child: etree._Element) -> None:
    text = child.tail or ""
    matches = list(URL_RE.finditer(text))
    if not matches:
        return
    parent = child.getparent()
    if parent is None:
        return
    child.tail = text[: matches[0].start()]
    insert_at = parent.index(child) + 1
    for index, match in enumerate(matches):
        url, trailing = clean_url(match.group(0))
        anchor = etree.Element("a", href=url)
        anchor.text = url
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        anchor.tail = trailing + text[match.end() : next_start]
        parent.insert(insert_at, anchor)
        insert_at += 1


def linkify_bare_urls(root: etree._Element) -> None:
    for element in list(root.iter()):
        if element.tag not in {"a", "code", "pre"} and not element.xpath("ancestor::a"):
            linkify_element_text(element)
        for child in list(element):
            linkify_tail(child)


def transform_claims_brief(root: etree._Element) -> None:
    for quote in root.xpath(".//blockquote"):
        paragraph = quote.find("p")
        strong = paragraph.find("strong") if paragraph is not None else None
        if strong is None or "Claims in brief" not in "".join(strong.itertext()):
            continue
        add_classes(quote, "claims-brief")
        label = etree.Element("span")
        label.set("class", "mono")
        label.text = "Claims in brief:"
        label.tail = " "
        remainder = strong.tail or ""
        strong.tail = None
        paragraph.remove(strong)
        paragraph.text = ((paragraph.text or "") + remainder).lstrip(": ")
        quote.insert(0, label)
        break


def transform_footnotes(root: etree._Element, author_note: str) -> etree._Element:
    source_notes = root.xpath(".//section[@id='footnotes']")
    if len(source_notes) != 1:
        raise RuntimeError(f"expected one notes section, found {len(source_notes)}")
    source_notes = source_notes[0]

    for reference in root.xpath(".//a[contains(concat(' ', normalize-space(@class), ' '), ' footnote-ref ')]"):
        number = int("".join(reference.itertext()).strip()) + 1
        reference.set("href", f"#note-{number}")
        reference.set("id", f"note-ref-{number}")
        reference.set("class", "footnote-ref")
        reference.attrib.pop("role", None)
        sup = reference.find("sup")
        if sup is not None:
            sup.text = str(number)

    note_bodies: list[etree._Element] = []
    for item in source_notes.xpath(".//ol/li"):
        paragraph = item.find("p")
        if paragraph is None:
            continue
        for backlink in paragraph.xpath(".//a[contains(concat(' ', normalize-space(@class), ' '), ' footnote-back ')]"):
            parent = backlink.getparent()
            if parent is not None:
                parent.remove(backlink)
        first_sup = paragraph.find("sup")
        if first_sup is not None and (first_sup.text or "").strip().isdigit():
            tail = first_sup.tail or ""
            paragraph.text = ((paragraph.text or "") + tail).lstrip()
            paragraph.remove(first_sup)
        note_bodies.append(paragraph)
    source_notes.getparent().remove(source_notes)

    notes = etree.Element("section", id="notes")
    notes.set("class", "paper-notes")
    heading = etree.SubElement(notes, "h2")
    heading.text = "Notes"
    ordered = etree.SubElement(notes, "ol")

    author_item = etree.SubElement(ordered, "li", id="note-1")
    author_item.text = author_note + " "
    author_back = etree.SubElement(author_item, "a", href="#note-ref-1")
    author_back.set("class", "footnote-back")
    author_back.text = "↩"

    for number, paragraph in enumerate(note_bodies, start=2):
        item = etree.SubElement(ordered, "li", id=f"note-{number}")
        if paragraph.text:
            item.text = paragraph.text
        for child in list(paragraph):
            paragraph.remove(child)
            item.append(child)
        if len(item):
            item[-1].tail = (item[-1].tail or "") + " "
        else:
            item.text = (item.text or "") + " "
        backlink = etree.SubElement(item, "a", href=f"#note-ref-{number}")
        backlink.set("class", "footnote-back")
        backlink.text = "↩"

    return notes


def transform_body(fragment_html: str, frontmatter: dict[str, str]) -> tuple[str, str]:
    root = lhtml.fragment_fromstring(fragment_html, create_parent="div")

    first = root.find("p")
    if first is not None and "Keywords:" in "".join(first.itertext()):
        root.remove(first)

    toc_links: list[str] = []
    for heading in root.xpath(".//h1"):
        title = " ".join("".join(heading.itertext()).split())
        match = re.match(r"^(\d+)\.\s+(.*)$", title)
        heading.tag = "h2"
        add_classes(heading, "paper-section-title")
        for child in list(heading):
            heading.remove(child)
        heading.text = None
        if match:
            number, display = match.groups()
            marker = etree.SubElement(heading, "span")
            marker.text = number
            marker.tail = display
        else:
            number, display = "·", title
            heading.text = display
        toc_links.append(f'<a href="#{heading.get("id")}"><span>{number}</span>{html.escape(display)}</a>')

    for heading in root.xpath(".//h2[not(contains(concat(' ', normalize-space(@class), ' '), ' paper-section-title '))]"):
        heading.tag = "h3"

    figures = root.xpath(".//figure")
    if len(figures) != len(FIGURE_NAMES):
        raise RuntimeError(f"expected {len(FIGURE_NAMES)} figures, found {len(figures)}")
    for figure, filename in zip(figures, FIGURE_NAMES):
        add_classes(figure, "paper-figure")
        image = figure.find("img")
        if image is None:
            raise RuntimeError(f"missing image in {filename}")
        image.set("src", f"../assets/img/paper/{filename}")
        image.attrib.pop("style", None)
        if image.getparent().tag != "a":
            parent = image.getparent()
            index = parent.index(image)
            parent.remove(image)
            anchor = etree.Element("a", href=f"../assets/img/paper/{filename}")
            anchor.append(image)
            parent.insert(index, anchor)

    for table in list(root.xpath(".//table")):
        wrapper = etree.Element("div")
        wrapper.set("class", "paper-data-table")
        parent = table.getparent()
        index = parent.index(table)
        parent.remove(table)
        wrapper.append(table)
        parent.insert(index, wrapper)

    transform_claims_brief(root)
    notes = transform_footnotes(root, frontmatter["author_note"])

    reference_heading = root.xpath(".//h2[@id='references']")
    if reference_heading:
        in_references = False
        for child in list(root):
            if child is reference_heading[0]:
                in_references = True
                continue
            if in_references and child.tag == "p":
                add_classes(child, "reference")

    linkify_bare_urls(root)

    abstract = etree.Element("section")
    abstract.set("class", "paper-abstract")
    label = etree.SubElement(abstract, "span")
    label.set("class", "mono")
    label.text = "Abstract"
    abstract_text = etree.SubElement(abstract, "p")
    abstract_text.text = frontmatter["abstract"]

    byline = etree.Element("p")
    byline.set("class", "paper-byline")
    byline.text = frontmatter["author"]
    author_ref = etree.SubElement(byline, "a", href="#note-1", id="note-ref-1")
    author_ref.set("class", "footnote-ref")
    author_sup = etree.SubElement(author_ref, "sup")
    author_sup.text = "1"

    keywords = etree.Element("p")
    keywords.set("class", "paper-keywords")
    keywords.text = frontmatter["keywords"]

    root.insert(0, keywords)
    root.insert(0, byline)
    root.insert(0, abstract)
    root.append(notes)

    article = "\n".join(lhtml.tostring(child, encoding="unicode", method="html") for child in root)
    toc = "\n".join(toc_links) + '\n<a href="#notes"><span>·</span>Notes</a>'
    return article, toc


def replace_once(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"could not replace {label}: found {count}")
    return updated


def update_page(article: str, toc: str, title: str) -> None:
    page = OUTPUT_HTML.read_text(encoding="utf-8")
    main_title, subtitle = title.split(":", 1)
    main_title = main_title.strip()
    subtitle = subtitle.strip()
    citation = f"Korpman, Matthew J. 2026. {main_title}: {subtitle}. Working paper."

    page = replace_once(
        page,
        r'<div class="paper-status-row mono">.*?</div>',
        '<div class="paper-status-row mono"><span>Working paper</span><span>HTML reading edition</span></div>',
        "paper status",
    )
    title_match = re.search(r'(<header class="paper-hero">.*?<h1>).*?(</h1>)', page, flags=re.DOTALL)
    if title_match is None:
        raise RuntimeError("could not replace paper title")
    page = page[: title_match.start()] + title_match.group(1) + html.escape(main_title) + title_match.group(2) + page[title_match.end() :]
    page = replace_once(page, r'<p class="paper-subtitle">.*?</p>', f'<p class="paper-subtitle">{html.escape(subtitle)}</p>', "paper subtitle")
    page = replace_once(page, r'data-citation="[^"]*"', f'data-citation="{html.escape(citation, quote=True)}"', "citation")
    page = replace_once(
        page,
        r'<aside class="paper-toc no-print" aria-label="Paper contents">.*?</aside>',
        f'<aside class="paper-toc no-print" aria-label="Paper contents"><span class="mono">Contents</span>{toc}</aside>',
        "contents",
    )
    page = replace_once(
        page,
        r'<article class="paper-article" id="article">.*?</article>',
        f'<article class="paper-article" id="article">{article}</article>',
        "article",
    )
    OUTPUT_HTML.write_text(page, encoding="utf-8")


def copy_public_pdf() -> None:
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_PDF, PDF_OUT)


def main() -> None:
    if SOURCE_DOCX is None or SOURCE_PDF is None:
        raise SystemExit("set MJK_PAPER_DOCX and MJK_PAPER_PDF to the approved source artifacts")

    for required in (SOURCE_DOCX, SOURCE_PDF, PYTHON, PANDOC, ACCEPT_CHANGES, OUTPUT_HTML):
        if not required.exists():
            raise SystemExit(f"missing required file: {required}")

    with tempfile.TemporaryDirectory(prefix="mjk-paper-site-") as temporary:
        work = Path(temporary)
        accepted = work / "accepted.docx"
        fragment = work / "accepted.html"
        media = work / "media"

        run(PYTHON, ACCEPT_CHANGES, "--mode", "accept", "--out", accepted, SOURCE_DOCX)
        frontmatter = read_frontmatter(accepted)
        frontmatter["title"] = frontmatter["title"].replace("Their Relevance", "Its Relevance")
        run(PANDOC, accepted, "-t", "html", "--wrap=none", "--extract-media", media, "-o", fragment)
        fragment_html = apply_author_decisions(fragment.read_text(encoding="utf-8"))
        article, toc = transform_body(fragment_html, frontmatter)
        update_page(article, toc, frontmatter["title"])
        copy_figures(accepted)
        copy_public_pdf()

    print(OUTPUT_HTML)
    print(f"article_bytes={len(article.encode('utf-8'))}")
    print(PDF_OUT)


if __name__ == "__main__":
    main()
