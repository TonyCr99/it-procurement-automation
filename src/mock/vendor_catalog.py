# ============================================================
# IT Procurement Automation — Vendor Catalog Mock Data
# ============================================================
# Simulates product catalog and quotes from vendor portal.
# Prices in MXN — update periodically to reflect market rates.
# Selection criteria: meets specs → stock >= 20 → lowest price

MOCK_CATALOG = {
    "macbook": {
        "standard": [
            {
                "sku": "MQLD3E/A",
                "name": 'Apple MacBook Air 13.6"',
                "specs": {
                    "chip": "Apple M4",
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "screen_inch": 13.6,
                },
                "price_mxn": 28999.00,
                "stock": 45,
            },
            {
                "sku": "MQLE3E/A",
                "name": 'Apple MacBook Air 13.6"',
                "specs": {
                    "chip": "Apple M4",
                    "ram_gb": 16,
                    "storage_gb": 256,
                    "screen_inch": 13.6,
                },
                "price_mxn": 24999.00,
                "stock": 32,
            },
        ],
        "standard_plus": [
            {
                "sku": "MX2Y3E/A",
                "name": 'Apple MacBook Pro 14.2"',
                "specs": {
                    "chip": "Apple M4 Pro",
                    "ram_gb": 24,
                    "storage_gb": 512,
                    "screen_inch": 14.2,
                },
                "price_mxn": 52129.00,
                "stock": 28,
            },
            {
                "sku": "MX2F3E/A",
                "name": 'Apple MacBook Pro 14.2"',
                "specs": {
                    "chip": "Apple M4 Pro",
                    "ram_gb": 24,
                    "storage_gb": 512,
                    "screen_inch": 14.2,
                },
                "price_mxn": 54999.00,
                "stock": 6,
            },
        ],
        "power": [
            {
                "sku": "MGDN4E/A",
                "name": 'Apple MacBook Pro 16.2"',
                "specs": {
                    "chip": "Apple M5 Pro",
                    "ram_gb": 24,
                    "storage_gb": 1024,
                    "screen_inch": 16.2,
                },
                "price_mxn": 48369.00,
                "stock": 45,
            },
            {
                "sku": "MDE64E/A",
                "name": 'Apple MacBook Pro 16.2"',
                "specs": {
                    "chip": "Apple M5",
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "screen_inch": 16.2,
                },
                "price_mxn": 41839.00,
                "stock": 15,
            },
        ],
    },
    "windows": {
        "standard": [
            {
                "sku": "21HN0044US",
                "name": "Lenovo ThinkPad E14 Gen 5",
                "specs": {
                    "processor": "Intel Core i5-1335U",
                    "processor_gen": 13,
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "screen_inch": 14.0,
                },
                "price_mxn": 18999.00,
                "stock": 67,
            },
            {
                "sku": "21HN0045US",
                "name": "Lenovo ThinkPad E14 Gen 5",
                "specs": {
                    "processor": "Intel Core i5-1335U",
                    "processor_gen": 13,
                    "ram_gb": 16,
                    "storage_gb": 256,
                    "screen_inch": 14.0,
                },
                "price_mxn": 16999.00,
                "stock": 42,
            },
        ],
        "standard_plus": [
            {
                "sku": "21HN0050US",
                "name": "Lenovo ThinkPad E14 Gen 5",
                "specs": {
                    "processor": "Intel Core i7-1355U",
                    "processor_gen": 13,
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "screen_inch": 14.0,
                },
                "price_mxn": 24999.00,
                "stock": 41,
            },
        ],
        "power": [
            {
                "sku": "21HN0060US",
                "name": "Lenovo ThinkPad X1 Carbon Gen 12",
                "specs": {
                    "processor": "Intel Core i7-1365U",
                    "processor_gen": 13,
                    "ram_gb": 32,
                    "storage_gb": 1024,
                    "screen_inch": 15.6,
                },
                "price_mxn": 42999.00,
                "stock": 23,
            },
        ],
    },
}

# Minimum stock required to proceed with purchase
MINIMUM_STOCK = 20

# Warranty options
WARRANTY_OPTIONS = {
    "none": {
        "label": "No warranty",
        "price_mxn": 0.00
    },
    "applecare_3y": {
        "label": "AppleCare+ 3 Years",
        "price_mxn": 4889.00
    },
    "warranty_1y": {
        "label": "1 Year Extended Warranty",
        "price_mxn": 1299.00
    },
    "warranty_2y": {
        "label": "2 Year Extended Warranty",
        "price_mxn": 2199.00
    },
    "warranty_3y": {
        "label": "3 Year Extended Warranty",
        "price_mxn": 2999.00
    },
}