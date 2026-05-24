# ============================================================
# IT Procurement Automation — Vendor Connector
# ============================================================
# Handles all interactions with the vendor procurement portal.
# Uses mock mode by default — set VENDOR_MOCK=false in .env
# to enable live web scraping via Playwright.
#
# Run from project root for testing:
#   python -m src.connectors.vendor

from src.config_loader import config, env
from src.mock.vendor_catalog import MOCK_CATALOG, MINIMUM_STOCK, WARRANTY_OPTIONS


class VendorConnector:
    """
    Manages all vendor portal operations.
    Mock mode returns catalog data from vendor_catalog.py.
    Live mode scrapes the vendor portal using Playwright.
    """

    def __init__(self):
        self.mock = env("VENDOR_MOCK", required=False) != "false"
        self.min_stock = MINIMUM_STOCK

        if self.mock:
            print("⚙️  Vendor running in mock mode.")
        else:
            self._connect()

    def _connect(self):
        """Launches Playwright browser and logs into vendor portal."""
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._page = self._browser.new_page()

        self._page.goto(env("VENDOR_URL"))
        self._page.fill("input[name='email']", env("VENDOR_USER"))
        self._page.fill("input[name='password']", env("VENDOR_PASSWORD"))
        self._page.click("button[type='submit']")
        self._page.wait_for_load_state("networkidle")
        print("✅ Connected to vendor portal.")

    # ----------------------------------------------------------
    # Read operations
    # ----------------------------------------------------------

    def get_product(self, hardware_type: str, tier: str) -> dict:
        """
        Returns product details for a given hardware type and tier.
        Validates minimum specs and stock availability.
        """
        if self.mock:
            product = MOCK_CATALOG.get(hardware_type, {}).get(tier)
            if not product:
                raise ValueError(
                    f"No product found for type='{hardware_type}' tier='{tier}'\n"
                    f"Check config.yaml hardware section."
                )
            return product

        # Live mode — scrape vendor portal
        search_term = "MacBook" if hardware_type == "macbook" else "Lenovo ThinkPad"
        self._page.fill("input[type='search']", search_term)
        self._page.keyboard.press("Enter")
        self._page.wait_for_load_state("networkidle")

        # TODO: implement product selector logic when testing on live portal
        raise NotImplementedError("Live vendor scraping not yet implemented.")

    def get_warranty_options(self) -> dict:
        """Returns available warranty options."""
        if self.mock:
            return WARRANTY_OPTIONS

        # TODO: implement live warranty scraping
        raise NotImplementedError("Live warranty scraping not yet implemented.")

    def validate_stock(self, hardware_type: str, tier: str) -> bool:
        """
        Returns True if product has enough stock to proceed.
        Minimum stock defined in vendor_catalog.py
        """
        product = self.get_product(hardware_type, tier)
        stock = product["stock"]
        available = stock >= self.min_stock

        if not available:
            print(
                f"⚠️  Low stock: {stock} units available "
                f"(minimum required: {self.min_stock})"
            )
        return available

    def validate_specs(self, hardware_type: str, tier: str) -> bool:
        """Returns True if product meets minimum hardware specifications."""
        product = self.get_product(hardware_type, tier)
        if not product["meets_minimum"]:
            print(f"⚠️  Spec warning: {product['notes']}")
        return product["meets_minimum"]

    # ----------------------------------------------------------
    # Quote operations
    # ----------------------------------------------------------

    def get_quote(self, hardware_type: str, tier: str, warranty: str = "none") -> dict:
        """
        Builds a quote for a given product and warranty option.
        Returns a dict with all pricing details.
        """
        product = self.get_product(hardware_type, tier)
        warranty_options = self.get_warranty_options()
        warranty_detail = warranty_options.get(warranty, warranty_options["none"])

        subtotal = product["price_mxn"]
        warranty_cost = warranty_detail["price_mxn"]
        total = subtotal + warranty_cost

        return {
            "sku": product["sku"],
            "name": product["name"],
            "specs": product["specs"],
            "hardware_type": hardware_type,
            "tier": tier,
            "stock": product["stock"],
            "meets_minimum": product["meets_minimum"],
            "warranty": warranty_detail["label"],
            "price_mxn": subtotal,
            "warranty_cost_mxn": warranty_cost,
            "total_mxn": total,
            "notes": product["notes"]
        }

    def close(self):
        """Closes browser session (live mode only)."""
        if not self.mock:
            self._browser.close()
            self._playwright.stop()


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    vendor = VendorConnector()

    print("\n--- Product lookup ---")
    product = vendor.get_product("macbook", "power")
    print(f"  Name  : {product['name']}")
    print(f"  Chip  : {product['specs']['chip']}")
    print(f"  Price : ${product['price_mxn']:,.2f} MXN")
    print(f"  Stock : {product['stock']} units")

    print("\n--- Stock validation ---")
    vendor.validate_stock("windows", "standard")
    vendor.validate_stock("macbook", "standard")

    print("\n--- Spec validation ---")
    vendor.validate_specs("macbook", "standard")
    vendor.validate_specs("macbook", "standard_plus")

    print("\n--- Quote with warranty ---")
    quote = vendor.get_quote("windows", "standard_plus", "2_year")
    print(f"  Product  : {quote['name']}")
    print(f"  Subtotal : ${quote['price_mxn']:,.2f} MXN")
    print(f"  Warranty : {quote['warranty']} — ${quote['warranty_cost_mxn']:,.2f} MXN")
    print(f"  Total    : ${quote['total_mxn']:,.2f} MXN")