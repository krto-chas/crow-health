# ADR-0009: Runtime identity diagnostics

## Status

Proposed in RC0 Pass 7.

## Context

Editable installations, user-level Python installations and virtual environments can expose different `crow-health` executables on the same workstation. This has already caused the CLI to run older code than the checked-out repository.

Troubleshooting must begin by identifying the code and environment that are actually running rather than assuming that the active Git branch and executable are aligned.

## Decision

Add a `crow-health version` command that reports machine-readable runtime identity:

- installed package version;
- Git commit when the executable is run inside a Git worktree;
- optional commit supplied by `CROW_HEALTH_COMMIT` for packaged deployments;
- Python version;
- operating system;
- Python executable path;
- detected project root;
- available Crow Health capabilities.

Failure to find Git is not an error. Packaged deployments may legitimately have no repository metadata.

## Consequences

Support and deployment procedures can verify the active executable before importing private health data. The command is portable across Windows and Linux and does not read health records.

The reported Git commit describes the current worktree HEAD, not whether the worktree contains uncommitted changes. Build-time provenance and signed releases remain future concerns.
