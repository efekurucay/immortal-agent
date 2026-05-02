"""
dashboard.py — Live Rich terminal dashboard for ImmortalAgent.

Shows:
  - Agent uptime + generation counter
  - Per-wrapper: status, health score, success/fail counts, P95 latency, circuit state
  - Rate budget gauge
  - Last 10 events

Usage: python dashboard.py
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    raise ImportError("pip install rich")

from memory import init_db, get_wrapper_stats, get_recent_events
from rate_budget import BUDGET

console = Console()
_start_time = time.time()


def _uptime() -> str:
    s = int(time.time() - _start_time)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _health_color(score: float) -> str:
    if score >= 0.75:
        return "green"
    if score >= 0.4:
        return "yellow"
    return "red"


async def _build_layout() -> Layout:
    stats = await get_wrapper_stats()
    events = await get_recent_events(10)
    budget = BUDGET.stats()

    # ── Wrapper table ──────────────────────────────────────────────
    tbl = Table(title="Wrappers", expand=True, border_style="dim")
    tbl.add_column("Name", style="bold")
    tbl.add_column("Status", justify="center")
    tbl.add_column("Health", justify="right")
    tbl.add_column("Succ", justify="right")
    tbl.add_column("Fail", justify="right")
    tbl.add_column("AvgLat", justify="right")

    for s in stats:
        name = s["name"]
        status = s.get("status", "?")
        score = float(s.get("health_score") or 0)
        succ = s.get("success_count", 0)
        fail = s.get("fail_count", 0)
        total = max(succ + fail, 1)
        avg_lat = int((s.get("total_latency_ms") or 0) / total)
        color = _health_color(score)
        tbl.add_row(
            name,
            Text("✅" if status == "alive" else "💀", justify="center"),
            Text(f"{score:.2f}", style=color),
            str(succ),
            str(fail),
            f"{avg_lat}ms",
        )

    # ── Event log ─────────────────────────────────────────────────
    ev_lines = []
    for e in events:
        ts = e.get("timestamp", "")[:19]
        etype = e.get("event_type", "")
        wname = e.get("wrapper_name", "")
        ev_lines.append(f"[dim]{ts}[/dim] [bold]{etype}[/bold] [cyan]{wname}[/cyan]")
    ev_panel = Panel(
        "\n".join(ev_lines) or "No events yet",
        title="Recent Events",
        border_style="dim",
    )

    # ── Header ────────────────────────────────────────────────────
    alive = sum(1 for s in stats if s.get("status") == "alive")
    rpm = budget["calls_this_minute"]
    header = Panel(
        f"🧬 [bold green]ImmortalAgent v3.0[/bold green]  "
        f"uptime=[yellow]{_uptime()}[/yellow]  "
        f"alive=[green]{alive}/{len(stats)}[/green]  "
        f"rpm=[cyan]{rpm}/{budget['max_rpm']}[/cyan]  "
        f"[dim]{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC[/dim]",
        border_style="green",
    )

    layout = Layout()
    layout.split_column(
        Layout(header, size=3),
        Layout(tbl, ratio=2),
        Layout(ev_panel, ratio=1),
    )
    return layout


async def run_dashboard():
    await init_db()
    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            layout = await _build_layout()
            live.update(layout)
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_dashboard())
