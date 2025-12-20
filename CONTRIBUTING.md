# Contributing to Khayal

Thanks for helping improve Khayal! This document summaries the key workflow and rules to make contributions consistent and easy to review.

## Quick checklist
- Fork or branch from `main` using the pattern `feat/<short-desc>` or `chore/<short-desc>`.
- Run tests locally before creating a PR: `pytest`.
- Ensure code style and linting: `ruff check .` (or your preferred linter).
- Keep changes small and focused; prefer multiple small PRs to one large PR.
- Add or update documentation where relevant (docs or README).

## Branch & PR workflow
1. Create a new branch: `git checkout -b feat/your-feature`.
2. Make changes, run tests and lint.
3. Commit with clear, conventional commit messages (e.g., `feat: add X`, `fix: correct Y`).
4. Push and open a Pull Request to `main`, add a short description and link to any related issues.
5. Request a review from a team member; address feedback, then merge when approved.

## Testing and quality
- Add unit tests for new features or bug fixes.
- Rely on `tox`/`pytest` where available; CI runs tests on PRs.
- Update `VERIFICATION_CHECKLIST.md` if you change release or verification steps.

## Documentation
 - Keep `docs/extras/DOCUMENTATION_INDEX.md` up-to-date when adding or removing docs.
- Large changes should include a short doc explaining migration or rationale.

Thanks — your contributions matter. If you have questions, open an issue or ping a maintainer.
