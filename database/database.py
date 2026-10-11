"""MySQL connection factory for LOCUS."""

import mysql.connector
from mysql.connector import Error


# ── Local development credentials ──────────────────────────────────────────
# Change these to match your MySQL installation.
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",            # your MySQL username
    "password": "Juilakal123",    # your MySQL password
    "database": "library_hotdesking",
    "charset":  "utf8mb4",
    "autocommit": False,      # we manage transactions ourselves
}
# ───────────────────────────────────────────────────────────────────────────


def get_connection():
    """
    Return a new mysql.connector connection.

    Raises:
        mysql.connector.Error – if the connection cannot be established.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as exc:
        raise exc
