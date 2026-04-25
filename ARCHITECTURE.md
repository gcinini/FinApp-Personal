# FinApp — Architecture & File Guide

_Last updated: 2026-04-24_

This document is a tour of the codebase, file by file. It complements:

- [SPECIFICATION.md](./SPECIFICATION.md) — what the product should do.
- [PROJECT_STATUS.md](./PROJECT_STATUS.md) — what is currently implemented.

---

## 1. Bird's-eye view

```
┌──────────────────────────────────────────────────────────────┐
│  GUI (PySide6)                                               │
│  src/finapp/gui/{app, panels, dialogs}                       │
└──────────────┬───────────────────────────────────────────────┘
               │ calls service methods, receives DTOs
┌──────────────▼───────────────────────────────────────────────┐
│  Services (pure Python, no Qt)                               │
│  src/finapp/services/{account, import, reconciliation}       │
│  Returns DTOs from src/finapp/services/dto.py                │
└──────────────┬───────────────────────────────────────────────┘
               │ uses session_scope() per operation
┌──────────────▼───────────────────────────────────────────────┐
│  ORM models (SQLAlchemy 2.x)                                 │
│  src/finapp/models/                                          │
└──────────────┬───────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────┐
│  DB engine + session factory                                 │
│  src/finapp/db/{base, engine, seed}                          │
└──────────────┬───────────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │  SQLite DB  │  data/finapp.sqlite (WAL mode)
        └─────────────┘

External integrations (independent of GUI/services flow):
  src/finapp/integrations/{fx, llm, market_data, parsers/}
```

**Hard rules** (from [SPECIFICATION.md §3.1](./SPECIFICATION.md)):
1. The GUI never touches the ORM directly — only Services.
2. Services return **DTOs** (frozen dataclasses), never live ORM objects, so the GUI is safe from SQLAlchemy lazy-loading on closed sessions.
3. Money is always stored as `(amount_minor: INTEGER, currency: TEXT)` — never floats.
4. Each service method opens its own `session_scope()`; sessions are short-lived.

---

## 2. Top-level files

| File | Purpose |
|------|---------|
| `SPECIFICATION.md` | The full product spec (what FinApp is supposed to be). |
| `PROJECT_STATUS.md` | Implementation status against the spec, per area and per phase. |
| `ARCHITECTURE.md` | **This file.** Per-module guide for newcomers. |
| `README.md` | Setup + run instructions. |
| `pyproject.toml` | Build config, package metadata, console scripts. |
| `requirements.txt` | Pinned dependencies (SQLAlchemy, PySide6, pydantic, etc.). |
| `alembic.ini` + `alembic/` | Schema migration tooling. **First revision not yet generated.** |
| `.env.template` | Template for environment variables (DB path, AI keys, etc.). |
| `data/` | Default location of the SQLite database file. |
| `tests/` | Pytest suite. |

---

## 3. The `finapp` package

### 3.1 Package roots

| File | What it does |
|------|---------------|
| `src/finapp/__init__.py` | Package marker; exposes `__version__ = "0.1.0"`. |
| `src/finapp/__main__.py` | Entry point so `python -m finapp` runs the Typer CLI. |
| `src/finapp/config.py` | `Settings` (pydantic-settings) loaded from `.env`. Holds DB path, FX/market/AI provider choices, locale, log level. Singleton via `get_settings()`. |
| `src/finapp/logging_setup.py` | structlog configuration (ISO timestamps, level filtering). Provides `get_logger()`. |
| `src/finapp/money.py` | **Critical helper.** `to_minor()`/`from_minor()` convert Decimal ↔ integer minor units using banker's rounding; `decimals_for()` knows JPY=0, BHD=3, etc.; `Money` dataclass for typed amounts. |
| `src/finapp/cli.py` | Typer-based CLI. Subcommands: `db init`, `db seed`, `db accounts`, `import file`, `gui`. Uses `session_scope()` and rich tables. |

### 3.2 Database layer (`finapp/db/`)

