# FinApp — Personal Finance Management Application

## 1. Overview

FinApp is a cross-platform personal finance management application inspired by Quicken, designed for users with financial activity in **multiple countries and currencies** — with a primary focus on **Brazilian Reais (BRL)** and **US Dollars (USD)**.

It centralizes bank accounts, brokerage accounts, transactions, investments, and reporting in a single local-first application backed by an embedded **SQLite** database, with a Python GUI front end and pluggable AI hooks for intelligent automation.

### 1.1 Goals

- Single source of truth for personal finances across countries.
- Local-first storage (SQLite), no mandatory cloud dependency.
- Extensible architecture with clean hooks for AI/LLM-powered features.
- Automated statement import and intelligent multi-source reconciliation.
- Investment portfolio tracking with real-time pricing.
- Strong multi-currency support with FX-aware reporting.

### 1.2 Non-Goals (initial version)

- Bill payment / direct money movement.
- Multi-user collaboration / cloud sync (planned for later phase).
- Tax filing automation (export-only support).

---

## 2. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Matches repository conventions; rich data ecosystem. |
| Database | SQLite 3 (via SQLAlchemy 2.x ORM) | Local-first, zero-config, transactional. |
| Migrations | Alembic | Schema evolution. |
| GUI | **PySide6 (Qt 6)** primary; pluggable view layer | Native look on Windows/macOS/Linux, mature tables/charts. Alternative: Flet or Textual for lighter footprint. |
| Charting | PyQtGraph + Matplotlib | Interactive portfolio charts and reports. |
| Market data | yfinance, Alpha Vantage, BCB (PTAX) | Stocks, FX, Brazilian rates. |
| AI/LLM | Pluggable provider interface; default Azure OpenAI (re-using `agents/Foundry-test` patterns) | Aligns with existing repo. |
| Statement parsing | OFX (`ofxparse`), QIF, CSV, PDF (pdfplumber + LLM fallback) | Coverage for BR + US banks. |
| Packaging | PyInstaller / Briefcase | Single-binary distribution. |
| Testing | pytest, pytest-qt | Unit + GUI. |
| Logging | structlog | Structured JSON logs. |
| Config | pydantic-settings + `.env` | Repo convention. |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     PySide6 GUI                         │
│  Dashboard │ Accounts │ Transactions │ Portfolio │ AI   │
└──────────────┬──────────────────────────────────────────┘
               │  (signals/slots, async tasks)
┌──────────────▼──────────────────────────────────────────┐
│                  Application Services                   │
│  AccountService │ TransactionService │ ImportService    │
│  ReconciliationService │ PortfolioService │ FXService   │
│  ReportingService │ AIService                           │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼─────────┐  ┌──────────────────────────┐
│  Repository / ORM      │  │  Integrations            │
│  (SQLAlchemy)          │  │  - Market data adapters  │
│                        │  │  - Statement parsers     │
│                        │  │  - LLM providers         │
└──────────────┬─────────┘  └──────────────────────────┘
               │
        ┌──────▼──────┐
        │  SQLite DB  │  (encrypted via SQLCipher option)
        └─────────────┘
