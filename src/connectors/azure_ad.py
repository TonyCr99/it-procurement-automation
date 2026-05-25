# ============================================================
# IT Procurement Automation — Azure AD Connector
# ============================================================
# Retrieves user cost center from Azure AD (Entra ID)
# and validates against the cost centers Excel reference file.
#
# Flow:
#   1. Look up user by email in Azure AD via Graph API
#   2. Extract Cost Center number from user profile
#   3. Look up Cost Center name and LVL 1 approver in Excel
#   4. Validate LVL 1 approver matches Netsuite PO approver
#
# Run from project root for testing:
#   python -m src.connectors.azure_ad

import pandas as pd
from src.config_loader import config, env


# ------------------------------------------------------------
# Mock data — simulates Azure AD user profiles
# ------------------------------------------------------------
MOCK_USERS = {
    "maria.garcia@company.com": {
        "display_name": "Maria Garcia",
        "email": "maria.garcia@company.com",
        "job_title": "Marketing Coordinator",
        "cost_center_number": 108,
    },
    "juan.perez@company.com": {
        "display_name": "Juan Perez",
        "email": "juan.perez@company.com",
        "job_title": "Software Engineer",
        "cost_center_number": 107,
    },
    "sofia.ramos@company.com": {
        "display_name": "Sofia Ramos",
        "email": "sofia.ramos@company.com",
        "job_title": "Sales Executive",
        "cost_center_number": 110,
    },
}


class AzureADConnector:
    """
    Retrieves user cost center data from Azure AD and Excel reference.
    Mock mode uses MOCK_USERS dict.
    Live mode uses Microsoft Graph API.
    """

    def __init__(self):
        self.mock = env("AZURE_AD_MOCK", required=False) != "false"
        self.cc_file = "src/data/cost_centers.xlsx"
        self._cc_data = None

        if self.mock:
            print("⚙️  Azure AD running in mock mode.")
        else:
            self._connect()

    def _connect(self):
        """Authenticates with Microsoft Graph API."""
        import requests

        tenant_id = env("AZURE_TENANT_ID")
        client_id = env("AZURE_CLIENT_ID")
        client_secret = env("AZURE_CLIENT_SECRET")

        response = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        self._headers = {"Authorization": f"Bearer {self._token}"}
        print("✅ Connected to Azure AD.")

    # ----------------------------------------------------------
    # Cost center Excel lookup
    # ----------------------------------------------------------

    def _load_cc_data(self) -> pd.DataFrame:
        """Loads cost centers Excel file into a DataFrame."""
        if self._cc_data is None:
            self._cc_data = pd.read_excel(
                self.cc_file,
                header=1,
                dtype={"Numeração Novo Centro de Custo": str},
            )
        return self._cc_data

    def lookup_cost_center(self, cc_number: int) -> dict:
        """
        Looks up cost center details by number in the Excel reference.
        Returns name, ID and LVL 1 approver.
        """
        df = self._load_cc_data()
        cc_str = str(cc_number)

        match = df[
            df["Numeração Novo Centro de Custo"].astype(str) == cc_str
        ]

        if match.empty:
            raise ValueError(
                f"Cost center {cc_number} not found in reference file.\n"
                f"Check src/data/cost_centers.xlsx."
            )

        row = match.iloc[0]
        return {
            "number": cc_number,
            "name": row["Nome Novo Centro de Custo"],
            "internal_id": row["ID Interno"],
            "approver_lvl1": row["Aprobador LVL 1"],
            "nivel1": row.get("Nivel 1", ""),
            "nivel2": row.get("Nivel 2", ""),
        }

    # ----------------------------------------------------------
    # User lookup
    # ----------------------------------------------------------

    def get_user(self, email: str) -> dict:
        """Returns user profile including cost center number."""
        if self.mock:
            user = MOCK_USERS.get(email.lower())
            if not user:
                raise ValueError(f"User '{email}' not found in mock data.")
            return user

        import requests

        response = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{email}"
            f"?$select=displayName,mail,jobTitle,department,officeLocation",
            headers=self._headers,
        )
        response.raise_for_status()
        data = response.json()

        # Cost center number lives in officeLocation or a custom extension
        # Adjust field name based on your Azure AD configuration
        cc_raw = data.get("officeLocation") or data.get("department") or ""
        cc_number = int("".join(filter(str.isdigit, cc_raw))) if cc_raw else None

        return {
            "display_name": data.get("displayName"),
            "email": data.get("mail"),
            "job_title": data.get("jobTitle"),
            "cost_center_number": cc_number,
        }

    def get_user_cost_center(self, email: str) -> dict:
        """
        Full lookup — gets user from Azure AD then resolves
        cost center name and approver from Excel reference.
        Returns combined result.
        """
        user = self.get_user(email)
        cc_number = user.get("cost_center_number")

        if not cc_number:
            raise ValueError(
                f"No cost center number found for user '{email}'.\n"
                f"Check Azure AD profile — field: officeLocation or department."
            )

        cc = self.lookup_cost_center(cc_number)

        return {
            "user_name": user["display_name"],
            "user_email": email,
            "user_title": user["job_title"],
            "cc_number": cc["number"],
            "cc_name": cc["name"],
            "cc_internal_id": cc["internal_id"],
            "cc_approver_lvl1": cc["approver_lvl1"],
        }

    # ----------------------------------------------------------
    # Approver validation
    # ----------------------------------------------------------

    def validate_approver(
        self,
        cc_number: int,
        netsuite_approver: str
    ) -> dict:
        """
        Validates that the Netsuite PO approver matches
        the LVL 1 approver defined in the cost center Excel.
        Returns validation result with recommendation.
        """
        cc = self.lookup_cost_center(cc_number)
        excel_approver = cc["approver_lvl1"]

        match = (
            excel_approver.strip().lower()
            == netsuite_approver.strip().lower()
        )

        return {
            "cc_number": cc_number,
            "cc_name": cc["name"],
            "excel_approver": excel_approver,
            "netsuite_approver": netsuite_approver,
            "match": match,
            "recommendation": (
                "✅ Approvers match — safe to proceed."
                if match else
                f"⚠️ Approver mismatch detected.\n"
                f"   Excel LVL 1 : {excel_approver}\n"
                f"   Netsuite    : {netsuite_approver}\n"
                f"   Verify cost center selection before continuing."
            ),
        }


# ------------------------------------------------------------
# Quick test
# ------------------------------------------------------------
if __name__ == "__main__":
    azure = AzureADConnector()

    print("\n--- User cost center lookup ---")
    result = azure.get_user_cost_center("maria.garcia@company.com")
    print(f"  User     : {result['user_name']}")
    print(f"  Title    : {result['user_title']}")
    print(f"  CC #     : {result['cc_number']}")
    print(f"  CC Name  : {result['cc_name']}")
    print(f"  Approver : {result['cc_approver_lvl1']}")

    print("\n--- Cost center direct lookup ---")
    cc = azure.lookup_cost_center(104)
    print(f"  CC #     : {cc['number']}")
    print(f"  Name     : {cc['name']}")
    print(f"  Approver : {cc['approver_lvl1']}")

    print("\n--- Approver validation — match ---")
    result = azure.validate_approver(104, "Carlos Mendez")
    print(f"  {result['recommendation']}")

    print("\n--- Approver validation — mismatch ---")
    result = azure.validate_approver(104, "John Smith")
    print(f"  {result['recommendation']}")