"""SQLite storage helpers for the nutrition bot."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional

_DB_PATH = Path(__file__).resolve().parent.parent / "nutrition_bot.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                gender TEXT,
                age INTEGER,
                height REAL,
                weight REAL,
                goal TEXT,
                activity TEXT,
                norm_kcal REAL,
                norm_p REAL,
                norm_f REAL,
                norm_c REAL,
                step TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS templates (
                user_id INTEGER,
                name TEXT,
                grams REAL,
                kcal REAL,
                protein REAL,
                fat REAL,
                carb REAL,
                PRIMARY KEY (user_id, name)
            );

            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                grams REAL,
                kcal REAL,
                protein REAL,
                fat REAL,
                carb REAL,
                eaten_at TEXT,
                day TEXT
            );

            CREATE TABLE IF NOT EXISTS day_closures (
                user_id INTEGER,
                day TEXT,
                closed INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, day)
            );
            """
        )
    conn.close()


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def fetch_one(query: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    with session() as conn:
        cur = conn.execute(query, tuple(params))
        return cur.fetchone()


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with session() as conn:
        cur = conn.execute(query, tuple(params))
        return cur.fetchall()


def execute(query: str, params: Iterable[Any] = ()) -> None:
    with session() as conn:
        conn.execute(query, tuple(params))


def executemany(query: str, params: Iterable[Iterable[Any]]) -> None:
    with session() as conn:
        conn.executemany(query, params)


def get_all_users() -> list[int]:
    rows = fetch_all("SELECT user_id FROM users")
    return [int(row["user_id"]) for row in rows]


def upsert_user(user_id: int, data: Dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat()
    columns = [
        "gender",
        "age",
        "height",
        "weight",
        "goal",
        "activity",
        "norm_kcal",
        "norm_p",
        "norm_f",
        "norm_c",
        "step",
    ]
    values = [data.get(col) for col in columns]
    execute(
        """
        INSERT INTO users (user_id, gender, age, height, weight, goal, activity, norm_kcal, norm_p, norm_f, norm_c, step, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            gender=excluded.gender,
            age=excluded.age,
            height=excluded.height,
            weight=excluded.weight,
            goal=excluded.goal,
            activity=excluded.activity,
            norm_kcal=excluded.norm_kcal,
            norm_p=excluded.norm_p,
            norm_f=excluded.norm_f,
            norm_c=excluded.norm_c,
            step=excluded.step,
            updated_at=excluded.updated_at
        """,
        [user_id, *values, now, now],
    )


def update_step(user_id: int, step: str | None) -> None:
    execute("UPDATE users SET step=?, updated_at=? WHERE user_id=?", (step, datetime.utcnow().isoformat(), user_id))


def store_meal(user_id: int, item: Dict[str, Any]) -> None:
    now = datetime.utcnow()
    eaten_day = item.get("date") or now.date().isoformat()
    execute(
        """
        INSERT INTO meals (user_id, name, grams, kcal, protein, fat, carb, eaten_at, day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            item.get("name"),
            item.get("grams"),
            item.get("kcal"),
            item.get("protein"),
            item.get("fat"),
            item.get("carb"),
            now.isoformat(),
            eaten_day,
        ),
    )


def upsert_template(user_id: int, item: Dict[str, Any]) -> None:
    execute(
        """
        INSERT INTO templates (user_id, name, grams, kcal, protein, fat, carb)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, name) DO UPDATE SET
            grams=excluded.grams,
            kcal=excluded.kcal,
            protein=excluded.protein,
            fat=excluded.fat,
            carb=excluded.carb
        """,
        (
            user_id,
            item.get("name"),
            item.get("grams"),
            item.get("kcal"),
            item.get("protein"),
            item.get("fat"),
            item.get("carb"),
        ),
    )


def load_templates(user_id: int) -> Dict[str, Dict[str, Any]]:
    rows = fetch_all("SELECT * FROM templates WHERE user_id=?", (user_id,))
    return {row["name"].lower(): dict(row) for row in rows}


def get_totals(user_id: int, day: date) -> Optional[Dict[str, Any]]:
    row = fetch_one(
        """
        SELECT day, SUM(kcal) as kcal, SUM(protein) as protein, SUM(fat) as fat, SUM(carb) as carb
        FROM meals
        WHERE user_id=? AND day=?
        GROUP BY day
        """,
        (user_id, day.isoformat()),
    )
    return dict(row) if row else None


def list_meals_for_day(user_id: int, day: date) -> list[Dict[str, Any]]:
    rows = fetch_all("SELECT * FROM meals WHERE user_id=? AND day=? ORDER BY eaten_at", (user_id, day.isoformat()))
    return [dict(row) for row in rows]


def mark_day_closed(user_id: int, day: date) -> None:
    execute(
        """
        INSERT INTO day_closures (user_id, day, closed)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, day) DO UPDATE SET closed=1
        """,
        (user_id, day.isoformat()),
    )


def is_day_closed(user_id: int, day: date) -> bool:
    row = fetch_one("SELECT closed FROM day_closures WHERE user_id=? AND day=?", (user_id, day.isoformat()))
    return bool(row and row["closed"])
