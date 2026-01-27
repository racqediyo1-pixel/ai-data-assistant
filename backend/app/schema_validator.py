import re

def extract_table_and_columns(sql: str):
    """
    Very simple SQL parser for SELECT queries.
    """
    table_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
    columns_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE)

    table = table_match.group(1) if table_match else None
    columns_raw = columns_match.group(1) if columns_match else None

    if columns_raw == "*":
        columns = ["*"]
    else:
        columns = [c.strip() for c in columns_raw.split(",")]

    return table, columns


def validate_sql_against_schema(sql: str, schema: dict):
    table, columns = extract_table_and_columns(sql)

    if not table:
        return False, "No table found in SQL."

    if table not in schema:
        return False, f"Table '{table}' does not exist."

    if columns != ["*"]:
        for col in columns:
            if col not in schema[table]:
                return False, f"Column '{col}' does not exist in table '{table}'."

    return True, {
        "table": table,
        "columns": columns
    }
