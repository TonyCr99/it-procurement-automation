# ============================================================
# IT Procurement Automation — Jira Connector
# ============================================================
# Handles all interactions with Jira REST API v3.
# Uses mock mode by default — set JIRA_MOCK=false in .env
# to connect to a real Jira instance.
#
# Usage:
#   from src.connectors.jira import JiraConnector
#   jira = JiraConnector()
#
# Run directly for testing (always from project root):
#   python -m src.connectors.jira

from src.config_loader import config, env
from datetime import datetime
from src.mock.jira_tickets import MOCK_TICKETS # Mock data — simulates real Jira tickets for testing

# ------------------------------------------------------------
# Jira Connector
# ------------------------------------------------------------
class JiraConnector:
    """
    Manages all Jira operations.
    Runs in mock mode unless JIRA_MOCK=false in .env
    """

    def __init__(self):
        self.mock = env("JIRA_MOCK", required=False) != "false"
        self.statuses = config["ticket"]["statuses"]

        if self.mock:
            print("⚙️  Jira running in mock mode.")
        else:
            self._connect()

    def _connect(self):
        """Connects to real Jira instance using credentials from .env"""
        from jira import JIRA
        self.client = JIRA(
            server=env("JIRA_URL"),
            basic_auth=(env("JIRA_USER"), env("JIRA_API_TOKEN"))
        )
        print("✅ Connected to Jira.")

    # ----------------------------------------------------------
    # Read operations
    # ----------------------------------------------------------

    def get_ticket(self, ticket_id: str) -> dict:
        """Returns ticket details by ID."""
        if self.mock:
            ticket = MOCK_TICKETS.get(ticket_id)
            if not ticket:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
            return ticket

        issue = self.client.issue(ticket_id)
        return {
            "id": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
            "reporter": issue.fields.reporter.displayName,
            "created": issue.fields.created,
            "approver": issue.fields.customfield_approver if hasattr(issue.fields, 'customfield_approver') else None,
            "comments": [
                {
                    "author": c.author.displayName,
                    "body": c.body,
                    "created": c.created
                }
                for c in issue.fields.comment.comments
            ]
        }

    def get_active_tickets(self) -> list:
        """Returns all open tickets in the project."""
        if self.mock:
            return [t for t in MOCK_TICKETS.values() if t["status"] != "Closed"]

        project_key = config["ticket"]["project_key"]
        issues = self.client.search_issues(
            f'project={project_key} AND status != Closed ORDER BY created DESC'
        )
        return [self.get_ticket(i.key) for i in issues]

    # ----------------------------------------------------------
    # Write operations
    # ----------------------------------------------------------

    def update_status(self, ticket_id: str, new_status: str) -> None:
        """Updates the status of a ticket."""
        if self.mock:
            if ticket_id not in MOCK_TICKETS:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
            old_status = MOCK_TICKETS[ticket_id]["status"]
            MOCK_TICKETS[ticket_id]["status"] = new_status
            print(f"✅ [{ticket_id}] Status: '{old_status}' → '{new_status}'")
            return

        transitions = self.client.transitions(ticket_id)
        target = next(
            (t for t in transitions if t["name"] == new_status), None
        )
        if not target:
            raise ValueError(f"Transition '{new_status}' not available for {ticket_id}.")
        self.client.transition_issue(ticket_id, target["id"])

    def add_comment(self, ticket_id: str, comment: str) -> None:
        """Adds a comment to a ticket."""
        if self.mock:
            if ticket_id not in MOCK_TICKETS:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
            MOCK_TICKETS[ticket_id]["comments"].append({
                "author": "System",
                "body": comment,
                "created": datetime.now().isoformat()
            })
            print(f"✅ [{ticket_id}] Comment added.")
            return

        self.client.add_comment(ticket_id, comment)


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    jira = JiraConnector()

    print("\n--- Active Tickets ---")
    for ticket in jira.get_active_tickets():
        print(f"  {ticket['id']} | {ticket['status']:<25} | {ticket['summary']}")

    print("\n--- Get single ticket ---")
    ticket = jira.get_ticket("IT-001")
    print(f"  ID      : {ticket['id']}")
    print(f"  Summary : {ticket['summary']}")
    print(f"  Status  : {ticket['status']}")
    print(f"  Manager : {ticket['manager']}")

    print("\n--- Update status ---")
    jira.update_status("IT-001", "Waiting for Approval")

    print("\n--- Add comment ---")
    jira.add_comment("IT-001", "Quote attached. Total: $25,000 MXN")