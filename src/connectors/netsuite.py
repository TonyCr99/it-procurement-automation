# ============================================================
# IT Procurement Automation — Netsuite Connector
# ============================================================
# Handles all interactions with Netsuite REST API.
# Uses mock mode by default — set NETSUITE_MOCK=false in .env
# to connect to a real Netsuite instance.
#
# Run from project root for testing:
#   python -m src.connectors.netsuite

from src.config_loader import config, env
from src.mock.netsuite_orders import (
    MOCK_ORDERS,
    ITEM_CODES,
    PO_DEFAULTS,
    IVA_RATE,
    calculate_pretax,
    build_po_note
)
from datetime import datetime


class NetsuiteConnector:
    """
    Manages all Netsuite purchase order operations.
    Mock mode simulates PO creation and approval flow.
    Live mode connects to Netsuite REST API.
    """

    def __init__(self):
        self.mock = env("NETSUITE_MOCK", required=False) != "false"
        self.company = config["company"]["name"]
        self.po_reasons = config["hardware"]["po_reasons"]

        if self.mock:
            print("⚙️  Netsuite running in mock mode.")
        else:
            self._connect()

    def _connect(self):
        """Connects to Netsuite via TBA (Token Based Authentication)."""
        # Netsuite uses OAuth 1.0 Token Based Authentication
        # Credentials are configured in .env
        from requests_oauthlib import OAuth1Session
        self.session = OAuth1Session(
            client_key=env("NETSUITE_CONSUMER_KEY"),
            client_secret=env("NETSUITE_CONSUMER_SECRET"),
            resource_owner_key=env("NETSUITE_TOKEN_ID"),
            resource_owner_secret=env("NETSUITE_TOKEN_SECRET"),
        )
        self.base_url = (
            f"https://{env('NETSUITE_ACCOUNT_ID')}"
            f".suitetalk.api.netsuite.com/services/rest/record/v1"
        )
        print("✅ Connected to Netsuite.")

    # ----------------------------------------------------------
    # Read operations
    # ----------------------------------------------------------

    def get_order(self, po_number: str) -> dict:
        """Returns purchase order details by PO number."""
        if self.mock:
            order = MOCK_ORDERS.get(po_number)
            if not order:
                raise ValueError(f"PO '{po_number}' not found.")
            return order

        # TODO: implement live Netsuite PO lookup
        raise NotImplementedError("Live Netsuite lookup not yet implemented.")

    def get_active_orders(self) -> list:
        """Returns all open purchase orders."""
        if self.mock:
            return [
                o for o in MOCK_ORDERS.values()
                if o["status"] != "Closed"
            ]

        # TODO: implement live Netsuite PO list
        raise NotImplementedError("Live Netsuite lookup not yet implemented.")

    # ----------------------------------------------------------
    # PO creation
    # ----------------------------------------------------------

    def create_order(
        self,
        ticket_id: str,
        product_name: str,
        total: float,
        cost_center: str,
        po_reason: str,
        assigned_user: str,
    ) -> dict:
        """
        Creates a new purchase order.
        Calculates pre-tax rate from total automatically.
        Returns the created PO details.
        """
        reason_label = self.po_reasons.get(po_reason, po_reason.upper())
        note = build_po_note(product_name, reason_label, assigned_user, ticket_id)
        rate = calculate_pretax(total)
        tax = round(total - rate, 2)
        po_number = f"PO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        po = {
            "po_number": po_number,
            "ticket_id": ticket_id,
            "status": "Pending Approval",
            "vendor": "Vendor Portal",
            "employee": env("JIRA_USER", required=False) or "IT Agent",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "note": note,
            "classification": {
                "service_nature": PO_DEFAULTS["service_nature"],
                "cost_center": cost_center,
                "location": self.company,
            },
            "items": [
                {
                    "item_code": ITEM_CODES["laptop"],
                    "conta_contabil": PO_DEFAULTS["conta_contabil"],
                    "description": note,
                    "rate": rate,
                    "quantity": PO_DEFAULTS["quantity"],
                    "units": PO_DEFAULTS["units"],
                    "amount": rate,
                    "cost_center": cost_center,
                }
            ],
            "subtotal": rate,
            "tax": tax,
            "total": total,
        }

        if self.mock:
            MOCK_ORDERS[po_number] = po
            print(f"✅ PO created: {po_number}")
            return po

        # TODO: implement live Netsuite PO creation
        raise NotImplementedError("Live Netsuite PO creation not yet implemented.")

    # ----------------------------------------------------------
    # PO approval
    # ----------------------------------------------------------

    def submit_for_approval(self, po_number: str) -> None:
        """Submits PO to finance approval queue."""
        if self.mock:
            if po_number not in MOCK_ORDERS:
                raise ValueError(f"PO '{po_number}' not found.")
            MOCK_ORDERS[po_number]["status"] = "Sent to Finance Approve"
            print(f"✅ [{po_number}] Sent to Finance Approve.")
            return

        # TODO: implement live Netsuite approval submission
        raise NotImplementedError("Live Netsuite approval not yet implemented.")

    def get_order_status(self, po_number: str) -> str:
        """Returns current status of a PO."""
        if self.mock:
            order = MOCK_ORDERS.get(po_number)
            if not order:
                raise ValueError(f"PO '{po_number}' not found.")
            return order["status"]

        # TODO: implement live status check
        raise NotImplementedError("Live status check not yet implemented.")


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    netsuite = NetsuiteConnector()

    print("\n--- Create PO ---")
    po = netsuite.create_order(
        ticket_id="IT-001",
        product_name='MacBook Pro 14" M4 Pro 24GB 512GB SSD',
        total=54999.00,
        cost_center="CC-MKT-001",
        po_reason="replacement",
        assigned_user="Maria Garcia",
    )
    print(f"  PO #     : {po['po_number']}")
    print(f"  Note     : {po['note']}")
    print(f"  Rate     : ${po['items'][0]['rate']:,.2f} MXN")
    print(f"  Tax      : ${po['tax']:,.2f} MXN")
    print(f"  Total    : ${po['total']:,.2f} MXN")
    print(f"  Status   : {po['status']}")

    print("\n--- Submit for approval ---")
    netsuite.submit_for_approval(po["po_number"])

    print("\n--- Check status ---")
    status = netsuite.get_order_status(po["po_number"])
    print(f"  Status   : {status}")

    print("\n--- Active orders ---")
    for order in netsuite.get_active_orders():
        print(f"  {order['po_number']} | {order['status']:<25} | {order['ticket_id']}")