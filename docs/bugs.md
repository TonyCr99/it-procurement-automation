# Bug Tracker

> Known issues and bugs in IT Procurement Automation.
> For feature requests, see the roadmap in README.md

---

## Open

### BUG-003 — Jira custom fields return None in live mode
**Status:** Open  
**File:** `src/connectors/jira.py`  
**Description:** Fields like `approver`, `hardware_type`, `hardware_tier`,
`cost_center` and `po_reason` return `None` in live mode because they are
custom fields in Jira with company-specific field IDs.  
**Workaround:** Mock mode returns all fields correctly.  
**Next step:** Identify custom field IDs in Jira and map them in the connector.

### BUG-005 — Scripts not on PATH (Windows)
**Status:** Open — low priority  
**Description:** On some Windows environments, pip installs executable
scripts to a folder not on PATH (pygmentize, playwright, markdown-it).  
**Impact:** None — project runs via `python -m src.cli`, not direct scripts.  
**Fix if needed:** Add Python Scripts folder to Windows PATH:
`C:\Users\{user}\AppData\Local\Python\pythoncore-3.14-64\Scripts`

---

## Closed

### BUG-004 — No loading indicator during API calls
**Status:** Fixed  
**Fix:** Added `rich` spinner via `with_spinner()` helper in `src/cli.py`.
Displays animated dots during Jira API calls in live mode.

### BUG-001 — Jira library defaults to API v2
**Status:** Fixed  
**Fix:** Replaced jira library calls with direct requests to REST API v3
in all methods of `src/connectors/jira.py`.

### BUG-002 — pip install not installing all dependencies
**Status:** Fixed  
**Fix:** Created `pyproject.toml` with compatible version ranges.
Updated `requirements.txt` to support Python >= 3.10.

---




---

## Closed

_No closed bugs yet._
