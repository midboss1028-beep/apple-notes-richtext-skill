# apple-notes-richtext-skill

An Apple Notes rich-text Skill for AI agents on macOS. It ships a small CLI named `anote` plus a reusable Agent Skill, so agents can save UTF-8 Markdown or HTML into Apple Notes without losing Chinese text, line breaks, or basic rich-text formatting.

> Repository name keeps the core signal short: Apple Notes + rich text + skill. The terminal command stays shorter: `anote`.

## Background

Many agents can already write to Apple Notes through generic CLIs or ad-hoc AppleScript, but these workflows often break in exactly the places agents care about:

- Chinese text becomes garbled.
- Multiline content is collapsed into one paragraph.
- Markdown headings, lists, bold, italic, code blocks, and links are lost.
- Quotes, backslashes, backticks, dollar signs, and code snippets break AppleScript escaping.
- The note body is passed directly through shell arguments or `osascript -e`, which is fragile and unsafe for generated content.

`apple-notes-richtext-skill` fixes that by making the safe path the default path: agents write Markdown/HTML to a UTF-8 temp file, `anote` converts it to clean HTML, and AppleScript reads the body/title/account/folder from temp files instead of interpolating user content into script strings.

## What It Solves

- Reliable UTF-8 title/body handling, including Chinese.
- Real Markdown line breaks preserved as paragraphs or `<br>`.
- Markdown converted to Apple Notes friendly HTML.
- Safer AppleScript invocation with temp files instead of shell/body string interpolation.
- A ready-to-copy Agent Skill that tells agents when and how to call `anote`.
- Clear errors for missing folders/accounts, automation permission issues, and `osascript` failures.

## Advantages

- **Agent-first**: designed for AI agents that generate long Markdown notes.
- **Rich text**: preserves headings, paragraphs, tables, lists, bold, italic, inline code, fenced code blocks, and links.
- **UTF-8 safe**: all file reads/writes are explicit UTF-8.
- **AppleScript safe**: note body is never passed as a shell argument or embedded inside `osascript -e`.
- **Debuggable**: `--dry-run` prints final HTML without opening Notes or creating a note.
- **Small MVP**: Python + Typer + markdown + subprocess; no heavy framework.

## Requirements

- macOS with Notes.app
- Python 3.11+
- Apple Notes automation permission for your terminal/Python/agent runtime when prompted

## Install

From a local checkout:

```bash
git clone https://github.com/midboss1028-beep/apple-notes-richtext-skill.git
cd apple-notes-richtext-skill
python3 -m pip install -e .
```

For development:

```bash
python3 -m pip install -e ".[dev]"
pytest
```

With `pipx`:

```bash
pipx install git+https://github.com/midboss1028-beep/apple-notes-richtext-skill.git
```

Check the CLI:

```bash
anote --version
```

## CLI Usage

Create a sample Markdown file:

~~~bash
cat > note.md <<'EOF'
# Project Memo

Chinese text: 你好，Apple Notes.
This line break should be preserved.

- List item
- **Bold** and *italic*

```python
print("Hello, Apple Notes")
```
EOF
~~~

Create a note from Markdown:

```bash
anote add --title "Project Memo" --from note.md
```

Create a note from stdin:

```bash
cat note.md | anote add --title "Project Memo" --stdin
```

Write to a folder:

```bash
anote add --title "Project Memo" --folder "Work" --from note.md
```

Write to an account/folder:

```bash
anote add --title "Project Memo" --account "iCloud" --folder "Notes" --from note.md
```

Use HTML input:

```bash
anote add --title "HTML Note" --from note.html --format html
```

Preview converted HTML without opening Notes or creating a note:

```bash
anote add --title "Project Memo" --from note.md --dry-run
```

Debug paths and target selection without printing note body:

```bash
anote add --title "Project Memo" --from note.md --debug
```

## Agent Skill Installation

This repository includes an Agent Skill at:

```text
skills/anote/SKILL.md
```

The skill teaches an agent to use `anote` for Apple Notes creation, and to avoid old fragile `memo` or direct AppleScript body interpolation workflows.

### OpenClaw

Copy the skill into your OpenClaw workspace:

```bash
mkdir -p ~/.openclaw/workspace/skills/anote
cp skills/anote/SKILL.md ~/.openclaw/workspace/skills/anote/SKILL.md
openclaw gateway restart
openclaw skills info anote
```

