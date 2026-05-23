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
    print(f"  Manager  : {t['manager']}")
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


# ------------------------------------------------------------
# Main menu
# ------------------------------------------------------------

def main():
    jira = JiraConnector()

    while True:
        clear()
        header()
        print("\n  1. View active tickets")
        print("  2. View ticket detail")
        print("  3. Update ticket status")
        print("  4. Add comment to ticket")
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
        elif choice == "0":
            clear()
            print("\n  Goodbye. 👋\n")
            break
        else:
            print("\n  ❌ Invalid option. Try again.")
            pause()


if __name__ == "__main__":
    main()