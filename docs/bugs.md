# Bug Tracker

> Known issues and bugs in IT Procurement Automation.
> For feature requests, see the roadmap in README.md

---

## Open

### BUG-001 — Jira library defaults to API v2
**Status:** Fixed in dev, pending retest  
**File:** `src/connectors/jira.py`  
**Description:** The `jira` Python library uses REST API v2 by default,
which Atlassian removed in 2026. All live mode calls now use `requests`
with API v3 directly.  
**Fix:** Replaced `_connect`, `get_ticket`, `get_active_tickets`,
`update_status`, `add_comment` with direct API v3 calls via `requests`.

---

### BUG-002 — `pip install -r requirements.txt` not installing all dependencies
**Status:** Open  
**File:** `requirements.txt`  
**Description:** On some Windows environments, `jira` and `python-dotenv`
are not installed correctly via requirements.txt.  
**Workaround:** Install manually:
execute:    
    pip install jira
    pip install python-dotenv

**Next step:** Investigate Python 3.14 compatibility with current package versions.

---

### BUG-003 — Jira custom fields return None in live mode
**Status:** Open  
**File:** `src/connectors/jira.py`  
**Description:** Fields like `approver`, `hardware_type`, `hardware_tier`,
`cost_center` and `po_reason` return `None` in live mode because they are
custom fields in Jira with company-specific field IDs.  
**Workaround:** Mock mode returns all fields correctly.  
**Next step:** Identify custom field IDs in Jira and map them in the connector.

---

## Closed

### BUG-004 — No loading indicator during API calls
**Status:** Fixed  
**Fix:** Added `rich` spinner via `with_spinner()` helper in `src/cli.py`.
Displays animated dots during Jira API calls in live mode.

### BUG-005 — Scripts not on PATH (Windows)
**Status:** Open — low priority  
**Description:** On some Windows environments, pip installs executable
scripts to a folder not on PATH (pygmentize, playwright, markdown-it).  
**Impact:** None — project runs via `python -m src.cli`, not direct scripts.  
**Fix if needed:** Add Python Scripts folder to Windows PATH:
`C:\Users\{user}\AppData\Local\Python\pythoncore-3.14-64\Scripts`

---

## Closed

_No closed bugs yet._
