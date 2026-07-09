DARK_THEME = """
QMainWindow {
    background-color: #111827;
}

QWidget {
    background-color: #111827;
    color: #E5E7EB;
    font-size: 10.5pt;
}

QTabWidget::pane {
    border: 1px solid #374151;
    border-radius: 8px;
    background: #111827;
}

QTabBar::tab {
    background: #1F2937;
    color: #D1D5DB;
    padding: 10px 18px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
}

QTabBar::tab:selected {
    background: #2563EB;
    color: white;
}

QTabBar::tab:hover {
    background: #374151;
}

QGroupBox {
    border: 1px solid #374151;
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px;
    font-weight: bold;
    color: #F9FAFB;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QLabel {
    color: #E5E7EB;
}

QLineEdit {
    background-color: #1F2937;
    color: #F9FAFB;
    border: 1px solid #4B5563;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #2563EB;
}

QLineEdit:focus {
    border: 1px solid #60A5FA;
}

QPushButton {
    background-color: #2563EB;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3B82F6;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QTextEdit {
    background-color: #020617;
    color: #E5E7EB;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 10px;
    font-family: Consolas, Menlo, monospace;
}

QTableWidget {
    background-color: #0F172A;
    alternate-background-color: #111827;
    color: #E5E7EB;
    gridline-color: #334155;
    border: 1px solid #374151;
    border-radius: 10px;
    selection-background-color: #1F2937;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 6px;
    background-color: #0F172A;
    color: #E5E7EB;
}

QTableWidget::item:selected {
    background-color: #374151;
    color: #FFFFFF;
}

QTableWidget::item:focus {
    border: 1px solid #60A5FA;
}

QTableWidget QLineEdit {
    background-color: #111827;
    color: #FFFFFF;
    border: 1px solid #60A5FA;
    border-radius: 6px;
    padding: 4px;
}

QHeaderView::section {
    background-color: #1F2937;
    color: #F9FAFB;
    padding: 8px;
    border: 1px solid #374151;
    font-weight: bold;
}

QScrollBar:vertical {
    background: #111827;
    width: 12px;
}

QScrollBar::handle:vertical {
    background: #4B5563;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: #6B7280;
}

QStatusBar {
    background-color: #0F172A;
    color: #D1D5DB;
}
"""