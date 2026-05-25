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

        self._page.goto(f"{env('VENDOR_URL')}/login")
        self._page.wait_for_load_state("networkidle")
        self._page.fill("input[name='user']", env("VENDOR_USER"))
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
            chip = specs.get("chip", "")
            chip_min = required["chip_min"]
            chip_gen = self._parse_apple_chip_gen(chip)
            chip_gen_min = self._parse_apple_chip_gen(chip_min)
            if chip_gen < chip_gen_min:
                return False

        elif hardware_type == "windows":
            if specs.get("processor_gen", 0) < required["processor_gen_min"]:
                return False

        if specs.get("ram_gb", 0) < required["ram_min_gb"]:
            return False

        if specs.get("storage_gb", 0) < required["storage_min_gb"]:
            return False

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

        spec_qualified = [
            p for p in candidates
            if self._meets_specs(p, hardware_type, tier)
        ]

        if not spec_qualified:
            raise ValueError(
                f"No products meet minimum specs for {hardware_type} {tier}.\n"
                f"Check config.yaml hardware.specs section."
            )

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

        best = min(stock_qualified, key=lambda p: p["price_mxn"])

        print(f"✅ Selected: {best['name']} ({best['sku']})")
        print(f"   Price : ${best['price_mxn']:,.2f} MXN")
        print(f"   Stock : {best['stock']} units")

        return best

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
    # Live mode — Playwright scraper
    # ----------------------------------------------------------

    def _scrape_products(
        self, hardware_type: str, tier: str
    ) -> list:
        """
        Scrapes vendor portal for products matching hardware type and tier.
        Returns list of product dicts with same structure as mock catalog.
        """
        search_term = "MacBook" if hardware_type == "macbook" else "Lenovo ThinkPad"

        self._page.fill("input[name='searchparam']", search_term)
        self._page.keyboard.press("Enter")
        self._page.wait_for_load_state("networkidle")

        products = []
        cards = self._page.query_selector_all(".c-product-price")

        for card in cards:
            try:
                name_el = card.query_selector(
                    "[data-testid='cpx-truncated__text']"
                )
                if not name_el:
                    continue
                name = name_el.get_attribute("title") or name_el.inner_text()
                name = name.split("―")[0].strip()

                price_el = card.query_selector(".cpx-text--price-total")
                if not price_el:
                    continue
                price_text = price_el.inner_text()
                price = float(
                    price_text.replace("$", "")
                    .replace(",", "")
                    .strip()
                )

                stock_el = card.query_selector(".cpx-text--caption-bold")
                stock = 0
                if stock_el:
                    stock_text = stock_el.inner_text()
                    stock = int("".join(filter(str.isdigit, stock_text)))

                link_el = card.query_selector("a[href]")
                sku = ""
                if link_el:
                    href = link_el.get_attribute("href") or ""
                    sku = href.split("/")[-1]

                specs = self._parse_specs_from_name(name, hardware_type)

                products.append({
                    "sku": sku,
                    "name": name,
                    "specs": specs,
                    "price_mxn": price,
                    "stock": stock,
                })

            except Exception:
                continue

        return products

    def _parse_specs_from_name(
        self, name: str, hardware_type: str
    ) -> dict:
        """
        Parses product specs from the product name string.
        Used in live mode to extract RAM, storage, screen, chip/processor.
        """
        name_upper = name.upper()
        specs = {}

        for ram in [64, 48, 36, 32, 24, 16, 8]:
            if f"{ram}GB" in name_upper:
                specs["ram_gb"] = ram
                break

        for storage, label in [
            (2048, "2TB"), (1024, "1TB"),
            (512, "512GB"), (256, "256GB")
        ]:
            if label in name_upper:
                specs["storage_gb"] = storage
                break

        for size in [16.2, 16.0, 15.6, 14.2, 14.0, 13.6, 13.3, 13.0]:
            if str(size) in name or f'{size}"' in name:
                specs["screen_inch"] = size
                break

        if hardware_type == "macbook":
            for chip in ["M5 PRO", "M5 MAX", "M5", "M4 PRO", "M4 MAX", "M4"]:
                if chip in name_upper:
                    specs["chip"] = f"Apple {chip.title()}"
                    break
        else:
            for gen in range(14, 10, -1):
                if (
                    f"{gen}TH" in name_upper
                    or f"{gen}VA" in name_upper
                    or f"GEN {gen}" in name_upper
                ):
                    specs["processor_gen"] = gen
                    specs["processor"] = self._extract_processor(name)
                    break

        return specs

    def _extract_processor(self, name: str) -> str:
        """Extracts processor model from product name."""
        name_upper = name.upper()
        for model in ["I9", "I7", "I5", "I3"]:
            if model in name_upper:
                idx = name_upper.find(model)
                return name[idx:idx + 12].strip()
        return "Intel Core"

    def _scrape_quote(self, product: dict) -> str:
        """
        Adds product to cart, handles warranty modal,
        and generates quote PDF from vendor portal.
        Returns the path to the downloaded PDF.
        """
        self._page.fill("input[name='searchparam']", product["sku"])
        self._page.keyboard.press("Enter")
        self._page.wait_for_load_state("networkidle")

        add_btn = self._page.query_selector(
            "[data-testid='add-to-cart-button']"
        )
        if not add_btn:
            raise ValueError(
                f"Add to cart button not found for {product['sku']}"
            )
        add_btn.click()
        self._page.wait_for_timeout(1500)

        try:
            continue_btn = self._page.query_selector(
                "text=Continuar comprando"
            )
            if continue_btn:
                continue_btn.click()
                self._page.wait_for_timeout(1000)
        except Exception:
            pass

        self._page.goto(f"{env('VENDOR_URL')}/carrito-de-compras/")
        self._page.wait_for_load_state("networkidle")

        quote_btn = self._page.query_selector("text=Crear cotización")
        if not quote_btn:
            raise ValueError("Create quote button not found in cart.")

        with self._page.expect_download() as download_info:
            quote_btn.click()
        download = download_info.value
        pdf_path = f"quote_{product['sku']}.pdf"
        download.save_as(pdf_path)
        print(f"✅ Quote PDF saved: {pdf_path}")
        return pdf_path

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