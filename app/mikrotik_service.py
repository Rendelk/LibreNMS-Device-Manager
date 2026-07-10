class MikroTikService:
    @staticmethod
    def escape_routeros_string(value: str) -> str:
        """
        Екранує значення для безпечного використання
        всередині подвійних лапок RouterOS.

        Особливо важливо:
        $ передається як \\24, щоб RouterOS не сприймав
        його як початок змінної.
        """
        if value is None:
            return ""

        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("$", "\\24")
            .replace("\r", "")
            .replace("\n", "")
        )

    @staticmethod
    def build_add_user_command(
        username: str,
        password: str,
        group: str,
        allowed_address: str = "",
    ) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)
        safe_password = MikroTikService.escape_routeros_string(password)
        safe_group = MikroTikService.escape_routeros_string(group)

        command = (
            "/user/add "
            f'name="{safe_username}" '
            f'password="{safe_password}" '
            f'group="{safe_group}"'
        )

        if allowed_address.strip():
            clean_address = allowed_address.replace(" ", "")
            safe_address = MikroTikService.escape_routeros_string(
                clean_address
            )
            command += f' address="{safe_address}"'

        return command

    @staticmethod
    def build_remove_user_command(username: str) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)

        return (
            '/user/remove '
            f'[find where name="{safe_username}"]'
        )

    @staticmethod
    def build_enable_user_command(username: str) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)

        return (
            '/user/enable '
            f'[find where name="{safe_username}"]'
        )

    @staticmethod
    def build_disable_user_command(username: str) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)

        return (
            '/user/disable '
            f'[find where name="{safe_username}"]'
        )

    @staticmethod
    def build_change_password_command(
        username: str,
        password: str,
    ) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)
        safe_password = MikroTikService.escape_routeros_string(password)

        return (
            '/user/set '
            f'[find where name="{safe_username}"] '
            f'password="{safe_password}"'
        )

    @staticmethod
    def build_change_group_command(
        username: str,
        group: str,
    ) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)
        safe_group = MikroTikService.escape_routeros_string(group)

        return (
            '/user/set '
            f'[find where name="{safe_username}"] '
            f'group="{safe_group}"'
        )

    @staticmethod
    def build_change_allowed_address_command(
        username: str,
        allowed_address: str,
    ) -> str:
        safe_username = MikroTikService.escape_routeros_string(username)

        clean_address = allowed_address.replace(" ", "")
        safe_address = MikroTikService.escape_routeros_string(
            clean_address
        )

        return (
            '/user/set '
            f'[find where name="{safe_username}"] '
            f'address="{safe_address}"'
        )

    @staticmethod
    def build_command(
        action: str,
        username: str,
        password: str = "",
        group: str = "",
        allowed_address: str = "",
    ) -> str:
        if action == "Add User":
            return MikroTikService.build_add_user_command(
                username=username,
                password=password,
                group=group,
                allowed_address=allowed_address,
            )

        if action == "Delete User":
            return MikroTikService.build_remove_user_command(
                username
            )

        if action == "Enable User":
            return MikroTikService.build_enable_user_command(
                username
            )

        if action == "Disable User":
            return MikroTikService.build_disable_user_command(
                username
            )

        if action == "Change Password":
            return MikroTikService.build_change_password_command(
                username=username,
                password=password,
            )

        if action == "Change Group":
            return MikroTikService.build_change_group_command(
                username=username,
                group=group,
            )

        if action == "Change Allowed Address":
            return (
                MikroTikService
                .build_change_allowed_address_command(
                    username=username,
                    allowed_address=allowed_address,
                )
            )

        raise ValueError(
            f"Unknown MikroTik action: {action}"
        )

    @staticmethod
    def build_history_message(
        action: str,
        username: str,
    ) -> str:
        messages = {
            "Add User": (
                f"додано користувача {username}"
            ),
            "Delete User": (
                f"видалено користувача {username}"
            ),
            "Enable User": (
                f"увімкнено користувача {username}"
            ),
            "Disable User": (
                f"вимкнено користувача {username}"
            ),
            "Change Password": (
                f"змінено пароль користувача {username}"
            ),
            "Change Group": (
                f"змінено групу користувача {username}"
            ),
            "Change Allowed Address": (
                "змінено Allowed Address "
                f"користувача {username}"
            ),
        }

        return messages.get(
            action,
            action,
        )

    @staticmethod
    def build_safe_log_message(
        action: str,
        username: str,
        group: str = "",
        allowed_address: str = "",
    ) -> str:
        """
        Повертає безпечний текст для логів.
        Пароль сюди навмисно не передається.
        """
        parts = [
            f'action="{action}"',
            f'user="{username}"',
        ]

        if action in ["Add User", "Change Group"] and group:
            parts.append(f'group="{group}"')

        if (
            action in ["Add User", "Change Allowed Address"]
            and allowed_address
        ):
            parts.append(
                f'allowed_address="{allowed_address}"'
            )

        if action in ["Add User", "Change Password"]:
            parts.append('password="********"')

        return "MikroTik command: " + ", ".join(parts)