Optional: if you want to replace OpenClaw's bundled `apple-notes` skill name, create a compatibility skill:

```bash
mkdir -p ~/.openclaw/workspace/skills/apple-notes
cp skills/anote/SKILL.md ~/.openclaw/workspace/skills/apple-notes/SKILL.md
python3 - <<'PY'
from pathlib import Path
p = Path.home() / ".openclaw/workspace/skills/apple-notes/SKILL.md"
text = p.read_text(encoding="utf-8")
text = text.replace("name: anote", "name: apple-notes", 1)
p.write_text(text, encoding="utf-8")
PY
openclaw gateway restart
openclaw skills info apple-notes
```

### Codex / Claude Code / Other Local Agents

Copy the skill folder into the agent's skill directory, or paste the content of `skills/anote/SKILL.md` into that agent's custom instructions.

Common patterns:

```bash
# Codex-style local skills
mkdir -p ~/.codex/skills/anote
cp skills/anote/SKILL.md ~/.codex/skills/anote/SKILL.md

# Claude-style local skills, if your setup uses this folder
mkdir -p ~/.claude/skills/anote
cp skills/anote/SKILL.md ~/.claude/skills/anote/SKILL.md
```

If your agent does not support skill files, use the prompt below.

## Prompt For Agents

```text
When the user asks to save, store, write, add, or create content in Apple Notes, use the anote CLI.

Rules:
- Write generated note content to a UTF-8 temp Markdown or HTML file first.
- Run: anote add --title "TITLE" --from /tmp/anote-note.md --format markdown
- Use --folder "FOLDER" when the user specifies an Apple Notes folder.
- Do not pass note body text directly into osascript or shell arguments.
- Do not use osascript -e '...body...'.
- Do not use memo notes -a for rich Markdown note creation.
- Use --dry-run only for preview/debugging; it must not create a note.
- Avoid echoing sensitive note content back to the user unless asked.
- If permissions fail, tell the user to grant Automation permission for Terminal/Python/the agent runtime to control Notes.app.

Supported formatting: headings, paragraphs, real line breaks, tables, unordered lists, ordered lists, bold, italic, inline code, fenced code blocks, and links.
Not supported in v1: native checklist items, images, attachments, search, append, update, and delete.
```

## How It Works

`anote` does not put the note body into shell arguments or AppleScript string literals. On write, it creates UTF-8 temp files:

- `anote-body-*.html`
- `anote-title-*.txt`
- `anote-account-*.txt`
- `anote-folder-*.txt`

AppleScript receives only file paths, reads them with UTF-8, then creates the note:

```applescript
make new note with properties {name:titleText, body:htmlText}
```

Markdown conversion uses `fenced_code`, `tables`, `sane_lists`, and `nl2br`, so empty lines become paragraphs and real line breaks inside a paragraph become `<br>`.

## Supported Markdown

- Headings
- Paragraphs
- Real line breaks
- Unordered lists
- Ordered lists
- Bold
- Italic
- Inline code
- Fenced code blocks
- Tables
- Links

Apple Notes decides final rendering. Blockquotes, horizontal rules, and nested formatting may be simplified.

## Project Structure

```text
.
├── README.md
├── pyproject.toml
├── anote
│   ├── __init__.py
│   ├── cli.py
│   ├── convert.py
│   └── notes.py
├── skills
│   └── anote
│       └── SKILL.md
├── examples
│   └── rich-test.md
└── tests
    ├── test_cli.py
    ├── test_convert.py
    └── test_notes.py
```

## Test

```bash
python3 -m pip install -e ".[dev]"
pytest
```

## Known Limitations

- macOS only.
- Creates new notes only.
- Does not support native Apple Notes checklist items.
- Does not support images, attachments, or complex tables (simple tables with `tables` extension are supported).
- Does not support search, append, update, or delete yet.
- Folder must already exist; v1 does not auto-create folders.
- First run may require macOS Automation permission.

## Roadmap

- `anote folders` / `anote accounts`
- `anote search`
- `anote append`
- `anote update`
- Optional folder creation
- MCP server for direct agent tool use
- Better task-list support
- Image and attachment support

## License

MIT

---

# apple-notes-richtext-skill 中文说明

这是一个面向 AI Agent 的 Apple Notes / 备忘录富文本写入 Skill。项目包含一个名为 `anote` 的 macOS CLI，以及一个可复制给 Agent 使用的 Skill，让 Agent 可以把 UTF-8 Markdown 或 HTML 稳定保存到 Apple Notes，不再丢中文、换行和基础 Markdown 格式。

