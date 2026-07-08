import shlex


class DeviceService:
    @staticmethod
    def build_add_ping_only_command(device_ip: str) -> str:
        return f"cd /opt/librenms && sudo -u librenms ./lnms device:add --ping-only {shlex.quote(device_ip)}"

    @staticmethod
    def build_set_display_name_command(device_ip: str, display_name: str) -> str:
        ip = device_ip.replace("'", "\\'")
        name = display_name.replace("'", "\\'")

        php_code = (
            f"$device = \\App\\Models\\Device::where('hostname', '{ip}')->first(); "
            f"if (!$device) {{ echo 'DEVICE_NOT_FOUND'; return; }} "
            f"$device->display = '{name}'; "
            f"$device->display_template = '{name}'; "
            f"$device->save(); "
            f"echo 'DISPLAY_UPDATED';"
        )

        return (
            "cd /opt/librenms && "
            "sudo -u librenms php artisan tinker "
            f"--execute={shlex.quote(php_code)}"
        )