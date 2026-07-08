from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QTabWidget,
    QTableWidget,
    QHeaderView,
)

from app.device_service import DeviceService
from app.validators import is_valid_ip
from app.ssh_client import SSHClient
from app.logger import setup_logger
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.logger = setup_logger()
        self.logger.info("Application started")

        self.setWindowTitle("LibreNMS Device Manager")
        self.resize(950, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.devices_tab = QWidget()
        self.bulk_tab = QWidget()
        self.settings_tab = QWidget()
        self.log_tab = QWidget()

        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.bulk_tab, "Bulk Add")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.log_tab, "Log")

        self.build_devices_tab()
        self.build_bulk_tab()
        self.build_settings_tab()
        self.build_log_tab()

        self.statusBar().showMessage("Ready")

    def build_devices_tab(self):
        layout = QVBoxLayout()

        device_group = QGroupBox("Add Ping Only Device")
        form = QFormLayout()

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP адреса пристрою")

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Display Name пристрою")

        form.addRow("Device IP:", self.ip_input)
        form.addRow("Display Name:", self.display_name_input)

        device_group.setLayout(form)

        self.add_button = QPushButton("Add Ping Only Device")
        self.add_button.clicked.connect(self.add_ping_only_device)

        layout.addWidget(device_group)
        layout.addWidget(self.add_button)
        layout.addStretch()

        self.devices_tab.setLayout(layout)

    def build_bulk_tab(self):
        layout = QVBoxLayout()

        info = QLabel(
            "Bulk Add: масове додавання Ping Only пристроїв.\n"
            "Формат таблиці: IP Address | Display Name"
        )

        self.bulk_table = QTableWidget()
        self.bulk_table.setColumnCount(2)
        self.bulk_table.setHorizontalHeaderLabels(["IP Address", "Display Name"])
        self.bulk_table.setRowCount(10)

        self.bulk_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.bulk_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )

        buttons_layout = QHBoxLayout()

        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Selected Row")
        self.validate_bulk_button = QPushButton("Validate Table")
        self.prepare_bulk_button = QPushButton("Prepare Commands")
        self.add_all_button = QPushButton("Add All Devices")

        buttons_layout.addWidget(self.add_row_button)
        buttons_layout.addWidget(self.remove_row_button)
        buttons_layout.addWidget(self.validate_bulk_button)
        buttons_layout.addWidget(self.prepare_bulk_button)
        buttons_layout.addWidget(self.add_all_button)

        self.add_row_button.clicked.connect(self.add_bulk_row)
        self.remove_row_button.clicked.connect(self.remove_selected_bulk_row)
        self.validate_bulk_button.clicked.connect(self.validate_bulk_list)
        self.prepare_bulk_button.clicked.connect(self.prepare_bulk_commands)
        self.add_all_button.clicked.connect(self.add_all_bulk_devices)

        layout.addWidget(info)
        layout.addWidget(self.bulk_table)
        layout.addLayout(buttons_layout)

        self.bulk_tab.setLayout(layout)

    def build_settings_tab(self):
        layout = QVBoxLayout()

        ssh_group = QGroupBox("LibreNMS SSH Settings")
        form = QFormLayout()

        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("IP або DNS сервера LibreNMS")

        self.port_input = QLineEdit()
        self.port_input.setText("22")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("SSH користувач")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("SSH пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        form.addRow("Server:", self.server_input)
        form.addRow("Port:", self.port_input)
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)

        ssh_group.setLayout(form)

        layout.addWidget(ssh_group)
        layout.addStretch()

        self.settings_tab.setLayout(layout)

    def build_log_tab(self):
        layout = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Тут буде журнал виконання...")

        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log)

        self.log_tab.setLayout(layout)

    def add_ping_only_device(self):
        server, port, username, password = self.get_ssh_settings()

        if not self.validate_settings(server, port, username, password):
            return

        device_ip = self.ip_input.text().strip()
        display_name = self.display_name_input.text().strip()

        if not self.validate_device(device_ip, display_name):
            return

        self.run_device_add(server, port, username, password, device_ip, display_name)

    def add_all_bulk_devices(self):
        server, port, username, password = self.get_ssh_settings()

        if not self.validate_settings(server, port, username, password):
            return

        devices, errors = self.parse_bulk_lines()

        self.append_log("────────────────────────")
        self.append_log("Bulk Add execution")

        if errors:
            for error in errors:
                self.append_log(f"❌ {error}", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        success_count = 0
        failed_count = 0

        for device_ip, display_name in devices:
            result = self.run_device_add(
                server,
                port,
                username,
                password,
                device_ip,
                display_name,
            )

            if result:
                success_count += 1
            else:
                failed_count += 1

        if failed_count == 0:
            self.append_log(
                f"✅ Bulk Add finished successfully. Added: {success_count}",
                "success",
            )
        else:
            self.append_log(
                f"⚠️ Bulk Add completed with errors. Success: {success_count}, Failed: {failed_count}",
                "warning",
            )

        self.tabs.setCurrentWidget(self.log_tab)

    def run_device_add(self, server, port, username, password, device_ip, display_name):
        add_command = DeviceService.build_add_ping_only_command(device_ip)
        rename_command = DeviceService.build_set_display_name_command(
            device_ip, display_name
        )

        ssh = SSHClient(server, int(port), username, password)

        self.append_log("────────────────────────")
        self.append_log(f"SSH connect: {username}@{server}:{port}")
        self.append_log(f"Adding Ping Only device: {device_ip}")

        code, out, err = ssh.run_command(add_command)

        if out:
            self.append_log(out.strip())
        if err:
            self.append_log(err.strip())

        if code != 0:
            self.append_log(f"❌ Device add failed: {device_ip}")
            self.tabs.setCurrentWidget(self.log_tab)
            return False

        self.append_log(f"✅ Device add command completed: {device_ip}")
        self.append_log(f"Setting Display Name: {display_name}")

        code, out, err = ssh.run_command(rename_command)

        if out:
            self.append_log(out.strip())
        if err:
            self.append_log(err.strip())

        if code != 0:
            self.append_log(f"❌ Display Name update failed: {device_ip}")
            self.tabs.setCurrentWidget(self.log_tab)
            return False

        self.append_log(f"✅ Display Name updated: {device_ip}")
        self.tabs.setCurrentWidget(self.log_tab)
        return True

    def prepare_bulk_commands(self):
        server, port, username, password = self.get_ssh_settings()

        if not self.validate_settings(server, port, username, password):
            return

        devices, errors = self.parse_bulk_lines()

        self.append_log("────────────────────────")
        self.append_log("Bulk command preparation")

        if errors:
            for error in errors:
                self.append_log(f"❌ {error}")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        self.append_log(f"SSH connect: {username}@{server}:{port}")
        self.append_log("")

        for ip, display_name in devices:
            add_command = DeviceService.build_add_ping_only_command(ip)
            rename_command = DeviceService.build_set_display_name_command(
                ip, display_name
            )

            self.append_log(f"Device: {ip} / {display_name}")
            self.append_log(f"1. {add_command}")
            self.append_log(f"2. {rename_command}")
            self.append_log("")

        self.tabs.setCurrentWidget(self.log_tab)

    def parse_bulk_lines(self):
        devices = []
        errors = []

        row_count = self.bulk_table.rowCount()

        for row in range(row_count):
            ip_item = self.bulk_table.item(row, 0)
            display_item = self.bulk_table.item(row, 1)

            ip = ip_item.text().strip() if ip_item else ""
            display_name = display_item.text().strip() if display_item else ""

            if not ip and not display_name:
                continue

            line_number = row + 1

            if not ip:
                errors.append(f"Рядок {line_number}: IP порожній")
                continue

            if not is_valid_ip(ip):
                errors.append(f"Рядок {line_number}: неправильний IP: {ip}")
                continue

            if not display_name:
                errors.append(f"Рядок {line_number}: Display Name порожній")
                continue

            devices.append((ip, display_name))

        if not devices and not errors:
            errors.append("Таблиця порожня")

        return devices, errors

    def validate_bulk_list(self):
        devices, errors = self.parse_bulk_lines()

        self.append_log("────────────────────────")
        self.append_log("Bulk validation")

        if errors:
            for error in errors:
                self.append_log(f"❌ {error}")
        else:
            self.append_log(f"✅ Список коректний. Пристроїв: {len(devices)}")

        self.tabs.setCurrentWidget(self.log_tab)

    def validate_device(self, device_ip, display_name):
        if not device_ip:
            self.append_log("❌ Device IP is empty")
            return False

        if not is_valid_ip(device_ip):
            self.append_log("❌ Device IP is invalid")
            return False

        if not display_name:
            self.append_log("❌ Display Name is empty")
            return False

        return True

    def validate_settings(self, server, port, username, password):
        if not server:
            self.append_log("❌ Server is empty")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not port:
            self.append_log("❌ SSH port is empty")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not port.isdigit():
            self.append_log("❌ SSH port must be a number")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not username:
            self.append_log("❌ Username is empty")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not password:
            self.append_log("❌ Password is empty")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        return True

    def get_ssh_settings(self):
        server = self.server_input.text().strip()
        port = self.port_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        return server, port, username, password

    def add_bulk_row(self):
        row = self.bulk_table.rowCount()
        self.bulk_table.insertRow(row)

    def remove_selected_bulk_row(self):
        selected_rows = sorted(
            set(index.row() for index in self.bulk_table.selectedIndexes()),
            reverse=True,
        )

        if not selected_rows:
            self.append_log("❌ Не вибрано рядок для видалення")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        for row in selected_rows:
            self.bulk_table.removeRow(row)

        self.append_log(f"✅ Видалено рядків: {len(selected_rows)}")

    def append_log(self, message: str, level: str = "info"):
        text = str(message)
        time_text = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#dcdcdc",
            "success": "#4caf50",
            "warning": "#ffb300",
            "error": "#f44336",
        }

        labels = {
            "info": "INFO",
            "success": "OK",
            "warning": "WARN",
            "error": "ERROR",
        }

        color = colors.get(level, "#dcdcdc")
        label = labels.get(level, "INFO")

        html = f'<span style="color:{color};">[{time_text}] [{label}] {text}</span>'
        self.log.append(html)

        if hasattr(self, "logger"):
            if level == "error":
                self.logger.error(text)
            elif level == "warning":
                self.logger.warning(text)
            else:
                self.logger.info(text)