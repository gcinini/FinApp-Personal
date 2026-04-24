"""FinApp command-line interface."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from finapp.config import get_settings
from finapp.db.base import Base
from finapp.db.engine import get_engine, session_scope
from finapp.db.seed import seed_all
from finapp.logging_setup import configure_logging
from finapp.models import Account, Institution  # noqa: F401  (register tables)
from finapp.services.import_service import ImportService

app = typer.Typer(help="FinApp — personal finance CLI", no_args_is_help=True)
db_app = typer.Typer(help="Database utilities")
import_app = typer.Typer(help="Statement import utilities")
app.add_typer(db_app, name="db")
app.add_typer(import_app, name="import")

console = Console()


@app.callback()
def _root() -> None:
    configure_logging(get_settings().log_level)


@db_app.command("init")
def db_init() -> None:
    """Create the SQLite file and all tables (no migrations yet)."""
    # Importing finapp.models registers all tables on Base.metadata.
    import finapp.models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(engine)
    console.print(f"[green]Database initialized at[/green] {get_settings().db_path}")


@db_app.command("seed")
def db_seed() -> None:
    """Insert default currencies, categories, and known institutions."""
    with session_scope() as s:
        seed_all(s)
    console.print("[green]Seed data inserted.[/green]")


@db_app.command("accounts")
def db_accounts() -> None:
    """List configured accounts."""
    with session_scope() as s:
        rows = s.query(Account).all()
        table = Table("ID", "Institution", "Name", "Type", "Currency")
        for a in rows:
            table.add_row(
                str(a.id),
                a.institution.name if a.institution else "-",
                a.name,
                a.account_type.value if hasattr(a.account_type, "value") else str(a.account_type),
                a.currency,
            )
        console.print(table)


@import_app.command("file")
def import_file(
    path: Path = typer.Argument(..., exists=True, readable=True),
    account_id: int = typer.Option(..., "--account", "-a"),
    template: Path | None = typer.Option(
        None, "--template", "-t", help="Optional JSON template (CSV/PDF mapping)."
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Import an OFX/CSV/PDF/QFX statement into the given account."""
    import json

    tpl = json.loads(template.read_text(encoding="utf-8")) if template else None
    with session_scope() as s:
        result = ImportService(s).import_file(path, account_id, template=tpl, dry_run=dry_run)
    console.print(result)


@app.command("gui")
def gui() -> None:
    """Launch the PySide6 GUI."""
    from finapp.gui.app import main

    main()


if __name__ == "__main__":
    app()