```

### 3.1 Layering rules

- GUI layer never touches the ORM directly — only Services.
- Services are pure Python, fully unit-testable without Qt.
- Integrations expose abstract interfaces (`StatementParser`, `MarketDataProvider`, `LLMProvider`).
- All money values stored as `Decimal` (never float), persisted as INTEGER minor units + currency code.

---

## 4. Data Model

All amounts stored as `(amount_minor: INTEGER, currency: TEXT)` to avoid floating-point drift.

### 4.1 Core entities

- **Institution** — bank or brokerage. Fields: `id`, `name`, `country` (BR/US/…), `type` (BANK/BROKERAGE/CARD_ISSUER/EXCHANGE), `swift_bic`, `routing_or_ispb`, `website`, `notes`.
- **Account** — `id`, `institution_id`, `name`, `account_type` (CHECKING, SAVINGS, CREDIT_CARD, BROKERAGE, INVESTMENT, LOAN, CASH, CRYPTO_WALLET), `currency`, `account_number_masked`, `opening_balance`, `opening_date`, `is_active`, `tax_country`, `notes`.
- **AccountHolder** — for joint accounts.
- **Transaction** — `id`, `account_id`, `posted_date`, `value_date`, `amount_minor`, `currency`, `description_raw`, `description_clean`, `category_id`, `subcategory_id`, `payee_id`, `memo`, `external_id` (from import), `import_batch_id`, `status` (PENDING, CLEARED, RECONCILED, VOID), `reconciliation_id`, `transfer_pair_id`, `tags`, `attachment_path`, `created_at`, `updated_at`, `source` (MANUAL, IMPORT_OFX, IMPORT_CSV, IMPORT_PDF, AI_SUGGESTED).
- **TransactionSplit** — multi-category splits for one transaction.
- **Transfer** — links two transactions (one debit, one credit) potentially in different currencies; stores `fx_rate`, `fees`.
- **Category / Subcategory** — hierarchical, user-editable, with default seed (Income, Housing, Food, Transport, Investments, Taxes, BR-specific: IOF, IR, DARF; US-specific: 401k, HSA).
- **Payee** — normalized merchant. Fields: `id`, `display_name`, `aliases[]`, `default_category_id`, `tax_id`.
- **Tag** — free-form labels; many-to-many with transactions.
- **Rule** — auto-categorization. Fields: `id`, `priority`, `match_type` (REGEX, CONTAINS, AMOUNT_RANGE, AI_EMBEDDING), `pattern`, `account_scope`, `set_category_id`, `set_payee_id`, `set_tags`, `enabled`.
- **Budget** — per category, per period (monthly/yearly), per currency.
- **Goal** — savings/investment goals with target amount, date, linked accounts.

### 4.2 Investments

- **Security** — `id`, `symbol`, `exchange` (BVMF, NASDAQ, NYSE, B3), `isin`, `cusip`, `cnpj`, `name`, `security_type` (STOCK, ETF, FII, FUND, BOND, TESOURO_DIRETO, CDB, LCI, LCA, CRYPTO, OPTION), `currency`, `quote_provider`, `metadata_json`.
- **Holding** — denormalized current position view (computed).
- **Lot** — `id`, `account_id`, `security_id`, `acquired_date`, `quantity`, `cost_basis_minor`, `cost_currency`, `fx_rate_at_acquisition`, `source_transaction_id`. Supports FIFO/LIFO/average-cost cost basis.
- **InvestmentTransaction** — `id`, `account_id`, `security_id`, `trade_date`, `settle_date`, `type` (BUY, SELL, DIVIDEND, INTEREST, JCP, SPLIT, MERGER, BONUS, FEE, TAX_WITHHELD, TRANSFER_IN, TRANSFER_OUT, REINVEST), `quantity`, `price_minor`, `fees_minor`, `taxes_minor`, `currency`, `linked_cash_transaction_id`.
- **PriceHistory** — `security_id`, `date`, `open`, `high`, `low`, `close`, `volume`, `currency`.
- **CorporateAction** — splits, dividends, mergers.

### 4.3 Multi-currency

- **Currency** — `code` (ISO 4217), `name`, `symbol`, `decimal_places`.
- **FxRate** — `date`, `base_currency`, `quote_currency`, `rate`, `source` (BCB_PTAX, ECB, YAHOO, MANUAL). Daily snapshot table.
- **ExchangeOperation** — explicit BRL↔USD conversions (e.g., remittance via Wise, Avenue) linking two transfer transactions plus IOF and spread.

### 4.4 Reconciliation

- **StatementImport** — `id`, `account_id`, `file_path`, `file_hash`, `format`, `period_start`, `period_end`, `opening_balance`, `closing_balance`, `imported_at`, `status`.
- **ReconciliationSession** — `id`, `account_id`, `statement_import_id`, `period_start`, `period_end`, `expected_balance`, `actual_balance`, `difference`, `status` (OPEN, MATCHED, PARTIAL, CLOSED), `closed_at`.
- **ReconciliationMatch** — `id`, `session_id`, `book_transaction_id`, `statement_transaction_id`, `match_type` (EXACT, FUZZY, AI, MANUAL), `confidence`, `reviewed_by_user`.

### 4.5 AI / audit

- **AIInteraction** — prompt, response, model, tokens, cost, linked entity.
- **AuditLog** — every mutation, for traceability.
- **Attachment** — receipts/PDFs linked to transactions.

---

## 5. Functional Requirements

### 5.1 Accounts & institutions

- CRUD for institutions and accounts.
- Account hierarchy (e.g., brokerage → sub-portfolios).
- Closed accounts retained read-only.
- Per-account default currency; per-account opening balance.

### 5.2 Transaction management

- Manual entry with quick-add (date, payee, amount, category).
- Split transactions across multiple categories.
- Recurring/scheduled transactions with auto-post option.
- Transfers between own accounts (auto-detected when amounts match in opposite signs and dates are close, even cross-currency).
- Bulk edit, search with full-text + structured filters.
- Attachments (receipt PDFs/images), inline preview.
- Status workflow: `PENDING → CLEARED → RECONCILED`.

### 5.3 Statement import

Supported formats:
- **OFX / QFX** (most US banks, some BR brokers).
- **OFC**.
- **CSV** with mapping templates per institution (saved).
- **PDF** statements via `pdfplumber`; layout rules per institution; LLM fallback for unknown layouts.
- **Excel (XLSX)**.
- **Brazilian-specific:** Nota de Corretagem (B3 brokerage notes), extrato Itaú/Bradesco/BB/Nubank/Inter, CEI/B3 CSV.
- **US-specific:** Chase, BoA, Fidelity, Schwab, Vanguard CSV/OFX.

Import features:
- Idempotent imports (file hash + per-row external_id dedup).
- Preview screen showing diff (new / duplicate / modified).
- Auto-apply rules during import.
- Multi-file batch import with per-file account selection.
- Drag-and-drop into the GUI.

### 5.4 Reconciliation

- Manual reconciliation: select statement opening/closing balance and date range; tick off transactions until difference is zero.
- Statement-driven reconciliation: import statement → system auto-matches book transactions to statement lines.
- Match algorithm:
  1. Exact match: same date ± N days, same amount, same currency.
  2. Fuzzy match: amount tolerance for FX-converted entries, payee similarity (Levenshtein + token ratio).
  3. AI match: semantic similarity on description embeddings.
- Unmatched book transactions flagged; unmatched statement lines proposed as new transactions.
- One-click "accept all high-confidence matches".
- Audit trail of every match decision.
- Re-open and undo a closed reconciliation.

### 5.5 Categorization & rules

- Hierarchical categories with seed taxonomy in pt-BR and en-US.
- Per-rule priority and dry-run preview.
- Learn-from-history: when user re-categorizes, suggest creating/updating rule.
- AI-assisted suggestions for uncategorized transactions, batch-applied with confirmation.

### 5.6 Investment portfolio

- Real-time and EOD pricing per security.
- Position view: quantity, average cost (BRL and USD), market value, unrealized P/L, % of portfolio, daily change.
- Performance: TWR (time-weighted return) and MWR/IRR (money-weighted return), per account / per asset class / per currency, with arbitrary date ranges.
- Asset allocation by class, sector, geography, currency.
- Dividend / JCP / interest income tracking and projection.
- Cost-basis methods: FIFO (default), LIFO, Average — selectable per account, BR brokerage typically uses average.
- Corporate actions: splits, bonuses, mergers, ticker renames.
- Fixed-income tracking (Tesouro Direto, CDB, LCI/LCA): accrual curve, daily mark-to-market via Tesouro/B3 data.
- Crypto: optional, via CoinGecko adapter.
- Tax lot drill-down for capital-gains preparation.

### 5.7 Multi-currency

- Every account has a native currency; every transaction stores its native amount + currency.
- Reports support a **Reporting Currency** (BRL or USD, user-chosen, switchable).
- FX conversion uses:
  - Daily PTAX (BCB) for BRL-anchored conversions.
  - ECB / Yahoo for cross rates.
  - User-overridable rate per transaction (e.g., for remittance).
- Realized FX gain/loss tracking on currency conversions.
- Display rule: never auto-convert in the source-currency ledger view; only convert in reporting/dashboard views.

### 5.8 Reporting & dashboards

- Cash-flow (income vs. expenses) by month / quarter / year.
- Net worth over time (assets − liabilities), by currency and consolidated.
- Spending by category with drill-down.
- Budget vs. actual with variance alerts.
- Investment performance dashboard.
- Custom report builder (filter by account, category, tag, date, currency).
- Export to CSV, XLSX, PDF.
- BR tax helpers: annual position snapshot for IRPF "Bens e Direitos", IR on stock sales (DARF projections, monthly 20k BRL exemption tracking).
- US tax helpers: 1099-style summaries, wash-sale awareness flag.

### 5.9 Budgets & goals

- Envelope-style budgets per category and currency.
- Rollover option for unused amounts.
- Goal tracking with linked accounts and projected completion date.

### 5.10 AI hooks (pluggable)

Provider-agnostic `LLMProvider` interface (default: Azure OpenAI, matching `agents/Foundry-test`).

Built-in AI features:
- **Smart categorization** — embeddings-based similarity to historical transactions + LLM fallback.
- **Transaction enrichment** — clean merchant names, infer payee from raw description.
- **Cross-source correlation** — detect that a credit-card payment in one account corresponds to a debit in another; detect FX remittances across BR/US accounts.
- **Statement layout learning** — given an unknown PDF, ask the LLM to produce a parser template; persist for reuse.
- **Anomaly detection** — flag unusual spending, possible duplicates, possible fraud.
- **Natural-language query** — "Quanto gastei com restaurantes em São Paulo no último trimestre?" / "How did my US portfolio perform vs. SPY YTD?". Translates to SQL over a read-only view.
- **Monthly insights digest** — narrative summary with charts.
- **Receipt OCR + extraction** — attach a photo, extract vendor/amount/date, draft a transaction.

All AI calls are logged in `AIInteraction` with cost; user can disable AI globally or per-feature; offline mode supported.

---

## 6. Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| Performance | Open a 50k-transaction database in < 2 s; common queries < 200 ms. |
| Storage | SQLite file portable, < 200 MB for typical 10-year history. |
| Security | Optional database encryption via SQLCipher; OS keychain for API keys; no secrets in plaintext config. |
| Privacy | Local-first; AI calls opt-in per feature; redact account numbers before sending to LLM. |
| Reliability | All writes inside transactions; nightly auto-backup (rotating, configurable retention). |
| Portability | Runs on Windows, macOS, Linux. |
| Internationalization | UI strings in pt-BR and en-US, switchable; locale-aware number/date formatting. |
| Accessibility | Keyboard navigation, high-contrast theme, screen-reader labels on key views. |
| Observability | Structured logs, optional crash reports (opt-in). |
| Testing | ≥ 80% coverage on services layer; smoke tests on GUI. |

---

## 7. Security & Privacy

- Master password unlocks the database (PBKDF2 → SQLCipher key).
- API keys (market data, LLM) stored in OS keychain (`keyring` library).
- PII redaction layer applied before any outbound LLM call (mask account numbers, CPF, SSN).
- Audit log immutable (append-only; integrity hash chain).
- Optional auto-lock after idle.

---

## 8. UI / UX

### 8.1 Main views

1. **Dashboard** — net worth (consolidated + per currency), this-month cash flow, top categories, portfolio snapshot, alerts.
2. **Accounts sidebar** — grouped by institution and country; balances in native currency with reporting-currency tooltip.
3. **Transaction register** — Excel-like grid; inline edit; column chooser; saved filters.
4. **Reconciliation workspace** — split view: book vs. statement; match/unmatch buttons; running difference indicator.
5. **Portfolio view** — holdings table, allocation pie/treemap, performance chart, dividends calendar.
6. **Reports** — pre-built + custom builder.
7. **Budgets & Goals** — progress bars per envelope.
8. **Rules** — editor with test/preview against historical data.
9. **AI Assistant** — chat panel anchored side-drawer; can reference selected transactions.
10. **Settings** — currencies, FX sources, AI providers, backup, encryption.

### 8.2 UX principles

- Keyboard-first power-user shortcuts (Quicken-like: Ctrl+N new tx, Ctrl+R reconcile).
- Dark/light themes.
- Undo/redo for destructive operations.
- Confirmation only for irreversible actions; otherwise toast + undo.

---

## 9. Suggested Additional Features

Beyond the user's request, the following are typical and recommended:

- **Recurring transaction engine** with reminders.
- **Bill calendar** with due-date forecasting and projected balance.
- **Loan/mortgage amortization** tracking with principal/interest split per payment.
- **Credit-card cycle tracking** (statement close date, due date, available credit).
- **Refund/return matching** to original purchase.
- **Mileage / kilometers tracker** for tax-deductible vehicle use.
- **Receipts vault** with OCR.
- **Net-worth snapshots** taken automatically at month-end.
- **What-if scenarios** (e.g., "if I save R$ 2k/month at 12% a.a. for 5 years…").
- **Retirement projection** combining BR (Previdência, INSS) and US (401k, IRA) accounts.
- **Tax-lot harvesting suggestions**.
- **Bank-fee analyzer** highlighting recurring fees.
- **Subscription detector** identifying recurring SaaS/streaming charges.
- **Shared expense tracking** (split with spouse / roommate) without full multi-user.
- **CSV/JSON export** for everything (data portability).
- **Plugin API** so power users can add custom parsers/providers.
- **Mobile companion (read-only)** via a generated static dashboard or future React Native app — out of initial scope but architecture should not block it.

---

## 10. Roadmap (proposed phases)

### Phase 1 — Core ledger (MVP)
- Schema + migrations, SQLAlchemy models.
- Institutions, accounts, manual transactions, transfers, categories, payees, tags.
- Multi-currency storage and FX rate table (manual + BCB PTAX fetch).
- Basic dashboard, register grid, simple reports.
- SQLite encryption, backup.

### Phase 2 — Import & reconciliation
- OFX/QFX/CSV importers with mapping templates.
- Rule engine.
- Manual + statement-driven reconciliation with fuzzy matching.

### Phase 3 — Investments
- Securities, lots, investment transactions, price history.
- Portfolio view, performance metrics, dividends.
- BR fixed-income (Tesouro Direto) adapter.

### Phase 4 — AI features
- Embedding store (sqlite-vss or chromadb-local).
- Smart categorization, enrichment, anomaly detection.
- Natural-language query.
- PDF statement learning.

### Phase 5 — Polish & extras
- Budgets, goals, recurring engine.
- Tax helpers (BR IRPF, US 1099 summary).
- Plugin API, exports, additional locales.

---

## 11. Open Questions

1. Should the application support multiple **profiles/databases** (e.g., personal vs. family) from one install?
    No, each install is for a single person's finances
2. Preferred AI provider default — Azure OpenAI only, or also support local models via Ollama for offline?
    Also support local models
3. Is cloud sync (e.g., user-supplied OneDrive/Dropbox folder) acceptable as a Phase 5 feature, or strictly local-only?
    Yes, cloud sync via OneDrive, local folder, or Dropbox, and also a periodic backup function 
4. For BR brokerage, do we integrate directly with **B3 CEI/Investidor** (web scraping / no official API) or rely on user-uploaded notes?
    Rely on user-uploaded notes for now.
5. Required minimum Python version and OS targets for distribution?
    Windows 11, Linux Debian or Ubuntu latest available now

---

## 12. Repository conventions applied

- Python 3.11+, `from __future__ import annotations`, full PEP 484 type hints.
- `@dataclass` (or Pydantic models) for DTOs at service boundaries.
- Configuration via `.env` (never committed) loaded with `pydantic-settings`.
- UI strings primarily in **pt-BR** (with en-US toggle) per repo convention.
- Project lives under `agents/FinApp/` with its own `requirements.txt` and `README.md`.
