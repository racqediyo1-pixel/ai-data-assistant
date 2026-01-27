from fastapi import FastAPI
from pydantic import BaseModel

import logging

from app.db import engine
from app.sql_ai import generate_sql_from_nl, execute_sql
from app.schema import get_db_schema
from app.schema_validator import validate_sql_against_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class NLQuery(BaseModel):
    question: str


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

    # STEP 2: Generate SQL using schema
    sql = generate_sql_from_nl(data.question, schema)

    # STEP 3: Validate SQL against schema (SAFETY)
    is_valid, validation_result = validate_sql_against_schema(sql, schema)

    if not is_valid:
         return {
               "error": "Invalid SQL generated",
               "reason": validation_result, 
               "sql": sql } 
    # STEP 4: Execute SQL (SELECT-only safe) 
    rows = execute_sql(sql) 
    return { "sql": sql,  
             "table_used": validation_result["table"], 
             "columns_used": validation_result["columns"], 
             "data": rows }

@app.post("/nl-to-sql")
def nl_to_sql(data: NLQuery):
    logger.info("NL-to-SQL endpoint hit")
    logger.info(f"User question: {data.question}")

    # STEP 1: Read schema dynamically
    schema = get_db_schema()
    logger.info(f"Schema loaded: {schema}")

    # STEP 2: Generate SQL using schema
    sql = generate_sql_from_nl(data.question, schema)
    logger.info(f"Generated SQL: {sql}")

    # STEP 3: Validate SQL against schema
    is_valid, validation_result = validate_sql_against_schema(sql, schema)
    logger.info(f"SQL validation: {is_valid}")

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

    

        






