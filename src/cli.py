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

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

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

    tickets = jira.get_active_tickets()

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
        t = jira.get_ticket(ticket_id)
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
    print(f"  Hardware : {t['hardware_type'].capitalize()} — {t['hardware_tier'].replace('_', ' ').title()}")
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
        quote = quotes.generate_quote(ticket_id)
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

# ------------------------------------------------------------
# Main menu
# ------------------------------------------------------------

def main():
    jira = JiraConnector()
    quotes = QuoteModule()

    while True:
        clear()
        header()
        print("\n  1. View active tickets")
        print("  2. View ticket detail")
        print("  3. Update ticket status")
        print("  4. Add comment to ticket")
        print("  5. New quote")
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
        elif choice == "0":
            clear()
            print("\n  Goodbye. 👋\n")
            break
        else:
            print("\n  ❌ Invalid option. Try again.")
            pause()

if __name__ == "__main__":
    main()