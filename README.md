# FinApp

Personal finance management application — multi-currency (BRL/USD focused), local-first, with AI hooks.

See [SPECIFICATION.md](./SPECIFICATION.md) for the full product specification.

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

```
agents/FinApp/
├── SPECIFICATION.md
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.template
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/finapp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py              # pydantic-settings
│   ├── logging_setup.py
│   ├── money.py               # Decimal/minor-unit helpers
│   ├── cli.py                 # typer CLI
│   ├── db/
│   │   ├── base.py            # DeclarativeBase
│   │   ├── engine.py          # engine + session factory
│   │   └── seed.py
│   ├── models/                # SQLAlchemy 2.x models
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── mixins.py
│   │   ├── institution.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── category.py
│   │   ├── payee.py
│   │   ├── tag.py
│   │   ├── rule.py
│   │   ├── budget.py
│   │   ├── goal.py
│   │   ├── currency.py
│   │   ├── investment.py
│   │   ├── reconciliation.py
│   │   ├── ai.py
│   │   └── audit.py
│   ├── services/              # business logic (pure Python, GUI-independent)
│   ├── integrations/          # parsers, market data, LLM providers
│   └── gui/                   # PySide6 application
└── tests/
```

## Conventions

- Python 3.11+, `from __future__ import annotations`, full PEP 484 type hints.
- Money stored as `(amount_minor: INTEGER, currency: TEXT)`; never floats.
- UI strings primarily in pt-BR (en-US toggle planned).
- Azure OpenAI via the same env vars as `agents/Foundry-test`.
