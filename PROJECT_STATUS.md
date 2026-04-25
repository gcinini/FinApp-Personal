# FinApp — Project Status

_Last updated: 2026-04-24 (PM)_

This document tracks implementation progress against [SPECIFICATION.md](./SPECIFICATION.md). It complements the roadmap in §10 of the spec with concrete file-level status.

Legend: ✅ Done · 🟡 Partial / scaffolded · ⛔ Not started

---

## 1. Snapshot

| Area | Status | Notes |
|------|--------|-------|
| Project skeleton | ✅ | `src/finapp/` package, `pyproject.toml`, `requirements.txt`, `.env.template`, `.gitignore`, `README.md` |
| Configuration & logging | ✅ | `config.py` (pydantic-settings), `logging_setup.py` (structlog) |
| Money / Decimal helpers | ✅ | `money.py` with minor-units conversion + currency-specific decimals |
| SQLite engine + session | ✅ | `db/engine.py` with WAL, foreign-keys pragma, session_scope |
| SQLAlchemy 2.x schema | ✅ | All entities from spec §4 modeled (see §3 below) |
| Seed data | ✅ | Default currencies (BRL/USD/EUR/GBP/JPY), pt-BR categories, BR+US institutions |
| Alembic | 🟡 | `alembic.ini` + `env.py` + template ready; **first revision not yet generated** |
| Statement parsers — CSV | ✅ | Template-driven, end-to-end tested |
| Statement parsers — PDF | 🟡 | Template-driven (regex + table) implemented; **AI fallback is a stub** |
| Statement parsers — OFX/QFX | 🟡 | Implemented but **untested** (needs sample file) |
| Statement parsers — XLSX, QIF, OFC | ⛔ | Not started |
| Import service | ✅ | File-hash + per-row external_id dedup; ties to `StatementImport` batch; tested |
| Reconciliation service | 🟡 | Exact + fuzzy (rapidfuzz); **AI matching not started**; **no GUI workspace yet** |
| Account / transaction services | 🟡 | Create + DTO-based query methods (list/summary/balance/recent/categories) + tx update/delete with status guards; no transfer/split/recurring yet |
| Service DTO layer | ✅ | `services/dto.py` — frozen dataclasses (InstitutionSummary, AccountSummary, TransactionRow, CurrencyBalance, CategoryItem) keep GUI detached from ORM |
| Market data adapter | 🟡 | `YahooMarketData` implemented; **not wired into a service** |
| FX adapter (BCB PTAX) | 🟡 | Implemented; **no scheduled fetch / FxRate persistence service** |
| LLM provider (Azure OpenAI) | 🟡 | Implemented; **no local-model (Ollama) provider** (per Q11.2) |
| CLI (Typer) | ✅ | `db init`, `db seed`, `db accounts`, `import file`, `gui` |
| GUI (PySide6) | 🟡 | Dark theme + 3 functional panels: **Dashboard** (net worth by currency, account balances, recent txns), **Contas** (institution/account tree + detail + add dialogs), **Transações** (QTableView register + filters + add dialog). Reconciliação/Portfólio/Relatórios/IA still placeholders |
| Tests | 🟡 | 6 passing (money, account service, CSV import); coverage ≪ 80% target |
| Backups / cloud sync | ⛔ | Not started (per Q11.3 — OneDrive/Dropbox/local folder + periodic backup) |
| SQLCipher encryption | ⛔ | Optional dep listed; not wired into engine |
| OS keychain (`keyring`) | ⛔ | Listed in `requirements.txt`; not used yet |
| PII redaction for LLM calls | ⛔ | Not implemented |
| Audit log writer | 🟡 | Table modeled; no service writing into it yet |
| Packaging (PyInstaller) | ⛔ | Not started — Windows 11 + Debian/Ubuntu targets per Q11.5 |
| i18n (pt-BR / en-US toggle) | ⛔ | Strings hardcoded in pt-BR; no translation framework wired |

---

## 2. Decisions captured (from spec §11)

