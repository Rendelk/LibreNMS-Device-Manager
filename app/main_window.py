
from datetime import datetime

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
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
)

from app.history import HistoryDatabase
from app.mikrotik_service import MikroTikService
from app.device_service import DeviceService
from app.validators import is_valid_ip
from app.ssh_client import SSHClient
from app.logger import setup_logger
from app.report_writer import ReportWriter


class MainWindow(QMainWindow):
    def update_device_mode_fields(self):
        is_snmp = self.mode_input.currentText() == "SNMP"

        self.snmp_version_input.setEnabled(is_snmp)
        self.community_input.setEnabled(is_snmp)
        self.snmp_port_input.setEnabled(is_snmp)
        self.transport_input.setEnabled(is_snmp)

        if not is_snmp:
            self.os_input.setText("ping")
        else:
            self.os_input.clear()

    def __init__(self):
        super().__init__()

        self.logger = setup_logger()
        self.logger.info("Application started")

        self.history_db = HistoryDatabase()
        self.report_writer = ReportWriter()

        self.setWindowTitle("LibreNMS Device Manager")
        self.resize(950, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.devices_tab = QWidget()
        self.mikrotik_tab = QWidget()
        self.bulk_tab = QWidget()
        self.settings_tab = QWidget()
        self.log_tab = QWidget()

        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.mikrotik_tab, "MikroTik Users")
        self.tabs.addTab(self.bulk_tab, "Bulk Add")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.log_tab, "Log")

        self.build_devices_tab()
        self.build_mikrotik_tab()
        self.build_bulk_tab()
        self.build_settings_tab()
        self.build_log_tab()

        self.statusBar().showMessage("Ready")
    
    def update_mikrotik_action_fields(self):
        action = self.mikrotik_action_input.currentText()

        need_password = action in ["Add User", "Change Password"]
        need_allowed_address = action in ["Add User", "Change Allowed Address"]
        need_group = action in ["Add User", "Change Group"]

        self.mikrotik_user_password_input.setEnabled(need_password)
        self.mikrotik_allowed_address_input.setEnabled(need_allowed_address)
        self.mikrotik_group_input.setEnabled(need_group)

    def build_mikrotik_tab(self):
        layout = QVBoxLayout()

        info = QLabel(
            "MikroTik Users: масове додавання або видалення користувача.\n"
            "Введи список IP, кожен IP з нового рядка."
        )

        self.mikrotik_ip_list = QPlainTextEdit()
        self.mikrotik_ip_list.setPlaceholderText(
            "10.10.10.1\n10.10.10.2\n10.10.10.3"
        )

        form_group = QGroupBox("User action")
        form = QFormLayout()

        self.mikrotik_action_input = QComboBox()
        self.mikrotik_action_input.addItems([
    "Add User",
    "Delete User",
    "Enable User",
    "Disable User",
    "Change Password",
    "Change Group",
    "Change Allowed Address",
])
        self.mikrotik_action_input.currentTextChanged.connect(
        self.update_mikrotik_action_fields
)

        self.mikrotik_user_login_input = QLineEdit()
        self.mikrotik_user_login_input.setPlaceholderText("Логін користувача")

        self.mikrotik_user_password_input = QLineEdit()
        self.mikrotik_user_password_input.setPlaceholderText("Пароль користувача")
        self.mikrotik_user_password_input.setEchoMode(QLineEdit.Password)

        self.mikrotik_allowed_address_input = QLineEdit()
        self.mikrotik_allowed_address_input.setPlaceholderText("Наприклад: 10.0.0.0/8")

        self.mikrotik_group_input = QComboBox()
        self.mikrotik_group_input.addItems(["read", "write", "full"])

        form.addRow("Action:", self.mikrotik_action_input)
        form.addRow("Login:", self.mikrotik_user_login_input)
        form.addRow("Password:", self.mikrotik_user_password_input)
        form.addRow("Allowed Address:", self.mikrotik_allowed_address_input)
        form.addRow("Group:", self.mikrotik_group_input)

        form_group.setLayout(form)

        self.mikrotik_execute_button = QPushButton("Execute MikroTik Action")
        self.mikrotik_execute_button.clicked.connect(self.execute_mikrotik_users)

        layout.addWidget(info)
        layout.addWidget(self.mikrotik_ip_list)
        layout.addWidget(form_group)
        layout.addWidget(self.mikrotik_execute_button)
        layout.addStretch()

        self.mikrotik_tab.setLayout(layout)
        self.update_mikrotik_action_fields()

    def execute_mikrotik_users(self):
        ip_text = self.mikrotik_ip_list.toPlainText().strip()
        action = self.mikrotik_action_input.currentText()

        ssh_port = self.mikrotik_ssh_port_input.text().strip()
        ssh_username = self.mikrotik_ssh_username_input.text().strip()
        ssh_password = self.mikrotik_ssh_password_input.text()

        target_username = self.mikrotik_user_login_input.text().strip()
        target_password = self.mikrotik_user_password_input.text()
        allowed_address = self.mikrotik_allowed_address_input.text().strip()
        group = self.mikrotik_group_input.currentText()

        self.append_log("────────────────────────")
        self.append_log("MikroTik Automation execution")
        self.append_log(f"Action: {action}")
        self.append_log(f"SSH username: {ssh_username}")
        self.append_log(f"Target username: {target_username}")

        if not ip_text:
            self.append_log("❌ MikroTik IP list is empty", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        if not ssh_port or not ssh_port.isdigit():
            self.append_log("❌ MikroTik SSH port is invalid", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return

        if not ssh_username:
            self.append_log("❌ MikroTik SSH username is empty", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return

        if not ssh_password:
            self.append_log("❌ MikroTik SSH password is empty", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return

        if not target_username:
            self.append_log("❌ Target user login is empty", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        if action in ["Add User", "Change Password"] and not target_password:
            self.append_log("❌ Password is empty", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        if action in ["Add User", "Change Allowed Address"] and not allowed_address:
            self.append_log("❌ Allowed Address is empty", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        mikrotik_ips = [
            line.strip()
            for line in ip_text.splitlines()
            if line.strip()
        ]

        self.append_log(f"Parsed MikroTik IPs: {mikrotik_ips}")

        success_count = 0
        failed_count = 0

        session_id = self.history_db.create_session(
            action=action,
            target="MikroTik Users",
            username=target_username,
        )

        self.report_writer.start_session(action, target_username)

        for ip in mikrotik_ips:
            self.append_log("────────────────────────")
            self.append_log(f"Connecting to MikroTik {ip}:{ssh_port} ...")

            if not is_valid_ip(ip):
                message = f"{ip} - неправильна IP адреса"

                self.append_log(f"❌ {message}", "error")
                self.report_writer.add_line(message)
                self.history_db.add_item(
                    session_id=session_id,
                    device_ip=ip,
                    status="FAILED",
                    message=message,
                    exit_code=None,
                    stdout="",
                    stderr="Invalid IP address",
                )
                failed_count += 1
                continue

            try:
                command = MikroTikService.build_command(
                    action=action,
                    username=target_username,
                    password=target_password,
                    group=group,
                    allowed_address=allowed_address,
                )
            except ValueError as e:
                message = f"{ip} - {e}"

                self.append_log(f"❌ {message}", "error")
                self.report_writer.add_line(message)
                self.history_db.add_item(
                    session_id=session_id,
                    device_ip=ip,
                    status="FAILED",
                    message=message,
                    exit_code=None,
                    stdout="",
                    stderr=str(e),
                )
                failed_count += 1
                continue

            self.append_log(f"MikroTik: {ip}")
            self.append_log(f"COMMAND: {command}")

            ssh = SSHClient(ip, int(ssh_port), ssh_username, ssh_password)
            code, out, err = ssh.run_command(command, timeout=10)

            combined_output = f"{out}\n{err}".lower()

            mikrotik_error = (
                "failure:" in combined_output
                or "syntax error" in combined_output
                or "bad command" in combined_output
                or "no such item" in combined_output
                or "already exists" in combined_output
                or "invalid" in combined_output
            )

            if out and out.strip():
                self.append_log(out.strip())

            if err and err.strip():
                self.append_log(err.strip(), "error")

            if code == 0 and not mikrotik_error:
                action_text = MikroTikService.build_history_message(
                    action,
                    target_username,
                )

                history_message = f"{ip} - {action_text}"

                self.append_log(f"✅ {history_message}", "success")
                self.report_writer.add_line(history_message)
                self.history_db.add_item(
                    session_id=session_id,
                    device_ip=ip,
                    status="SUCCESS",
                    message=history_message,
                    exit_code=code,
                    stdout=out.strip() if out else "",
                    stderr=err.strip() if err else "",
                )
                success_count += 1

            else:
                action_text = MikroTikService.build_history_message(
                    action,
                    target_username,
                )

                error_text = err.strip() if err else out.strip() if out else "Unknown error"
                history_message = (
                    f"{ip} - не вдалося виконати: {action_text}. "
                    f"Помилка: {error_text}"
                )

                self.append_log(f"❌ {history_message}", "error")
                self.report_writer.add_line(history_message)
                self.history_db.add_item(
                    session_id=session_id,
                    device_ip=ip,
                    status="FAILED",
                    message=history_message,
                    exit_code=code,
                    stdout=out.strip() if out else "",
                    stderr=err.strip() if err else "",
                )
                failed_count += 1

        if failed_count == 0:
            self.append_log(
                f"✅ MikroTik Automation finished successfully. Success: {success_count}",
                "success",
            )
        else:
            self.append_log(
                f"⚠️ MikroTik Automation completed with errors. Success: {success_count}, Failed: {failed_count}",
                "warning",
            )

        self.report_writer.end_session()
        self.tabs.setCurrentWidget(self.log_tab)

    def build_devices_tab(self):
        layout = QVBoxLayout()

        device_group = QGroupBox("Add Device")
        form = QFormLayout()

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP адреса пристрою")

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Display Name пристрою")

        self.mode_input = QComboBox()
        self.mode_input.addItems(["Ping Only", "SNMP"])

        self.snmp_version_input = QComboBox()
        self.snmp_version_input.addItems(["v2c", "v1", "v3"])

        self.community_input = QLineEdit()
        self.community_input.setText("public")

        self.snmp_port_input = QLineEdit()
        self.snmp_port_input.setText("161")

        self.transport_input = QComboBox()
        self.transport_input.addItems(["udp", "udp6", "tcp", "tcp6"])

        self.os_input = QLineEdit()
        self.os_input.setPlaceholderText("optional")

        self.force_add_input = QCheckBox("Force add")

        form.addRow("Device IP:", self.ip_input)
        form.addRow("Display Name:", self.display_name_input)
        form.addRow("Mode:", self.mode_input)
        form.addRow("SNMP Version:", self.snmp_version_input)
        form.addRow("Community:", self.community_input)
        form.addRow("SNMP Port:", self.snmp_port_input)
        form.addRow("Transport:", self.transport_input)
        form.addRow("OS:", self.os_input)
        form.addRow("", self.force_add_input)

        device_group.setLayout(form)

        self.add_button = QPushButton("Add Device")
        self.add_button.clicked.connect(self.add_ping_only_device)

        layout.addWidget(device_group)
        layout.addWidget(self.add_button)
        layout.addStretch()

        self.devices_tab.setLayout(layout)

        self.mode_input.currentTextChanged.connect(self.update_device_mode_fields)
        self.update_device_mode_fields()

    def build_bulk_tab(self):
        layout = QVBoxLayout()

        info = QLabel(
            "Bulk Add: масове додавання пристроїв.\n"
            "Колонки: IP | Display Name | Mode | SNMP Version | Community | Port | Transport | OS | Force\n"
            "Mode: ping або snmp. Force: yes/no або true/false."
        )

        self.bulk_table = QTableWidget()
        self.bulk_table.setColumnCount(9)
        self.bulk_table.setHorizontalHeaderLabels(
            [
                "IP Address",
                "Display Name",
                "Mode",
                "SNMP Version",
                "Community",
                "Port",
                "Transport",
                "OS",
                "Force",
            ]
        )
        self.bulk_table.setRowCount(10)

        for column in range(9):
            self.bulk_table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.Stretch
            )

        buttons = QHBoxLayout()

        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Selected Row")
        self.validate_bulk_button = QPushButton("Validate Table")
        self.prepare_bulk_button = QPushButton("Prepare Commands")
        self.add_all_button = QPushButton("Add All Devices")

        buttons.addWidget(self.add_row_button)
        buttons.addWidget(self.remove_row_button)
        buttons.addWidget(self.validate_bulk_button)
        buttons.addWidget(self.prepare_bulk_button)
        buttons.addWidget(self.add_all_button)

        self.add_row_button.clicked.connect(self.add_bulk_row)
        self.remove_row_button.clicked.connect(self.remove_selected_bulk_row)
        self.validate_bulk_button.clicked.connect(self.validate_bulk_list)
        self.prepare_bulk_button.clicked.connect(self.prepare_bulk_commands)
        self.add_all_button.clicked.connect(self.add_all_bulk_devices)

        layout.addWidget(info)
        layout.addWidget(self.bulk_table)
        layout.addLayout(buttons)

        self.bulk_tab.setLayout(layout)

    def build_settings_tab(self):
        layout = QHBoxLayout()

        group = QGroupBox("LibreNMS SSH Settings")
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

        group.setLayout(form)

        layout.addWidget(group)

        self.settings_tab.setLayout(layout)
        mikrotik_group = QGroupBox("MikroTik SSH Settings")
        mikrotik_form = QFormLayout()

        self.mikrotik_ssh_port_input = QLineEdit()
        self.mikrotik_ssh_port_input.setText("22")

        self.mikrotik_ssh_username_input = QLineEdit()
        self.mikrotik_ssh_username_input.setPlaceholderText("MikroTik SSH користувач")

        self.mikrotik_ssh_password_input = QLineEdit()
        self.mikrotik_ssh_password_input.setPlaceholderText("MikroTik SSH пароль")
        self.mikrotik_ssh_password_input.setEchoMode(QLineEdit.Password)

        mikrotik_form.addRow("Port:", self.mikrotik_ssh_port_input)
        mikrotik_form.addRow("Username:", self.mikrotik_ssh_username_input)
        mikrotik_form.addRow("Password:", self.mikrotik_ssh_password_input)

        mikrotik_group.setLayout(mikrotik_form)

        layout.addWidget(mikrotik_group)

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

        for device in devices:
            result = self.run_device_add(
                server,
                port,
                username,
                password,
                device["ip"],
                device["display_name"],
                device["mode"],
                device["community"],
                device["snmp_version"],
                device["port"],
                device["transport"],
                device["os_name"],
                device["force_add"],
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

    def run_device_add(
    self,
    server,
    port,
    username,
    password,
    device_ip,
    display_name,
    mode=None,
    community=None,
    snmp_version=None,
    snmp_port=None,
    transport=None,
    os_name=None,
    force_add=None,
):
        if mode is None:
            mode = "ping" if self.mode_input.currentText() == "Ping Only" else "snmp"

        if community is None:
            community = self.community_input.text().strip()

        if snmp_version is None:
            snmp_version = self.snmp_version_input.currentText()

        if snmp_port is None:
            snmp_port = self.snmp_port_input.text().strip()

        if transport is None:
            transport = self.transport_input.currentText()

        if os_name is None:
            os_name = self.os_input.text().strip()

        if force_add is None:
            force_add = self.force_add_input.isChecked()

        command = DeviceService.build_add_device_command(
            device_ip=device_ip,
            display_name=display_name,
            mode=mode,
            snmp_version=snmp_version,
            community=community,
            port=snmp_port,
            transport=transport,
            os_name=os_name,
            force_add=force_add,
        )

        ssh = SSHClient(server, int(port), username, password)

        self.append_log("────────────────────────")
        self.append_log(f"SSH connect: {username}@{server}:{port}")
        self.append_log(f"Adding Ping Only device: {device_ip}")
        self.append_log(f"Display Name: {display_name}")
        self.append_log(f"COMMAND: {command}")

        code, out, err = ssh.run_command(command)
        

        if out and out.strip():
            self.append_log(out.strip(), "info")

        if err and err.strip():
            self.append_log(err.strip(), "error")

        if code != 0:
            self.append_log(
                f"❌ Device add failed: {device_ip}. Exit code: {code}",
                "error",
            )
            self.tabs.setCurrentWidget(self.log_tab)
            return False

        self.append_log(f"✅ Device added successfully: {device_ip}", "success")
        self.tabs.setCurrentWidget(self.log_tab)
        return True

    def prepare_bulk_commands(self):
        devices, errors = self.parse_bulk_lines()

        self.append_log("────────────────────────")
        self.append_log("Bulk command preparation")

        if errors:
            for error in errors:
                self.append_log(f"❌ {error}", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        for device in devices:
            command = DeviceService.build_add_device_command(
                device_ip=device["ip"],
                display_name=device["display_name"],
                mode=device["mode"],
                snmp_version=device["snmp_version"],
                community=device["community"],
                port=device["port"],
                transport=device["transport"],
                os_name=device["os_name"],
                force_add=device["force_add"],
            )

            self.append_log(
                f"Device: {device['ip']} / {device['display_name']} / {device['mode']}"
            )
            self.append_log(f"COMMAND: {command}")
            self.append_log("")

        self.tabs.setCurrentWidget(self.log_tab)

    def parse_bulk_lines(self):
        devices = []
        errors = []

        for row in range(self.bulk_table.rowCount()):
            values = []

            for column in range(9):
                item = self.bulk_table.item(row, column)
                values.append(item.text().strip() if item else "")

            ip, display_name, mode, snmp_version, community, port, transport, os_name, force = values

            if not any(values):
                continue

            line_number = row + 1
            mode = mode.lower() if mode else "ping"
            snmp_version = snmp_version.lower() if snmp_version else "v2c"
            community = community if community else "public"
            port = port if port else "161"
            transport = transport.lower() if transport else "udp"
            force_add = force.lower() in ["yes", "true", "1", "y", "так"]

            if not ip:
                errors.append(f"Рядок {line_number}: IP порожній")
                continue

            if not is_valid_ip(ip):
                errors.append(f"Рядок {line_number}: неправильний IP: {ip}")
                continue

            if not display_name:
                errors.append(f"Рядок {line_number}: Display Name порожній")
                continue

            if mode not in ["ping", "snmp"]:
                errors.append(f"Рядок {line_number}: Mode має бути ping або snmp")
                continue

            if snmp_version not in ["v1", "v2c", "v3"]:
                errors.append(f"Рядок {line_number}: SNMP Version має бути v1, v2c або v3")
                continue

            if not port.isdigit():
                errors.append(f"Рядок {line_number}: Port має бути числом")
                continue

            if transport not in ["udp", "udp6", "tcp", "tcp6"]:
                errors.append(f"Рядок {line_number}: Transport має бути udp, udp6, tcp або tcp6")
                continue

            if mode == "ping":
                community = ""
                snmp_version = "v2c"
                port = "161"
                transport = "udp"
                os_name = "ping"

            devices.append(
                {
                    "ip": ip,
                    "display_name": display_name,
                    "mode": mode,
                    "snmp_version": snmp_version,
                    "community": community,
                    "port": port,
                    "transport": transport,
                    "os_name": os_name,
                    "force_add": force_add,
                }
            )

        if not devices and not errors:
            errors.append("Таблиця порожня")

        return devices, errors

    def validate_bulk_list(self):
        devices, errors = self.parse_bulk_lines()

        self.append_log("────────────────────────")
        self.append_log("Bulk validation")

        if errors:
            for error in errors:
                self.append_log(f"❌ {error}", "error")
        else:
            self.append_log(f"✅ Список коректний. Пристроїв: {len(devices)}", "success")

        self.tabs.setCurrentWidget(self.log_tab)

    def validate_device(self, device_ip, display_name):
        if not device_ip:
            self.append_log("❌ Device IP is empty", "error")
            return False

        if not is_valid_ip(device_ip):
            self.append_log("❌ Device IP is invalid", "error")
            return False

        if not display_name:
            self.append_log("❌ Display Name is empty", "error")
            return False

        return True

    def validate_settings(self, server, port, username, password):
        if not server:
            self.append_log("❌ Server is empty", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not port:
            self.append_log("❌ SSH port is empty", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not port.isdigit():
            self.append_log("❌ SSH port must be a number", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not username:
            self.append_log("❌ Username is empty", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        if not password:
            self.append_log("❌ Password is empty", "error")
            self.tabs.setCurrentWidget(self.settings_tab)
            return False

        return True

    def get_ssh_settings(self):
        return (
            self.server_input.text().strip(),
            self.port_input.text().strip(),
            self.username_input.text().strip(),
            self.password_input.text(),
        )

    def add_bulk_row(self):
        self.bulk_table.insertRow(self.bulk_table.rowCount())

    def remove_selected_bulk_row(self):
        selected_rows = sorted(
            set(index.row() for index in self.bulk_table.selectedIndexes()),
            reverse=True,
        )

        if not selected_rows:
            self.append_log("❌ Не вибрано рядок для видалення", "error")
            self.tabs.setCurrentWidget(self.log_tab)
            return

        for row in selected_rows:
            self.bulk_table.removeRow(row)

        self.append_log(f"✅ Видалено рядків: {len(selected_rows)}", "success")

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