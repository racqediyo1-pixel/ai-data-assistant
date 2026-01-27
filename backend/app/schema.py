from app.db import engine
from sqlalchemy import text

def get_db_schema():
    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """

    schema = {}

    with engine.connect() as conn:
        result = conn.execute(text(query))
        for table, column in result:
            if table not in schema:
                schema[table] = []
            schema[table].append(column)

    return schema
def schema_to_text(schema: dict) -> str:
    lines = []
    for table, columns in schema.items():
        cols = ", ".join(columns)
        lines.append(f"Table {table} has columns: {cols}")
    return "\n".join(lines)