| # | Question | Decision | Implementation impact |
|---|----------|----------|----------------------|
| 1 | Multiple profiles per install? | **No — single user per install** | Simplifies config; no `User` table needed. |
| 2 | LLM provider | **Azure OpenAI + local models (Ollama)** | Need second `LLMProvider` implementation: `OllamaProvider`. Settings switch in `config.py`. |
| 3 | Cloud sync | **Yes — OneDrive / Dropbox / local folder + periodic backup** | New `BackupService`; settings for sync target, frequency, retention. |
| 4 | BR brokerage integration | **User-uploaded notes only (no scraping)** | Defer B3/CEI scraping; focus on CSV + PDF parsers for nota de corretagem. |
| 5 | OS targets | **Windows 11, latest Debian/Ubuntu, Python 3.11+** | PyInstaller spec for Win11; AppImage or `.deb` for Linux; CI matrix to add. |

---

## 3. Schema completeness vs. spec §4

| Spec entity | Model file | Status |
|-------------|-----------|--------|
| Institution | [account.py](./src/finapp/models/account.py) | ✅ |
| Account, AccountHolder | [account.py](./src/finapp/models/account.py) | ✅ |
| Transaction, TransactionSplit, Transfer | [transaction.py](./src/finapp/models/transaction.py) | ✅ |
| Category, Payee, Tag, Rule | [category.py](./src/finapp/models/category.py) | ✅ |
| Budget, Goal | [budget.py](./src/finapp/models/budget.py) | ✅ |
| Currency, FxRate | [currency.py](./src/finapp/models/currency.py) | ✅ |
| Security, Lot, InvestmentTransaction, PriceHistory, CorporateAction | [investment.py](./src/finapp/models/investment.py) | ✅ |
| StatementImport, ParserTemplate, ReconciliationSession, ReconciliationMatch | [reconciliation.py](./src/finapp/models/reconciliation.py) | ✅ |
| AIInteraction, AuditLog | [ai.py](./src/finapp/models/ai.py) | ✅ |
| `ExchangeOperation` (BRL↔USD remittance with IOF + spread) | — | ⛔ Not modeled yet |
| `Attachment` (separate table; currently inline `attachment_path` field) | — | 🟡 Inline field only |
| `Holding` (denormalized view) | — | ⛔ Will be a SQL view / computed |
| Recurring / scheduled transaction definition | — | ⛔ Not started |
| Backup metadata (target, schedule, last status) | — | ⛔ Not started |

---

## 4. Roadmap progress (spec §10)

### Phase 1 — Core ledger (MVP) — **~80 %**

- [x] Schema + SQLAlchemy models
- [x] Institutions, accounts, manual transactions (basic create)
- [x] Multi-currency storage; `FxRate` table; BCB PTAX adapter
- [x] Basic dashboard widgets (net worth by currency, account balances, recent transactions)
- [x] Register grid in GUI (QTableView + QAbstractTableModel with status/account filters)
- [x] Transaction edit / delete (services with reconciled/imported guards; no GUI yet)
- [ ] **Alembic first revision generated**
- [ ] Transfer creation/editing UX (cross-currency)
- [ ] Transaction search / bulk-edit (GUI)
- [ ] Splits CRUD
- [ ] Cash-flow dashboard widget
- [ ] SQLite encryption (SQLCipher) toggle
- [ ] Backup engine (local folder / OneDrive / Dropbox)

### Phase 2 — Import & reconciliation — **~40 %**

- [x] CSV importer with template support
- [x] PDF importer (template mode)
- [x] OFX/QFX importer (untested)
- [x] Idempotent import (file hash + external_id)
- [x] Reconciliation matching engine (exact + fuzzy)
- [ ] Rule engine (apply during import + retro-apply)
- [ ] Import preview screen (new / duplicate / modified diff)
- [ ] Drag-and-drop into GUI
- [ ] Multi-file batch import
- [ ] Reconciliation workspace (split view, accept-all)
- [ ] Re-open / undo closed reconciliations

### Phase 3 — Investments — **~10 %**

