import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).parent.parent / "math_feedback.db"
SEED_DATA_PATH = Path(__file__).parent.parent.parent / "seed_data.json"


def get_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Create topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                grade_level INTEGER
            )
        """)

        # Create problems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                FOREIGN KEY (topic_id) REFERENCES topics (id)
            )
        """)

        # Create submissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL,
                image_data TEXT,
                extracted_text TEXT,
                extracted_latex TEXT,
                is_correct BOOLEAN,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems (id)
            )
        """)

        conn.commit()


def seed_db():
    """Seed database with initial data from seed_data.json."""
    if not SEED_DATA_PATH.exists():
        print(f"Seed data file not found: {SEED_DATA_PATH}")
        return

    with open(SEED_DATA_PATH, "r") as f:
        data = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()

        for topic in data["topics"]:
            # Insert topic
            cursor.execute("""
                INSERT OR REPLACE INTO topics (id, name, description, grade_level)
                VALUES (?, ?, ?, ?)
            """, (topic["id"], topic["name"], topic["description"], topic["grade_level"]))

            # Insert problems
            for problem in topic["problems"]:
                cursor.execute("""
                    INSERT OR REPLACE INTO problems (id, topic_id, question, correct_answer)
                    VALUES (?, ?, ?, ?)
                """, (problem["id"], topic["id"], problem["question"], problem["correct_answer"]))

        conn.commit()

    print("Database seeded successfully!")


def reset_db():
    """Reset database by dropping all tables and reinitializing."""
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    init_db()
    seed_db()
