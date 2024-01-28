import requests
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Check:
    test_id: str
    interval: int
    last_run_successful: Optional[bool]
    last_run_time: str
    name: str
    options: Dict
    stdout: Optional[str]
    extended_results: Optional[str]
    extended: Optional[str]
    target: str

    def __str__(self):
        return f"Check(id={self.id}, name={self.name}, target={self.target})"
    
    @classmethod
    def from_dict(cls, check_dict):
        return cls(**check_dict)    

@dataclass
class Group:
    failing_checks: List[str]
    name: str
    checks: List[Check]

    def __str__(self):
        return f"Group(group_name={self.group_name}, checks={len(self.checks)} checks)"
    
    @classmethod
    def from_dict(cls, check_dict):
        checks_data = check_dict.pop("checks", [])
        checks_list = [Check.from_dict(check_data) for check_data in checks_data]
        return cls(checks=checks_list, **check_dict)    

@dataclass
class DashboardResponse:
    groups: List[Group]

    def __str__(self):
        return f"ApiResponse(groups={len(self.groups)} groups)"
    
    @classmethod
    def from_dict(cls, results_dict):
        group_data = results_dict.get("groups", [])
        group_list = [Group.from_dict(group_data) for group_data in group_data]
        results_dict.pop("groups")
        return cls(groups=group_list, **results_dict)



class Client:
    def __init__(self, url="http://127.0.0.1:5000"):
        self.url = url
        self.data = []

    def fetch_data(self, path:str):
        response = requests.get(f"{self.url}{path}")
        json_data = response.json()
        self.data = json_data
        return json_data
    
    def fetch_scoreboard(self) -> dict:
        return DashboardResponse.from_dict(self.fetch_data(path="/api/scoreboard"))

