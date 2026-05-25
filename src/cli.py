# ============================================================
# IT Procurement Automation — CLI
# ============================================================
# Main entry point of the system.
# Orchestrates all modules through an interactive text menu.
#
# Run from project root:
#   python -m src.cli

import os
from src.config_loader import config
from src.connectors.jira import JiraConnector
from src.modules.quotes import QuoteModule
from src.connectors.netsuite import NetsuiteConnector
from src.modules.price_validator import PriceValidator
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from src.connectors.azure_ad import AzureADConnector

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

console = Console()


def with_spinner(message: str, func, *args, **kwargs):
    """
    Runs a function while displaying a loading spinner.
    Usage: result = with_spinner("Loading tickets...", jira.get_active_tickets)
    """
    with Live(Spinner("dots", text=message), console=console, transient=True):
        return func(*args, **kwargs)


def clear():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def header():
    """Prints the app header."""
    company = config["company"]["name"]
    print("=" * 52)
    print("  IT Procurement Automation")
    print(f"  {company}")
    print("=" * 52)


def pause():
    """Waits for user input before continuing."""
    input("\n  Press Enter to continue...")


# ------------------------------------------------------------
# Screens
# ------------------------------------------------------------


def screen_tickets(jira: JiraConnector):
    """Shows all active tickets."""
    clear()
    header()
    print("\n  ACTIVE TICKETS\n")

    tickets = with_spinner("Fetching tickets from Jira...", jira.get_active_tickets)

    if not tickets:
        print("  No active tickets found.")
        pause()
        return

    print(f"  {'ID':<10} {'STATUS':<28} {'SUMMARY'}")
    print("  " + "-" * 70)
    for t in tickets:
        print(f"  {t['id']:<10} {t['status']:<28} {t['summary']}")

    pause()


def screen_ticket_detail(jira: JiraConnector):
    """Shows full detail of a single ticket."""
    clear()
    header()
    print("\n  TICKET DETAIL\n")

    ticket_id = input("  Enter ticket ID (e.g. IT-001): ").strip().upper()

    try:
        t = with_spinner(f"Loading {ticket_id}...", jira.get_ticket, ticket_id)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        pause()
        return

    print(f"\n  ID       : {t['id']}")
    print(f"  Summary  : {t['summary']}")
    print(f"  Status   : {t['status']}")
    print(f"  Reporter : {t['reporter']}")
    print(f"  Approver  : {t['approver']}")
    print(f"  Cost Ctr : {t['cost_center']}")
    print(
        f"  Hardware : {t['hardware_type'].capitalize()} — {t['hardware_tier'].replace('_', ' ').title()}"
    )
    print(f"  Created  : {t['created']}")

    if t["comments"]:
        print(f"\n  COMMENTS ({len(t['comments'])})")
        print("  " + "-" * 50)
        for c in t["comments"]:
            print(f"  [{c['created'][:10]}] {c['author']}: {c['body']}")
    else:
        print("\n  No comments yet.")

    pause()


def screen_update_status(jira: JiraConnector):
    """Updates the status of a ticket."""
    clear()
    header()
    print("\n  UPDATE TICKET STATUS\n")

    ticket_id = input("  Enter ticket ID (e.g. IT-001): ").strip().upper()

    try:
        t = jira.get_ticket(ticket_id)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        pause()
        return

    print(f"\n  Current status: {t['status']}")
    print("\n  Available statuses:")

    statuses = list(config["ticket"]["statuses"].values())
    for i, s in enumerate(statuses, 1):
        print(f"    {i}. {s}")

    choice = input("\n  Select new status (number): ").strip()

    try:
        new_status = statuses[int(choice) - 1]
    except (ValueError, IndexError):
        print("\n  ❌ Invalid selection.")
        pause()
        return

    jira.update_status(ticket_id, new_status)
    pause()


def screen_add_comment(jira: JiraConnector):
    """Adds a comment to a ticket."""
    clear()
    header()
    print("\n  ADD COMMENT\n")

    ticket_id = input("  Enter ticket ID (e.g. IT-001): ").strip().upper()

    try:
        jira.get_ticket(ticket_id)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        pause()
        return

    comment = input("  Comment: ").strip()

    if not comment:
        print("\n  ❌ Comment cannot be empty.")
        pause()
        return

    jira.add_comment(ticket_id, comment)
    pause()


