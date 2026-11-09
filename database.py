
import mysql.connector
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote
import os

load_dotenv()

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Hosted EthioDeploy MySQL connection
        parsed = urlparse(database_url)

        return mysql.connector.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=unquote(parsed.username or ""),
            password=unquote(parsed.password or ""),
            database=parsed.path.lstrip("/")
        )

    # Local MySQL connection
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
