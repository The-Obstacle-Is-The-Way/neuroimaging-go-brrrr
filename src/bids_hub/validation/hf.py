"""Generic HuggingFace dataset validation framework.

This module provides base classes and utilities for validating HuggingFace datasets.
Dataset-specific validation (ARC, ISLES24) should be in their respective modules.

Architecture follows Single Responsibility Principle:
- hf.py: Generic HF validation classes (this file)
- arc.py: ARC-specific validation (OpenNeuro + HuggingFace)
- isles24.py: ISLES24-specific validation (Zenodo download)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.compute as pc

if TYPE_CHECKING:
    from datasets import Dataset

logger = logging.getLogger(__name__)


@dataclass
class HFValidationCheck:
    """Result of a single HuggingFace dataset validation check.

    Attributes:
        name: Name of the check (e.g., "schema", "row_count").
        expected: What was expected.
        actual: What was found.
        passed: Whether the check passed.
        details: Additional details about the check result.
    """

    name: str
    expected: str
    actual: str
    passed: bool
    details: str = ""


@dataclass
class HFValidationResult:
    """Complete validation result for a HuggingFace dataset.

    Attributes:
        dataset_name: HuggingFace repository ID (e.g., "hugging-science/arc-aphasia-bids").
        checks: List of validation check results.
    """

    dataset_name: str
    checks: list[HFValidationCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if all checks passed."""
        return all(check.passed for check in self.checks)

    @property
    def failed_count(self) -> int:
        """Number of failed checks."""
        return sum(1 for check in self.checks if not check.passed)

    def add(self, check: HFValidationCheck) -> None:
        """Add a validation check result."""
        self.checks.append(check)

    def summary(self) -> str:
        """Human-readable summary of validation results."""
        lines = [
            f"HuggingFace Validation Results for: {self.dataset_name}",
            "=" * 60,
        ]
        for check in self.checks:
            status = "✅ PASS" if check.passed else "❌ FAIL"
            lines.append(f"{status} {check.name}")
            if not check.passed:
                lines.append(f"       Expected: {check.expected}")
                lines.append(f"       Actual:   {check.actual}")
                if check.details:
                    lines.append(f"       Details:  {check.details}")
        lines.append("=" * 60)
        if self.passed:
            lines.append("✅ All validations passed! HF dataset matches SSOT.")
        else:
            lines.append(f"❌ {self.failed_count}/{len(self.checks)} checks failed.")
        return "\n".join(lines)


# --- Generic validation helper functions ---


def check_schema(
    ds: Dataset,
    expected_columns: list[str],
) -> HFValidationCheck:
    """Verify dataset has expected columns.

    Args:
        ds: HuggingFace Dataset to check.
        expected_columns: List of expected column names.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    actual_cols = list(ds.column_names)

    missing = set(expected_columns) - set(actual_cols)
    extra = set(actual_cols) - set(expected_columns)

    if not missing and not extra:
        return HFValidationCheck(
            name="schema",
            expected=f"{len(expected_columns)} columns",
            actual=f"{len(actual_cols)} columns",
            passed=True,
        )

    details = []
    if missing:
        details.append(f"Missing: {sorted(missing)}")
    if extra:
        details.append(f"Extra: {sorted(extra)}")

    return HFValidationCheck(
        name="schema",
        expected=f"{len(expected_columns)} columns",
        actual=f"{len(actual_cols)} columns",
        passed=False,
        details="; ".join(details),
    )


def check_row_count(ds: Dataset, expected: int) -> HFValidationCheck:
    """Verify dataset has expected number of rows.

    Args:
        ds: HuggingFace Dataset to check.
        expected: Expected row count.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    actual = len(ds)
    return HFValidationCheck(
        name="row_count",
        expected=str(expected),
        actual=str(actual),
        passed=actual == expected,
    )


def check_unique_values(
    ds: Dataset,
    column: str,
    expected: int,
    check_name: str | None = None,
) -> HFValidationCheck:
    """Count unique values in a column.

    Args:
        ds: HuggingFace Dataset to check.
        column: Column name to count unique values.
        expected: Expected count of unique values.
        check_name: Optional custom check name (defaults to "{column}_unique").

    Returns:
        HFValidationCheck with pass/fail status.
    """
    values = ds.data.table.column(column).combine_chunks()
    actual = len(pc.unique(values))
    return HFValidationCheck(
        name=check_name or f"{column}_unique",
        expected=str(expected),
        actual=str(actual),
        passed=actual == expected,
    )


