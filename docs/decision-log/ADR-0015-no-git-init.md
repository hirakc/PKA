# ADR-0015 — Repository / version-control posture during build

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-06-07

## Context

The workspace is not yet a git repository. During the build, the question arose whether to run
`git init` and commit progress automatically.

## Decision

**Do not initialize git or create commits automatically.** Commits are made only when the user
explicitly asks. A `.gitignore` is provided so that, once the user initializes git, build
artifacts and secrets are excluded: `backend/.venv/`, `backend/data/`, `__pycache__/`,
`frontend/node_modules/`, `frontend/dist/`, `.env`.

## Consequences

**Pros**
- Respects the user's control over their version-control history.
- The `.gitignore` makes a future `git init` clean from the first commit.

**Cons**
- No automatic checkpoint history during the build (acceptable; the user can commit when ready).

## Alternatives considered

- **Auto `git init` + commits per milestone** — rejected: committing without explicit request is
  undesirable and could pollute history.
