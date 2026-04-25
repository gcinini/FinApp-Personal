"""Transactions panel — register grid with QTableView + model, filters, add dialog."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from finapp.db.engine import session_scope
from finapp.money import from_minor
from finapp.services.account_service import AccountService, TransactionService
from finapp.services.dto import AccountSummary, TransactionRow
from finapp.gui.dialogs.transaction_dialog import AddTransactionDialog


_COLUMNS = ["Data", "Descrição", "Categoria", "Valor", "Status"]
_STATUS_LABELS = {
    "PENDING": "Pendente",
    "CLEARED": "Compensada",
    "RECONCILED": "Conciliada",
    "VOID": "Anulada",
}


class TransactionTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[TransactionRow] = []

    def set_data(self, rows: list[TransactionRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return row.posted_date.strftime("%d/%m/%Y")
            elif col == 1:
                return row.description
            elif col == 2:
                return row.category_name or "—"
            elif col == 3:
                val = from_minor(row.amount_minor, row.currency)
                sign = "-" if val < 0 else ""
                return f"{sign}{row.currency_symbol} {abs(val):,.2f}"
            elif col == 4:
                return _STATUS_LABELS.get(row.status, row.status)

        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 3:
                if row.amount_minor >= 0:
                    return QBrush(QColor("#4ade80"))
                else:
                    return QBrush(QColor("#f87171"))

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 3:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            elif col == 0 or col == 4:
                return Qt.AlignmentFlag.AlignCenter

        elif role == Qt.ItemDataRole.UserRole:
            return row.id

        return None

    def get_row(self, index: int) -> TransactionRow | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None


class TransactionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._accounts: list[AccountSummary] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Transações")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_row.addWidget(title)
        title_row.addStretch()

        btn_add = QPushButton("+ Nova Transação")
        btn_add.clicked.connect(self._on_add_transaction)
        title_row.addWidget(btn_add)

        btn_refresh = QPushButton("⟳ Atualizar")
        btn_refresh.clicked.connect(self._reload_transactions)
        title_row.addWidget(btn_refresh)

        layout.addLayout(title_row)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Conta:"))
        self._account_combo = QComboBox()
        self._account_combo.setMinimumWidth(300)
        self._account_combo.currentIndexChanged.connect(self._reload_transactions)
        filter_row.addWidget(self._account_combo)

        filter_row.addWidget(QLabel("Status:"))
        self._status_combo = QComboBox()
        self._status_combo.addItem("Todos", None)
        self._status_combo.addItem("Pendente", "PENDING")
        self._status_combo.addItem("Compensada", "CLEARED")
        self._status_combo.addItem("Conciliada", "RECONCILED")
        self._status_combo.addItem("Anulada", "VOID")
        self._status_combo.currentIndexChanged.connect(self._reload_transactions)
        filter_row.addWidget(self._status_combo)

        filter_row.addStretch()

        self._count_label = QLabel("")
        filter_row.addWidget(self._count_label)

        layout.addLayout(filter_row)

        # Table
        self._model = TransactionTableModel(self)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self._table.setSortingEnabled(False)
        layout.addWidget(self._table, stretch=1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._load_accounts()

    def _load_accounts(self) -> None:
        try:
            with session_scope() as s:
                svc = AccountService(s)
                self._accounts = svc.list_account_summaries()
        except Exception:
            return

        prev = self._account_combo.currentData()
        self._account_combo.blockSignals(True)
        self._account_combo.clear()
        for a in self._accounts:
            label = f"{a.institution_name} — {a.name} ({a.currency})"
            self._account_combo.addItem(label, a.id)
        # Restore selection
        if prev is not None:
            for i in range(self._account_combo.count()):
                if self._account_combo.itemData(i) == prev:
                    self._account_combo.setCurrentIndex(i)
                    break
        self._account_combo.blockSignals(False)
        self._reload_transactions()

    def _reload_transactions(self) -> None:
        acct_id = self._account_combo.currentData()
        if acct_id is None:
            self._model.set_data([])
            self._count_label.setText("")
            return

        from finapp.models.enums import TransactionStatus

        status_val = self._status_combo.currentData()
        status_enum = TransactionStatus(status_val) if status_val else None

        try:
            with session_scope() as s:
                tx_svc = TransactionService(s)
                rows = tx_svc.list_transactions(
                    acct_id,
                    status=status_enum,
                    limit=500,
                )
        except Exception:
            rows = []

        self._model.set_data(rows)
        self._count_label.setText(f"{len(rows)} transações")

        # Auto-resize columns after data load
        for col in range(len(_COLUMNS)):
            self._table.resizeColumnToContents(col)

    def _on_add_transaction(self) -> None:
        if not self._accounts:
            QMessageBox.information(
                self, "Atenção",
                "Cadastre uma conta antes de criar transações.",
            )
            return

        try:
            with session_scope() as s:
                tx_svc = TransactionService(s)
                categories = tx_svc.list_categories()
        except Exception:
            categories = []

        preselect = self._account_combo.currentData()
        dlg = AddTransactionDialog(
            self._accounts, categories, self,
            preselect_account_id=preselect,
        )
        if dlg.exec() == AddTransactionDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                with session_scope() as s:
                    tx_svc = TransactionService(s)
                    tx_svc.add(**data)
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))
                return
            self._reload_transactions()
