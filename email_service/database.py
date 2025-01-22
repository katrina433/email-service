import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = "localhost"
DB_PORT = 3306
DATABASE = "EmailService"
DB_URL = f"mysql+aiomysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE}"

engine = create_async_engine(DB_URL)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=AsyncSession)
Base = declarative_base()
