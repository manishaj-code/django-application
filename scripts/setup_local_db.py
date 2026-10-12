"""
Create the local PostgreSQL role and database described in .env.

Usage (from the project root, virtual environment active):

    python scripts/setup_local_db.py

It connects as a PostgreSQL superuser (default ``postgres``; override with
``PG_SUPERUSER``) and asks for that user's password unless ``PGPASSWORD`` is
set or pgpass/trust authentication is configured. It then:

* creates the role ``DB_USER`` (LOGIN, no superuser, password ``DB_PASSWORD``),
  with CREATEDB so the test suite can create its throw-away test database;
* creates the database ``DB_NAME`` owned by that role;
* revokes public CONNECT/CREATE rights so only the app role can use it.

It never drops or alters anything that already exists.
"""

import getpass
import os
import sys
from pathlib import Path

import environ
import psycopg
from psycopg import sql

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    env = environ.Env()
    env_file = BASE_DIR / ".env"
    if not env_file.is_file():
        sys.exit("No .env file found. Copy .env.example to .env and fill in the DB_* values first.")
    env.read_env(env_file)

    db_name, db_user, db_password = env("DB_NAME"), env("DB_USER"), env("DB_PASSWORD")
    host, port = env("DB_HOST", default="localhost"), env("DB_PORT", default="5432")
    superuser = os.environ.get("PG_SUPERUSER", "postgres")

    connect_kwargs = {"host": host, "port": port, "user": superuser, "dbname": "postgres"}
    try:
        conn = psycopg.connect(**connect_kwargs, autocommit=True)
    except psycopg.OperationalError:
        password = getpass.getpass(f"Password for PostgreSQL superuser '{superuser}': ")
        conn = psycopg.connect(**connect_kwargs, password=password, autocommit=True)

    with conn:
        role_exists = conn.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s", [db_user]
        ).fetchone()
        if role_exists:
            print(f"Role '{db_user}' already exists - left unchanged.")
        else:
            conn.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEROLE CREATEDB"
                ).format(sql.Identifier(db_user), sql.Literal(db_password))
            )
            print(f"Created role '{db_user}'.")

        db_exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", [db_name]
        ).fetchone()
        if db_exists:
            print(f"Database '{db_name}' already exists - left unchanged.")
        else:
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER {} ENCODING 'UTF8' TEMPLATE template0").format(
                    sql.Identifier(db_name), sql.Identifier(db_user)
                )
            )
            conn.execute(
                sql.SQL("REVOKE CONNECT, TEMPORARY ON DATABASE {} FROM PUBLIC").format(
                    sql.Identifier(db_name)
                )
            )
            print(f"Created database '{db_name}' owned by '{db_user}'.")

    print("Done. Next: python manage.py migrate && python manage.py createcachetable")


if __name__ == "__main__":
    main()
