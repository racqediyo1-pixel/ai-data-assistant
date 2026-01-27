
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:TECH_B@localhost:5432/ai_data_assistant"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
