import sqlparse
import re


def extract_tables_from_sql(sql: str):
    """
    Extract table names from FROM and JOIN clauses using regex.
    """
    sql = sql.lower()

    tables = []
    tables += re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql)
    tables += re.findall(r'join\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql)

    return list(set(tables))  # unique tables


def extract_columns_from_sql(sql: str):
    """
    Extract column names from SELECT clause using sqlparse.
    """
    parsed = sqlparse.parse(sql)[0]
    columns = []

    for token in parsed.tokens:
        # Identifier or IdentifierList are usually inside token groups
        if token.ttype is None and hasattr(token, "tokens"):
            for subtoken in token.tokens:
                if subtoken.ttype is None:
                    value = str(subtoken).strip()
                    if value:
                        columns.append(value)

    return columns


def validate_sql_against_schema(sql: str, schema: dict):
    """
    Validate generated SQL against DB schema.
    """

    # 1️⃣ Allow only SELECT queries
    if not sql.strip().lower().startswith("select"):
        return False, "Only SELECT queries are allowed"

    # 2️⃣ Extract tables
    tables_used = extract_tables_from_sql(sql)

    if not tables_used:
        return False, "No table detected in SQL"

    # 3️⃣ Validate tables exist
    for table in tables_used:
        if table not in schema:
            return False, f"Table '{table}' does not exist in schema"

    # 4️⃣ Extract columns
    columns_used = extract_columns_from_sql(sql)

    # 5️⃣ Validate columns (basic, safe rules)
    for col in columns_used:
        col_lower = col.lower()

        # Allow wildcards and aggregates
        if col == "*" or "count" in col_lower or "sum" in col_lower or "avg" in col_lower:
            continue

        # Column must exist in at least one referenced table
        if not any(col in schema[table] for table in tables_used):
            return False, f"Column '{col}' does not exist in referenced tables"

    # 6️⃣ Success
    return True, {
        "tables": tables_used,
        "columns": columns_used
    }
