from dataclasses import dataclass, field
from typing import List
from enum import Enum

class CheckTypes(Enum):
    PING = "ping"
    DNS = "dns"
    PORT = "port"
    HTTP_STATUS = "http_status"
    BROWSER = "browser"


def validate_test_type(value):
    if not isinstance(value, CheckTypes):
        raise ValueError(f"Invalid test type: {value}")
    return value

@dataclass
class Check:
    type: str = field(metadata={'validate': validate_test_type})
    enabled: bool
    display_name: str
    interval: int
    options: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, check_dict):
        return cls(**check_dict)

@dataclass
class Host:
    name: str
    group: str
    target: str
    checks: List[Check]

    @classmethod
    def from_dict(cls, target_dict):
        checks_data = target_dict.pop("checks", [])
        checks_list = [Check.from_dict(check_data) for check_data in checks_data]
        return cls(checks=checks_list, **target_dict)

@dataclass
class Config:
    config_version: int
    hosts: List[Host]

    @classmethod
    def from_dict(cls, config_dict):
        hosts_data = config_dict.get("hosts", [])
        host_list = [Host.from_dict(hosts_data) for hosts_data in hosts_data]
        config_dict.pop("hosts")
        return cls(hosts=host_list, **config_dict)