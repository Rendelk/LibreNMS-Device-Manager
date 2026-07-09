import shlex


class DeviceService:
    @staticmethod
    def build_add_device_command(
        device_ip: str,
        display_name: str,
        mode: str = "ping",
        snmp_version: str = "v2c",
        community: str = "public",
        port: str = "161",
        transport: str = "udp",
        os_name: str = "",
        force_add: bool = False,
    ) -> str:
        command = (
            "cd /opt/librenms && "
            "sudo -u librenms ./lnms device:add "
            f"{shlex.quote(device_ip)} "
            f"-d {shlex.quote(display_name)} "
        )

        if force_add:
            command += "-f "

        if mode == "ping":
            command += "-P -o ping "
            return command.strip()

        if snmp_version == "v1":
            command += "-1 "
        elif snmp_version == "v2c":
            command += "-2 "
        elif snmp_version == "v3":
            command += "-3 "

        if community:
            command += f"-c {shlex.quote(community)} "

        if port:
            command += f"-r {shlex.quote(str(port))} "

        if transport:
            command += f"-t {shlex.quote(transport)} "

        if os_name:
            command += f"-o {shlex.quote(os_name)} "

        return command.strip()