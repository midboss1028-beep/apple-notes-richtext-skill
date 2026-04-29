from __future__ import annotations

from pathlib import Path
import sys
from typing import Annotated

import typer

from anote import __version__
from anote.convert import InputFormat, convert_to_html
from anote.notes import NotesError, create_note


app = typer.Typer(
    help="Write UTF-8 Markdown or HTML into Apple Notes.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"anote {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Apple Notes writer for AI agents and terminal workflows."""


@app.command()
def add(
    title: Annotated[str, typer.Option("--title", "-t", help="Apple Notes note title.")],
    from_path: Annotated[
        Path | None,
        typer.Option(
            "--from",
            "-f",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Input file path. Read as UTF-8.",
        ),
    ] = None,
    use_stdin: Annotated[
        bool,
        typer.Option("--stdin", help="Read input from standard input as UTF-8."),
    ] = False,
    input_format: Annotated[
        InputFormat,
        typer.Option("--format", case_sensitive=False, help="Input format."),
    ] = InputFormat.MARKDOWN,
    account: Annotated[
        str | None,
        typer.Option("--account", help="Apple Notes account name, such as iCloud."),
    ] = None,
    folder: Annotated[
        str | None,
        typer.Option("--folder", help="Apple Notes folder name."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print final HTML without writing to Apple Notes."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Print paths and target logic without body content."),
    ] = False,
) -> None:
    """Create a new Apple Notes note from Markdown or HTML."""
    try:
        source = _read_source(from_path=from_path, use_stdin=use_stdin)
        html = convert_to_html(source, input_format)
    except UnicodeDecodeError as exc:
        _fail(f"Input is not valid UTF-8: {exc}")
    except OSError as exc:
        _fail(f"Failed to read input: {exc}")

    if dry_run:
        typer.echo(html)
        return

    try:
        result = create_note(
            title=title,
            html=html,
            account=account,
            folder=folder,
            debug=debug,
        )
    except NotesError as exc:
        _fail(str(exc))

    if debug:
        typer.echo(f"debug: target = {result.target_description}", err=True)
        typer.echo(f"debug: temp_dir = {result.temp_dir}", err=True)
        typer.echo(f"debug: html_path = {result.html_path}", err=True)
        typer.echo(f"debug: title_path = {result.title_path}", err=True)
        typer.echo(f"debug: account_path = {result.account_path}", err=True)
        typer.echo(f"debug: folder_path = {result.folder_path}", err=True)
        typer.echo("debug: AppleScript reads UTF-8 temp files and creates a note.", err=True)

    note_id = result.stdout.strip()
    if note_id:
        typer.echo(f"Created Apple Notes note: {note_id}")
    else:
        typer.echo("Created Apple Notes note.")


def _read_source(*, from_path: Path | None, use_stdin: bool) -> str:
    if from_path and use_stdin:
        _fail("Use either --from or --stdin, not both.")

    if not from_path and not use_stdin:
        _fail("Provide an input file with --from, or pipe content with --stdin.")

    if from_path:
        return from_path.read_text(encoding="utf-8")

    return sys.stdin.buffer.read().decode("utf-8")


def _fail(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)

