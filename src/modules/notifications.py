# ============================================================
# IT Procurement Automation — Notifications Module
# ============================================================
# Handles all outbound notifications to approvers and teams.
# Supports email (required), Slack and Teams (optional).
#
# Channels are configured in .env:
#   NOTIFY_EMAIL=true
#   NOTIFY_SLACK=false
#   NOTIFY_TEAMS=false
#
# Run from project root for testing:
#   python -m src.modules.notifications

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config_loader import config, env


class NotificationModule:
    """
    Sends notifications through configured channels.
    Email is the primary channel — Slack and Teams are optional.
    """

    def __init__(self):
        self.mock = env("NOTIFY_MOCK", required=False) != "false"
        self.email_enabled = env("NOTIFY_EMAIL", required=False) == "true"
        self.slack_enabled = env("NOTIFY_SLACK", required=False) == "true"
        self.teams_enabled = env("NOTIFY_TEAMS", required=False) == "true"

        if self.mock:
            print("⚙️  Notifications running in mock mode.")

    # ----------------------------------------------------------
    # Core send method
    # ----------------------------------------------------------

    def send(self, recipient: str, subject: str, body: str) -> None:
        """
        Sends a notification through all enabled channels.
        In mock mode, prints to console instead of sending.
        """
        if self.mock:
            self._mock_send(recipient, subject, body)
            return

        if self.email_enabled:
            self._send_email(recipient, subject, body)

        if self.slack_enabled:
            self._send_slack(body)

        if self.teams_enabled:
            self._send_teams(body)

    def _mock_send(self, recipient: str, subject: str, body: str) -> None:
        """Simulates sending a notification — prints to console."""
        print(f"\n📧 MOCK NOTIFICATION")
        print(f"   To      : {recipient}")
        print(f"   Subject : {subject}")
        print(f"   Body    :")
        for line in body.split("\n"):
            print(f"             {line}")

    # ----------------------------------------------------------
    # Email
    # ----------------------------------------------------------

    def _send_email(self, recipient: str, subject: str, body: str) -> None:
        """Sends an email via SMTP."""
        sender = env("NOTIFY_EMAIL_SENDER")
        password = env("NOTIFY_EMAIL_PASSWORD")
        smtp_host = env("NOTIFY_SMTP_HOST", required=False) or "smtp.gmail.com"
        smtp_port = int(env("NOTIFY_SMTP_PORT", required=False) or 587)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        print(f"✅ Email sent to {recipient}")

    # ----------------------------------------------------------
    # Slack
    # ----------------------------------------------------------

    def _send_slack(self, body: str) -> None:
        """Sends a message to Slack via webhook."""
        import requests
        webhook_url = env("SLACK_WEBHOOK_URL")
        requests.post(webhook_url, json={"text": body})
        print(f"✅ Slack notification sent.")

    # ----------------------------------------------------------
    # Teams
    # ----------------------------------------------------------

    def _send_teams(self, body: str) -> None:
        """Sends a message to Teams via webhook."""
        import requests
        webhook_url = env("TEAMS_WEBHOOK_URL")
        requests.post(webhook_url, json={"text": body})
        print(f"✅ Teams notification sent.")

    # ----------------------------------------------------------
    # Notification templates
    # ----------------------------------------------------------

    def notify_approval_request(
        self,
        approver_email: str,
        approver_name: str,
        reporter_name: str,
        ticket_id: str,
        product_name: str,
        total: float
    ) -> None:
        """
        Sends approval request notification to the approver.
        Triggered after a quote is submitted.
        """
        subject = f"[IT Procurement] Approval Required — {ticket_id}"
        body = (
            f"Hi {approver_name},\n\n"
            f"{reporter_name} has requested a hardware purchase "
            f"that requires your approval.\n\n"
            f"  Ticket  : {ticket_id}\n"
            f"  Product : {product_name}\n"
            f"  Total   : ${total:,.2f} MXN\n\n"
            f"Please review and approve or reject the request "
            f"in Jira at your earliest convenience.\n\n"
            f"SLA: Response required within "
            f"{config['ticket']['approval']['sla_hours']} hours.\n\n"
            f"This is an automated message from IT Procurement Automation."
        )
        self.send(approver_email, subject, body)

    def notify_approval_reminder(
        self,
        approver_email: str,
        approver_name: str,
        ticket_id: str,
        total: float
    ) -> None:
        """
        Sends a reminder if approver hasn't responded within SLA.
        """
        reminder_hours = config["ticket"]["approval"]["reminder_after_hours"]
        subject = f"[IT Procurement] Reminder — Approval Pending {ticket_id}"
        body = (
            f"Hi {approver_name},\n\n"
            f"This is a reminder that ticket {ticket_id} is still "
            f"pending your approval.\n\n"
            f"  Total   : ${total:,.2f} MXN\n\n"
            f"This request has been waiting {reminder_hours} hours "
            f"for your response.\n\n"
            f"This is an automated message from IT Procurement Automation."
        )
        self.send(approver_email, subject, body)

    def notify_finance_payment(
        self,
        finance_email: str,
        ticket_id: str,
        product_name: str,
        total: float,
        po_number: str
    ) -> None:
        """
        Sends payment request to finance team.
        Triggered after PO is approved in Netsuite.
        """
        subject = f"[IT Procurement] Payment Request — {ticket_id}"
        body = (
            f"Hi Finance Team,\n\n"
            f"Please process the payment for the following "
            f"approved purchase order.\n\n"
            f"  Ticket  : {ticket_id}\n"
            f"  Product : {product_name}\n"
            f"  PO #    : {po_number}\n"
            f"  Total   : ${total:,.2f} MXN\n\n"
            f"The approved Jira ticket and purchase order "
            f"are attached for reference.\n\n"
            f"This is an automated message from IT Procurement Automation."
        )
        self.send(finance_email, subject, body)


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    notify = NotificationModule()

    print("\n--- Approval request ---")
    notify.notify_approval_request(
        approver_email="carlos.lopez@company.com",
        approver_name="Carlos Lopez",
        reporter_name="Maria Garcia",
        ticket_id="IT-001",
        product_name="MacBook Pro 14\"",
        total=54999.00
    )

    print("\n--- Approval reminder ---")
    notify.notify_approval_reminder(
        approver_email="carlos.lopez@company.com",
        approver_name="Carlos Lopez",
        ticket_id="IT-001",
        total=54999.00
    )

    print("\n--- Finance payment request ---")
    notify.notify_finance_payment(
        finance_email="finanzas@company.com",
        ticket_id="IT-001",
        product_name="MacBook Pro 14\"",
        total=54999.00,
        po_number="PO-2024-001"
    )