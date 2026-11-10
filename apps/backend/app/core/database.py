"""Database Core and Schema Compatibility Probe (Stage B Phase 6.2)
Provides read-only introspective schema compatibility checks and readiness state management.
Does NOT execute DDL or modify database records.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.models.base import Base
# Ensure all models are registered on Base.metadata
import app.models.user
import app.models.detection


# Module-level per-worker application readiness state
_IS_APPLICATION_READY: bool = False


def is_application_ready() -> bool:
    """Return whether current worker has passed security and schema readiness checks."""
    global _IS_APPLICATION_READY
    return _IS_APPLICATION_READY


def set_application_ready(ready: bool) -> None:
    """Set the application readiness state for the current worker."""
    global _IS_APPLICATION_READY
    _IS_APPLICATION_READY = ready


def reset_application_readiness() -> None:
    """Reset application readiness to False (e.g. during test setup or shutdown)."""
    global _IS_APPLICATION_READY
    _IS_APPLICATION_READY = False


@dataclass
class SchemaProbeResult:
    """Structured diagnostic result returned by probe_schema_compatibility."""
    compatible: bool = True
    missing_tables: List[str] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    primary_key_mismatches: List[str] = field(default_factory=list)
    nullability_mismatches: List[str] = field(default_factory=list)
    missing_unique_constraints: List[str] = field(default_factory=list)
    missing_unique_indexes: List[str] = field(default_factory=list)
    foreign_key_mismatches: List[str] = field(default_factory=list)
    type_mismatches: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def probe_schema_compatibility(engine: Engine) -> SchemaProbeResult:
    """Perform a strictly read-only introspective probe comparing the database schema
    against ORM declarations registered on Base.metadata.

    Verifies:
    1. Table presence for all ORM models.
    2. Column presence and name matching.
    3. Primary key column structure.
    4. Exact nullability matching between ORM declarations and reflected columns.
    5. Unique constraints and unique indexes.
    6. Foreign key declarations.
    """
    result = SchemaProbeResult()

    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
    except Exception as exc:
        result.compatible = False
        result.errors.append(f"Failed to inspect database tables: {exc}")
        return result
    # Source of truth: Base.metadata.tables
    expected_tables = Base.metadata.tables

    for table_name, table_obj in expected_tables.items():
        # Check 1: Table existence
        if table_name not in existing_tables:
            result.compatible = False
            result.missing_tables.append(table_name)
            continue

        try:
            reflected_columns = {col["name"]: col for col in inspector.get_columns(table_name)}
        except Exception as exc:
            result.compatible = False
            result.errors.append(f"Failed to inspect columns for table '{table_name}': {exc}")
            continue

        # Check 2: Column existence & Nullability
        for col_obj in table_obj.columns:
            col_name = col_obj.name
            if col_name not in reflected_columns:
                result.compatible = False
                result.missing_columns.append(f"{table_name}.{col_name}")
                continue

            ref_col = reflected_columns[col_name]
            # Exact nullability check
            orm_nullable = bool(col_obj.nullable)
            db_nullable = bool(ref_col.get("nullable", True))
            if orm_nullable != db_nullable:
                result.compatible = False
                result.nullability_mismatches.append(
                    f"{table_name}.{col_name} (ORM nullable={orm_nullable}, DB nullable={db_nullable})"
                )

            # Check 2b: Type affinity compatibility
            orm_affinity = getattr(col_obj.type, "_type_affinity", None)
            ref_type = ref_col.get("type")
            ref_affinity = getattr(ref_type, "_type_affinity", None) if ref_type is not None else None
            if orm_affinity is not None and ref_affinity is not None:
                if orm_affinity != ref_affinity:
                    result.compatible = False
                    result.type_mismatches.append(
                        f"{table_name}.{col_name} (ORM affinity={orm_affinity.__name__}, DB affinity={ref_affinity.__name__})"
                    )

        # Check 3: Primary key structure
        try:
            pk_constraint = inspector.get_pk_constraint(table_name)
            reflected_pk = pk_constraint.get("constrained_columns") or []
            expected_pk = [c.name for c in table_obj.primary_key.columns]
            if sorted(reflected_pk) != sorted(expected_pk):
                result.compatible = False
                result.primary_key_mismatches.append(
                    f"{table_name} (expected PK {expected_pk}, got {reflected_pk})"
                )
        except Exception as exc:
            result.compatible = False
            result.errors.append(f"Failed to inspect PK for table '{table_name}': {exc}")

        # Check 4: Unique constraints & unique indexes
        try:
            reflected_unique_constrs = inspector.get_unique_constraints(table_name)
            reflected_indexes = inspector.get_indexes(table_name)

            unique_cols_in_constraints = set()
            for uc in reflected_unique_constrs:
                for c in uc.get("column_names", []):
                    unique_cols_in_constraints.add(c)

            unique_cols_in_indexes = set()
            for idx in reflected_indexes:
                if idx.get("unique"):
                    for c in idx.get("column_names", []):
                        unique_cols_in_indexes.add(c)

            # Check each ORM column marked unique
            for col_obj in table_obj.columns:
                if col_obj.unique:
                    is_in_uc = col_obj.name in unique_cols_in_constraints
                    is_in_ui = col_obj.name in unique_cols_in_indexes
                    if not (is_in_uc or is_in_ui):
                        result.compatible = False
                        result.missing_unique_indexes.append(
                            f"{table_name}.{col_obj.name} (declared unique in ORM but missing unique constraint/index)"
                        )
        except Exception as exc:
            result.compatible = False
            result.errors.append(f"Failed to inspect unique constraints for '{table_name}': {exc}")

        # Check 5: Foreign key declarations
        try:
            reflected_fks = inspector.get_foreign_keys(table_name)
            # Map reflected FKs: {(constrained_col, referred_table, referred_col)}
            fk_tuples = set()
            for fk in reflected_fks:
                ref_table = fk.get("referred_table")
                c_cols = fk.get("constrained_columns", [])
                r_cols = fk.get("referred_columns", [])
                for cc, rc in zip(c_cols, r_cols):
                    fk_tuples.add((cc, ref_table, rc))

            for col_obj in table_obj.columns:
                for fk in col_obj.foreign_keys:
                    target_table = fk.column.table.name
                    target_col = fk.column.name
                    if (col_obj.name, target_table, target_col) not in fk_tuples:
                        result.compatible = False
                        result.foreign_key_mismatches.append(
                            f"{table_name}.{col_obj.name} -> {target_table}.{target_col} (missing FK in schema)"
                        )
        except Exception as exc:
            result.compatible = False
            result.errors.append(f"Failed to inspect foreign keys for '{table_name}': {exc}")

    return result