def check_non_null_count(
    ds: Dataset,
    column: str,
    expected: int,
) -> HFValidationCheck:
    """Count non-null values in a column.

    Args:
        ds: HuggingFace Dataset to check.
        column: Column name to count non-null values.
        expected: Expected count of non-null values.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    col = ds.data.table.column(column)
    non_null = len(col) - col.null_count
    return HFValidationCheck(
        name=f"{column}_non_null",
        expected=str(expected),
        actual=str(non_null),
        passed=non_null == expected,
    )


def check_list_sessions(
    ds: Dataset,
    column: str,
    expected: int,
) -> HFValidationCheck:
    """Count rows with at least one item in a list column.

    Args:
        ds: HuggingFace Dataset to check.
        column: Column name containing lists.
        expected: Expected count of rows with non-empty lists.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    col = ds.data.table.column(column)
    lengths = pc.fill_null(pc.list_value_length(col), 0)
    has_data = pc.greater(lengths, 0)
    sessions_with_data = pc.sum(pc.cast(has_data, pa.int64())).as_py() or 0
    return HFValidationCheck(
        name=f"{column}_sessions",
        expected=str(expected),
        actual=str(sessions_with_data),
        passed=sessions_with_data == expected,
    )


def check_total_list_items(
    ds: Dataset,
    column: str,
    expected: int,
) -> HFValidationCheck:
    """Count total items across all lists in a column.

    Args:
        ds: HuggingFace Dataset to check.
        column: Column name containing lists.
        expected: Expected total count of items.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    col = ds.data.table.column(column)
    lengths = pc.fill_null(pc.list_value_length(col), 0)
    total = pc.sum(lengths).as_py() or 0
    return HFValidationCheck(
        name=f"{column}_total",
        expected=str(expected),
        actual=str(total),
        passed=total == expected,
    )


def check_list_alignment(
    ds: Dataset,
    columns: list[str],
    row_id_columns: list[str] | None = None,
    sample_limit: int = 5,
) -> HFValidationCheck:
    """Verify multiple list columns have the same length per row.

    Useful for aligned data like DWI + bvals + bvecs.

    Args:
        ds: HuggingFace Dataset to check.
        columns: List of column names that should be aligned.
        row_id_columns: Optional columns used to identify rows in error output
            (e.g., ["subject_id", "session_id"]).
        sample_limit: Max number of misaligned rows to report.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    table = ds.data.table
    row_count = len(ds)
    length_lists = []
    for col_name in columns:
        col = table.column(col_name)
        lengths = pc.fill_null(pc.list_value_length(col), 0)
        length_lists.append(lengths.to_pylist())

    row_ids: dict[str, list[object]] = {}
    if row_id_columns:
        for col_name in row_id_columns:
            if col_name in table.column_names:
                row_ids[col_name] = table.column(col_name).to_pylist()

    misaligned = []
    for i in range(row_count):
        lengths = [col_lengths[i] for col_lengths in length_lists]
        if len(set(lengths)) > 1:
            pairs = zip(columns, lengths, strict=False)
            desc = ", ".join(f"{col}={ln}" for col, ln in pairs)
            if row_ids:
                ids = ", ".join(f"{k}={row_ids[k][i]}" for k in row_ids)
                misaligned.append(f"Row {i} ({ids}): {desc}")
            else:
                misaligned.append(f"Row {i}: {desc}")
            if len(misaligned) >= sample_limit:
                break

    if not misaligned:
        return HFValidationCheck(
            name=f"alignment_{'+'.join(columns)}",
            expected="All rows aligned",
            actual="All rows aligned",
            passed=True,
        )

    return HFValidationCheck(
        name=f"alignment_{'+'.join(columns)}",
        expected="All rows aligned",
        actual=f"{len(misaligned)}+ misaligned rows",
        passed=False,
        details="; ".join(misaligned[:3]),
    )