| File | What it does |
|------|---------------|
| `db/base.py` | `class Base(DeclarativeBase)` — root for all ORM models. |
| `db/engine.py` | Lazy-singleton `get_engine()` (SQLite + WAL + foreign-keys pragma) and `get_sessionmaker()`. **`session_scope()` context manager** is the canonical way to do transactional work: commits on success, rolls back on exception, always closes. `expire_on_commit=False` so attributes stay readable after commit. |
| `db/seed.py` | `seed_all(session)` inserts the 5 default currencies, 14 pt-BR categories, and 15 BR/US institutions if absent (idempotent). |

### 3.3 Domain models (`finapp/models/`)

All model files use SQLAlchemy 2.x typed `Mapped[...]` columns and inherit `TimestampMixin` for `created_at`/`updated_at`.

| File | Models | Purpose |
|------|--------|---------|
| `models/__init__.py` | — | Re-exports every model so `Base.metadata` knows about all tables. |
| `models/enums.py` | InstitutionType, AccountType, TransactionStatus, TransactionSource, SecurityType, InvestmentTxType, CostBasisMethod, ReconciliationStatus, MatchType, RuleMatchType, FxSource | All Python enums used as typed columns across the schema. |
| `models/mixins.py` | TimestampMixin | Auto-managed `created_at` (server default `now()`) and `updated_at` (auto-touched on update). |
| `models/account.py` | **Institution**, **Account**, **AccountHolder** | A bank/brokerage and the accounts inside it. Account stores `opening_balance_minor` + `currency`. |
| `models/transaction.py` | **Transaction**, **TransactionSplit**, **Transfer** | The core ledger entry plus support for multi-category splits and cross-account/cross-currency transfers (`fx_rate`, `fees_minor`). |
| `models/category.py` | **Category**, **Payee**, **Tag**, **Rule**, `transaction_tag` | Hierarchical categories (self-referential), payees with aliases, free-form tags (M:N to transactions), and auto-categorization rules. |
| `models/currency.py` | **Currency**, **FxRate** | ISO 4217 currencies and dated FX-rate snapshots (unique per date+pair+source). |
| `models/budget.py` | **Budget**, **Goal** | Spending envelopes (per category, period, currency, with optional rollover) and savings/investment goals. |
| `models/investment.py` | **Security**, **Lot**, **InvestmentTransaction**, **PriceHistory**, **CorporateAction** | Securities universe + per-account holdings (lots), trades (BUY/SELL/DIVIDEND/JCP/SPLIT/…), price history (unique per security+date), and corporate actions. |
| `models/reconciliation.py` | **StatementImport**, **ParserTemplate**, **ReconciliationSession**, **ReconciliationMatch** | Batch metadata for an imported statement file (file_hash for dedup), reusable parser configs, reconciliation sessions, and per-match decisions. |
| `models/ai.py` | **AIInteraction**, **AuditLog** | Records every LLM call (prompt, response, tokens, cost) and every domain mutation (with optional integrity hash chain). |

### 3.4 Service layer (`finapp/services/`)

Pure Python, no Qt imports, fully unit-testable. **All read methods return DTOs from `dto.py`.** Mutations may return ORM objects internally for the caller within the same `session_scope()`.

| File | What it does |
|------|---------------|
| `services/__init__.py` | Package marker. |
| `services/dto.py` | **Frozen dataclasses** the GUI consumes: `InstitutionSummary`, `AccountSummary`, `TransactionRow`, `CategoryItem`, `CurrencyBalance`. These are session-detached and safe to pass anywhere. |
| `services/account_service.py` | **`AccountService`** — `create_institution`, `create_account`, `list_institution_summaries`, `list_account_summaries` (with computed balance via `opening_balance + SUM(tx)`), `net_worth_by_currency`. **`TransactionService`** — `add`, `update` (sentinel-protected for nullable fields, blocks edits on RECONCILED), `delete` (blocks if RECONCILED or imported), `list_transactions` (account/status/date filters), `get_recent`, `list_categories`. |
| `services/import_service.py` | `ImportService.import_file(path, account_id, …)` — picks parser, hashes file for dedup, dedups rows by `external_id`, persists `Transaction` rows with `source=IMPORT_*` and `status=CLEARED`. Supports `dry_run`. Returns `{created, duplicates, import_id}`. |
| `services/reconciliation_service.py` | `ReconciliationService.open_session`, `propose_matches` (exact + fuzzy via rapidfuzz token-set ratio + date proximity, score threshold 0.6), `commit_matches` (writes `ReconciliationMatch` rows and flips `Transaction.status` to RECONCILED). |

