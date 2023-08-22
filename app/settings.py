import os
from dotenv import load_dotenv
load_dotenv()

DEBUG = False
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if DEBUG:
    SECRET_KEY = "b086383ed8359789994d15e5d0c4f6ce3e969b8897e43423a1e05bce7ec67cde"
    DB_USER = "test"
    DB_PASSWORD = "test"
    DB_HOST = "test"
    DB_NAME = "test"
else:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
