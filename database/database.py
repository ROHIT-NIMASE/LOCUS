
"""MySQL connection factory for LOCUS."""

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "library_hotdesking"),
    "charset": "utf8mb4",
    "autocommit": False,
}


def get_connection():
    """Return a new MySQL database connection."""
    if not DB_CONFIG["password"]:
        raise ValueError(
            "DB_PASSWORD is missing. Check your .env file."
        )

    return mysql.connector.connect(**DB_CONFIG)
