"""Dialog for adding a new transaction."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finapp.services.dto import AccountSummary, CategoryItem


class AddTransactionDialog(QDialog):
    def __init__(
        self,
        accounts: list[AccountSummary],
        categories: list[CategoryItem],
        parent: QWidget | None = None,
        preselect_account_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova Transação")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Account
        self.account_combo = QComboBox()
        self._account_currencies: dict[int, str] = {}
        for a in accounts:
            label = f"{a.institution_name} — {a.name} ({a.currency})"
            self.account_combo.addItem(label, a.id)
            self._account_currencies[a.id] = a.currency
        if preselect_account_id is not None:
            for i in range(self.account_combo.count()):
                if self.account_combo.itemData(i) == preselect_account_id:
                    self.account_combo.setCurrentIndex(i)
                    break
        form.addRow("Conta:", self.account_combo)

        # Date
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Data:", self.date_edit)

        # Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Ex: -150.00 (negativo = despesa)")
        form.addRow("Valor:", self.amount_edit)

        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Descrição da transação")
        form.addRow("Descrição:", self.description_edit)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItem("— Sem Categoria —", None)
        for cat in categories:
            prefix = "📈 " if cat.is_income else "📉 "
            self.category_combo.addItem(f"{prefix}{cat.name}", cat.id)
        form.addRow("Categoria:", self.category_combo)

        # Memo
        self.memo_edit = QTextEdit()
        self.memo_edit.setMaximumHeight(60)
        self.memo_edit.setPlaceholderText("Observações (opcional)")
        form.addRow("Memo:", self.memo_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if not self.description_edit.text().strip():
            self.description_edit.setFocus()
            return
        try:
            Decimal(self.amount_edit.text().strip().replace(",", "."))
        except (InvalidOperation, ValueError):
            self.amount_edit.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        acct_id = self.account_combo.currentData()
        currency = self._account_currencies.get(acct_id, "BRL")
        qdate = self.date_edit.date()
        memo_text = self.memo_edit.toPlainText().strip() or None
        return {
            "account_id": acct_id,
            "posted_date": date(qdate.year(), qdate.month(), qdate.day()),
            "amount": Decimal(self.amount_edit.text().strip().replace(",", ".")),
            "currency": currency,
            "description": self.description_edit.text().strip(),
            "category_id": self.category_combo.currentData(),
            "memo": memo_text,
        }
