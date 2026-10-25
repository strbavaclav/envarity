# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-10-25

### Added
- `report` command: an agent that investigates a diff on its own by calling
  `get_diff`, `get_key_history`, and `search_similar` as tools, deciding
  itself which to use and when, then writes up a markdown report
  (Summary, Risk, Flagged keys, Recommendation).

## [0.3.0] - 2026-10-24

### Added
- `history` command: tracks when a placeholder's value actually changed
  (not just when it was mentioned in a commit message), with ticket ID
  extraction and optional `--branches` scoping to cut out unrelated noise.
- `similar` command: semantic search over a file's full change history
  using embeddings, for natural-language queries without knowing the exact
  placeholder name.
- Automatic staleness check before `check`/`explain`/`history`/`similar`/
  `matrix`/`stale-images` run — warns and offers to fetch if the local
  clone hasn't been fetched from the remote in the last 15 minutes.

### Changed
- `explain` now pulls each flagged key's real change history and gives it
  to the LLM as context, instead of judging risk from the diff alone.
- `explain`'s system prompt no longer asserts that a ticketed history makes
  a key lower risk — that claim didn't hold up under scrutiny, so the
  model is now asked to weigh history as context, not as a verdict.

## [0.2.0] - 2026-10-24

### Added
- `explain` command: sends a diff to an LLM via an OpenAI-compatible
  gateway and returns a structured risk assessment (summary, risk level,
  reasoning).
- Few-shot calibration for `explain` using hand-judged ground-truth cases
  from `config/few_shots/` (gitignored; `.example.json` templates ship in
  git), with a `--no-fewshot` flag for comparison.

### Documentation
- Documented `explain` and added a "Why not just ask an agent?" section
  explaining the design rationale.

## [0.1.0] - 2026-10-23

### Added
- Initial project scaffold (`uv init --package`).
- `repos` command: register one or more git repositories and their
  environment branches/tiers via `config/repos.yaml`.
- `check` command: diff placeholder keys between two environments,
  classified against `config/rules.yaml` into expected vs. flagged
  differences.
- `matrix` command: overview of key/flag counts across every app and
  environment in a repo.
- `stale-images` command: how many days behind each environment's base
  images are, relative to the newest version seen anywhere in the repo.

### Changed
- Real `config/repos.yaml` and `config/rules.yaml` are gitignored; only
  `.example.yaml` templates are tracked in git.

### Fixed
- Environment tier order corrected to match the real promotion pipeline
  (test → preprod → staging → production).
- Commands now show a clean one-line error instead of a raw Python
  traceback when config files, branches, or files are missing.

### Documentation
- Added README covering setup, configuration, and usage for all commands.
