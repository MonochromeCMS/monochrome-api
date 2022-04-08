import asyncio
from os import getenv
from uuid import uuid4

import asyncpg
from deta import Deta
from passlib.hash import bcrypt

ADMIN_ROLE = "admin"


async def pg_main():
    """
    Creates an admin user in the `DB_URL` database.
    """
    HOST = getenv("PG_HOST")
    USER = getenv("PG_USER")
    PASS = getenv("PG_PASS")
    DB = getenv("PG_DB")

    PG_URL = f"postgresql://{USER}:{PASS}@{HOST}/{DB}"

    if getenv("MONOCHROME_TEST"):
        # Default user is generated for testing purposes.
        USERNAME = "admin"
        PASSWORD = "pass"
        uuid = "c603ef4f-08f9-4130-a770-3a34defa44b3"
    else:
        USERNAME = input("Username: ")
        PASSWORD = input("Password: ")
        uuid = uuid4()

    hashed_password = bcrypt.hash(PASSWORD)

    conn = await asyncpg.connect(PG_URL)

    query = """INSERT INTO "user" (version, id, username, hashed_password, role) VALUES(1, $1, $2, $3, $4);"""

    await conn.execute(query, uuid, USERNAME, hashed_password, ADMIN_ROLE)

    await conn.close()


def deta_main():
    PROJECT_KEY = getenv("DETA_PROJECT_KEY")

    if not PROJECT_KEY:
        raise OSError("DETA_PROJECT_KEY is required to add an admin user")

    if getenv("MONOCHROME_TEST"):
        USERNAME = "admin"
        PASSWORD = "pass"
        uuid = "c603ef4f-08f9-4130-a770-3a34defa44b3"
    else:
        USERNAME = input("Username: ")
        PASSWORD = input("Password: ")
        uuid = uuid4()

    hashed_password = bcrypt.hash(PASSWORD)

    deta = Deta(PROJECT_KEY)
    db = deta.Base("users")

    user = {
        "username": USERNAME,
        "email": None,
        "hashed_password": hashed_password,
        "version": 1,
        "id": str(uuid),
        "key": str(uuid),
        "role": "admin",
    }

    db.put(user)
    db.close()


if __name__ == "__main__":
    DB_BACKEND = getenv("DB_BACKEND")

    if DB_BACKEND == "POSTGRES":
        asyncio.run(pg_main())
    elif DB_BACKEND == "DETA":
        deta_main()
