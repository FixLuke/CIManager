from sqlalchemy import create_engine  # type: ignore[import]
from sqlalchemy.ext.declarative import declarative_base  # type: ignore[import]
from sqlalchemy.orm import sessionmaker  # type: ignore[import]

#Path to the SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./magazzino.db"

#The Engine manage the connection to the file
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

#Session needed to interact with the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#BaseClass for the models to inherit from
Base = declarative_base()