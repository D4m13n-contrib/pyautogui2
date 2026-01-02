# Contributing Guide

Thank you for your interest in contributing to PyAutoGUI2!
This guide explains how to report bugs, suggest features, and submit code or documentation changes.

---

## 1. How to Report a Bug

Before opening an issue, please:

1. Check the [Troubleshooting Guide](troubleshooting.md) — your issue may already be documented.
2. Search [existing issues](https://github.com/D4m13n-contrib/pyautogui2/issues) to avoid duplicates.

If the issue is new, open a bug report and include:

- **Your environment:** OS, Python version, PyAutoGUI2 version
- **Steps to reproduce:** a minimal script that triggers the bug
- **Expected behavior:** what you expected to happen
- **Actual behavior:** what actually happened, including the full traceback

> The more precise your report, the faster it can be triaged.

---

## 2. How to Suggest a Feature

Open a [feature request](https://github.com/D4m13n-contrib/pyautogui2/issues/new) and describe:

- **The problem you are trying to solve** — not just the solution you have in mind
- **Your proposed solution** — API sketch, expected behavior
- **Alternatives you considered** — and why you ruled them out

Feature requests are not guaranteed to be implemented, but all suggestions are read and considered.

---

## 3. How to Contribute Code

### 3.1 Fork & Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/pyautogui2.git
cd pyautogui2

# Add the upstream remote to stay in sync
git remote add upstream https://github.com/D4m13n-contrib/pyautogui2.git
```

Create a dedicated branch for your change — never work directly on `main`:

```bash
git checkout -b fix/my-bug-fix    # for a bug fix
git checkout -b feat/my-feature   # for a new feature
git checkout -b docs/my-edit      # for documentation
```

---

### 3.2 Set Up the Dev Environment

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Linux / MacOS
.venv\Scripts\activate          # Windows

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

### 3.3 Run the Test Suite

```bash
# Run all tests with coverage
pytest --cov=pyautogui2 --cov-report=term-missing

# Run a specific test file
pytest tests/test_pointer.py

# Run a specific test
pytest tests/test_pointer.py::TestPointerController::test_click
```

The coverage target is **100%**. Any pull request that reduces coverage will not be merged.

> Tests must not perform real mouse, keyboard, or screen operations.
> Use the mocks provided in `tests/mocks/` and fixtures in `tests/fixtures/`.

---

### 3.4 Code Standards

PyAutoGUI2 enforces strict code quality checks. Before submitting, make sure your code passes:

| Tool | Purpose | Config |
|---|---|---|
| **mypy** | Static type checking (strict mode) | `mypy.ini` |
| **ruff** | Linting and formatting | `ruff.toml` |
| **pytest** | Tests + coverage | `pytest.ini` |

```bash
mypy src/
ruff check src/ tests/
ruff format src/ tests/
```

A few non-negotiable rules:

- All code, docstrings, comments, and commit messages must be **in English**
- All public functions and classes must have a **docstring** (PEP 257)
- New code must match the **style and patterns** already established in the codebase — read the relevant files before writing
- **No `Any` types** unless strictly unavoidable and explicitly justified with a comment

---

## 4. How to Contribute Documentation

Documentation lives in the `docs/` folder and is written in Markdown.

Before editing:

- Read the existing files in the same section to match the established tone and structure
- Each code example must be **self-contained** — no shared state across sections
- Inline comments in code snippets should explain non-obvious lines
- For anything OS-specific, mention it briefly and link to [Platform Guides](../platforms/index.md)

To preview documentation locally, any Markdown previewer works (VS Code, Obsidian, etc.).
A proper static site build is planned for a future release.

---

## 5. Pull Request Process

1. **Sync with upstream** before opening your PR:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Verify everything passes** locally:
   ```bash
   mypy src/
   ruff check src/ tests/
   pytest --cov=pyautogui2
   ```

3. **Open the pull request** against the `main` branch with:
   - A clear title summarizing the change
   - A description explaining *what* changed and *why*
   - A reference to the related issue if applicable (`Closes #123`)

4. **Address review comments** by pushing new commits — do not force-push during review.

5. **Squash before merge** — the maintainer may ask you to squash your commits into one clean commit before merging.

> Pull requests that do not pass mypy, ruff, or the test suite will not be reviewed until fixed.

---

## Questions?

If you are unsure about anything before investing time in a contribution, open a
[discussion](https://github.com/D4m13n-contrib/pyautogui2/discussions) first.
It is always better to ask than to submit a large PR that turns out to go in the wrong direction.
