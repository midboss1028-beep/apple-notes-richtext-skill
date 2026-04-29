from pathlib import Path
import subprocess

import pytest

from anote.notes import NotesError, create_note


def test_create_note_passes_body_title_and_target_via_temp_files(monkeypatch: pytest.MonkeyPatch) -> None:
    body = '<p>中文 "double" \'single\' \\backtick `code` $HOME，标点。</p>'
    title = '标题 "quoted" 中文'
    captured_paths: list[Path] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert args[0:2] == ["osascript", "-e"]
        assert body not in args
        assert title not in args

        paths = [Path(value) for value in args[-4:]]
        captured_paths.extend(paths)

        html_path, title_path, account_path, folder_path = paths
        assert html_path.read_text(encoding="utf-8") == body
        assert title_path.read_text(encoding="utf-8") == title
        assert account_path.read_text(encoding="utf-8") == "iCloud"
        assert folder_path.read_text(encoding="utf-8") == "工作"

        return subprocess.CompletedProcess(args=args, returncode=0, stdout="note-id\n", stderr="")

    monkeypatch.setattr("anote.notes.subprocess.run", fake_run)

    result = create_note(
        title=title,
        html=body,
        account="iCloud",
        folder="工作",
    )

    assert result.stdout == "note-id"
    assert captured_paths
    assert all(not path.exists() for path in captured_paths)


def test_create_note_uses_empty_temp_files_for_default_target(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        html_path, title_path, account_path, folder_path = [Path(value) for value in args[-4:]]
        assert html_path.read_text(encoding="utf-8") == "<p>正文</p>"
        assert title_path.read_text(encoding="utf-8") == "标题"
        assert account_path.read_text(encoding="utf-8") == ""
        assert folder_path.read_text(encoding="utf-8") == ""
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="note-id\n", stderr="")

    monkeypatch.setattr("anote.notes.subprocess.run", fake_run)

    result = create_note(title="标题", html="<p>正文</p>")

    assert result.target_description == "default Notes location"


def test_create_note_formats_osascript_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="execution error: Apple Notes folder not found in default account: 工作",
        )

    monkeypatch.setattr("anote.notes.subprocess.run", fake_run)

    with pytest.raises(NotesError) as exc_info:
        create_note(title="标题", html="<p>正文</p>", folder="工作")

    message = str(exc_info.value)
    assert "Apple Notes write failed." in message
    assert "Apple Notes folder not found" in message
    assert "permission to automate Notes" in message


def test_create_note_formats_osascript_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=args, timeout=60)

    monkeypatch.setattr("anote.notes.subprocess.run", fake_run)

    with pytest.raises(NotesError) as exc_info:
        create_note(title="标题", html="<p>正文</p>")

    message = str(exc_info.value)
    assert "Apple Notes write timed out" in message
    assert "Automation permission" in message
