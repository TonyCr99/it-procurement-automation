# ============================================================
# IT Procurement Automation — Vendor Connector
# ============================================================
# Handles all interactions with the vendor procurement portal.
# Uses mock mode by default — set VENDOR_MOCK=false in .env
# to enable live web scraping via Playwright.
#
# Selection criteria (autonomous mode):
#   1. Meets minimum specs (chip/processor, RAM, storage, screen)
#   2. Stock >= MINIMUM_STOCK
#   3. Lowest price among qualifying products
#
# Run from project root for testing:
#   python -m src.connectors.vendor

from src.config_loader import config, env
from src.mock.vendor_catalog import (
    MOCK_CATALOG,
    MINIMUM_STOCK,
    WARRANTY_OPTIONS,
)


class VendorConnector:
    """
    Manages all vendor portal operations.
    Mock mode returns catalog data from vendor_catalog.py.
    Live mode scrapes the vendor portal using Playwright.
    """

    def __init__(self):
        self.mock = env("VENDOR_MOCK", required=False) != "false"
        self.min_stock = MINIMUM_STOCK
        self.specs = config["hardware"]["specs"]

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
    # Spec validation
    # ----------------------------------------------------------

    def _meets_specs(self, product: dict, hardware_type: str, tier: str) -> bool:
        """
        Validates a product against minimum specs from config.yaml.
        Returns True if product meets all requirements.
        """
        required = self.specs[hardware_type][tier]
        specs = product["specs"]

        if hardware_type == "macbook":
            # Validate chip generation
            chip = specs.get("chip", "")
            chip_min = required["chip_min"]
            chip_gen = self._parse_apple_chip_gen(chip)
            chip_gen_min = self._parse_apple_chip_gen(chip_min)
            if chip_gen < chip_gen_min:
                return False

        elif hardware_type == "windows":
            # Validate processor generation
            if specs.get("processor_gen", 0) < required["processor_gen_min"]:
                return False

        # Validate RAM
        if specs.get("ram_gb", 0) < required["ram_min_gb"]:
            return False

        # Validate storage
        if specs.get("storage_gb", 0) < required["storage_min_gb"]:
            return False

        # Validate screen size
        if specs.get("screen_inch", 0) < required["screen_inch"]:
            return False

        return True

    def _parse_apple_chip_gen(self, chip: str) -> int:
        """
        Parses Apple chip name and returns a comparable generation number.
        M4 = 4, M4 Pro = 4, M5 = 5, M5 Pro = 5, etc.
        """
        chip = chip.upper()
        for gen in range(10, 0, -1):
            if f"M{gen}" in chip:
                return gen
        return 0

    # ----------------------------------------------------------
    # Product selection
    # ----------------------------------------------------------

    def get_best_product(self, hardware_type: str, tier: str) -> dict:
        """
        Selects the best product for a given hardware type and tier.
        Filters by specs and stock, then returns the lowest price option.
        Raises ValueError if no qualifying product is found.
        """
        if self.mock:
            candidates = MOCK_CATALOG.get(hardware_type, {}).get(tier, [])
        else:
            candidates = self._scrape_products(hardware_type, tier)

        if not candidates:
            raise ValueError(
                f"No products found for {hardware_type} {tier}."
            )

        # Filter by specs
        spec_qualified = [
            p for p in candidates
            if self._meets_specs(p, hardware_type, tier)
        ]

        if not spec_qualified:
            raise ValueError(
                f"No products meet minimum specs for {hardware_type} {tier}.\n"
                f"Check config.yaml hardware.specs section."
            )

        # Filter by stock
        stock_qualified = [
            p for p in spec_qualified
            if p["stock"] >= self.min_stock
        ]

        if not stock_qualified:
            raise ValueError(
                f"No products have sufficient stock (>= {self.min_stock}) "
                f"for {hardware_type} {tier}.\n"
                f"Spec-qualified products found: {len(spec_qualified)} "
                f"but all below minimum stock."
            )

        # Select lowest price
        best = min(stock_qualified, key=lambda p: p["price_mxn"])

        print(f"✅ Selected: {best['name']} ({best['sku']})")
        print(f"   Price : ${best['price_mxn']:,.2f} MXN")
        print(f"   Stock : {best['stock']} units")

        return best

    # ----------------------------------------------------------
    # Legacy method — kept for compatibility
    # ----------------------------------------------------------

    def get_product(self, hardware_type: str, tier: str) -> dict:
        """Alias for get_best_product — selects optimal product."""
        return self.get_best_product(hardware_type, tier)

    # ----------------------------------------------------------
    # Quote operations
    # ----------------------------------------------------------

    def get_quote(
        self,
        hardware_type: str,
        tier: str,
        warranty: str = "none"
    ) -> dict:
        """
        Builds a quote for the best available product.
        Warranty is selected automatically by the vendor portal in live mode.
        """
        product = self.get_best_product(hardware_type, tier)
        warranty_options = self.get_warranty_options()
        warranty_detail = warranty_options.get(
            warranty, warranty_options["none"]
        )

        total = product["price_mxn"] + warranty_detail["price_mxn"]

        return {
            "sku": product["sku"],
            "name": product["name"],
            "specs": product["specs"],
            "hardware_type": hardware_type,
            "tier": tier,
            "stock": product["stock"],
            "warranty": warranty_detail["label"],
            "price_mxn": product["price_mxn"],
            "warranty_cost_mxn": warranty_detail["price_mxn"],
            "total_mxn": total,
        }

    def get_warranty_options(self) -> dict:
        """
        Returns available warranty options.
        In live mode, warranty is selected automatically by the portal.
        """
        if self.mock:
            return WARRANTY_OPTIONS
        raise NotImplementedError("Live warranty scraping not yet implemented.")

    # ----------------------------------------------------------
    # Stock validation
    # ----------------------------------------------------------

    def validate_stock(self, hardware_type: str, tier: str) -> bool:
        """Returns True if best product has sufficient stock."""
        try:
            self.get_best_product(hardware_type, tier)
            return True
        except ValueError:
            return False

    # ----------------------------------------------------------
    # Live mode — Playwright scraper (TODO)
    # ----------------------------------------------------------

    def _scrape_products(
        self, hardware_type: str, tier: str
    ) -> list:
        """
        Scrapes vendor portal for products matching hardware type and tier.
        Returns list of product dicts with same structure as mock catalog.
        TODO: implement when testing on live portal.
        """
        raise NotImplementedError(
            "Live vendor scraping not yet implemented.\n"
            "Set VENDOR_MOCK=true to use mock catalog."
        )

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

    print("\n--- Best MacBook Standard ---")
    product = vendor.get_best_product("macbook", "standard")
    print(f"  Selected : {product['name']} ({product['sku']})")
    print(f"  Chip     : {product['specs']['chip']}")
    print(f"  Screen   : {product['specs']['screen_inch']}\"")
    print(f"  Price    : ${product['price_mxn']:,.2f} MXN")
    print(f"  Stock    : {product['stock']} units")

    print("\n--- Best MacBook Power ---")
    product = vendor.get_best_product("macbook", "power")
    print(f"  Selected : {product['name']} ({product['sku']})")
    print(f"  Chip     : {product['specs']['chip']}")
    print(f"  Screen   : {product['specs']['screen_inch']}\"")
    print(f"  Price    : ${product['price_mxn']:,.2f} MXN")
    print(f"  Stock    : {product['stock']} units")

    print("\n--- Best Windows Standard Plus ---")
    product = vendor.get_best_product("windows", "standard_plus")
    print(f"  Selected : {product['name']} ({product['sku']})")
    print(f"  Processor: {product['specs']['processor']}")
    print(f"  Screen   : {product['specs']['screen_inch']}\"")
    print(f"  Price    : ${product['price_mxn']:,.2f} MXN")
    print(f"  Stock    : {product['stock']} units")

    print("\n--- Stock filter test (MacBook Standard Plus) ---")
    print("  MX2F3E/A has 6 units — should be filtered out")
    product = vendor.get_best_product("macbook", "standard_plus")
    print(f"  Selected : {product['sku']} — Stock: {product['stock']} units")
    print(f"  Price    : ${product['price_mxn']:,.2f} MXN")