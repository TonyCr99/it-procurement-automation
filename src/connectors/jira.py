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
from src.mock.jira_tickets import MOCK_TICKETS


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
        """Connects to real Jira instance using API v3."""
        import requests
        from requests.auth import HTTPBasicAuth

        self.base_url = f"{env('JIRA_URL')}/rest/api/3"
        self.auth = HTTPBasicAuth(env("JIRA_USER"), env("JIRA_API_TOKEN"))
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{self.base_url}/myself",
            headers=self.headers,
            auth=self.auth,
        )
        response.raise_for_status()
        print(f"✅ Connected to Jira as {response.json()['displayName']}")

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

        import requests

        response = requests.get(
            f"{self.base_url}/issue/{ticket_id}",
            headers=self.headers,
            auth=self.auth,
            params={"fields": "summary,status,assignee,reporter,comment,created"},
        )
        response.raise_for_status()
        issue = response.json()
        fields = issue["fields"]

        return {
            "id": issue["key"],
            "summary": fields["summary"],
            "status": fields["status"]["name"],
            "assignee": (
                fields["assignee"]["displayName"] if fields.get("assignee") else None
            ),
            "reporter": fields["reporter"]["displayName"],
            "approver": None,
            "cost_center": None,
            "hardware_type": None,
            "hardware_tier": None,
            "po_reason": None,
            "created": fields["created"],
            "comments": [
                {
                    "author": c["author"]["displayName"],
                    "body": c["body"],
                    "created": c["created"],
                }
                for c in fields["comment"]["comments"]
            ],
        }

    def get_active_tickets(self) -> list:
        """Returns all open tickets in the project."""
        if self.mock:
            return [t for t in MOCK_TICKETS.values() if t["status"] != "Closed"]

        import requests

        project_key = config["ticket"]["project_key"]
        response = requests.get(
            f"{self.base_url}/search/jql",
            headers=self.headers,
            auth=self.auth,
            params={
                "jql": f"project={project_key} AND assignee = currentUser() AND status != Closed ORDER BY created DESC",
                "fields": "summary,status,assignee,reporter,comment,created",
                "maxResults": 50,
        )
        response.raise_for_status()
        issues = response.json()["issues"]
        return [self.get_ticket(i["key"]) for i in issues]

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

        import requests

        transitions = requests.get(
            f"{self.base_url}/issue/{ticket_id}/transitions",
            headers=self.headers,
            auth=self.auth,
        ).json()["transitions"]

        target = next((t for t in transitions if t["name"] == new_status), None)
        if not target:
            raise ValueError(
                f"Transition '{new_status}' not available for {ticket_id}."
            )

        requests.post(
            f"{self.base_url}/issue/{ticket_id}/transitions",
            headers=self.headers,
            auth=self.auth,
            json={"transition": {"id": target["id"]}},
        )
        print(f"✅ [{ticket_id}] Status updated to '{new_status}'")

    def add_comment(self, ticket_id: str, comment: str) -> None:
        """Adds a comment to a ticket."""
        if self.mock:
            if ticket_id not in MOCK_TICKETS:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
            MOCK_TICKETS[ticket_id]["comments"].append(
                {
                    "author": "System",
                    "body": comment,
                    "created": datetime.now().isoformat(),
                }
            )
            print(f"✅ [{ticket_id}] Comment added.")
            return

        import requests

        requests.post(
            f"{self.base_url}/issue/{ticket_id}/comments",
            headers=self.headers,
            auth=self.auth,
            json={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}],
                        }
                    ],
                }
            },
        )
        print(f"✅ [{ticket_id}] Comment added.")


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
    print(f"  Approver: {ticket['approver']}")

    print("\n--- Update status ---")
    jira.update_status("IT-001", "Waiting for Approval")

    print("\n--- Add comment ---")
    jira.add_comment("IT-001", "Quote attached. Total: $25,000 MXN")
