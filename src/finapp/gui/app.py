"""PySide6 application entrypoint."""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import (
            QApplication,
            QLabel,
            QMainWindow,
            QStatusBar,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print(
            "PySide6 is not installed. Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    from finapp.gui.panels.dashboard import DashboardPanel
    from finapp.gui.panels.accounts import AccountsPanel
    from finapp.gui.panels.transactions import TransactionsPanel

    app = QApplication(sys.argv)
    app.setApplicationName("FinApp")

    # Apply dark theme stylesheet
    app.setStyleSheet(_DARK_STYLESHEET)

    window = QMainWindow()
    window.setWindowTitle("FinApp — Gestão Financeira Pessoal")
    window.resize(1280, 800)

    tabs = QTabWidget()

    # Functional panels
    tabs.addTab(DashboardPanel(), "Dashboard")
    tabs.addTab(AccountsPanel(), "Contas")
    tabs.addTab(TransactionsPanel(), "Transações")

    # Placeholder panels (future phases)
    for name in ("Reconciliação", "Portfólio", "Relatórios", "IA"):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(f"[{name}] — em construção"))
        tabs.addTab(page, name)

    window.setCentralWidget(tabs)

    status = QStatusBar()
    status.showMessage("Pronto")
    window.setStatusBar(status)

    window.show()
    return app.exec()


_DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: "Segoe UI", sans-serif;
}
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 4px;
}
QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #334155;
    color: #f8fafc;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton:pressed {
    background-color: #1d4ed8;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #475569;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #e2e8f0;
    selection-background-color: #334155;
}
QTableView {
    background-color: #1e293b;
    color: #e2e8f0;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 4px;
    selection-background-color: #334155;
    alternate-background-color: #162032;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    border: 1px solid #334155;
    padding: 4px 8px;
    font-weight: bold;
}
QTreeWidget {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 4px;
    show-decoration-selected: 1;
}
QTreeWidget::item:selected {
    background-color: #334155;
}
QTreeWidget::item:hover {
    background-color: #1e3a5f;
}
QScrollBar:vertical {
    background: #1e293b;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #475569;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QStatusBar {
    background-color: #0f172a;
    color: #64748b;
    border-top: 1px solid #334155;
}
QDialog {
    background-color: #1e293b;
    color: #e2e8f0;
}
QMessageBox {
    background-color: #1e293b;
    color: #e2e8f0;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
}
QLabel {
    color: #e2e8f0;
}
"""


if __name__ == "__main__":
    raise SystemExit(main())
