# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python automation project. As the codebase grows, update this file to reflect the actual structure and commands.

## Git Operation Rules

**Every code change must be committed and pushed to GitHub immediately after it is made.**

Workflow for every change:
```bash
git add <changed files>
git commit -m "meaningful commit message"
git push origin main
```

- Commit each logical change separately with a clear message
- Do not batch unrelated changes into a single commit
- Push to remote after every commit — do not let local commits accumulate
- If the repository has not been initialized yet, run `git init` and set the remote before pushing:
  ```bash
  git init
  git remote add origin <GitHub repository URL>
  git push -u origin main
  ```

## Python Environment

Use a virtual environment for dependency management:
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

To add a new dependency:
```bash
pip install <package>
pip freeze > requirements.txt
git add requirements.txt && git commit -m "add <package> dependency" && git push origin main
```

## Running Scripts

```bash
python <script_name>.py
```

## Testing

If tests are added (e.g., with `pytest`):
```bash
pytest                        # run all tests
pytest tests/test_foo.py      # run a single test file
pytest -k "test_function_name"  # run a single test by name
```
