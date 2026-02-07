from sqlalchemy import text
from app.db import engine
import re


# ---------------------------
# Utilities
# ---------------------------

def normalize(text: str) -> str:
    """Lowercase + normalize spaces"""
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_city(question: str, known_cities: list[str]) -> str | None:
    for city in known_cities:
        if city.lower() in question:
            return city
    return None


def is_count_query(question: str) -> bool:
    question = question.lower()

    patterns = [
        "count",
        "how many",
        "how much",
        "number of",
        "total",
        "total number",
        "students count"
    ]

    return any(p in question for p in patterns)


def is_group_by_city(question: str) -> bool:
    return "by city" in question


# ---------------------------
# Schema detection
# ---------------------------

def detect_table(question: str, schema: dict) -> str | None:
    question = question.lower()

    for table in schema.keys():
        if table in question:
            return table

    # fallback: single-table DB
    if len(schema) == 1:
        return list(schema.keys())[0]

    return None


def detect_columns(question: str, table: str, schema: dict) -> list[str]:
    question = question.lower()
    valid_columns = schema.get(table, [])
    return [col for col in valid_columns if col in question]

def extract_order_by(question: str, valid_columns: list[str]) -> str | None:
    for col in valid_columns:
        if f"by {col}" in question or f"order by {col}" in question:
            return col
    return None


# ---------------------------
# SQL safety
# ---------------------------

def is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper()

    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]

    # must be SELECT
    if not sql_upper.strip().startswith("SELECT"):
        return False

    # block dangerous keywords
    if any(word in sql_upper for word in forbidden):
        return False

    return True


# ---------------------------
# NL → SQL
# ---------------------------
def normalize_typos(text: str) -> str:
    fixes = {
        "mny": "many",
        "cnt": "count",
        "stduents": "students",
        "studnts": "students"
    }

    for wrong, right in fixes.items():
        text = text.replace(wrong, right)

    return text

def extract_limit(question: str) -> int | None:
    match = re.search(r"(top|first)\s+(\d+)", question)
    if match:
        return int(match.group(2))
    return None


def generate_sql_from_nl(user_question: str, schema: dict) -> str:
    question = normalize(normalize_typos(user_question))

    table = detect_table(question, schema)
    if not table:
        raise ValueError("No valid table detected")

    count_query = is_count_query(question)
    group_by_city = is_group_by_city(question)

    known_cities = ["Bangalore", "Delhi", "Chennai"]
    city = extract_city(question, known_cities)

    # -------- SELECT clause --------
    if count_query and group_by_city:
        sql = f"SELECT city, COUNT(*) AS count FROM {table}"
    elif count_query:
        sql = f"SELECT COUNT(*) AS count FROM {table}"
    else:
        columns = detect_columns(question, table, schema)
        sql = f"SELECT {', '.join(columns)} FROM {table}" if columns else f"SELECT * FROM {table}"

    # -------- WHERE --------
    if city:
        sql += f" WHERE city = '{city}'"

    # -------- GROUP BY --------
    if count_query and group_by_city:
        sql += " GROUP BY city"

    # ORDER BY (dynamic)
    order_col = extract_order_by(question, schema[table])
    if order_col:
        sql += f" ORDER BY {order_col} ASC"

    # LIMIT (dynamic)
    limit = extract_limit(question)
    if limit:
        sql += f" LIMIT {limit}"

    if not is_safe_sql(sql):
        raise ValueError("Unsafe SQL detected")

    return sql


# ---------------------------
# Execution
# ---------------------------

def execute_sql(sql: str) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]

def detect_required_tables(question: str):
    question = question.lower()

    tables = set()

    if "student" in question:
        tables.add("students")
    if "course" in question:
        tables.add("courses")
    if "enroll" in question or "enrolled" in question:
        tables.add("enrollments")

    return list(tables)

from relationships import RELATIONSHIPS

def build_join_query(tables):
    if len(tables) == 1:
        return f"SELECT * FROM {tables[0]}"

    if set(tables) == {"students", "courses", "enrollments"}:
        return """
        SELECT students.name, courses.course_name
        FROM students
        JOIN enrollments ON students.id = enrollments.student_id
        JOIN courses ON courses.id = enrollments.course_id
        """

    return None


