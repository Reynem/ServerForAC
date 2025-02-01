import databases
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://kerim:admin1234@localhost:5434/kerim"
database = databases.Database(DATABASE_URL)
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)