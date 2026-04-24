"""PySide6 application entrypoint (skeleton)."""
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
            QWidget,
            QVBoxLayout,
        )
    except ImportError:
        print(
            "PySide6 is not installed. Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("FinApp")

    window = QMainWindow()
    window.setWindowTitle("FinApp — Gestão Financeira Pessoal")
    window.resize(1280, 800)

    tabs = QTabWidget()
    for name in ("Dashboard", "Contas", "Transações", "Reconciliação", "Portfólio", "Relatórios", "IA"):
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


if __name__ == "__main__":
    raise SystemExit(main())
