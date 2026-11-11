import argparse

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings, validate_startup_security
from app.models.base import engine


def migrate_browser_identity(target_engine: Engine) -> None:
    inspector = inspect(target_engine)
    if "detection_logs" not in inspector.get_table_names():
        raise RuntimeError("The detection_logs table does not exist.")

    column_names = {
        column["name"] for column in inspector.get_columns("detection_logs")
    }
    index_names = {
        index["name"] for index in inspector.get_indexes("detection_logs")
    }

    with target_engine.begin() as connection:
        if "visitor_id" not in column_names:
            connection.execute(
                text("ALTER TABLE detection_logs ADD COLUMN visitor_id VARCHAR(32)")
            )
        if "ix_detection_logs_visitor_id" not in index_names:
            connection.execute(
                text(
                    "CREATE INDEX ix_detection_logs_visitor_id "
                    "ON detection_logs (visitor_id)"
                )
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add per-browser ownership to TRASCO detection logs."
    )
    parser.parse_args()
    validate_startup_security(settings)
    migrate_browser_identity(engine)
    print("Browser-identity schema migration completed.")


if __name__ == "__main__":
    main()
