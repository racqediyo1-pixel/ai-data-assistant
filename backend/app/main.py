from fastapi import FastAPI
from pydantic import BaseModel
import logging

from app.db import engine
from app.sql_ai import generate_sql_from_nl, execute_sql
from app.schema import get_db_schema
from app.schema_validator import validate_sql_against_schema
from app.relationships import RELATIONSHIPS


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class NLQuery(BaseModel):
    question: str


def is_aggregate_sql(sql: str) -> bool:
    """Detect COUNT / GROUP BY queries"""
    sql_upper = sql.upper()
    return "COUNT(" in sql_upper or "GROUP BY" in sql_upper


@app.get("/")
def root():
    return {"status": "API is running"}


@app.get("/db-check")
def db_check():
    try:
        with engine.connect():
            return {"db": "connected"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/nl-to-sql")
def nl_to_sql(data: NLQuery):
    logger.info("NL-to-SQL endpoint hit")
    logger.info(f"User question: {data.question}")

    # STEP 1: Load schema
    schema = get_db_schema()
    logger.info(f"Schema loaded: {schema}")

    # STEP 2: Generate SQL
    sql = generate_sql_from_nl(data.question, schema)
    logger.info(f"Generated SQL: {sql}")

    # STEP 3: Validate SQL
    if is_aggregate_sql(sql):
        # Skip strict column validation for COUNT / GROUP BY
        validation_result = {
            "table": list(schema.keys())[0],
            "columns": ["COUNT(*)"]
        }
    else:
        is_valid, validation_result = validate_sql_against_schema(sql, schema)
        if not is_valid:
            return {
                "error": "Invalid SQL generated",
                "reason": validation_result,
                "sql": sql
            }

    # STEP 4: Execute SQL
    rows = execute_sql(sql)
    logger.info(f"Rows returned: {len(rows)}")

    return {
        "sql": sql,
        "table_used": validation_result["table"],
        "columns_used": validation_result["columns"],
        "data": rows
    }


        






