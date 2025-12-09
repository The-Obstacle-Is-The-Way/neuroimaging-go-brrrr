# Integration Specs: bids-hub → neuroimaging-go-brrrr

These specs document the complete integration of `bids-hub` production pipeline into this repository.

## Execution Order

| Phase | Spec | Description | Complexity |
|-------|------|-------------|------------|
| 1 | [01-copy-source.md](./01-copy-source.md) | Copy src/bids_hub + docs | Trivial |
| 2 | [02-update-pyproject.md](./02-update-pyproject.md) | Replace pyproject.toml | Medium |
| 2b | [02b-merge-configs.md](./02b-merge-configs.md) | Merge .gitignore, .pre-commit, Makefile | Medium |
| 3 | [03-copy-tests.md](./03-copy-tests.md) | Replace tests/ | Trivial |
| 4 | [04-cleanup.md](./04-cleanup.md) | Delete obsolete + copy scripts | Trivial |
| 5 | [05-verify.md](./05-verify.md) | Full verification + commit | Verification |

## Overview

See [00-integration-overview.md](./00-integration-overview.md) for:
- What we're integrating (1,976 lines of production code)
- Why we keep `bids_hub` as package name
- Complete file mapping (source → destination)
- Files NOT copied (intentional exclusions)
- Success criteria

## Quick Reference

```bash
# Phase 1: Copy source + docs (NOT CONTRIBUTING.md - keep target's)
cp -r _reference_repos/bids-hub/src/bids_hub src/
cp _reference_repos/bids-hub/CLAUDE.md .
cp _reference_repos/bids-hub/UPSTREAM_BUG.md .
cp _reference_repos/bids-hub/CITATION.cff .
cp _reference_repos/bids-hub/CHANGELOG.md .

# Phase 2: Replace pyproject.toml (see spec for exact content)

# Phase 2b: Merge configs (see spec for details)
# - Append BIDS patterns to .gitignore
# - Replace .pre-commit-config.yaml with merged version
# - Replace Makefile with aligned targets

# Phase 3: Copy tests
rm -rf tests/ && cp -r _reference_repos/bids-hub/tests .

# Phase 4: Delete obsolete + copy scripts
rm -rf src/neuroimaging_go_brrrr/
rm scripts/push_to_hub_ds004884_full.py scripts/download_ds004884.sh
cp _reference_repos/bids-hub/scripts/download_arc.sh scripts/
cp _reference_repos/bids-hub/scripts/download_isles24.sh scripts/
chmod +x scripts/download_*.sh

# Phase 5: Verify
uv sync --all-extras
uv run pytest -v
uv run bids-hub --help
uv run ruff check src/ tests/
uv run mypy src/
```

## Source

All code comes from: `_reference_repos/bids-hub/` (git-delinked copy of https://github.com/The-Obstacle-Is-The-Way/bids-hub)

## Integration Checklist

- [ ] Phase 1: Source + docs copied
- [ ] Phase 2: pyproject.toml replaced
- [ ] Phase 2b: Configs merged (.gitignore, .pre-commit, Makefile)
- [ ] Phase 3: Tests copied
- [ ] Phase 4: Obsolete deleted, scripts copied
- [ ] Phase 5: All verification passes
- [ ] Committed and pushed
