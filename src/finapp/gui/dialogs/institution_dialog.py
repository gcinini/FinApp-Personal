"""Dialog for adding a new institution."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from finapp.models.enums import InstitutionType

_COUNTRIES = [("BR", "Brasil"), ("US", "Estados Unidos")]
_INST_TYPES = [
    (InstitutionType.BANK, "Banco"),
    (InstitutionType.BROKERAGE, "Corretora"),
    (InstitutionType.CARD_ISSUER, "Emissora de Cartão"),
    (InstitutionType.EXCHANGE, "Câmbio"),
    (InstitutionType.OTHER, "Outro"),
]


class AddInstitutionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova Instituição")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Nubank, Chase…")
        form.addRow("Nome:", self.name_edit)

        self.country_combo = QComboBox()
        for code, label in _COUNTRIES:
            self.country_combo.addItem(label, code)
        form.addRow("País:", self.country_combo)

        self.type_combo = QComboBox()
        for enum_val, label in _INST_TYPES:
            self.type_combo.addItem(label, enum_val)
        form.addRow("Tipo:", self.type_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "country": self.country_combo.currentData(),
            "type": self.type_combo.currentData(),
        }
