# Project Code Quality and Submission Guidelines

## Enabling Git Hooks

We use the `pre-commit` framework to automatically manage all local checking tools.

### Installation Steps

1.  Ensure your virtual environment is active:

    ```bash
    source .venv/bin/activate
    ```

2.  Install development dependencies (including `pre-commit` and all checking tools):

    These tools are defined in the `[project.optional-dependencies] dev` section of `pyproject.toml`.

    ```bash
    uv sync --extra dev
    ```

3.  Install the Git Hooks launcher: Run the following command to write the checking logic into your local `.git/hooks/` directory:

    ```bash
    pre-commit install --install-hooks
    ```

## Local Automated Checks (Pre-Commit Hooks)

Once the hooks are installed, the following checks will automatically run every time you execute `git commit`:

| Checking Hook | Trigger Time | Description |
| :--- | :--- | :--- |
| **ruff check** | pre-commit | Checks all Python files for code style (Linting), potential errors, and compliance issues. |
| **ruff format** | pre-commit | Automatically formats the code to the standard style. (Please check and accept the changes before committing!) |
| **bandit** | pre-commit | Performs static security analysis on all Python code, checking for common vulnerabilities and insecure code patterns. |
| **pip-audit** | pre-commit | Checks the project's dependencies (`requirements.txt` or environment) for known security vulnerabilities. |

**Note**: Any failed check will prevent the commit. Please fix the issues before attempting to commit again. If you need to temporarily bypass the hooks (not recommended), use `git commit --no-verify`.

# Standardized Commit Messages

We use **Commitizen** (`cz commit`) to ensure all commit messages adhere to the Conventional Commits specification (e.g., `feat: add file categorization functionality` or `fix: correct read permission error`).

### Recommended Commit Method

Please avoid using the traditional `git commit -m "..."`, and instead use the following command:

```bash
cz commit
````

After running this command:

1.  Commitizen will guide you to select the commit type (such as `feat`, `fix`, `docs`, etc.).
2.  It will prompt you to enter the subject and detailed description.
3.  It will generate a compliant commit message.

### Message Validation Hook

Even if you manually use `git commit`, the `commit-msg` hook will automatically run, using `cz check` to validate the message format. If the format is incorrect, the commit will fail.

It is highly recommended that all developers consistently use `cz commit` to ensure a smooth process.