### 3.5 Integrations (`finapp/integrations/`)

External-facing adapters. All expose abstract interfaces so the rest of the app stays provider-agnostic.

| File | What it does |
|------|---------------|
| `integrations/__init__.py` | Package marker. |
| `integrations/fx.py` | `FxProvider` interface + `BcbPtaxProvider` (Banco Central do Brasil PTAX endpoint) for BRL↔USD daily rates. Not yet wired to a service that persists into `FxRate`. |
| `integrations/llm.py` | `LLMProvider` interface + `AzureOpenAIProvider` (`complete()`, `complete_json()`) with token/cost tracking. **No Ollama provider yet** (decision Q11.2 still pending implementation). |
| `integrations/market_data.py` | `MarketDataProvider` interface + `YahooMarketData` (yfinance) for current quotes and historical OHLCV. Not yet wired to a `PortfolioService`. |
| `integrations/parsers/__init__.py` | Re-exports the registry; importing it side-loads CSV/OFX/PDF parsers so they auto-register. |
| `integrations/parsers/base.py` | `ParsedTransaction` and `ParsedStatement` dataclasses, abstract `StatementParser`, and a registry: `@register("CSV")` decorator + `detect_parser(path)` to pick a parser by file extension/content. |
| `integrations/parsers/csv_parser.py` | Template-driven CSV parser. Templates configure column mapping (date, debit, credit, etc.), date format, decimal separator. Auto-detects encoding (chardet) and emits a row hash for `external_id`. |
| `integrations/parsers/ofx_parser.py` | OFX/QFX parser via `ofxparse`. Extracts transactions, account hint, closing balance. **Implemented but untested** (no sample file in repo yet). |
| `integrations/parsers/pdf_parser.py` | Template-driven PDF parser via `pdfplumber`, supporting regex and table-extraction modes. AI-fallback (`_parse_with_ai_fallback`) is currently a **stub** — needs wiring to `LLMProvider` for unknown layouts. |

### 3.6 GUI layer (`finapp/gui/`)

PySide6 (Qt 6). The GUI never touches the ORM — only services + DTOs.

| File | What it does |
|------|---------------|
| `gui/app.py` | `main()` builds `QApplication`, applies the dark stylesheet (`_DARK_STYLESHEET`), assembles the `QMainWindow` with a `QTabWidget`. Tabs: **Dashboard**, **Contas**, **Transações** (functional) plus Reconciliação/Portfólio/Relatórios/IA placeholders. |
| `gui/__init__.py` | Package marker. |

#### Panels (`finapp/gui/panels/`)

| File | What it does |
|------|---------------|
| `panels/dashboard.py` | **`DashboardPanel`** — three sections: net-worth cards per currency, scrollable account-balance list, scrollable recent-transactions list (last 15). Refreshes on every `showEvent`. Uses `_clear_layout()` helper to repopulate without leaks. |
| `panels/accounts.py` | **`AccountsPanel`** — `QSplitter` with a `QTreeWidget` (institutions → accounts) on the left and a `QFormLayout` detail panel on the right. Toolbar buttons open `AddInstitutionDialog` / `AddAccountDialog`. Selection is preserved by storing `("institution"\|"account", id)` in `Qt.UserRole`. |
| `panels/transactions.py` | **`TransactionsPanel`** + **`TransactionTableModel`** (`QAbstractTableModel`). Columns: Data, Descrição, Categoria, Valor, Status. Account dropdown + status filter at top, "+ Nova Transação" and "⟳ Atualizar" buttons. Color-codes amounts (green/red) via `ForegroundRole`. |
| `panels/__init__.py` | Package marker. |

#### Dialogs (`finapp/gui/dialogs/`)

