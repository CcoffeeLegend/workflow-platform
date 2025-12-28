import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://workflow_platform:workflow_platform_pw@localhost:5432/workflow_platform",
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
