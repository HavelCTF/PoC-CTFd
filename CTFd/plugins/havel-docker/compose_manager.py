import subprocess
import os
import json
import tempfile
import shutil

from CTFd.models import db


class ComposeManager:
    def __init__(self, compose_settings):
        self.compose_settings = compose_settings
        self.temp_dir = tempfile.mkdtemp()

    @staticmethod
    def check(filename: str, compose_content: str) -> bool:
        """
        Checks if a compose file is valid and can be run.

        Args:
            filename (str): The filename to write the compose content to
            compose_content (str): The content of the compose.yml file as a string

        Returns:
            bool: True if the file was created and validated successfully
        """
        try:
            subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
        except Exception:
            raise Exception("Docker Compose is not installed. Please install Docker Compose and try again.")

        temp_dir = tempfile.mkdtemp()
        file_path: str = os.path.join(temp_dir, filename)

        file_exists = os.path.exists(file_path)

        if not file_exists:
            with open(file_path, 'w') as f:
                f.write(compose_content)

        is_valid = True
        try:
            subprocess.run(["docker", "compose", "--file", file_path, "config", "--quiet"], check=True)
        except Exception:
            is_valid = False

        shutil.rmtree(temp_dir)
        return is_valid


    def run(self, filename: str, compose_content: str):
        """
        Runs a docker compose file.

        Args:
            filename (str): The name of the docker compose file
            compose_content (str): The content of the compose.yml file as a string
        """
        file_path: str = os.path.join(self.temp_dir, filename)

        with open(file_path, 'w') as f:
            f.write(compose_content)

        result = subprocess.run(["docker", "compose", "--file", file_path, "up", "-d"], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception("Error starting Docker Compose.\n", result.stderr)


    def stop(self, filename: str):
        """
        Stops a running docker compose file.

        Args:
            filename (str): The name of the docker compose file
        """
        file_path = os.path.join(self.temp_dir, filename)
        result = subprocess.run(["docker", "compose", "--file", file_path, "down", "--volumes"], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception("Error stopping Docker Compose.")


    def reset(self, filename: str, compose_content: str):
        """
        Recreates a docker compose file.

        Args:
            filename (str): The name of the docker compose file
            compose_content (str): The content of the compose.yml file as a string
        """
        self.stop(filename)
        self.run(filename, compose_content)


    def is_running(self, filename: str) -> bool:
        """
        Checks if a docker compose file is running.

        Args:
            filename (str): The name of the docker compose file

        Returns:
            bool: True if the file is running, False otherwise
        """
        file_path: str = os.path.join(self.temp_dir, filename)

        if not os.path.exists(file_path):
            return False

        result_running_services = subprocess.run(
            ["docker", "compose", "--file", file_path, "ps", "--services", "--filter", "status=running"],
            capture_output=True, text=True)
        result_services = subprocess.run(
            ["docker", "compose", "--file", file_path, "config", "--services"],
            capture_output=True, text=True)

        if result_running_services.returncode != 0 or result_services.returncode != 0:
            return False
        return result_running_services.stdout == result_services.stdout


    def get_config(self, filename: str, compose_content: str = "") -> object:
        """
        Gets the configuration of a docker compose file.

        Args:
            filename (str): The name of the docker compose file

        Returns:
            object: The configuration of the compose file
        """
        file_path: str = os.path.join(self.temp_dir, filename)

        if not os.path.exists(file_path):
            if (compose_content != ""):
                with open(file_path, 'w') as f:
                    f.write(compose_content)
            else:
                raise Exception("File does not exist")

        result = subprocess.run(
            ["docker", "compose", "--file", file_path, "config", "--format", "json"],
            capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception("Error getting compose config")

        config = json.loads(result.stdout)

        services = []
        ports = []
        for services_name, service_data in config["services"].items():
            services.append(services_name)
            if "ports" in service_data:
                for port in service_data["ports"]:
                    ports.append(port["published"])

        return {
            "services": list(config["services"].keys()),
            "ports": ports
        }


    def get_settings(self):
        """
        Gets the settings for the compose manager.

        Returns:
            dict: The settings for the compose manager
        """
        return {
            "hostname": self.compose_settings.hostname
        }


    def set_settings(self, settings):
        """
        Sets the settings for the compose manager.

        Args:
            settings (dict): The settings to set
        """
        self.compose_settings.hostname = settings["hostname"]
        db.session.commit()
