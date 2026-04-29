from pathlib import Path

from typer.testing import CliRunner

from anote.cli import app


def test_dry_run_outputs_html_without_writing_notes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "note.md"
    source_path.write_text("# 项目备忘\n\n中文正文", encoding="utf-8")

    def fail_create_note(**kwargs):
        raise AssertionError("dry-run must not write to Apple Notes")

    monkeypatch.setattr("anote.cli.create_note", fail_create_note)

    result = CliRunner().invoke(
        app,
        ["add", "--title", "项目备忘", "--from", str(source_path), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "<h1>项目备忘</h1>" in result.stdout
    assert "<p>中文正文</p>" in result.stdout

