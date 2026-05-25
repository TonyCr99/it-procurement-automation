# ============================================================
# IT Procurement Automation — Netsuite Mock Data
# ============================================================
# Simulates purchase orders and Netsuite catalog data.
# Replace with real Netsuite credentials in .env for live mode.

# ------------------------------------------------------------
# Default PO template
# ------------------------------------------------------------
PO_DEFAULTS = {
    "service_nature": "Gastos Hardware",
    "location": "config:company.name",      # pulled from config.yaml
    "conta_contabil": "Equipo de Computo",
    "quantity": 1,
    "units": "SERV",
}

# ------------------------------------------------------------
# Item codes by category
# ------------------------------------------------------------
ITEM_CODES = {
    "laptop": "HW-LAPTOP-001",              # fixed code for all laptops
    "gadget": "HW-GADGET-001",              # TODO: v2
    "shipping": "HW-SHIPPING-001",          # TODO: v2
}

# ------------------------------------------------------------
# Mock purchase orders
# ------------------------------------------------------------
MOCK_ORDERS = {
    "PO-2024-001": {
        "po_number": "PO-2024-001",
        "ticket_id": "IT-001",
        "status": "Pending Approval",
        "vendor": "Vendor Portal",
        "employee": "Tony",
        "date": "2024-01-15",
        "note": (
            "EQUIPO DE COMPUTO - MacBook Pro 14\" M4 Pro 24GB 512GB SSD"
            " - REPOSICION DE EQUIPO - Maria Garcia (IT-001)"
        ),
        "classification": {
            "service_nature": "Gastos Hardware",
            "cost_center": "CC-MKT-001",
            "location": "Your Company Name",
        },
        "items": [
            {
                "item_code": "HW-LAPTOP-001",
                "conta_contabil": "Equipo de Computo",
                "description": (
                    "EQUIPO DE COMPUTO - MacBook Pro 14\" M4 Pro 24GB 512GB SSD"
                    " - REPOSICION DE EQUIPO - Maria Garcia (IT-001)"
                ),
                "rate": 47413.79,           # price before IVA (16%)
                "quantity": 1,
                "units": "SERV",
                "amount": 47413.79,         # auto-calculated
                "cost_center": "CC-MKT-001",
            }
        ],
        "subtotal": 47413.79,
        "tax": 7586.21,
        "total": 54999.00,
    }
}

# ------------------------------------------------------------
# IVA rate — matches config.yaml finance.tax_rate
# ------------------------------------------------------------
IVA_RATE = 0.16


def calculate_pretax(total: float) -> float:
    """
    Calculates the price before IVA from a total that includes IVA.
    Used to populate the 'rate' field in Netsuite items.
    Example: $54,999.00 MXN total → $47,413.79 MXN before IVA
    """
    return round(total / (1 + IVA_RATE), 2)


def build_po_note(product_name: str, reason: str, user: str, ticket_id: str) -> str:
    """
    Builds the PO note field in the standard format.
    Example: EQUIPO DE COMPUTO - MacBook Pro 14" - REPOSICION - Maria Garcia (IT-001)
    """
    return f"EQUIPO DE COMPUTO - {product_name} - {reason} - {user} ({ticket_id})"