# FinApp

Personal finance management application — multi-currency (BRL/USD focused), local-first, with AI hooks.

See [SPECIFICATION.md](./SPECIFICATION.md) for the full product specification, [ARCHITECTURE.md](./ARCHITECTURE.md) for a per-file tour of the codebase, and [PROJECT_STATUS.md](./PROJECT_STATUS.md) for current implementation status.

## Setup

```powershell
cd agents/FinApp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

Copy-Item .env.template .env
# edit .env and fill in values
```

## Initialize the database

```powershell
finapp db init                 # create SQLite file + run migrations
finapp db seed                 # load default currencies, categories, institutions
```

## Run

```powershell
finapp-gui                     # launch PySide6 GUI
finapp --help                  # CLI utilities (import, reconcile, export, etc.)
```

## Project layout

See [ARCHITECTURE.md](./ARCHITECTURE.md) for a complete file-by-file guide. High-level structure:

```
FinApp-Personal/
├── SPECIFICATION.md       # what the product should be
├── ARCHITECTURE.md        # per-file tour of the codebase
├── PROJECT_STATUS.md      # implementation progress
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.template
├── alembic.ini
├── alembic/
├── data/                  # default SQLite location
├── src/finapp/
│   ├── config.py          # pydantic-settings
│   ├── logging_setup.py   # structlog
│   ├── money.py           # Decimal/minor-unit helpers
│   ├── cli.py             # typer CLI
│   ├── db/                # engine, base, seed
│   ├── models/            # SQLAlchemy 2.x ORM models
│   ├── services/          # business logic + DTOs (GUI-independent)
│   ├── integrations/      # parsers (CSV/OFX/PDF), market data, FX, LLM
│   └── gui/               # PySide6 — app, panels/, dialogs/
└── tests/
```

## Conventions

- Python 3.11+, `from __future__ import annotations`, full PEP 484 type hints.
- Money stored as `(amount_minor: INTEGER, currency: TEXT)`; never floats.
- UI strings primarily in pt-BR (en-US toggle planned).
- Azure OpenAI via the same env vars as `agents/Foundry-test`.
