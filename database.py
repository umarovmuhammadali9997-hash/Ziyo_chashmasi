import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            grade       TEXT,
            phone       TEXT,
            direction   TEXT,
            balance     INTEGER DEFAULT 0,
            ref_count   INTEGER DEFAULT 0,
            referred_by INTEGER,
            joined_at   TEXT
        )
    """)
    # Kim kimni taklif qilganini saqlash (takror hisoblanmasligi uchun UNIQUE)
    c.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            referred_id INTEGER UNIQUE,
            created_at  TEXT
        )
    """)
    # Eski bazalar uchun migratsiya (ustun bo'lmasa qo'shadi)
    for col, decl in [("balance", "INTEGER DEFAULT 0"),
                      ("ref_count", "INTEGER DEFAULT 0"),
                      ("referred_by", "INTEGER")]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError:
            pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            subject     TEXT,
            score       INTEGER,
            total       INTEGER,
            answers     TEXT,
            created_at  TEXT
        )
    """)
    # Foydalanuvchining hozir yechayotgan testi (savol kalitlari)
    c.execute("""
        CREATE TABLE IF NOT EXISTS active_tests (
            user_id     INTEGER PRIMARY KEY,
            subject     TEXT,
            answer_key  TEXT,
            created_at  TEXT
        )
    """)
    conn.commit()
    conn.close()


def register_user(user_id, username, full_name, grade, phone, direction):
    conn = _conn()
    conn.execute(
        """INSERT OR REPLACE INTO users
           (user_id, username, full_name, grade, phone, direction, joined_at)
           VALUES (?,?,?,?,?,?,?)""",
        (user_id, username, full_name, grade, phone, direction,
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def is_registered(user_id):
    conn = _conn()
    row = conn.execute(
        "SELECT phone FROM users WHERE user_id=? AND phone IS NOT NULL", (user_id,)
    ).fetchone()
    conn.close()
    return row is not None


def get_user(user_id):
    conn = _conn()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# Referal har bir muvaffaqiyatli taklif uchun beriladigan bonus
REFERRAL_BONUS = 1


def add_referral(referrer_id, referred_id):
    """Yangi taklifni qayd qiladi. Bonus berilgan bo'lsa True qaytaradi."""
    if referrer_id == referred_id:
        return False
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (?,?,?)",
            (referrer_id, referred_id, datetime.now().isoformat(timespec="seconds")),
        )
    except sqlite3.IntegrityError:
        conn.close()
        return False  # bu odam allaqachon taklif qilingan
    conn.execute(
        "UPDATE users SET ref_count = ref_count + 1, balance = balance + ? WHERE user_id=?",
        (REFERRAL_BONUS, referrer_id),
    )
    conn.execute("UPDATE users SET referred_by=? WHERE user_id=?", (referrer_id, referred_id))
    conn.commit()
    conn.close()
    return True


def referral_stats(user_id):
    conn = _conn()
    row = conn.execute(
        "SELECT ref_count, balance FROM users WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"ref_count": 0, "balance": 0}
    return {"ref_count": row["ref_count"] or 0, "balance": row["balance"] or 0}


def all_user_ids():
    conn = _conn()
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def user_count():
    conn = _conn()
    n = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    conn.close()
    return n


def set_active_test(user_id, subject, answer_key):
    """answer_key: ['a','c','b',...] tartibida to'g'ri javoblar"""
    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO active_tests (user_id, subject, answer_key, created_at) VALUES (?,?,?,?)",
        (user_id, subject, json.dumps(answer_key), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def get_active_test(user_id):
    conn = _conn()
    row = conn.execute("SELECT * FROM active_tests WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {"subject": row["subject"], "answer_key": json.loads(row["answer_key"])}


def clear_active_test(user_id):
    conn = _conn()
    conn.execute("DELETE FROM active_tests WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def save_result(user_id, subject, score, total, answers):
    conn = _conn()
    conn.execute(
        "INSERT INTO results (user_id, subject, score, total, answers, created_at) VALUES (?,?,?,?,?,?)",
        (user_id, subject, score, total, answers, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def user_results(user_id, limit=10):
    conn = _conn()
    rows = conn.execute(
        "SELECT subject, score, total, created_at FROM results WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
