# HYDRA Git Changelog Generator

Generate a categorized CHANGELOG.md from Git history since the latest tag. Categories: Added, Fixed, Changed, Removed. Requires Python 3 and Git, no external Python packages.

## Setup (2 steps)

1. Download `changelog.py`.
2. Run `python3 changelog.py --repo /path/to/repo --output CHANGELOG.md`.

Without tags, the script includes all commits. Conventional Commit prefixes are classified first; other subjects use keyword heuristics. Merge commits are skipped. Existing output is overwritten.

## Testing

The original delivery package includes three unittest cases for commit classification, tagged histories, and untagged histories. Download the tested package from the original delivery.

## Example

```markdown
# Changelog

## 2026-10-14 (since v1.0.0)

### Fixed
- resolve regression (\`a1b2c3d\`)
```

The example SHA is illustrative. This is a HYDRA portfolio sample built on the owner's own account, not a paid client project.
