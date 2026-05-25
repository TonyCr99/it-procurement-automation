# ============================================================
# IT Procurement Automation — Quotes Module
# ============================================================
# Handles quote generation and approval request comments.
# Connects Jira ticket data with vendor catalog.
#
# Run from project root for testing:
#   python -m src.modules.quotes

from src.connectors.jira import JiraConnector
from src.connectors.vendor import VendorConnector


class QuoteModule:
    """
    Manages the quoting process for a hardware purchase ticket.
    Validates product specs and stock, then generates
    the approval request comment for Jira.
    """

    def __init__(self):
        self.jira = JiraConnector()
        self.vendor = VendorConnector()

    # ----------------------------------------------------------
    # Quote generation
    # ----------------------------------------------------------

    def generate_quote(self, ticket_id: str) -> dict:
        """
        Builds a quote for a given Jira ticket.
        Returns quote details including product, price and validations.
        """
        ticket = self.jira.get_ticket(ticket_id)

        hardware_type = ticket["hardware_type"]
        tier = ticket["hardware_tier"]

        # Validate specs and stock before quoting
        specs_ok = self.vendor.validate_specs(hardware_type, tier)
        stock_ok = self.vendor.validate_stock(hardware_type, tier)

        if not stock_ok:
            raise ValueError(
                f"Insufficient stock for {hardware_type} {tier}. "
                f"Cannot proceed with quote."
            )

        product = self.vendor.get_product(hardware_type, tier)

        return {
            "ticket_id": ticket_id,
            "reporter": ticket["reporter"],
            "approver": ticket["approver"],
            "hardware_type": hardware_type,
            "tier": tier,
            "product_name": product["name"],
            "specs": product["specs"],
            "stock": product["stock"],
            "specs_ok": specs_ok,
            "stock_ok": stock_ok,
            "price_mxn": product["price_mxn"],
        }

    # ----------------------------------------------------------
    # Comment generation
    # ----------------------------------------------------------

    def build_approval_comment(self, quote: dict, total: float) -> str:
        """
        Builds the Jira approval request comment.
        Total is entered manually by the agent after reviewing the PDF.
        """
        return (
            f"Hi @{quote['reporter']}. "
            f"The total for your order is ${total:,.2f} MXN.\n\n"
            f"To proceed with the purchase order, "
            f"we need your manager's approval.\n\n"
            f"Hi @{quote['approver']}, do you approve this request?"
        )

    def submit_quote(self, ticket_id: str, total: float) -> None:
        """
        Full quote flow:
        - Generates quote
        - Builds approval comment
        - Updates ticket status
        - Posts comment to Jira
        """
        quote = self.generate_quote(ticket_id)

        comment = self.build_approval_comment(quote, total)

        self.jira.update_status(
            ticket_id,
            "Waiting for Approval"
        )
        self.jira.add_comment(ticket_id, comment)

        print(f"\n✅ Quote submitted for {ticket_id}.")
        print(f"   Status  : Waiting for Approval")
        print(f"   Total   : ${total:,.2f} MXN")
        print(f"   Approver: {quote['approver']}")


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    quotes = QuoteModule()

    print("\n--- Generate quote for IT-001 ---")
    quote = quotes.generate_quote("IT-001")
    print(f"  Ticket  : {quote['ticket_id']}")
    print(f"  Product : {quote['product_name']}")
    print(f"  Reporter: {quote['reporter']}")
    print(f"  Approver: {quote['approver']}")
    print(f"  Price   : ${quote['price_mxn']:,.2f} MXN")
    print(f"  Stock   : {quote['stock']} units")
    print(f"  Specs OK: {quote['specs_ok']}")

    print("\n--- Build approval comment ---")
    comment = quotes.build_approval_comment(quote, total=54999.00)
    print(f"\n{comment}")

    print("\n--- Submit quote for IT-003 ---")
    quotes.submit_quote("IT-003", total=24999.00)