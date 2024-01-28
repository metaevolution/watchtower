from __future__ import annotations

try:
    import httpx
except ImportError:
    raise ImportError("Please install httpx with 'pip install httpx' ")

import argparse
import datetime
import time
from itertools import cycle

from rich import print
from rich.table import Table
from rich.tree import Tree
from textual import work
from textual.app import App, ComposeResult, RenderResult
from textual.containers import Container, HorizontalScroll, VerticalScroll
from textual.widget import Widget
from textual.widgets import Footer, Header, Log, Pretty, Static, TabbedContent
from watchtower.client import Client
from watchtower.logging_config import logger


class Status(Static):
    def on_mount(self) -> None:
        table = Table()
        self.update(table)


class WatchTowerClient(App):
    # CSS_PATH = "watchtower.tcss"
    # CSS_PATH = "grid_layout6_row_span.tcss"

    def __init__(self, api_url: str = "http://127.0.0.1:5000") -> None:
        self.api_url = api_url
        self.connected = False
        super().__init__()

    def compose(self) -> ComposeResult:
        self.logo = ""

        yield Static(self.logo, id="current_time")
        yield Header()
        yield Static(id="notification")

        with TabbedContent("Overall", "Table", "Tree", "Log"):
            yield Status(id="tree2", classes="box")
            yield Status(id="table", classes="box")
            yield Status(id="tree", classes="box")
            yield Static(id="log", classes="box")

        # yield Footer()

    def on_mount(self) -> None:
        self.fetch_scoreboard()
        self.update_time()
        self.client = Client(self.api_url)
        self.title = "WATCHTOWER TERMINAL"

    async def populate_detail_tree(self, results):
        tree = Tree("System Status", guide_style="bright_black")
        for group in results.groups:
            if len(group.failing_checks) > 0:
                group_status = (
                    f"[bold red][Problem][/bold red] [bold]{group.name}[/bold]"
                )
            else:
                group_status = (
                    f"[bold green][Operational][/bold green] [bold]{group.name}[/bold]"
                )
            g = tree.add(group_status)

            for check in group.checks:
                t = g.add(check.name)

                status = (
                    "[bold green][PASS][/bold green]"
                    if check.last_run_successful
                    else "[bold red][FAIL][/bold red]"
                    if check.last_run_successful is False
                    else "[bold gray][PENDING][/bold gray]"
                )
                t.add(f"{status} {check.name}")
        return tree

    async def populate_summary_tree(self, results):
        tree = Tree("Overall Status", guide_style="bright_black")
        status = f"["
        for group in results.groups:
            for check in group.checks:
                if check.last_run_successful:
                    status += f"[green]\u25A0[/green]"
                elif check.last_run_successful == False:
                    status += f"[red]\u25A0[/red]"
                else:
                    status += f"[gray]\u25A0[/gray]"

        status += "]"
        tree.add(f"{status}")
        return tree

    async def populate_table(self, results):
        table = Table(
            "Group",
            "Check",
            "Target",
            "Last Run",
            "Status",
            "Interval",
            "Details",
            title="System Status",
        )
        for group in results.groups:
            for check in group.checks:
                if check.last_run_successful:
                    status = f"[bold green][PASS][/bold green]"
                elif check.last_run_successful == False:
                    status = f"[bold red][FAIL][/bold red]"
                else:
                    status = f"[bold gray][PENDING][/bold gray]"
                table.add_row(
                    group.name,
                    check.name,
                    check.target,
                    check.last_run_time,
                    str(status),
                    str(check.interval),
                    check.extended_results,
                )
        return table

    def error(self, msg):
        self.call_from_thread(
            self.query_one("#log", Static).update, f"[bold red]{msg}[/bold red]"
        )

    @work(exclusive=False, thread=True)
    async def fetch_scoreboard(self) -> None:
        """Fetch data from REST api."""
        while True:
            try:
                results = self.client.fetch_scoreboard()
                self.connected = True
            except Exception as e:
                self.error(f"Failed to connect to server '{e}'")
                self.connected = False

                time.sleep(5)
                continue
            # POPULATE TREE DETAIL VIEW
            tree = await self.populate_detail_tree(results)

            # POPULATE TREE SUMMARY VIEW
            tree2 = await self.populate_summary_tree(results)

            # POPULATE TABLE VIEW
            table = await self.populate_table(results)

            self.call_from_thread(self.query_one("#table", Status).update, table)
            self.call_from_thread(self.query_one("#tree", Status).update, tree)
            self.call_from_thread(self.query_one("#tree2", Status).update, tree2)

            time.sleep(5)

    @work(exclusive=False, thread=True)
    async def update_time(self) -> None:
        while True:
            if self.connected:
                connection_status = f"[bold green][Connected][/bold green]"
            else:
                connection_status = f"[bold red][Disconnected][/bold red]"
            self.logo = f"""
   /\   /\    
  /  \ /  \  
 /  WATCH  \    Current Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}
 \  TOWER  /    API Server: {self.api_url} {connection_status}
  \  / \  /  
   \/   \/
"""
            self.call_from_thread(
                self.query_one("#current_time", Static).update, self.logo
            )
            time.sleep(1)


def run():
    parser = argparse.ArgumentParser(
        prog="WatchTower",
        description="WatchTower is a flexable/lightweight system monitoring dashboard.",
        epilog="Text at the bottom of help",
    )
    parser.add_argument("-u", "--url", help="URL of the WatchTower API server.")
    args = parser.parse_args()

    if args.url:
        app = WatchTowerClient(args.url)
    else:
        app = WatchTowerClient()

    app.run()


if __name__ == "__main__":
    run()
