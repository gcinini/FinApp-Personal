"""Dashboard panel — net worth by currency, account balances, recent transactions."""
from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finapp.db.engine import session_scope
from finapp.money import from_minor
from finapp.services.account_service import AccountService, TransactionService
from finapp.services.dto import AccountSummary, CurrencyBalance, TransactionRow


def _fmt_money(minor: int, currency: str, symbol: str, decimals: int = 2) -> str:
    value = from_minor(minor, currency)
    sign = "-" if value < 0 else ""
    abs_val = abs(value)
    formatted = f"{abs_val:,.{decimals}f}"
    return f"{sign}{symbol} {formatted}"


class DashboardPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Net worth section
        self._net_worth_box = QGroupBox("Patrimônio Líquido")
        self._net_worth_box.setFont(QFont("Segoe UI", 11))
        self._net_worth_layout = QHBoxLayout(self._net_worth_box)
        self._net_worth_layout.setSpacing(24)
        layout.addWidget(self._net_worth_box)

        # Two-column area
        columns = QHBoxLayout()
        columns.setSpacing(16)

        # Left: account balances
        self._accounts_box = QGroupBox("Saldos das Contas")
        self._accounts_box.setFont(QFont("Segoe UI", 11))
        self._accounts_layout = QVBoxLayout(self._accounts_box)

        accounts_scroll = QScrollArea()
        accounts_scroll.setWidgetResizable(True)
        accounts_scroll.setWidget(self._accounts_box)
        accounts_scroll.setFrameShape(QFrame.Shape.NoFrame)
        columns.addWidget(accounts_scroll, stretch=1)

        # Right: recent transactions
        self._recent_box = QGroupBox("Transações Recentes")
        self._recent_box.setFont(QFont("Segoe UI", 11))
        self._recent_layout = QVBoxLayout(self._recent_box)

        recent_scroll = QScrollArea()
        recent_scroll.setWidgetResizable(True)
        recent_scroll.setWidget(self._recent_box)
        recent_scroll.setFrameShape(QFrame.Shape.NoFrame)
        columns.addWidget(recent_scroll, stretch=1)

        layout.addLayout(columns, stretch=1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        try:
            with session_scope() as s:
                acct_svc = AccountService(s)
                tx_svc = TransactionService(s)
                balances = acct_svc.net_worth_by_currency()
                accounts = acct_svc.list_account_summaries(active_only=True)
                recent = tx_svc.get_recent(limit=15)
        except Exception:
            return

        self._populate_net_worth(balances)
        self._populate_accounts(accounts)
        self._populate_recent(recent)

    def _populate_net_worth(self, balances: list[CurrencyBalance]) -> None:
        self._clear_layout(self._net_worth_layout)
        if not balances:
            self._net_worth_layout.addWidget(QLabel("Nenhuma conta cadastrada"))
            return
        for b in balances:
            card = self._currency_card(b)
            self._net_worth_layout.addWidget(card)
        self._net_worth_layout.addStretch()

    def _currency_card(self, b: CurrencyBalance) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background: #1e293b; border-radius: 8px; padding: 12px; }"
        )
        frame.setMinimumWidth(180)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(12, 8, 12, 8)

        cur_label = QLabel(b.currency)
        cur_label.setFont(QFont("Segoe UI", 10))
        cur_label.setStyleSheet("color: #94a3b8;")
        vbox.addWidget(cur_label)

        amount_text = _fmt_money(b.total_minor, b.currency, b.symbol, b.decimal_places)
        amount_label = QLabel(amount_text)
        amount_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        color = "#4ade80" if b.total_minor >= 0 else "#f87171"
        amount_label.setStyleSheet(f"color: {color};")
        vbox.addWidget(amount_label)

        return frame

    def _populate_accounts(self, accounts: list[AccountSummary]) -> None:
        self._clear_layout(self._accounts_layout)
        if not accounts:
            self._accounts_layout.addWidget(QLabel("Nenhuma conta cadastrada"))
            self._accounts_layout.addStretch()
            return
        for a in accounts:
            row = QHBoxLayout()
            name_lbl = QLabel(f"{a.institution_name} — {a.name}")
            name_lbl.setFont(QFont("Segoe UI", 10))
            name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row.addWidget(name_lbl)

            bal_text = _fmt_money(a.balance_minor, a.currency, a.currency_symbol)
            bal_lbl = QLabel(bal_text)
            bal_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            bal_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            color = "#4ade80" if a.balance_minor >= 0 else "#f87171"
            bal_lbl.setStyleSheet(f"color: {color};")
            row.addWidget(bal_lbl)

            self._accounts_layout.addLayout(row)
        self._accounts_layout.addStretch()

    def _populate_recent(self, recent: list[TransactionRow]) -> None:
        self._clear_layout(self._recent_layout)
        if not recent:
            self._recent_layout.addWidget(QLabel("Nenhuma transação registrada"))
            self._recent_layout.addStretch()
            return
        for tx in recent:
            row = QHBoxLayout()

            date_lbl = QLabel(tx.posted_date.strftime("%d/%m"))
            date_lbl.setFont(QFont("Segoe UI", 9))
            date_lbl.setStyleSheet("color: #94a3b8;")
            date_lbl.setFixedWidth(40)
            row.addWidget(date_lbl)

            desc_lbl = QLabel(tx.description[:40])
            desc_lbl.setFont(QFont("Segoe UI", 10))
            desc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row.addWidget(desc_lbl)

            amt_text = _fmt_money(tx.amount_minor, tx.currency, tx.currency_symbol)
            amt_lbl = QLabel(amt_text)
            amt_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            amt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            color = "#4ade80" if tx.amount_minor >= 0 else "#f87171"
            amt_lbl.setStyleSheet(f"color: {color};")
            row.addWidget(amt_lbl)

            self._recent_layout.addLayout(row)
        self._recent_layout.addStretch()

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                DashboardPanel._clear_layout(item.layout())
