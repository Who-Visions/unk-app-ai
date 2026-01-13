#!/usr/bin/env python3
"""
Notion Rich Live CLI
====================
Interactive CLI for managing Notion integrations with rich UI elements.
Features: Static prints, progress bars, spinners, rich text.
"""

import os
import random
import sys
import time
from typing import Dict, List

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import config (mocking if needed for standalone run)
try:
    from routers.config import (NOTION_OBSERVATORY_SECRET,
                                NOTION_WHO_VISIONS_SECRET)
except ImportError:
    NOTION_WHO_VISIONS_SECRET = "ntn_mock_who_visions"
    NOTION_OBSERVATORY_SECRET = "ntn_mock_observatory"

console = Console()


class NotionCLI:
    def __init__(self):
        self.console = console
        self.secrets = {
            "Who Visions": NOTION_WHO_VISIONS_SECRET,
            "The Observatory": NOTION_OBSERVATORY_SECRET
        }
        self.selected_workspace = "The Observatory"  # Default

    def clear(self):
        self.console.clear()

    def print_header(self):
        title = Text("🧠 UNK AGENT NOTION CLI", style="bold white on blue", justify="center")
        subtitle = Text("Who Visions LLC | The Observatory", style="italic cyan", justify="center")

        grid = Table.grid(expand=True)
        grid.add_column(justify="center")
        grid.add_row(Panel(title, border_style="blue"))
        grid.add_row(subtitle)
        grid.add_row("")
        self.console.print(grid)

    def select_workspace(self):
        self.console.print(
            f"\n[bold]Configuration:[/bold] Using [cyan]{self.selected_workspace}[/cyan]")
        self.console.print(f"[dim]Token: {self.secrets[self.selected_workspace][:15]}...[/dim]\n")

    def show_spinner(self, text="Loading..."):
        """Displays a static-style spinner (rich status)."""
        with self.console.status(f"[bold green]{text}[/bold green]", spinner="dots"):
            time.sleep(1.5)  # Simulate work
        self.console.print(f"[bold green]✓ {text} Complete![/bold green]")

    def mock_fetch_pages(self) -> List[Dict]:
        """Simulate fetching pages from Notion."""
        time.sleep(0.5)
        pages = [
            {"id": "page_1", "title": "Agent Manifesto",
             "status": "Live", "last_edited": "2 mins ago"},
            {"id": "page_2", "title": "Memory Schema",
             "status": "Draft", "last_edited": "1 hour ago"},
            {"id": "page_3", "title": "Observatory Layout",
             "status": "Review", "last_edited": "Yesterday"},
            {"id": "page_4", "title": "Unk Protocol",
             "status": "Live", "last_edited": "Today"},
            {"id": "page_5", "title": "Dav3 Biography",
             "status": "Archived", "last_edited": "Last Week"},
        ]
        return pages

    def display_pages_table(self, pages: List[Dict]):
        table = Table(title=f"Pages in {self.selected_workspace}", border_style="cyan")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Title", style="bold white")
        table.add_column("Status", style="magenta")
        table.add_column("Last Edited", style="green")

        for page in pages:
            table.add_row(page["id"], page["title"], page["status"], page["last_edited"])

        self.console.print(table)

    def run_sync_demo(self):
        """Demonstrates a progress bar for syncing."""
        self.console.print("\n[bold]Initiating Sync Sequence...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:

            task1 = progress.add_task("[cyan]Connecting to Notion API...", total=100)
            task2 = progress.add_task("[magenta]Fetching Blocks...", total=100, start=False)
            task3 = progress.add_task("[green]Updating Vector Store...", total=100, start=False)

            while not progress.finished:
                # Task 1
                if not progress.tasks[0].finished:
                    progress.update(task1, advance=5)
                    if progress.tasks[0].completed >= 100:
                        progress.start_task(task2)

                # Task 2
                elif not progress.tasks[1].finished:
                    progress.update(task2, advance=3)
                    if progress.tasks[1].completed >= 100:
                        progress.start_task(task3)

                # Task 3
                elif not progress.tasks[2].finished:
                    progress.update(task3, advance=4)

                time.sleep(0.1)

        self.console.print("[bold green]✨ Sync Completed Successfully![/bold green]")

    def live_dashboard(self):
        """Shows a live updating dashboard panel."""
        self.console.print("\n[bold]Live Agent Observatory (Press Ctrl+C to exit)[/bold]")

        def generate_content():
            stats_table = Table.grid(expand=True)
            stats_table.add_column()
            stats_table.add_column(justify="right")
            stats_table.add_row("Active Agents", "[green]4[/green]")
            stats_table.add_row("Memory Usage", f"[yellow]{random.randint(40, 60)}%[/yellow]")
            stats_table.add_row("API Latency", f"[cyan]{random.randint(100, 300)}ms[/cyan]")

            return Panel(
                stats_table,
                title="System Status",
                border_style="green"
            )

        try:
            with Live(generate_content(), refresh_per_second=4) as live:
                for _ in range(20):  # Run for 5 seconds then exit demo
                    time.sleep(0.25)
                    live.update(generate_content())
        except KeyboardInterrupt:
            pass

        self.console.print("[dim]Live view closed.[/dim]")

    def main_menu(self):
        while True:
            self.clear()
            self.print_header()
            self.select_workspace()

            self.console.print(Panel(
                "[1] 📋 List Pages\n"
                "[2] 🔄 Sync Teamspace\n"
                "[3] 📡 Live Observatory\n"
                "[4] ⚙️  Switch Workspace\n"
                "[q] 🚪 Quit",
                title="Menu",
                border_style="blue"
            ))

            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "q"], default="1")

            if choice == "1":
                self.show_spinner("Fetching Page Metadata")
                pages = self.mock_fetch_pages()
                self.display_pages_table(pages)
                Prompt.ask("\nPress Enter to continue")

            elif choice == "2":
                self.run_sync_demo()
                Prompt.ask("\nPress Enter to continue")

            elif choice == "3":
                self.live_dashboard()
                Prompt.ask("\nPress Enter to continue")

            elif choice == "4":
                new_ws = Prompt.ask("Choose Workspace", choices=[
                                    "Who Visions", "The Observatory"], default="Who Visions")
                self.selected_workspace = new_ws
                self.show_spinner("Authing with new context")

            elif choice == "q":
                self.console.print("[bold]Goodbye![/bold] 👋")
                break


if __name__ == "__main__":
    try:
        cli = NotionCLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
