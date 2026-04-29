from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile


class NotesError(RuntimeError):
    """Raised when Apple Notes cannot create the requested note."""


@dataclass(frozen=True)
class NotesWriteResult:
    stdout: str
    stderr: str
    temp_dir: Path | None
    html_path: Path | None
    title_path: Path | None
    account_path: Path | None
    folder_path: Path | None
    target_description: str


@dataclass(frozen=True)
class _TempFiles:
    html_path: Path
    title_path: Path
    account_path: Path
    folder_path: Path

    @property
    def paths(self) -> tuple[Path, Path, Path, Path]:
        return (self.html_path, self.title_path, self.account_path, self.folder_path)


_APPLESCRIPT = r'''
on readUtf8(posixPath)
    set theFile to POSIX file posixPath
    try
        return read theFile as «class utf8»
    on error errorMessage number errorNumber
        if errorNumber is -39 then
            return ""
        end if

        error errorMessage number errorNumber
    end try
end readUtf8

on run argv
    set htmlPath to item 1 of argv
    set titlePath to item 2 of argv
    set accountPath to item 3 of argv
    set folderPath to item 4 of argv

    set htmlText to my readUtf8(htmlPath)
    set titleText to my readUtf8(titlePath)
    set accountName to my readUtf8(accountPath)
    set folderName to my readUtf8(folderPath)

    tell application "Notes"
        if accountName is not "" then
            if not (exists account accountName) then
                error "Apple Notes account not found: " & accountName
            end if

            set targetAccount to account accountName
            tell targetAccount
                if folderName is "" then
                    set folderName to "Notes"
                end if

                if not (exists folder folderName) then
                    error "Apple Notes folder not found in account \"" & accountName & "\": " & folderName
                end if

                set targetFolder to folder folderName
                make new note at targetFolder with properties {name:titleText, body:htmlText}
            end tell
        else if folderName is not "" then
            set targetAccount to default account
            tell targetAccount
                if not (exists folder folderName) then
                    error "Apple Notes folder not found in default account: " & folderName
                end if

                set targetFolder to folder folderName
                make new note at targetFolder with properties {name:titleText, body:htmlText}
            end tell
        else
            make new note with properties {name:titleText, body:htmlText}
        end if

        return "created"
    end tell
end run
'''


def create_note(
    *,
    title: str,
    html: str,
    account: str | None = None,
    folder: str | None = None,
    debug: bool = False,
) -> NotesWriteResult:
    """Create an Apple Notes note from HTML using temporary UTF-8 files."""
    try:
        temp_files = _create_temp_files(
            html=html,
            title=title,
            account=account or "",
            folder=folder or "",
        )
    except OSError as exc:
        raise NotesError(f"Failed to create UTF-8 temporary files: {exc}") from exc

    try:
        completed = _run_osascript(
            html_path=temp_files.html_path,
            title_path=temp_files.title_path,
            account_path=temp_files.account_path,
            folder_path=temp_files.folder_path,
        )

        if completed.returncode != 0:
            raise NotesError(_format_osascript_error(completed))

        return NotesWriteResult(
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
            temp_dir=temp_files.html_path.parent if debug else None,
            html_path=temp_files.html_path if debug else None,
            title_path=temp_files.title_path if debug else None,
            account_path=temp_files.account_path if debug else None,
            folder_path=temp_files.folder_path if debug else None,
            target_description=_describe_target(account=account, folder=folder),
        )
    except FileNotFoundError as exc:
        raise NotesError(
            "osascript was not found. anote only runs on macOS with AppleScript available."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise NotesError(
            "Apple Notes write timed out while waiting for osascript. "
            "Please check whether Notes.app is responsive and whether macOS is waiting "
            "for Automation permission."
        ) from exc
    except OSError as exc:
        raise NotesError(f"Failed to start osascript: {exc}") from exc
    finally:
        if not debug:
            for path in temp_files.paths:
                path.unlink(missing_ok=True)


def _create_temp_files(*, html: str, title: str, account: str, folder: str) -> _TempFiles:
    created: list[Path] = []

    try:
        html_path = _write_temp_text(prefix="anote-body-", suffix=".html", text=html)
        created.append(html_path)
        title_path = _write_temp_text(prefix="anote-title-", suffix=".txt", text=title)
        created.append(title_path)
        account_path = _write_temp_text(prefix="anote-account-", suffix=".txt", text=account)
        created.append(account_path)
        folder_path = _write_temp_text(prefix="anote-folder-", suffix=".txt", text=folder)
        created.append(folder_path)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise

    return _TempFiles(
        html_path=html_path,
        title_path=title_path,
        account_path=account_path,
        folder_path=folder_path,
    )


def _write_temp_text(*, prefix: str, suffix: str, text: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=prefix,
        suffix=suffix,
        delete=False,
    ) as temp_file:
        temp_file.write(text)
        return Path(temp_file.name)


def _run_osascript(
    *,
    html_path: Path,
    title_path: Path,
    account_path: Path,
    folder_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "osascript",
            "-e",
            _APPLESCRIPT,
            str(html_path),
            str(title_path),
            str(account_path),
            str(folder_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )


def _format_osascript_error(completed: subprocess.CompletedProcess[str]) -> str:
    details = completed.stderr.strip() or completed.stdout.strip()
    if not details:
        details = f"osascript exited with status {completed.returncode}."

    return (
        "Apple Notes write failed.\n"
        f"{details}\n"
        "Please check that Notes.app is available, the account/folder names are correct, "
        "and your terminal has permission to automate Notes."
    )


def _describe_target(*, account: str | None, folder: str | None) -> str:
    if account and folder:
        return f'account "{account}", folder "{folder}"'
    if account:
        return f'account "{account}", folder "Notes"'
    if folder:
        return f'default account, folder "{folder}"'
    return "default Notes location"
