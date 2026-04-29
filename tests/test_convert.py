from anote.convert import InputFormat, convert_to_html


def test_markdown_to_html_keeps_common_rich_text_elements() -> None:
    source = """# 标题

这是 **粗体** 和 *斜体*，以及 `代码`。

- 项一
- 项二

1. 第一
2. 第二

```python
print("你好")
```

[链接](https://example.com)
"""

    html = convert_to_html(source, InputFormat.MARKDOWN)

    assert html.startswith("<!doctype html>")
    assert '<meta charset="utf-8">' in html
    assert "<h1>标题</h1>" in html
    assert "<strong>粗体</strong>" in html
    assert "<em>斜体</em>" in html
    assert "<code>代码</code>" in html
    assert "<ul>" in html
    assert "<ol>" in html
    assert "<pre><code" in html
    assert "print(&quot;你好&quot;)" in html
    assert '<a href="https://example.com">链接</a>' in html


def test_markdown_real_linebreaks_are_preserved() -> None:
    html = convert_to_html("第一行\n第二行\n\n第三段", InputFormat.MARKDOWN)

    assert "<p>第一行<br>\n第二行</p>" in html
    assert "<p>第三段</p>" in html


def test_markdown_special_characters_and_code_blocks_are_preserved() -> None:
    source = """正文包含 "double"、'single'、\\backslash、`inline`、$HOME、中文标点：你好。

```sh
echo "hi" && printf '%s\\n' "$HOME"
```
"""

    html = convert_to_html(source, InputFormat.MARKDOWN)

    assert '"double"' in html
    assert "'single'" in html
    assert "\\backslash" in html
    assert "<code>inline</code>" in html
    assert "$HOME" in html
    assert "中文标点：你好。" in html
    assert "<pre><code" in html
    assert "printf '%s\\n' &quot;$HOME&quot;" in html


def test_html_fragment_is_wrapped_in_utf8_document() -> None:
    html = convert_to_html("<h1>Hello</h1>", InputFormat.HTML)

    assert html.startswith("<!doctype html>")
    assert '<meta charset="utf-8">' in html
    assert "<body>\n<h1>Hello</h1>\n</body>" in html


def test_complete_html_document_is_preserved() -> None:
    source = '<html><head><meta charset="utf-8"></head><body><p>Hi</p></body></html>'

    assert convert_to_html(source, InputFormat.HTML) == source
