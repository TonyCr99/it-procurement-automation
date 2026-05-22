# Development Guide

## Running scripts

Always run scripts from the project root folder:
Use the `-m` flag to run any module directly:
python -m src.connectors.jira
python -m src.config_loader

Never run files with their path directly — Python won't resolve
internal imports correctly:
❌ This will fail
python src/connectors/jira.py
✅ This works
python -m src.connectors.jira

## Project structure

Every folder inside `src/` has an `__init__.py` file that tells
Python it's an importable package. If you add a new folder,
remember to add its `__init__.py`.