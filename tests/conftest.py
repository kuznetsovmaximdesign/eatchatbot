import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_sessionstart(session):
    from nutrition_bot.storage import db

    db_path = Path(db.__file__).resolve().parent.parent / "nutrition_bot.db"
    if db_path.exists():
        db_path.unlink()
    db.init_db()

    os.environ.setdefault("BOT_TOKEN", "TEST_TOKEN")
    custom_products = Path(__file__).resolve().parents[1] / "src" / "nutrition_bot" / "data" / "products_custom.json"
    if custom_products.exists():
        custom_products.unlink()
