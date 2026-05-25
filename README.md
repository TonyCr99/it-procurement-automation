# IT Procurement Automation

> Automates the end-to-end hardware procurement process for IT teams —
> from Jira ticket creation to laptop delivery.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

---

## The Problem

IT procurement in mid-size companies is a manual, error-prone process.
Agents juggle multiple tools — Jira, Netsuite, vendor portals, email —
with no integration between them. A single laptop purchase can take
5+ days and require 20+ manual actions across 4 different platforms.

Common pain points:
- Quotes generated manually, one by one, from vendor portals
- Approvals with no SLA — requests sit unattended for days
- Purchase orders created by hand in Netsuite and copy-pasted into Jira
- Price fluctuations between approval and payment force the process to restart
- No visibility into where each request stands at any given moment

---

## What This Does

- 🎫 Reads incoming Jira tickets and manages their full lifecycle automatically
- 💰 Generates hardware quotes based on equipment type and tier
- ✅ Routes approval requests to the right manager with automatic reminders
- 📋 Creates purchase orders in Netsuite without manual data entry
- 🔔 Notifies stakeholders at every step via email and Slack
- ⚠️ Detects price changes before payment and alerts the team
- 📦 Tracks delivery status and closes the ticket on confirmation

---
> ✅ Tested in production — Jira live mode verified May 2026

## Tech Stack

- **Python 3.12+**
- **Jira REST API v3** — ticket management
- **Netsuite REST API** — purchase order creation
- **YAML config** — fully customizable per organization

---

## Roadmap

- [x] Project architecture and configuration
- [x] Jira connector — read and update tickets
- [x] Interactive CLI menu
- [x] Quote generation module
- [x] Approval notification engine
- [x] Netsuite purchase order connector
- [x] Price change validation
- [x] Setup wizard — guided first-time configuration
- [x] Azure AD — cost center lookup and approver validation
- [x] Vendor scraper — autonomous product selection
- [ ] Fix: Jira custom fields mapping in live mode
- [ ] Vendor scraper — Playwright live mode test
- [ ] Netsuite live mode — OAuth configuration
- [ ] Azure AD live mode — Graph API test
- [ ] Web dashboard
- [ ] Multi-tenant support

---

## License

MIT © [TonyCr99](https://github.com/TonyCr99)
