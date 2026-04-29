---
name: anote
description: Use the anote CLI to create UTF-8 rich-text Apple Notes from Markdown or HTML on macOS. Trigger whenever the user asks to save, store, write, add, or create content in Apple Notes/备忘录, especially Chinese text, multiline text, Markdown, HTML, headings, lists, bold, italic, code blocks, or links. Prefer this over memo/apple-notes for creating notes.
metadata:
  openclaw:
    emoji: "📝"
    os: ["darwin"]
    requires:
      bins: ["anote"]
---

# anote Apple Notes Writer

Use `anote` when the user wants content saved into Apple Notes/备忘录. This replaces the old `memo`-based Apple Notes creation workflow because it handles UTF-8, Chinese, multiline Markdown, HTML, and richer formatting more reliably.

Open-source project: `apple-notes-richtext-skill`.

## Quick Workflow

1. Prepare the note content as UTF-8 Markdown or HTML.
2. Write the body to a temporary file, usually under `/tmp`, with a safe suffix such as `.md` or `.html`.
3. Run `anote add` with `--title` and `--from`.
4. Report the title and destination after success. Do not echo sensitive note content back unless the user asks.

Markdown example:

```bash
anote add --title "项目备忘" --from /tmp/anote-note.md --format markdown
```

HTML example:

```bash
anote add --title "项目备忘" --from /tmp/anote-note.html --format html
```

Folder example:

```bash
anote add --title "项目备忘" --folder "工作" --from /tmp/anote-note.md
```

Account and folder example:

```bash
anote add --title "项目备忘" --account "iCloud" --folder "Notes" --from /tmp/anote-note.md
```

## Content Handling Rules

- Always use UTF-8 for input files.
- Prefer `--from` with a temp file for generated content.
- `--stdin` is acceptable for short, non-sensitive content:

```bash
printf '%s\n' '# 标题' '' '正文' | anote add --title "标题" --stdin
```

- Do not pass the note body directly into AppleScript or `osascript`.
- Do not use `osascript -e '...正文...'`.
- Do not use `memo` to create rich Markdown notes; use `anote`.
- Avoid `--debug` for sensitive content. It prints temp paths, not the body, but still indicates where files are.
- Use `--dry-run` only when the user wants to inspect HTML or when debugging non-sensitive content. `--dry-run` does not open Notes and does not create a note.

## Supported Formatting

The first version supports:

- headings
- paragraphs and real line breaks
- unordered lists
- ordered lists
- bold
- italic
- inline code
- fenced code blocks
- links

Notes.app decides final rendering, so blockquotes, horizontal rules, tables, and nested formatting may be simplified.

## Error Handling

If `anote` fails:

- Folder missing: tell the user the folder does not exist; do not auto-create folders unless asked.
- Account missing: tell the user the account name was not found.
- Automation permission: tell the user to allow Terminal/Python/OpenClaw to control Notes.app in System Settings > Privacy & Security > Automation.
- Timeout: tell the user Notes.app may be unresponsive or waiting for permission; retry once only if it is safe.

Never delete Apple Notes unless the user explicitly asks and confirms at action time.

## Limits

This skill is for creating new Apple Notes. It does not support native checklist items, images, attachments, search, append, update, or delete. For unsupported operations, explain the limitation and ask how the user wants to proceed.
