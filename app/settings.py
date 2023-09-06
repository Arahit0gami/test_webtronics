import os
from dotenv import load_dotenv


load_dotenv()

DEBUG = False
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_HOURS = 24*3
CONCURRENT_CONNECTIONS = 0

DB_USER_TEST = os.getenv("DB_USER_TEST")
DB_PASS_TEST = os.getenv("DB_PASS_TEST")
DB_HOST_TEST = os.getenv("DB_HOST_TEST")
DB_PORT_TEST = os.getenv("DB_PORT_TEST")
DB_NAME_TEST = os.getenv("DB_NAME_TEST")

if DEBUG:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DB_USER = DB_USER_TEST
    DB_PASSWORD = DB_PASS_TEST
    DB_HOST = DB_HOST_TEST
    DB_PORT = DB_PORT_TEST
    DB_NAME = DB_NAME_TEST
else:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
