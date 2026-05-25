# ============================================================
# IT Procurement Automation — Price Validator
# ============================================================
# Validates current vendor price against the approved quote.
# Triggers re-approval flow if price increased beyond tolerance.
#
# Run from project root for testing:
#   python -m src.modules.price_validator

from src.config_loader import config, env
from src.connectors.jira import JiraConnector
from src.connectors.vendor import VendorConnector
from src.modules.notifications import NotificationModule


class PriceValidator:
    """
    Compares current vendor price against approved quote total.
    If price increased beyond tolerance, triggers re-approval flow.
    If price decreased or unchanged, clears for payment.
    """

    def __init__(self):
        self.jira = JiraConnector()
        self.vendor = VendorConnector()
        self.notifications = NotificationModule()
        self.tolerance_pct = config["finance"]["price_change_tolerance_pct"]

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    def validate(
        self,
        ticket_id: str,
        approved_total: float,
        hardware_type: str,
        hardware_tier: str,
    ) -> dict:
        """
        Compares current vendor price against approved total.
        Returns validation result with recommendation.
        """
        product = self.vendor.get_product(hardware_type, hardware_tier)
        current_price = product["price_mxn"]

        difference = current_price - approved_total
        difference_pct = (difference / approved_total) * 100

        # Determine result
        if difference > 0 and difference_pct > self.tolerance_pct:
            result = "reapproval_required"
            recommendation = (
                f"Price increased by ${difference:,.2f} MXN "
                f"({difference_pct:.2f}%). Re-approval required."
            )
        elif difference < 0:
            result = "price_decreased"
            recommendation = (
                f"Price decreased by ${abs(difference):,.2f} MXN "
                f"({abs(difference_pct):.2f}%). Safe to proceed."
            )
        else:
            result = "price_unchanged"
            recommendation = "Price unchanged. Safe to proceed."

        return {
            "ticket_id": ticket_id,
            "approved_total": approved_total,
            "current_price": current_price,
            "difference": difference,
            "difference_pct": difference_pct,
            "tolerance_pct": self.tolerance_pct,
            "result": result,
            "recommendation": recommendation,
            "safe_to_proceed": result != "reapproval_required",
        }

    # ----------------------------------------------------------
    # Re-approval flow
    # ----------------------------------------------------------

    def handle_price_change(
        self,
        validation: dict,
        approver_name: str,
        approver_email: str,
        product_name: str,
    ) -> None:
        """
        Handles a price increase that requires re-approval.
        Updates Jira status and notifies the approver.
        """
        ticket_id = validation["ticket_id"]

        # Update Jira status back to Waiting for Approval
        self.jira.update_status(ticket_id, "Waiting for Approval")

        # Add comment explaining the price change
        comment = (
            f"⚠️ Price change detected before payment.\n\n"
            f"  Approved total : ${validation['approved_total']:,.2f} MXN\n"
            f"  Current price  : ${validation['current_price']:,.2f} MXN\n"
            f"  Difference     : +${validation['difference']:,.2f} MXN "
            f"({validation['difference_pct']:.2f}%)\n\n"
            f"Re-approval required before proceeding with payment.\n"
            f"Hi @{approver_name}, please review the updated price."
        )
        self.jira.add_comment(ticket_id, comment)

        # Notify approver
        self.notifications.notify_approval_request(
            approver_email=approver_email,
            approver_name=approver_name,
            reporter_name="IT Procurement System",
            ticket_id=ticket_id,
            product_name=product_name,
            total=validation["current_price"],
        )

        print(f"\n⚠️  Re-approval triggered for {ticket_id}.")
        print(f"   Approved : ${validation['approved_total']:,.2f} MXN")
        print(f"   Current  : ${validation['current_price']:,.2f} MXN")
        print(f"   Approver notified: {approver_name}")


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    validator = PriceValidator()

    print("\n--- Scenario 1: Price unchanged ---")
    result = validator.validate(
        ticket_id="IT-003",
        approved_total=18999.00,
        hardware_type="windows",
        hardware_tier="standard",
    )
    print(f"  Result      : {result['result']}")
    print(f"  Approved    : ${result['approved_total']:,.2f} MXN")
    print(f"  Current     : ${result['current_price']:,.2f} MXN")
    print(f"  Proceed     : {result['safe_to_proceed']}")
    print(f"  Recommendation: {result['recommendation']}")

    print("\n--- Scenario 2: Price decreased ---")
    result = validator.validate(
        ticket_id="IT-003",
        approved_total=20000.00,
        hardware_type="windows",
        hardware_tier="standard",
    )
    print(f"  Result      : {result['result']}")
    print(f"  Approved    : ${result['approved_total']:,.2f} MXN")
    print(f"  Current     : ${result['current_price']:,.2f} MXN")
    print(f"  Proceed     : {result['safe_to_proceed']}")
    print(f"  Recommendation: {result['recommendation']}")

    print("\n--- Scenario 3: Price increased — re-approval required ---")
    result = validator.validate(
        ticket_id="IT-001",
        approved_total=50000.00,
        hardware_type="macbook",
        hardware_tier="power",
    )
    print(f"  Result      : {result['result']}")
    print(f"  Approved    : ${result['approved_total']:,.2f} MXN")
    print(f"  Current     : ${result['current_price']:,.2f} MXN")
    print(f"  Proceed     : {result['safe_to_proceed']}")
    print(f"  Recommendation: {result['recommendation']}")

    print("\n--- Handle price change ---")
    validator.handle_price_change(
        validation=result,
        approver_name="Carlos Lopez",
        approver_email="carlos.lopez@company.com",
        product_name='MacBook Pro 14"',
    )