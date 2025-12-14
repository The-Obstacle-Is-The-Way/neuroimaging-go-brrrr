"""Generic HuggingFace dataset validation framework.

This module provides base classes and utilities for validating HuggingFace datasets.
Dataset-specific validation (ARC, ISLES24) should be in their respective modules.

Architecture follows Single Responsibility Principle:
- hf.py: Generic HF validation classes (this file)
- arc.py: ARC-specific validation (OpenNeuro + HuggingFace)
- isles24.py: ISLES24-specific validation (Zenodo + HuggingFace)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
            lines.append(
                f"❌ {self.failed_count}/{len(self.checks)} checks failed."
            )
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
    actual = len(set(ds[column]))
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
    non_null = sum(1 for val in ds[column] if val is not None)
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
    sessions_with_data = sum(1 for val in ds[column] if val and len(val) > 0)
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
    total = sum(len(val) for val in ds[column] if val)
    return HFValidationCheck(
        name=f"{column}_total",
        expected=str(expected),
        actual=str(total),
        passed=total == expected,
    )


def check_list_alignment(
    ds: Dataset,
    columns: list[str],
    sample_limit: int = 5,
) -> HFValidationCheck:
    """Verify multiple list columns have the same length per row.

    Useful for aligned data like DWI + bvals + bvecs.

    Args:
        ds: HuggingFace Dataset to check.
        columns: List of column names that should be aligned.
        sample_limit: Max number of misaligned rows to report.

    Returns:
        HFValidationCheck with pass/fail status.
    """
    misaligned = []
    for i in range(len(ds)):
        row = ds[i]
        lengths = [len(row[col]) if row[col] else 0 for col in columns]

        if len(set(lengths)) > 1:  # Not all same length
            pairs = zip(columns, lengths, strict=False)
            desc = ", ".join(f"{col}={ln}" for col, ln in pairs)
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
