ruff check
ruff format --check
uv run bandit -r . -c pyproject.toml --exclude tests
uv run pip-audit --local --ignore-vuln GHSA-4xh5-x5gv-qwph --skip-editable