All dialogs validate input and expose `get_data()` returning a dict ready to spread into the matching service method. They store enum/IDs in `QComboBox.itemData`, never the display string.

| File | What it does |
|------|---------------|
| `dialogs/institution_dialog.py` | **`AddInstitutionDialog`** — name + country (BR/US) + InstitutionType. |
| `dialogs/account_dialog.py` | **`AddAccountDialog`** — institution dropdown, name, AccountType, currency, opening balance (Decimal-validated), opening date. Optional `preselect_institution_id`. |
| `dialogs/transaction_dialog.py` | **`AddTransactionDialog`** — account dropdown (currency derived from selected account), date, amount (negative = expense), description, category, memo. Optional `preselect_account_id`. |
| `dialogs/__init__.py` | Package marker. |

---

## 4. Tests (`tests/`)

| File | What it does |
|------|---------------|
| `tests/conftest.py` | Pytest fixture providing an **in-memory SQLite session** with all ORM tables created. Each test gets a clean DB. |
| `tests/test_money.py` | Unit tests for `to_minor`/`from_minor`/`Money` — including JPY (0 decimals) and round-trips. |
| `tests/test_account_service.py` | Verifies `seed_all`, `create_institution`, `create_account` wiring. |
| `tests/test_csv_import.py` | End-to-end: parser auto-detection + `ImportService.import_file` + idempotency on re-import. |

Run them with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ -x -q --tb=short
```

---

## 5. How a typical operation flows

### Adding a transaction from the GUI

1. User clicks "+ Nova Transação" in `TransactionsPanel`.
2. Panel queries the latest accounts/categories via `session_scope()` → DTOs.
3. `AddTransactionDialog` is shown, user fills the form, clicks OK.
4. `dlg.get_data()` returns a plain dict.
5. Panel opens a fresh `session_scope()`, calls `TransactionService(s).add(**data)`.
6. The context manager commits; panel calls `_reload_transactions()`.
7. `TransactionService.list_transactions()` runs a SQL query joining Account/Category/Currency, returning `TransactionRow` DTOs.
8. `TransactionTableModel.set_data(rows)` triggers a `beginResetModel` / `endResetModel`; the `QTableView` repaints.

### Importing a statement (CLI today, GUI later)

1. `finapp import file path/to/extrato.csv -a 1`
2. `ImportService.import_file(path, account_id=1)`:
   - Hashes the file → checks `StatementImport.file_hash` for prior import.
   - `detect_parser(path)` returns the matching `StatementParser`.
   - Parser yields `ParsedTransaction`s.
   - For each row, dedup by `(account_id, external_id)`, insert as `Transaction` with `source=IMPORT_CSV` / `status=CLEARED`.
3. Returns `{created, duplicates, import_id}`.

---

## 6. Where to add new things

| Goal | Where it goes |
|------|---------------|
| New domain field/table | `models/<area>.py` + register in `models/__init__.py` + Alembic revision |
| New business rule / aggregation | New method on the relevant service, returning a DTO from `services/dto.py` |
| New screen | `gui/panels/<name>.py` + register the tab in `gui/app.py` |
| New input form | `gui/dialogs/<name>_dialog.py`, expose `get_data() -> dict` |
| New statement format | `integrations/parsers/<format>_parser.py` + `@register("FMT")` |
| New AI feature | New method on `LLMProvider` consumers in services; log into `AIInteraction` |
| New external data source | `integrations/<thing>.py` with an interface + concrete provider, switchable in `config.py` |

---

## 7. Conventions worth knowing

- **Python 3.11+**, `from __future__ import annotations` everywhere, full type hints.
- **Money never as float.** Always go through `money.to_minor()`/`from_minor()`.
- **Sessions are short-lived.** Use `with session_scope() as s:` per operation; never hold a session across a UI event loop tick.
- **Services return DTOs to the GUI.** Never expose ORM objects past the service boundary.
- **Enums in DB columns.** Stored as their string `.value`; access via `.value` in DTO conversion.
- **UI strings are pt-BR** (i18n is planned but not wired).
- **Dark theme** is the only theme today; controlled by `gui/app.py:_DARK_STYLESHEET`.
