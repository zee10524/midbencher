from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_layout_exists():
    for d in ["pack", "analysis", "notes", "backtest", "deck", "video", "chat-history",
              "app/reader", "app/rules", "app/sap", "app/tracker", "app/ui"]:
        assert (ROOT / d).is_dir(), d
    assert (ROOT / "notes" / "numbers.md").is_file()


def test_no_tracked_file_contains_an_api_key():
    """A key like Google's (AIza + 35 characters) must never be in a committed file; the key lives only in the git-ignored .env."""
    import re
    import subprocess
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    files = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
    rx = re.compile(r"AIza[0-9A-Za-z_\-]{35}")
    hits = [f for f in files if (root / f).is_file() and f.split(".")[-1].lower() in {"py", "md", "json", "csv", "txt", "js", "html", "css", "toml", "example", "yml", "yaml"} and rx.search((root / f).read_text(encoding="utf-8", errors="ignore"))]
    assert not hits, f"possible API key in: {hits}"
    assert ".env" not in files
