# init_db.py
"""
CREATE DATABASE sanatani_db;

CREATE USER sanatani_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE sanatani_db TO sanatani_user;
GRANT CREATE ON SCHEMA public TO sanatani_user;
GRANT USAGE, CREATE ON SCHEMA public TO sanatani_user;
ALTER SCHEMA public OWNER TO sanatani_user;


GRANT USAGE, CREATE ON SCHEMA public TO sanatani_user;
ALTER SCHEMA public OWNER TO sanatani_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sanatani_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sanatani_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO sanatani_user;

psql -d sanatani_db

GRANT USAGE ON SCHEMA public TO sanatani_user;
GRANT CREATE ON SCHEMA public TO sanatani_user;
"""

# to create the database and tables run:  python -m app.init_db
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base
from app.models import user, content, category  # ensure all models are imported

engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database and tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())

