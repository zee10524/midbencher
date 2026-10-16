from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_layout_exists():
    for d in ["pack", "analysis", "notes", "backtest", "deck", "video", "chat-history",
              "app/reader", "app/rules", "app/sap", "app/tracker", "app/ui"]:
        assert (ROOT / d).is_dir(), d
    assert (ROOT / "notes" / "numbers.md").is_file()
