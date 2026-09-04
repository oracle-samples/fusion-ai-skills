# Oracle Readiness Navigation Guide

Use this guide when the customer does not provide PDFs.

## Starting point

Open the Oracle Cloud Applications Readiness home page:

https://docs.oracle.com/en/cloud/saas/readiness/index.html

## Navigation pattern

1. Choose the product tile that matches the customer scope.
   - Enterprise Resource Planning
   - Enterprise Performance Management
   - Supply Chain & Manufacturing
   - Human Capital Management
   - Sales
   - Service
   - Marketing
   - NetSuite
   - Industries
   - Fusion Applications Common

2. On the tile page, use the "Select a Release" control.
   - Latest Update
   - Prior Update
   - All Updates

3. Use the release page headings and linked HTTPS "What's New" pages on Oracle-owned documentation domains as the source material.

4. If the customer skipped multiple releases, review each required release page and consolidate the net-new items.

## Product tile mapping

Map common customer terms to Oracle readiness tiles before collecting sources:

- ERP, Financials, Payables, Receivables, General Ledger, Cash Management, Assets, Expenses, Projects, Revenue Management -> Enterprise Resource Planning
- Procurement, Purchasing, Sourcing, Supplier Portal, Supplier Qualification, Supplier Contracts -> Enterprise Resource Planning or Supply Chain & Manufacturing, depending on where the readiness page places the module for that release
- Inventory, Manufacturing, Maintenance, Planning, Product Management, Quality, Cost Management, Order Management, Logistics -> Supply Chain & Manufacturing
- HR, HCM, Payroll, Recruiting, Talent, Benefits, Workforce Management, Learning, Compensation -> Human Capital Management
- Sales, CPQ, CX Sales, Incentive Compensation -> Sales
- Service, Help Desk, Field Service, Digital Customer Service -> Service
- Marketing, Responsys, Eloqua, Unity -> Marketing
- Planning, Close, Consolidation, Account Reconciliation, Profitability, Narrative Reporting, Enterprise Data Management -> Enterprise Performance Management
- Redwood, approvals, notifications, common UX, setup, shared security, common tools, common analytics -> Fusion Applications Common when the feature is not clearly owned by a single product tile

If a term could map to more than one tile, state the mapping assumption before analysis and prefer the tile that matches the customer's enabled modules.

## Practical rules

- Prefer the release family page that matches the customer's pillar first.
- Treat `https://docs.oracle.com/en/cloud/saas/readiness/index.html` as the primary starting point.
- Follow only HTTPS Oracle-owned documentation links. Prefer `docs.oracle.com`.
- Before using a linked source, verify that the final URL remains on `docs.oracle.com`, `www.oracle.com`, or another `*.oracle.com` host clearly serving Oracle documentation.
- Do not retrieve non-Oracle links, shortened links, raw IP address links, `http://` links, or redirects that leave Oracle-owned domains.
- If a readiness page links to a non-Oracle or unexpected location, do not retrieve it. Capture the link in source coverage as skipped because it is outside the allowed source domain.
- If the page shows both HTML and PDF links, use the HTML page for quick navigation and the PDF when it contains fuller content.
- Do not require the user to upload PDFs if the readiness site already exposes the needed release information.
- If a release page includes a global catalog or related module page, use it only when it clearly belongs to the customer's scope.
- Do not collect every feature from a broad readiness catalog. Filter to the customer's stated pillars, modules, personas, and cross-application dependencies.
- Keep features with unclear applicability in a separate "Potentially relevant" section for customer confirmation.
- When source coverage is incomplete, record which release, product tile, module page, or linked PDF could not be reviewed.
