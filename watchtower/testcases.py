import time
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from rich import print
from watchtower.checks import SchedulableCheck, BrowserCheck, DnsCheck, HttpStatusCheck, PingCheck, SpeedTestCheck, TcpCheck
from watchtower.config import AppConfig
from watchtower.models import Config, Host, Check, CheckTypes
from watchtower.logging_config import logger
from watchtower.exceptions import CheckNotFoundError


class TestGroup:
    def __init__(self, name:str ):
        self.name = name
        self.failing_checks = []
        self.checks = []

    def add(self, test: SchedulableCheck):
        self.checks.append(test)


class StateLog:
    def __init__(self):
        self.log = []
        # TODO: config max logs and truncate when hit

    def add(self, state):
        self.log.append(state)

    def to_json(self):
        results = []
        for state in self.log:
            results.append(state.__dict__)
        container = {"state_log": results}
        return container


class State:
    def __init__(self, test, previous_state, latest_state):
        self.test = test.__dict__
        self.previous_state = previous_state
        self.latest_state = latest_state
        self.timestamp = datetime.now()


check_mapping = {
    "ping": PingCheck,
    "browser": BrowserCheck,
    "http_status": HttpStatusCheck,
    "tcp": TcpCheck,
    "dns": DnsCheck,
    "speedtest": SpeedTestCheck
    # Add more mappings as needed
}


def get_check_class(check_name:str) -> Callable:
    """Returns a check's class from name"""
    return check_mapping.get(check_name)


class TestSuite:
    def __init__(self, scheduler=None, state_log=None):
        self.scheduler = scheduler or BackgroundScheduler()
        self.state_log = state_log or StateLog()        
        self.groups = []


    def reload(self):
        self.groups = []        
        self.stop()
        self.start()

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    def _group_tests(self, check, group_name):
        matching_group = [group for group in self.groups if group.name == group_name]
        if len(matching_group) == 1:
            group = matching_group[0]
            logger.debug(f"Group: '{group.name}' already exists.")  # debug log
            group.add(check)
        elif len(matching_group) == 0:
            logger.debug(f"Creating Group: {group_name} ")  # debug log
            group = TestGroup(group_name)
            group.add(check)
            self.groups.append(group)
        return group

    def add_test(self, host: Host, check: SchedulableCheck):
        if not host.group:
            group = "Ungrouped"

        g = self._group_tests(check, host.group)

        trigger = IntervalTrigger(seconds=check.interval)
        self.scheduler.add_job(self.run_test, trigger=trigger, args=(check, g))

    def run_test(self, test, group):
        last_state = test.last_run_successful
        test_result = test.run()
        current_datetime = datetime.now()
        test.last_run_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        test.last_run_successful = test_result
        if last_state != test.last_run_successful:
            self.state_log.add(State(test, last_state, test.last_run_successful))

        if test_result == False:
            if test.test_id not in group.failing_checks:
                group.failing_checks.append(test.test_id)
        elif test_result == True:
            group.failing_checks = [
                failing_checks
                for failing_checks in group.failing_checks
                if failing_checks != test.test_id
            ]
        return test_result

    def to_json(self):
        root_container = {'groups': []}
        for group in self.groups:
            group_container = {
                "name": group.name,
                "failing_checks": group.failing_checks,
                "checks": [],
            }
            for test in group.checks:
                group_container["checks"].append(
                    test.to_dict()

                )  # BUG: This is not ideal, non-serializable types cannot be used
            root_container['groups'].append(group_container)
        states = []
        # for state in self.state_log.log:
        #    states.append(state.__dict__)
        # state_container = {"state_log": states}
        # root_container.append(state_container)
        return root_container

    def initialize_tests(self, config: Config):
        for host in config.hosts:
            for check in host.checks:
                self.add_test(host=host, check=self.initialize_check(host, check))
        print(f"Loaded Tests: {self.groups}")

    def initialize_check(self, host: Host, check: Check):
        if not check.type.upper() in CheckTypes.__members__:
            error_msg = f"No test type found to handle: '{check.type}'. Must be one of: '{CheckTypes.__members__}'"
            logger.warning(error_msg)
            raise CheckNotFoundError(error_msg)

        if check.enabled == False:
            logger.debug("Check '%s' is disabled, ignoring...", check.name)
            return

        check_class = get_check_class(check.type)

        if check_class:
            return check_class(
                target=host.target,
                interval=check.interval,
                options=check.options,
            )

    def create_test(self, name, group, target, tests):
        for test_type, test_params in tests.items():
            print(f"test type: {test_type}")
            match test_type:
                case "ping":
                    print("PING")
                    self.add_test(
                        PingCheck(
                            target,
                            test_params.get("count", 1),
                            test_params.get("timeout", SchedulableCheck.DEFAULT_TIMEOUT),
                            name,
                            test_params.get("interval", SchedulableCheck.DEFAULT_INTERVAL),
                        ),
                        group,
                    )
                case "port":
                    self.add_test(
                        TcpCheck(
                            target,
                            test_params.get("port", 80),
                            test_params.get("timeout", SchedulableCheck.DEFAULT_TIMEOUT),
                            name,
                            test_params.get("interval", SchedulableCheck.DEFAULT_INTERVAL),
                        ),
                        group,
                    )
                case "dns":
                    self.add_test(
                        DnsCheck(
                            target,
                            test_params.get("timeout", SchedulableCheck.DEFAULT_TIMEOUT),
                            name,
                            test_params.get("interval", SchedulableCheck.DEFAULT_INTERVAL),
                            resolver=test_params.get("resolver", None),
                        ),
                        group,
                    )
                case "http_status":
                    self.add_test(
                        HttpStatusCheck(
                            test_params.get("url", ""),
                            name=name,
                            expected_status_codes=test_params.get(
                                "expected_statuses", [200]
                            ),
                            interval=test_params.get(
                                "interval", SchedulableCheck.DEFAULT_INTERVAL
                            ),
                            timeout=test_params.get(
                                "timeout", SchedulableCheck.DEFAULT_TIMEOUT
                            ),
                        ),
                        group,
                    )
                case "speedtest":
                    print("SPEEDTEST")
                case "browser":
                    print("BROWSER")