> 仓库名保留核心信号：Apple Notes + 富文本 + Skill。终端命令保持更短：`anote`。

## 项目背景

很多 Agent 已经可以通过通用 CLI 或临时 AppleScript 写入 Apple Notes，但常见问题很多：

- 中文标题或正文乱码。
- 多行文本被压成一段。
- Markdown 标题、列表、粗体、斜体、代码块、链接丢失。
- 英文引号、反斜杠、反引号、美元符号和代码片段容易破坏 AppleScript 转义。
- 正文直接通过 shell 参数或 `osascript -e` 拼进去，既脆弱，也不适合 Agent 生成的长内容。

这个项目把安全路径变成默认路径：Agent 先把 Markdown/HTML 写入 UTF-8 临时文件，`anote` 转成干净 HTML，然后 AppleScript 只从临时文件读取正文、标题、账户和文件夹，不把用户正文插入 AppleScript 字符串。

## 解决的痛点

- 中文标题和正文稳定 UTF-8。
- Markdown 真实换行保留为段落或 `<br>`。
- Markdown 转成 Apple Notes 友好的 HTML。
- 使用临时文件调用 AppleScript，避免正文转义问题。
- 内置 Agent Skill，告诉 Agent 何时以及如何调用 `anote`。
- 文件夹不存在、账户不存在、权限不足、`osascript` 失败时给出清晰错误。

## 优势

- **Agent-first**：专门为 Agent 生成长 Markdown 笔记设计。
- **富文本**：保留标题、段落、表格、列表、粗体、斜体、行内代码、代码块和链接。
- **UTF-8 安全**：所有文件读写都显式使用 UTF-8。
- **AppleScript 安全**：正文不通过 shell 参数传递，也不嵌入 `osascript -e`。
- **易调试**：`--dry-run` 只输出最终 HTML，不打开 Notes，也不创建笔记。
- **轻量 MVP**：Python + Typer + markdown + subprocess，没有重框架。

## 环境要求

- macOS 和 Notes.app / 备忘录
- Python 3.11+
- 第一次运行时可能需要给终端、Python 或 Agent runtime 授权控制 Notes.app

## 安装

从本地仓库安装：

```bash
git clone https://github.com/midboss1028-beep/apple-notes-richtext-skill.git
cd apple-notes-richtext-skill
python3 -m pip install -e .
```

开发安装：

```bash
python3 -m pip install -e ".[dev]"
pytest
```

使用 `pipx`：

```bash
pipx install git+https://github.com/midboss1028-beep/apple-notes-richtext-skill.git
```

检查命令：

```bash
anote --version
```

## CLI 用法

准备示例 Markdown：

~~~bash
cat > note.md <<'EOF'
# 项目备忘

第一段中文正文。
第二行会保留为 HTML 换行。

- 列表项
- **粗体** 和 *斜体*

```python
print("你好，Apple Notes")
```
EOF
~~~

从 Markdown 创建笔记：

```bash
anote add --title "项目备忘" --from note.md
```

从 stdin 创建笔记：

```bash
cat note.md | anote add --title "项目备忘" --stdin
```

写入指定文件夹：

```bash
anote add --title "项目备忘" --folder "工作" --from note.md
```

写入指定账户和文件夹：

```bash
anote add --title "项目备忘" --account "iCloud" --folder "Notes" --from note.md
```

写入 HTML：

```bash
anote add --title "HTML 笔记" --from note.html --format html
```

只预览转换后的 HTML，不打开 Notes，不创建笔记：

```bash
anote add --title "项目备忘" --from note.md --dry-run
```

输出调试路径和目标选择，不打印正文：

```bash
anote add --title "项目备忘" --from note.md --debug
```

## Agent Skill 安装

仓库内置 Skill 文件：

```text
skills/anote/SKILL.md
```

这个 Skill 会教 Agent 使用 `anote` 创建 Apple Notes，并避免旧的 `memo` 或直接拼 AppleScript 正文的脆弱流程。

### OpenClaw

复制 Skill 到 OpenClaw workspace：

```bash
mkdir -p ~/.openclaw/workspace/skills/anote
cp skills/anote/SKILL.md ~/.openclaw/workspace/skills/anote/SKILL.md
openclaw gateway restart
openclaw skills info anote
```

如果你想替换 OpenClaw 内置的 `apple-notes` 技能名，可以创建兼容 Skill：

