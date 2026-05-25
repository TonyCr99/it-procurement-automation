# ============================================================
# IT Procurement Automation — Jira Mock Data
# ============================================================
# Simulates real Jira tickets for testing and development.
# Replace with real Jira credentials in .env to use live data.

MOCK_TICKETS = {
    "IT-001": {
        "id": "IT-001",
        "summary": "MacBook Pro Power - Maria Garcia",
        "status": "New",
        "po_reason": "replacement",
        "assignee": "Tony",
        "reporter": "Maria Garcia",
        "approver": "Carlos Lopez",
        "cost_center": "CC-MKT-001",
        "hardware_type": "macbook",
        "hardware_tier": "power",
        "created": "2024-01-15T09:00:00",
        "comments": []
    },
    "IT-002": {
        "id": "IT-002",
        "summary": "Windows Standard - Juan Perez",
        "status": "Waiting for Approval",
        "po_reason": "new_joiner",
        "assignee": "Tony",
        "reporter": "Juan Perez",
        "approver": "Ana Martinez",
        "cost_center": "CC-ENG-002",
        "hardware_type": "windows",
        "hardware_tier": "standard",
        "created": "2024-01-14T10:30:00",
        "comments": [
            {
                "author": "Tony",
                "body": "Quote attached. Awaiting manager approval.",
                "created": "2024-01-14T11:00:00"
            }
        ]
    },
    "IT-003": {
        "id": "IT-003",
        "summary": "Windows Standard Plus - Sofia Ramos",
        "status": "Waiting for Delivery",
        "po_reason": "equipment_change",
        "po_reason": "new_joiner",
        "assignee": "Tony",
        "reporter": "Sofia Ramos",
        "approver": "Carlos Lopez",
        "cost_center": "CC-MKT-001",
        "hardware_type": "windows",
        "hardware_tier": "standard_plus",
        "created": "2024-01-10T08:00:00",
        "comments": []
    }
}