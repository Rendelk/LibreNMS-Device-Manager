class MikroTikService:
    @staticmethod
    def build_add_user_command(username, password, group, allowed_address):
        command = (
            "/user/add "
            f'name="{username}" '
            f'password="{password}" '
            f'group="{group}" '
        )

        if allowed_address.strip():
            clean_address = allowed_address.replace(" ", "")
            command += f'address="{clean_address}" '

        return command.strip()

    @staticmethod
    def build_remove_user_command(username):
        return f'/user/remove [find where name="{username}"]'

    @staticmethod
    def build_enable_user_command(username):
        return f'/user/enable [find where name="{username}"]'

    @staticmethod
    def build_disable_user_command(username):
        return f'/user/disable [find where name="{username}"]'

    @staticmethod
    def build_change_password_command(username, password):
        return (
            f'/user/set [find where name="{username}"] '
            f'password="{password}"'
        )

    @staticmethod
    def build_change_group_command(username, group):
        return (
            f'/user/set [find where name="{username}"] '
            f'group="{group}"'
        )

    @staticmethod
    def build_change_allowed_address_command(username, allowed_address):
        clean_address = allowed_address.replace(" ", "")
        return (
            f'/user/set [find where name="{username}"] '
            f'address="{clean_address}"'
        )

    @staticmethod
    def build_command(action, username, password="", group="", allowed_address=""):
        if action == "Add User":
            return MikroTikService.build_add_user_command(
                username=username,
                password=password,
                group=group,
                allowed_address=allowed_address,
            )

        if action == "Delete User":
            return MikroTikService.build_remove_user_command(username)

        if action == "Enable User":
            return MikroTikService.build_enable_user_command(username)

        if action == "Disable User":
            return MikroTikService.build_disable_user_command(username)

        if action == "Change Password":
            return MikroTikService.build_change_password_command(
                username,
                password,
            )

        if action == "Change Group":
            return MikroTikService.build_change_group_command(
                username,
                group,
            )

        if action == "Change Allowed Address":
            return MikroTikService.build_change_allowed_address_command(
                username,
                allowed_address,
            )

        raise ValueError(f"Unknown MikroTik action: {action}")

    @staticmethod
    def build_history_message(action, username):
        messages = {
            "Add User": f"додано користувача {username}",
            "Delete User": f"видалено користувача {username}",
            "Enable User": f"увімкнено користувача {username}",
            "Disable User": f"вимкнено користувача {username}",
            "Change Password": f"змінено пароль користувача {username}",
            "Change Group": f"змінено групу користувача {username}",
            "Change Allowed Address": (
                f"змінено Allowed Address користувача {username}"
            ),
        }

        return messages.get(action, action)