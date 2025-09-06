# Development Guide

Welcome to our repository! This document explains the **development workflow**, **commit message format**, and recommended tools for Python developers.

---

## 1️⃣ Development Workflow

We use a **Kanban-style board** for task management:
```
Backlog → Ready → In Progress → In Review → Testing → Done
```

- **Backlog**: Ideas and tasks not yet prioritized.
- **Ready**: Tasks ready to be developed, with clear description and acceptance criteria.
- **In Progress**: Tasks currently being worked on. Limit to 2 per developer.
- **In Review**: Pull Requests awaiting code review.
- **Testing**: Tasks merged into staging for QA / automated testing.
- **Done**: Completed tasks merged into main branch.

---

## 2️⃣ Commit Message Guidelines

We follow **Conventional Commits**:
```
<type>(<scope>): <subject>
### Commit Types:
- `feat` → New feature
- `fix` → Bug fix
- `docs` → Documentation updates
- `refactor` → Code refactoring
- `test` → Add / update tests
- `chore` → Other maintenance tasks

### Examples:
- feat(auth): add login endpoint
- fix(ui): correct button alignment
- docs: update README
```

> All commits **must follow this format**. Commits that do not follow the format will be rejected by our pre-commit hooks or CI checks.

---

## 3️⃣ Recommended Tools for Python Developers

We recommend using **Python Commitizen (`cz-cli`)** to standardize commit messages:

### Install Commitizen (Python version)
```bash
pip install commitizen
```
