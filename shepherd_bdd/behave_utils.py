from __future__ import annotations

from pathlib import Path
from typing import Generator, Iterable

BEHAVE_FLAGS_WITH_VALUES: frozenset[str] = frozenset(
    {
        "--tags",
        "-t",
        "--format",
        "-f",
        "--outfile",
        "-o",
        "--junit-directory",
        "--include",
        "-i",
        "--exclude",
        "-e",
        "--stage",
        "--lang",
        "--logging-level",
        "--logging-format",
        "--logging-filter",
        "--logging-filename",
        "--logging-filemode",
        "--logging-datefmt",
        "--runner",
        "-r",
        "--name",
        "-n",
        "-j",
        "--jobs",
        "--parallel",
    }
)


def iterate_tokens(
    parts: Iterable[str],
    flags_with_values: frozenset[str],
) -> Generator[tuple[str, bool], None, None]:
    """Yield (token, is_flag_value) pairs, marking tokens that are flag arguments."""
    skip_next = False
    for token in parts:
        if skip_next:
            skip_next = False
            yield token, True
            continue
        if token in flags_with_values:
            skip_next = True
            yield token, False
            continue
        yield token, False


def is_feature_target(token: str) -> bool:
    """Return True if token refers to a feature file (including file.feature:line notation)."""
    return ".feature" in token


def resolve_path(path: Path, bases: list[Path]) -> Path | None:
    """Resolve path against each base in order; return first existing match or None."""
    if path.is_absolute():
        return path if path.exists() else None
    for base in bases:
        candidate = (base / path).resolve(strict=False)
        if candidate.exists():
            return candidate
    return None
