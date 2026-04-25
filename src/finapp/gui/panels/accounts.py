"""Accounts panel — institution/account tree, detail view, add dialogs."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finapp.db.engine import session_scope
from finapp.money import from_minor
from finapp.services.account_service import AccountService
from finapp.services.dto import AccountSummary, InstitutionSummary
from finapp.gui.dialogs.institution_dialog import AddInstitutionDialog
from finapp.gui.dialogs.account_dialog import AddAccountDialog


def _fmt(minor: int, currency: str, symbol: str) -> str:
    val = from_minor(minor, currency)
    sign = "-" if val < 0 else ""
    return f"{sign}{symbol} {abs(val):,.2f}"


class AccountsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._institutions: list[InstitutionSummary] = []
        self._accounts: list[AccountSummary] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Contas")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_row.addWidget(title)
        title_row.addStretch()

        btn_inst = QPushButton("+ Instituição")
        btn_inst.clicked.connect(self._on_add_institution)
        title_row.addWidget(btn_inst)

        btn_acct = QPushButton("+ Conta")
        btn_acct.clicked.connect(self._on_add_account)
        title_row.addWidget(btn_acct)

        layout.addLayout(title_row)

        # Splitter: tree | detail
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Nome", "Tipo", "Saldo"])
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._tree)

        # Right: detail
        self._detail_box = QGroupBox("Detalhes")
        self._detail_layout = QFormLayout(self._detail_box)
        self._detail_fields: dict[str, QLabel] = {}
        for label_text in [
            "Nome", "Instituição", "Tipo", "Moeda",
            "Saldo", "Ativa", "Data de Abertura",
        ]:
            val = QLabel("—")
            val.setWordWrap(True)
            self._detail_layout.addRow(f"{label_text}:", val)
            self._detail_fields[label_text] = val
        splitter.addWidget(self._detail_box)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        try:
            with session_scope() as s:
                svc = AccountService(s)
                self._institutions = svc.list_institution_summaries()
                self._accounts = svc.list_account_summaries()
        except Exception:
            return
        self._populate_tree()

    def _populate_tree(self) -> None:
        self._tree.clear()
        accts_by_inst: dict[int, list[AccountSummary]] = {}
        for a in self._accounts:
            accts_by_inst.setdefault(a.institution_id, []).append(a)

        for inst in self._institutions:
            inst_item = QTreeWidgetItem([
                f"{inst.name} ({inst.country})",
                inst.type,
                "",
            ])
            inst_item.setData(0, Qt.ItemDataRole.UserRole, ("institution", inst.id))
            inst_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))

            for a in accts_by_inst.get(inst.id, []):
                acct_item = QTreeWidgetItem([
                    a.name,
                    a.account_type,
                    _fmt(a.balance_minor, a.currency, a.currency_symbol),
                ])
                acct_item.setData(0, Qt.ItemDataRole.UserRole, ("account", a.id))
                color = Qt.GlobalColor.green if a.balance_minor >= 0 else Qt.GlobalColor.red
                acct_item.setForeground(2, color)
                inst_item.addChild(acct_item)

            self._tree.addTopLevelItem(inst_item)
            inst_item.setExpanded(True)

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _prev) -> None:
        if current is None:
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        kind, obj_id = data
        if kind == "account":
            acct = next((a for a in self._accounts if a.id == obj_id), None)
            if acct:
                self._show_account_detail(acct)
        elif kind == "institution":
            inst = next((i for i in self._institutions if i.id == obj_id), None)
            if inst:
                self._show_institution_detail(inst)

    def _show_account_detail(self, a: AccountSummary) -> None:
        self._detail_fields["Nome"].setText(a.name)
        self._detail_fields["Instituição"].setText(a.institution_name)
        self._detail_fields["Tipo"].setText(a.account_type)
        self._detail_fields["Moeda"].setText(a.currency)
        self._detail_fields["Saldo"].setText(
            _fmt(a.balance_minor, a.currency, a.currency_symbol)
        )
        self._detail_fields["Ativa"].setText("Sim" if a.is_active else "Não")
        self._detail_fields["Data de Abertura"].setText("—")

    def _show_institution_detail(self, inst: InstitutionSummary) -> None:
        self._detail_fields["Nome"].setText(inst.name)
        self._detail_fields["Instituição"].setText("—")
        self._detail_fields["Tipo"].setText(inst.type)
        self._detail_fields["Moeda"].setText("—")
        self._detail_fields["Saldo"].setText("—")
        self._detail_fields["Ativa"].setText("—")
        self._detail_fields["Data de Abertura"].setText("—")

    # ── dialogs ──────────────────────────────────────────────────────

    def _on_add_institution(self) -> None:
        dlg = AddInstitutionDialog(self)
        if dlg.exec() == AddInstitutionDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                with session_scope() as s:
                    svc = AccountService(s)
                    svc.create_institution(**data)
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))
                return
            self.refresh()

    def _on_add_account(self) -> None:
        if not self._institutions:
            QMessageBox.information(
                self, "Atenção",
                "Cadastre uma instituição antes de criar uma conta.",
            )
            return

        preselect = None
        current = self._tree.currentItem()
        if current:
            data = current.data(0, Qt.ItemDataRole.UserRole)
            if data:
                kind, obj_id = data
                if kind == "institution":
                    preselect = obj_id
                elif kind == "account":
                    acct = next((a for a in self._accounts if a.id == obj_id), None)
                    if acct:
                        preselect = acct.institution_id

        dlg = AddAccountDialog(self._institutions, self, preselect_institution_id=preselect)
        if dlg.exec() == AddAccountDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                with session_scope() as s:
                    svc = AccountService(s)
                    svc.create_account(**data)
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))
                return
            self.refresh()
