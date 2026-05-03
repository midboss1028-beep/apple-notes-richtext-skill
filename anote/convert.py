from __future__ import annotations

from enum import Enum
import re

import markdown as markdown_lib


class InputFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"


_HTML_DOCUMENT_RE = re.compile(r"<html(?:\s|>)", re.IGNORECASE)


def convert_to_html(source: str, input_format: InputFormat) -> str:
    """Convert user input into a complete UTF-8 HTML document."""
    if input_format == InputFormat.MARKDOWN:
        body_html = markdown_to_body_html(source)
        return wrap_html_document(body_html)

    if input_format == InputFormat.HTML:
        return ensure_html_document(source)

    raise ValueError(f"Unsupported input format: {input_format}")


def markdown_to_body_html(source: str) -> str:
    """Convert Markdown text to HTML body markup."""
    return markdown_lib.markdown(
        source,
        extensions=["fenced_code", "nl2br", "sane_lists", "tables"],
        output_format="html5",
    )


def ensure_html_document(source: str) -> str:
    """Return a complete HTML document, wrapping fragments when needed."""
    if _HTML_DOCUMENT_RE.search(source):
        return source

    return wrap_html_document(source)


def wrap_html_document(body_html: str) -> str:
    """Wrap HTML body markup in a small Apple Notes friendly document."""
    body = body_html.strip()
    return (
        "<!doctype html>\n"
        "<html>\n"
        "<head>\n"
        '<meta charset="utf-8">\n'
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )
