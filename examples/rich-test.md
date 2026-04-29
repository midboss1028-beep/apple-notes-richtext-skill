# Apple Notes Rich Text Skill 富文本验收

这是第一段中文正文，用来确认 UTF-8 不乱码。
这是同一段里的真实换行，预期在 Apple Notes 中显示为换行。

## 基础样式

这一段包含 **粗体**、*斜体*、***粗斜体***、行内代码 `const ok = true`，以及一个链接：[OpenAI](https://openai.com)。

特殊字符压力测试："double quotes"、'single quotes'、反斜杠 \、反引号 `code`、美元符号 $HOME、中文标点：，。！？「」。

## 无序列表

- 第一项：中文列表项
- 第二项：包含 **粗体**
- 第三项：包含 `inline code`

## 有序列表

1. 第一步：读取 UTF-8 Markdown
2. 第二步：转换为 HTML
3. 第三步：通过临时 HTML 文件写入 Apple Notes

## 引用

> 这是一段 blockquote，用来观察 Apple Notes 是否保留引用样式。

## 代码块

```python
def hello(name: str) -> None:
    print(f"你好，{name}")
    path = r"C:\Users\jimmy\notes"
```

---

最后一段：如果你能看到上面的标题、段落、列表、粗体、斜体、代码块和链接，说明 MVP 的富文本路径基本符合预期。
