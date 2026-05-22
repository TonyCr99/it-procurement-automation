# ============================================================
# IT Procurement Automation — Config Loader
# ============================================================
# Loads and validates config.yaml and .env variables.
# All other modules import from this file.
#
# Usage:
#   from src.config_loader import config, env
#   jira_url = env("JIRA_URL")
#   tiers = config["hardware"]["tiers"]

import os
import yaml
from dotenv import load_dotenv

# ------------------------------------------------------------
# Load .env variables into the environment
# ------------------------------------------------------------
load_dotenv()


def env(key: str, required: bool = True) -> str:
    """
    Retrieves an environment variable by key.
    Raises an error if required and not found.
    """
    value = os.getenv(key)
    if required and not value:
        raise EnvironmentError(
            f"Missing required environment variable: '{key}'\n"
            f"Check your .env file — see .env.example for reference."
        )
    return value


# ------------------------------------------------------------
# Load config.yaml
# ------------------------------------------------------------
def load_config(path: str = "config.yaml") -> dict:
    """
    Reads and parses the config.yaml file.
    Raises an error if the file is missing or malformed.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"config.yaml not found at '{path}'\n"
            f"Make sure you're running the project from the root folder."
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ------------------------------------------------------------
# Global config object — imported by all other modules
# ------------------------------------------------------------
config = load_config()


# ------------------------------------------------------------
# Quick validation on startup
# ------------------------------------------------------------
def validate_config() -> None:
    """
    Checks that required config sections exist.
    Run this once on startup to catch missing config early.
    """
    required_sections = ["company", "hardware", "ticket", "integrations", "finance"]
    missing = [s for s in required_sections if s not in config]
    if missing:
        raise KeyError(
            f"Missing required config sections: {missing}\n"
            f"Check your config.yaml — see documentation for reference."
        )
    print("✅ Config loaded successfully.")
    print(f"   Company : {config['company']['name']}")
    print(f"   Timezone: {config['company']['timezone']}")
    print(f"   Tiers   : {list(config['hardware']['tiers'].keys())}")


if __name__ == "__main__":
    validate_config()