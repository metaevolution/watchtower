from datetime import datetime
import json
from abc import ABC, abstractmethod
from uuid import uuid4

from selenium import webdriver

import platform
import re
import subprocess
import socket
import requests
import os


class SchedulableCheck(ABC):
    def __init__(self, target: str, interval: int = 60, options: dict = None):
        self.name = self.__class__.__name__
        self.interval = interval
        self.options = options if options else {}
        self.target = target
        self.last_run_successful = None
        self.last_run_time = None
        self.stdout = None
        self.test_id = str(uuid4())
        self.extended_results = ""
        self.extended = ""

    @abstractmethod
    def run(self):
        raise NotImplementedError("Subclasses must implement the run() method.")

    def to_dict(self, include_private=False):
        filtered_dict = {
            key: value
            for key, value in self.__dict__.items()
            if include_private or not key.startswith("_")
        }
        return filtered_dict

    def to_json(self, include_private=False):
        return json.dumps(self.to_dict(include_private))


class PingCheck(SchedulableCheck):
    def _is_ping_success(self, result: str) -> bool:
        self.stdout = result.stdout.decode("UTF-8")
        packet_loss = re.search("\d+\.\d+% packet loss", self.stdout)

        if packet_loss:
            self.extended_results = packet_loss.group(0)

        result.stdout.decode("UTF-8")

        return True if result.returncode == 0 else False

    def _do_ping(self) -> str:
        count_flag = f"-n" if platform.system().lower() == "windows" else f"-c"
        wait_flag = f"-w" if platform.system().lower() == "windows" else f"-w"
        timeout = self.options.get("timeout", 5)
        count = self.options.get("count", 5)

        result = subprocess.run(
            ["ping", count_flag, f"{count}", wait_flag, str(timeout), self.target],
            capture_output=True,
        )
        return result

    def run(self):
        result = self._do_ping()
        return self._is_ping_success(result)


class TcpCheck(SchedulableCheck):
    def _validate_options(self):
        if not self.options.get("port"):
            raise Exception("TcpCheck is missing require option: 'port'")

    def run(self):
        self._validate_options()

        port = self.options.get("port")
        timeout = self.options.get("timeout", 5)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(self.timeout)
        try:
            self.extended_results = ""
            client_socket.connect((self.target, self.port))
            return True
        except socket.timeout:
            self.extended_results = "Connection timed out."
            return False
        except ConnectionRefusedError:
            self.extended_results = "Connection refused (server may not be available)."
            return False
        except Exception as e:
            self.extended_results = f"Socket error: {e}"
            return False
        finally:
            client_socket.close()


class DnsCheck(SchedulableCheck):
    # TODO: Ability to select another resolver

    def _validate_options(self):
        pass

    def run(self):
        self._validate_options()
        timeout = self.options.get("timeout", 5)

        try:
            ip_address = socket.gethostbyname(self.target)
            self.extended = (
                f"DNS resolution for {self.target} succeeded. IP address: {ip_address}"
            )
            return True
        except socket.gaierror:
            self.extended = f"DNS resolution for {self.target} failed. Could not resolve the domain."
            return False
        except Exception as e:
            self.extended = "Error:", e
            return False


class SpeedTestCheck(SchedulableCheck):
    # TODO: Finish this...

    def __init__(self, target: str, interval=60, options={}):
        super().__init__(target=target, interval=interval, options=options)

    def run(self):
        timeout = self.options.get("timeout", 5)
        pass


class HttpStatusCheck(SchedulableCheck):
    def run(self):
        timeout = self.options.get("timeout", 5)
        expected_status_codes = self.options.get("expected_status_codes", [200])
        try:
            r = requests.get(self.target, timeout=timeout)
        except requests.exceptions.ConnectionError:
            return False
        self.extended_results = f"HTTP Status Code: {r.status_code}"
        if r.status_code in expected_status_codes:
            return True
        else:
            return False


class WebDriverFactory:
    def __init__(self):
        self.chrome_driver = None
        self.firefox_driver = None

    def get_driver(self, browser="chrome", options={}):
        match browser.lower():
            case "chrome":
                if not self.chrome_driver:
                    from selenium.webdriver.chrome.options import Options

                    options = Options()
                    options.add_argument("--headless")
                    self.chrome_driver = webdriver.Chrome(options=options)
                return self.chrome_driver
            case "firefox":
                if not self.firefox_driver:
                    from selenium.webdriver.firefox.options import Options

                    options = Options()
                    options.add_argument("--headless")
                    self.firefox_driver = webdriver.Firefox(options=options)
                return self.firefox_driver


webdriver_factory = WebDriverFactory()


class BrowserCheck(SchedulableCheck):
    def __init__(self, target: str, interval=60, options={}):
        super().__init__(target=target, interval=interval, options=options)
        self.target = target
        self.timeout = options.get("timeout") or 5
        self.screenshot_dir = options.get("screenshot_dir") or "./screenshots/"
        self.browser = options.get("browser") or "chrome"

    def run(self):
        driver = webdriver_factory.get_driver(self.browser)
        current_datetime = datetime.now()

        domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        domain_match = re.findall(domain_pattern, self.target)
        if domain_match:
            domain = domain_match.group(0)
            screenshot_filename = f"{domain}.png"
        else:
            screenshot_filename = (
                f"{current_datetime.strftime('%Y-%m-%d-%H-%M-%S')}.png"
            )

        screenshot_full_path = os.path.join(self.screenshot_dir, screenshot_filename)
        self.extended_results = f"saved screenshot to {screenshot_full_path}"

        try:
            driver.get(self.target)
            driver.save_screenshot(screenshot_full_path)
            return True
        except:
            return False