def screen_quote(jira: JiraConnector, quotes: QuoteModule):
    """Runs the full quote flow for a ticket."""
    clear()
    header()
    print("\n  NEW QUOTE\n")

    ticket_id = input("  Enter ticket ID (e.g. IT-001): ").strip().upper()

    try:
        quote = with_spinner(f"Generating quote for {ticket_id}...", quotes.generate_quote, ticket_id)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        pause()
        return

    # Show product summary
    print(f"\n  TICKET   : {quote['ticket_id']}")
    print(f"  Reporter : {quote['reporter']}")
    print(f"  Approver : {quote['approver']}")
    print(f"\n  PRODUCT  : {quote['product_name']}")

    # Show specs based on hardware type
    specs = quote["specs"]
    if quote["hardware_type"] == "macbook":
        print(f"  Chip     : {specs['chip']}")
    else:
        print(f"  Processor: {specs['processor']}")
    print(f"  RAM      : {specs['ram']}")
    print(f"  Storage  : {specs['storage']}")
    print(f"  Stock    : {quote['stock']} units")

    # Spec warning
    if not quote["specs_ok"]:
        print(f"\n  ⚠️  Spec warning — product below minimum requirements")
        confirm = input("  Continue anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("\n  Quote cancelled.")
            pause()
            return

    # Warranty is selected automatically by the vendor portal.
    # In live mode, Playwright picks the recommended option.
    # In mock mode, default warranty is applied.
    warranty_key = "none"

    # Total amount
    print("\n  Enter the total from the vendor PDF")
    print("  (product + warranty + taxes as shown in portal)\n")
    try:
        total = float(input("  Total MXN: $").strip().replace(",", ""))
    except ValueError:
        print("\n  ❌ Invalid amount.")
        pause()
        return

    # Preview comment
    print("\n  APPROVAL COMMENT PREVIEW\n")
    print("  " + "-" * 50)
    comment = quotes.build_approval_comment(quote, total)
    for line in comment.split("\n"):
        print(f"  {line}")
    print("  " + "-" * 50)

    confirm = input("\n  Submit quote and update ticket? (y/n): ").strip().lower()
    if confirm != "y":
        print("\n  Quote cancelled.")
        pause()
        return

    quotes.submit_quote(ticket_id, total)
    pause()


def screen_create_po(jira: JiraConnector, netsuite: NetsuiteConnector, azure: AzureADConnector):
    """Creates a purchase order for an approved ticket."""
    clear()
    header()
    print("\n  CREATE PURCHASE ORDER\n")

    ticket_id = input("  Enter ticket ID (e.g. IT-001): ").strip().upper()

    try:
        ticket = with_spinner(f"Loading {ticket_id}...", jira.get_ticket, ticket_id)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        pause()
        return

    # Validate ticket status
    if ticket["status"] != "Waiting for Approval":
        print(f"\n  ❌ Ticket must be in 'Waiting for Approval' status.")
        print(f"     Current status: {ticket['status']}")
        pause()
        return

    print(f"\n  Ticket   : {ticket['id']}")
    print(f"  Reporter : {ticket['reporter']}")
    print(f"  Approver : {ticket['approver']}")
    print(
        f"  Hardware : {ticket['hardware_type'].capitalize()} — "
        f"{ticket['hardware_tier'].replace('_', ' ').title()}"
    )

    # PO reason selection
    print("\n  PURCHASE REASON\n")
    reasons = list(config["hardware"]["po_reasons"].items())
    for i, (key, label) in enumerate(reasons, 1):
        print(f"  {i}. {label}")

    reason_choice = input("\n  Select reason (number): ").strip()
    try:
        po_reason = reasons[int(reason_choice) - 1][0]
    except (ValueError, IndexError):
        print("\n  ❌ Invalid selection.")
        pause()
        return

    # Total amount
    try:
        total = float(
            input("\n  Total MXN (from approved quote): $").strip().replace(",", "")
        )
    except ValueError:
        print("\n  ❌ Invalid amount.")
        pause()
        return

# Cost center — resolved automatically from Azure AD
    try:
        cc_data = with_spinner(
            "Fetching user cost center...",
            azure.get_user_cost_center,
            f"{ticket['reporter'].lower().replace(' ', '.')}@company.com"
        )
        cost_center = cc_data["cc_name"]
        cc_approver = cc_data["cc_approver_lvl1"]
        print(f"\n  Cost center : {cost_center}")
        print(f"  CC Approver : {cc_approver}")
    except ValueError as e:
        print(f"\n  ⚠️  Could not resolve cost center automatically: {e}")
        cost_center = input("  Enter cost center manually: ").strip()
        cc_approver = None
        if not cost_center:
            print("\n  ❌ Cost center is required.")
            pause()
            return

    # Confirm
    product_name = f"{ticket['hardware_type'].capitalize()} {ticket['hardware_tier'].replace('_', ' ').title()}"
    note = f"EQUIPO DE COMPUTO - {product_name} - {config['hardware']['po_reasons'][po_reason]} - {ticket['reporter']} ({ticket_id})"

    print(f"\n  PO PREVIEW\n")
    print(f"  Note     : {note}")
    print(f"  Total    : ${total:,.2f} MXN")
    print(f"  Cost Ctr : {cost_center}")

    confirm = input("\n  Create and submit PO? (y/n): ").strip().lower()
    if confirm != "y":
        print("\n  PO cancelled.")
        pause()
        return

    # Create PO
    po = netsuite.create_order(
        ticket_id=ticket_id,
        product_name=product_name,
        total=total,
        cost_center=cost_center,
        po_reason=po_reason,
        assigned_user=ticket["reporter"],
    )

    # Submit for approval
    netsuite.submit_for_approval(po["po_number"])

     # Validate approver if CC data was resolved automatically
    if cc_approver:
        validation = with_spinner(
            "Validating cost center approver...",
            azure.validate_approver,
            cc_data["cc_number"],
            cc_approver
        )
        if not validation["match"]:
            print(f"\n  ⚠️  {validation['recommendation']}")
        else:
            print(f"\n  ✅ Cost center approver verified.")
            
    # Update Jira ticket
    jira.update_status(ticket_id, "Waiting for Delivery")
    jira.add_comment(
        ticket_id,
        f"Purchase order created: {po['po_number']}\n"
        f"Total: ${total:,.2f} MXN\n"
        f"Status: Sent to Finance Approve",
    )

    print(f"\n✅ PO {po['po_number']} created and submitted.")
    print(f"   Jira status updated to: Waiting for Delivery")
    pause()


def screen_validate_price(jira: JiraConnector, validator: PriceValidator):
    """Validates current vendor price against approved quote."""
    clear()
    header()
    print("\n  PRICE VALIDATION\n")

    ticket_id = input("  Enter ticket ID (e.g. IT-001): ").strip().upper()

    try:
        ticket = jira.get_ticket(ticket_id)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        pause()
        return

    try:
        approved_total = float(
            input("  Approved quote total MXN: $").strip().replace(",", "")
        )
    except ValueError:
        print("\n  ❌ Invalid amount.")
        pause()
        return

    result = validator.validate(
        ticket_id=ticket_id,
        approved_total=approved_total,
        hardware_type=ticket["hardware_type"],
        hardware_tier=ticket["hardware_tier"],
    )

    print(f"\n  Approved : ${result['approved_total']:,.2f} MXN")
    print(f"  Current  : ${result['current_price']:,.2f} MXN")
    print(f"  Result   : {result['recommendation']}")

    if not result["safe_to_proceed"]:
        confirm = input("\n  Trigger re-approval flow? (y/n): ").strip().lower()
        if confirm == "y":
            validator.handle_price_change(
                validation=result,
                approver_name=ticket["approver"],
                approver_email=f"{ticket['approver'].lower().replace(' ', '.')}@company.com",
                product_name=ticket["summary"],
            )
    else:
        print("\n  ✅ Safe to proceed with payment.")

    pause()


# ------------------------------------------------------------
# Main menu
# ------------------------------------------------------------


def main():
    jira = JiraConnector()
    quotes = QuoteModule()
    netsuite = NetsuiteConnector()
    validator = PriceValidator()
    azure = AzureADConnector()

    while True:
        clear()
        header()
        print("\n  1. View active tickets")
        print("  2. View ticket detail")
        print("  3. Update ticket status")
        print("  4. Add comment to ticket")
        print("  5. New quote")
        print("  6. Create purchase order")
        print("  7. Validate price before payment")
        print("\n  0. Exit")
        print("\n" + "=" * 52)

        choice = input("\n  Select an option: ").strip()

        if choice == "1":
            screen_tickets(jira)
        elif choice == "2":
            screen_ticket_detail(jira)
        elif choice == "3":
            screen_update_status(jira)
        elif choice == "4":
            screen_add_comment(jira)
        elif choice == "5":
            screen_quote(jira, quotes)
        elif choice == "6":
            screen_create_po(jira, netsuite, azure)
        elif choice == "7":
            screen_validate_price(jira, validator)
        elif choice == "0":
            clear()
            print("\n  Goodbye. 👋\n")
            break
        else:
            print("\n  ❌ Invalid option. Try again.")
            pause()


if __name__ == "__main__":
    main()