- [x] Securities, lots, investment transactions, price history (schema only)
- [ ] PortfolioService (positions, cost basis FIFO/LIFO/Avg)
- [ ] Performance metrics (TWR, MWR/IRR)
- [ ] Dividends/JCP tracking & projection
- [ ] Asset-allocation views
- [ ] Tesouro Direto / CDB / LCI / LCA accrual curves
- [ ] Crypto adapter (CoinGecko)
- [ ] Corporate actions automation

### Phase 4 — AI features — **~5 %**

- [x] `LLMProvider` interface + Azure OpenAI implementation
- [ ] Ollama provider (per Q11.2)
- [ ] Embedding store (sqlite-vss or chromadb-local)
- [ ] PII redaction layer
- [ ] Smart categorization service
- [ ] Transaction enrichment service
- [ ] Cross-source correlation
- [ ] Anomaly detection
- [ ] Natural-language → SQL query
- [ ] PDF layout learning (concrete impl of `_parse_with_ai_fallback`)
- [ ] AIInteraction logging + cost tracking

### Phase 5 — Polish & extras — **0 %**

- [ ] Budgets/Goals services + UI
- [ ] Recurring transaction engine + reminders
- [ ] Bill calendar
- [ ] Loan amortization
- [ ] Credit-card cycle tracking
- [ ] BR IRPF "Bens e Direitos" / DARF helpers
- [ ] US 1099 / wash-sale helpers
- [ ] Plugin API
- [ ] Exports (CSV/XLSX/PDF)
- [ ] en-US locale toggle
- [ ] Subscription detector, refund matcher, bank-fee analyzer

---

## 5. Quality & ops

| Area | Status | Target |
|------|--------|--------|
| Unit tests | 6 passing | ≥ 80 % services coverage |
| GUI tests (`pytest-qt`) | 0 | Smoke tests on each panel |
| Lint (`ruff`) | Configured, not enforced | CI gate |
| Types (`mypy --strict`) | Configured, not run | CI gate |
| CI/CD | None | GitHub Actions: lint → test → package (Win + Linux) |
| Crash reporting | None | Opt-in (Phase 5) |
| Performance benchmark | None | 50k transactions < 2 s (spec §6) |

---

## 6. Immediate next steps (recommended order)

1. `alembic revision --autogenerate -m "initial schema"` and commit the first migration.
2. Wire transaction **edit/delete** into the Transações panel (services already exist).
3. GUI smoke tests with `pytest-qt` for the three new panels.
4. `OllamaProvider` + provider switch in `config.py` (decision Q11.2).
5. Backup/sync service skeleton (decision Q11.3): local folder rotation first, then OneDrive/Dropbox via their official desktop sync (we just write into the synced folder).
6. Rule engine + auto-apply during `ImportService`.
7. Reconciliation workspace UI (split view, accept-all).
8. PortfolioService — positions and cost basis (Phase 3 kickoff).
9. CI workflow (lint + test) and PyInstaller spec for Windows 11 + Linux.

### Recently shipped (2026-04-24)

- **GUI panels (Dashboard / Contas / Transações)** — fully functional, dark theme, modular `gui/panels/` + `gui/dialogs/` structure.
- **Service DTO layer** — frozen dataclasses; GUI never touches ORM directly (per spec §3.1).
- **AccountService queries** — `list_institution_summaries`, `list_account_summaries`, `net_worth_by_currency` (balances computed in SQL).
- **TransactionService queries + mutations** — `list_transactions` (account/status/date filters), `get_recent`, `list_categories`, `update` and `delete` with reconciled/imported guards.

---

## 7. Known gaps / risks

- **PDF AI fallback** is a stub — first real Itaú/Nubank/Bradesco PDF will require a regex template before the LLM path is usable.
- **Cross-currency transfer auto-detection** logic exists in the schema (`Transfer`, `transfer_pair_id`) but no service implements detection yet.
- **Audit log** table exists but nothing writes to it; need a SQLAlchemy event listener layer.
- **Encryption** (SQLCipher) is listed as an optional dep; switching it on requires a different SQLAlchemy URL and key handling via `keyring`.
- **i18n**: all current GUI strings are hardcoded pt-BR; introducing `babel` translations should happen before more views are added.
- **Python 3.14** is installed locally — make sure CI pins to 3.11/3.12 to match the supported floor.
