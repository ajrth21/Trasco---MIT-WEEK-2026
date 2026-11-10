"""Database Initializer Module (Stage B Phase 6.1)
Provides an explicit, out-of-process database schema bootstrap mechanism.
Prevents accidental mutation of protected persistent databases.
"""

import os
import sys
import argparse
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings, Settings, validate_startup_security
from app.models.base import Base
# Import all model modules to register them on Base.metadata
import app.models.user
import app.models.detection


_PROTECTED_DB_NAME = "trasco.db"


def _is_protected_target(url_or_path: str) -> bool:
    """Check if the target URL or path resolves to the protected trasco.db."""
    clean_path = url_or_path.replace("sqlite:///", "").replace("sqlite://", "")
    if clean_path == ":memory:":
        return False
    try:
        resolved_target = os.path.realpath(os.path.abspath(clean_path))
        # Find where trasco.db would reside in backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        protected_db_path = os.path.realpath(os.path.abspath(os.path.join(backend_dir, _PROTECTED_DB_NAME)))
        if resolved_target == protected_db_path or os.path.basename(resolved_target) == _PROTECTED_DB_NAME:
            return True
    except Exception:
        # If path resolution fails, fall back to strict name check
        if _PROTECTED_DB_NAME in clean_path:
            return True
    return False


def _is_persistent_sqlite(target_url: str) -> bool:
    """Check if target URL is a persistent (file-based) SQLite database."""
    if not target_url.startswith("sqlite"):
        return True
    clean = target_url.replace("sqlite:///", "").replace("sqlite://", "")
    return clean != ":memory:"


def init_database(
    target_engine: Optional[Engine] = None,
    target_url: Optional[str] = None,
    current_settings: Optional[Settings] = None,
    allow_persistent: bool = False,
) -> bool:
    """Initialize database schema tables strictly on an explicitly specified target.

    Parameters:
    - target_engine: An explicitly instantiated SQLAlchemy Engine (e.g. in-memory test engine).
    - target_url: An explicit database connection string URL.
    - current_settings: Optional custom Settings instance.
    - allow_persistent: Explicit confirmation required if target_url is a persistent file.

    Raises:
    - ValueError: If target is ambiguous, missing, or unauthorized.
    - PermissionError: If target points to protected project database.
    - RuntimeError: If startup security validation fails.
    """
    # Rule 1: Exactly one of target_engine or target_url must be provided
    if target_engine is not None and target_url is not None:
        raise ValueError("Ambiguous target: cannot specify both target_engine and target_url.")
    if target_engine is None and target_url is None:
        raise ValueError("Missing target: an explicit target_engine or target_url must be provided.")

    # Rule 2: Startup security validation executes before opening connection or DDL
    effective_settings = current_settings or settings
    try:
        validate_startup_security(effective_settings)
    except SystemExit as exc:
        raise RuntimeError(f"Startup security validation rejected configuration: {exc}") from exc

    created_own_engine = False
    engine_to_use: Optional[Engine] = None

    try:
        if target_engine is not None:
            engine_to_use = target_engine
        else:
            # Rule 3: Check protected database files
            if _is_protected_target(target_url):
                raise PermissionError(
                    f"Access denied: '{_PROTECTED_DB_NAME}' is a protected persistent database and cannot be modified."
                )

            # Rule 4: Reject persistent database files unless explicitly allowed
            if _is_persistent_sqlite(target_url) and not allow_persistent:
                raise ValueError(
                    f"Target '{target_url}' is a persistent database. "
                    "Persistent database initialization is disabled by default; set allow_persistent=True to confirm."
                )

            connect_args = {"check_same_thread": False} if target_url.startswith("sqlite") else {}
            poolclass = StaticPool if target_url == "sqlite:///:memory:" else None

            if poolclass:
                engine_to_use = create_engine(target_url, connect_args=connect_args, poolclass=poolclass)
            else:
                engine_to_use = create_engine(target_url, connect_args=connect_args)
            created_own_engine = True

        # Rule 5: Run table creation exclusively on validated engine
        Base.metadata.create_all(bind=engine_to_use)
        return True

    finally:
        # Rule 6: Engine disposal ownership
        if created_own_engine and engine_to_use is not None:
            engine_to_use.dispose()


def main():
    """CLI entrypoint for explicit database initialization."""
    parser = argparse.ArgumentParser(
        description="TRASCO Explicit Database Schema Initializer"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Explicit database URL to initialize (e.g. sqlite:///:memory: or sqlite:////tmp/test.db)",
    )
    parser.add_argument(
        "--confirm-persistent",
        action="store_true",
        default=False,
        help="Explicitly confirm persistent database file initialization",
    )

    args = parser.parse_args()

    if not args.url:
        sys.stderr.write(
            "[ERROR] An explicit --url must be specified. "
            "Implicit default to project database is disabled for safety.\n"
        )
        sys.exit(1)

    try:
        init_database(
            target_url=args.url,
            allow_persistent=args.confirm_persistent,
        )
        print(f"[SUCCESS] Database schema initialized successfully on: {args.url}")
        sys.exit(0)
    except Exception as exc:
        sys.stderr.write(f"[ERROR] Database initialization failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
