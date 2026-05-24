# ============================================================
# IT Procurement Automation — Vendor Catalog Mock Data
# ============================================================
# Simulates product catalog and quotes from vendor portal.
# Prices in MXN — update periodically to reflect market rates.

MOCK_CATALOG = {
    "macbook": {
        "standard": {
            "sku": "APPLE-MB-STD-001",
            "name": "MacBook Air 13\"",
            "specs": {
                "chip": "Apple M4",
                "ram": "16GB",
                "storage": "256GB SSD",
                "display": "13.6 inch Liquid Retina"
            },
            "price_mxn": 28999.00,
            "stock": 45,
            "meets_minimum": False,   # 256GB below 512GB requirement
            "notes": "Below spec — 256GB SSD"
        },
        "standard_plus": {
            "sku": "APPLE-MB-STD-PLUS-001",
            "name": "MacBook Air 13\"",
            "specs": {
                "chip": "Apple M4",
                "ram": "16GB",
                "storage": "512GB SSD",
                "display": "13.6 inch Liquid Retina"
            },
            "price_mxn": 34999.00,
            "stock": 32,
            "meets_minimum": True,
            "notes": ""
        },
        "power": {
            "sku": "APPLE-MB-PWR-001",
            "name": "MacBook Pro 14\"",
            "specs": {
                "chip": "Apple M4 Pro",
                "ram": "24GB",
                "storage": "512GB SSD",
                "display": "14.2 inch Liquid Retina XDR"
            },
            "price_mxn": 54999.00,
            "stock": 28,
            "meets_minimum": True,
            "notes": ""
        }
    },
    "windows": {
        "standard": {
            "sku": "LNV-WIN-STD-001",
            "name": "Lenovo ThinkPad E14 Gen 5",
            "specs": {
                "processor": "Intel Core i5-1335U (13th Gen)",
                "ram": "16GB DDR4",
                "storage": "512GB SSD",
                "display": "14 inch FHD IPS"
            },
            "price_mxn": 18999.00,
            "stock": 67,
            "meets_minimum": True,
            "notes": ""
        },
        "standard_plus": {
            "sku": "LNV-WIN-STD-PLUS-001",
            "name": "Lenovo ThinkPad E16 Gen 2",
            "specs": {
                "processor": "Intel Core i7-1355U (13th Gen)",
                "ram": "16GB DDR4",
                "storage": "512GB SSD",
                "display": "16 inch FHD IPS"
            },
            "price_mxn": 24999.00,
            "stock": 41,
            "meets_minimum": True,
            "notes": ""
        },
        "power": {
            "sku": "LNV-WIN-PWR-001",
            "name": "Lenovo ThinkPad X1 Carbon Gen 12",
            "specs": {
                "processor": "Intel Core i7-1365U (13th Gen)",
                "ram": "32GB DDR5",
                "storage": "1TB SSD",
                "display": "14 inch 2.8K OLED"
            },
            "price_mxn": 42999.00,
            "stock": 23,
            "meets_minimum": True,
            "notes": ""
        }
    }
}

# Minimum stock required to proceed with purchase
MINIMUM_STOCK = 20

# Warranty options
WARRANTY_OPTIONS = {
    "none": {
        "label": "No warranty",
        "price_mxn": 0.00
    },
    "1_year": {
        "label": "1 Year Extended Warranty",
        "price_mxn": 1299.00
    },
    "2_year": {
        "label": "2 Year Extended Warranty",
        "price_mxn": 2199.00
    },
    "3_year": {
        "label": "3 Year Extended Warranty",
        "price_mxn": 2999.00
    }
}