from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateColumn
from sqlalchemy.sql.compiler import IdentifierPreparer
from sqlmodel import SQLModel


@dataclass
class TableReport:
    name: str
    created_table: bool = False
    added_columns: List[str] = field(default_factory=list)
    mismatched_columns: List[Tuple[str, str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        return bool(self.mismatched_columns or self.warnings)


@dataclass
class IntegrityReport:
    tables: List[TableReport]
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors) or any(table.has_issues() for table in self.tables)

    def summary_counts(self) -> Dict[str, int]:
        created = sum(1 for table in self.tables if table.created_table)
        added_columns = sum(len(table.added_columns) for table in self.tables)
        mismatches = sum(len(table.mismatched_columns) for table in self.tables)
        warnings = sum(len(table.warnings) for table in self.tables)
        return {
            "tables_created": created,
            "columns_added": added_columns,
            "mismatches": mismatches,
            "warnings": warnings,
        }


def _expected_type(column, engine: Engine) -> str:
    return column.type.compile(dialect=engine.dialect).lower()


def ensure_schema_integrity(engine: Engine) -> IntegrityReport:
    inspector = inspect(engine)
    metadata_tables = {table.name: table for table in SQLModel.metadata.sorted_tables}
    table_reports: List[TableReport] = []
    errors: List[str] = []

    preparer: IdentifierPreparer = engine.dialect.identifier_preparer

    with engine.begin() as connection:
        existing_tables = set(inspector.get_table_names())

        for table_name, table in metadata_tables.items():
            report = TableReport(name=table_name)

            if table_name not in existing_tables:
                try:
                    table.create(bind=engine, checkfirst=False)
                    report.created_table = True
                    existing_tables.add(table_name)
                    inspector = inspect(engine)
                except SQLAlchemyError as exc:
                    errors.append(f"Failed to create table '{table_name}': {exc}")
                    table_reports.append(report)
                    continue

            # Refresh columns for current table
            actual_columns = {col["name"]: col for col in inspect(engine).get_columns(table_name)}

            for column in table.columns:
                if column.name not in actual_columns:
                    create_sql = CreateColumn(column).compile(dialect=engine.dialect)
                    table_sql = preparer.quote(table_name)
                    try:
                        connection.execute(
                            text(f"ALTER TABLE {table_sql} ADD COLUMN {create_sql}"),
                        )
                        report.added_columns.append(column.name)
                        # Refresh inspector cache for this table
                        actual_columns = {
                            col["name"]: col for col in inspect(engine).get_columns(table_name)
                        }
                    except SQLAlchemyError as exc:
                        warn_msg = (
                            f"Could not add column '{column.name}' to '{table_name}': {exc}"  # noqa: E501
                        )
                        report.warnings.append(warn_msg)
                        continue

                actual = actual_columns.get(column.name)
                if actual is None:
                    # Column creation failed; warning already logged.
                    continue

                expected_type = _expected_type(column, engine)
                actual_type = actual["type"].compile(dialect=engine.dialect).lower()
                if expected_type != actual_type:
                    report.mismatched_columns.append(
                        (column.name, expected_type, actual_type)
                    )

            table_reports.append(report)

    return IntegrityReport(tables=table_reports, errors=errors)
