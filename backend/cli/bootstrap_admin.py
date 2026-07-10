from __future__ import annotations

import getpass
import os

from backend.database.models import Base
from backend.database.session import engine, ensure_schema_migrations, session_scope
from backend.services.auth import create_user, get_user_by_username


def main() -> int:
    username = (os.getenv("BOOTSTRAP_ADMIN_USERNAME") or input("Admin username: ")).strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or getpass.getpass("Temporary password: ")
    if not username or len(password) < 12:
        raise SystemExit("Username is required and the temporary password must be at least 12 characters.")
    Base.metadata.create_all(engine)
    ensure_schema_migrations(engine)
    with session_scope() as session:
        if get_user_by_username(session, username):
            print("Admin already exists; no account was created.")
            return 0
        create_user(session, username, password, role="admin", must_change_password=True)
    print("Admin created. Remove the one-time credential from the environment and change it at first login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