```bash
mkdir -p ~/.openclaw/workspace/skills/apple-notes
cp skills/anote/SKILL.md ~/.openclaw/workspace/skills/apple-notes/SKILL.md
python3 - <<'PY'
from pathlib import Path
p = Path.home() / ".openclaw/workspace/skills/apple-notes/SKILL.md"
text = p.read_text(encoding="utf-8")
text = text.replace("name: anote", "name: apple-notes", 1)
p.write_text(text, encoding="utf-8")
PY
openclaw gateway restart
openclaw skills info apple-notes
```

### Codex / Claude Code / 其他本地 Agent

把 Skill 文件复制到对应 Agent 的 skills 目录，或者把 `skills/anote/SKILL.md` 内容粘贴到该 Agent 的自定义指令里。

常见目录示例：

```bash
# Codex 风格本地 skills
mkdir -p ~/.codex/skills/anote
cp skills/anote/SKILL.md ~/.codex/skills/anote/SKILL.md

# Claude 风格本地 skills，如果你的配置使用该目录
mkdir -p ~/.claude/skills/anote
cp skills/anote/SKILL.md ~/.claude/skills/anote/SKILL.md
```

如果你的 Agent 不支持 Skill 文件，可以使用下面的提示词。

## 给 Agent 的提示词

```text
当用户要求保存、存储、写入、添加或创建 Apple Notes / 备忘录内容时，使用 anote CLI。

规则：
- 先把生成的笔记正文写入 UTF-8 Markdown 或 HTML 临时文件。
- 执行：anote add --title "标题" --from /tmp/anote-note.md --format markdown
- 如果用户指定 Apple Notes 文件夹，使用 --folder "文件夹名"。
- 不要把正文直接传给 osascript 或 shell 参数。
- 不要使用 osascript -e '...正文...'。
- 不要用 memo notes -a 创建富文本 Markdown 笔记。
- --dry-run 只用于预览/调试，不能创建笔记。
- 除非用户明确要求，不要在回复里复述敏感笔记正文。
- 如果权限失败，提醒用户在 macOS 系统设置中允许 Terminal/Python/Agent runtime 控制 Notes.app。

支持格式：标题、段落、真实换行、**表格**、无序列表、有序列表、粗体、斜体、行内代码、代码块、链接。
v1 不支持：原生 checklist、图片、附件、搜索、追加、更新和删除。
```

## 实现原理

`anote` 不把正文放进 shell 参数或 AppleScript 字符串。写入时会创建 UTF-8 临时文件：

- `anote-body-*.html`
- `anote-title-*.txt`
- `anote-account-*.txt`
- `anote-folder-*.txt`

AppleScript 只接收文件路径，用 UTF-8 读取后创建笔记：

```applescript
make new note with properties {name:titleText, body:htmlText}
```

Markdown 转换启用了 `fenced_code`、`tables`、`sane_lists` 和 `nl2br`，所以空行会形成段落，同一段里的真实换行会变成 `<br>`。

## 支持的 Markdown

- 标题
- 段落
- 真实换行
- 无序列表
- 有序列表
- 粗体
- 斜体
- 行内代码
- 代码块
- **表格**
- 链接

最终渲染由 Apple Notes 决定。引用、分隔线、复杂嵌套格式可能会被简化。

## 项目结构

```text
.
├── README.md
├── pyproject.toml
├── anote
│   ├── __init__.py
│   ├── cli.py
│   ├── convert.py
│   └── notes.py
├── skills
│   └── anote
│       └── SKILL.md
├── examples
│   └── rich-test.md
└── tests
    ├── test_cli.py
    ├── test_convert.py
    └── test_notes.py
```

## 测试

```bash
python3 -m pip install -e ".[dev]"
pytest
```

## 已知限制

- 仅支持 macOS。
- 目前只创建新笔记。
- 不支持 Apple Notes 原生 checklist。
- 不支持图片、附件、复杂表格（基础表格已支持）。
- 暂不支持搜索、追加、更新、删除。
- 文件夹必须已存在，v1 不会自动创建文件夹。
- 第一次运行可能需要 macOS Automation 权限。

## 路线图

- `anote folders` / `anote accounts`
- `anote search`
- `anote append`
- `anote update`
- 可选自动创建文件夹
- 面向 Agent 工具调用的 MCP server
- 更好的任务列表（checklist）支持
- 图片和附件支持

## 许可证

MIT
