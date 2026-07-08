import socket
import paramiko


class SSHClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def run_command(self, command: str, timeout: int = 60):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
                look_for_keys=False,
                allow_agent=False,
            )

            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

            out = stdout.read().decode(errors="ignore")
            err = stderr.read().decode(errors="ignore")
            exit_code = stdout.channel.recv_exit_status()

            return exit_code, out, err

        except paramiko.AuthenticationException:
            return 255, "", "SSH authentication failed: wrong username or password"

        except paramiko.SSHException as e:
            return 255, "", f"SSH error: {e}"

        except socket.timeout:
            return 255, "", "SSH connection timeout"

        except OSError as e:
            return 255, "", f"Network error: {e}"

        except Exception as e:
            return 255, "", f"Unexpected error: {e}"

        finally:
            client.close()