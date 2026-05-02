"""Live terminal dashboard for Immortal Agent using Rich."""

import asyncio
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

from memory import init_db, get_wrapper_stats, get_recent_events


console = Console()


def _make_wrapper_table(stats) -> Table:
    table = Table(title="Wrapper Health", expand=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Health", justify="right")
    table.add_column("Fails", justify="right")
    table.add_column("Succ", justify="right")
    table.add_column("Avg Latency (ms)", justify="right")

    for s in stats:
        total_calls = (s.get("success_count") or 0) + (s.get("fail_count") or 0)
        avg_latency = 0
        if total_calls > 0:
            avg_latency = int((s.get("total_latency_ms") or 0) / total_calls)

        status_icon = "✅" if s.get("status") == "alive" else "💀"
        health = s.get("health_score") or 0.0
        table.add_row(
            s["name"],
            status_icon + " " + (s.get("status") or ""),
            f"{health:.2f}",
            str(s.get("fail_count") or 0),
            str(s.get("success_count") or 0),
            str(avg_latency),
        )

    return table


def _make_events_panel(events) -> Panel:
    lines: list[str] = []
    for e in events:
        ts = (e.get("timestamp") or "")[:19]
        etype = e.get("event_type") or "event"
        name = e.get("wrapper_name") or "-"
        icon = {
            "alive": "💚",
            "ping_success": "💚",
            "ping_failed": "🔴",
            "all_dead": "💀",
            "repair_failed": "🔧",
            "wrapper_installed": "✨",
        }.get(etype, "•")
        lines.append(f"{icon} [{ts}] {etype} — {name}")

    text = "\n".join(lines) if lines else "No events yet. Run agent.py first."
    return Panel(Text(text), title="Recent Events", border_style="magenta")


def _make_header() -> Panel:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    title = Text(" IMMORTAL AGENT Dashboard ", style="bold white on blue")
    subtitle = Text(f"  {now}", style="dim")
    body = Text.assemble(title, "\n", subtitle)
    return Panel(body, style="bold")


def _make_layout(stats, events) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="right", ratio=2),
    )

    layout["header"].update(_make_header())
    layout["left"].update(_make_wrapper_table(stats))
    layout["right"].update(_make_events_panel(events))
    return layout


async def _refresh(live: Live, refresh_per_second: float = 1.0):
    await init_db()
    delay = 1.0 / max(refresh_per_second, 0.1)

    while True:
        stats = await get_wrapper_stats()
        events = await get_recent_events(limit=10)
        layout = _make_layout(stats, events)
        live.update(layout)
        await asyncio.sleep(delay)


def main():
    with Live(console=console, screen=True, refresh_per_second=4) as live:
        asyncio.run(_refresh(live))


if __name__ == "__main__":
    main()
