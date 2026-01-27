from sqlalchemy import text
from app.db import engine
from app.schema import get_db_schema, schema_to_text

def detect_table(question: str, schema: dict) -> str | None:
    question = question.lower()
    for table in schema.keys():
        if table in question:
            return table
    return None
def detect_columns(question: str, table: str, schema: dict) -> list[str]:
    question = question.lower()
    valid_columns = schema.get(table, [])
    used_columns = []

    for col in valid_columns:
        if col in question:
            used_columns.append(col)

    return used_columns


def is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper()
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]

    return (
        sql_upper.strip().startswith("SELECT")
        and not any(word in sql_upper for word in forbidden)
    )


def generate_sql_from_nl(user_question: str, schema: dict) -> str:
    print("DB SCHEMA:", schema)


    question = user_question.lower()

    table = detect_table(user_question, schema)
    if not table:
        raise ValueError("No valid table mentioned in query")

    columns = detect_columns(user_question, table, schema)

    # SELECT clause
    if columns:
        sql = f"SELECT {', '.join(columns)} FROM {table}"
    else:
        sql = f"SELECT * FROM {table}"

    # WHERE conditions
    if "bangalore" in question:
        sql += " WHERE city = 'Bangalore'"
    elif "delhi" in question:
        sql += " WHERE city = 'Delhi'"
    elif "chennai" in question:
        sql += " WHERE city = 'Chennai'"

    # ORDER BY
    if "order by name" in question or "sorted by name" in question:
        sql += " ORDER BY name ASC"
    elif "order by city" in question:
        sql += " ORDER BY city ASC"

    # LIMIT
    if "top 5" in question or "first 5" in question:
        sql += " LIMIT 5"

    sql += ";"

    if not is_safe_sql(sql):
        raise ValueError("Unsafe SQL detected")

    return sql

    # Execute query
def execute_sql(sql: str) -> list[dict]:
     with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()

     return [dict(zip(columns, row)) for row in rows]


