"""Simple terminal dashboard for Immortal Agent status."""
import asyncio
import os
from datetime import datetime
from memory import init_db, get_wrapper_stats, get_recent_events


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def bar(value: int, max_value: int, width: int = 20) -> str:
    filled = int((value / max(max_value, 1)) * width)
    return "█" * filled + "░" * (width - filled)


async def render():
    await init_db()
    clear()

    stats = await get_wrapper_stats()
    events = await get_recent_events(limit=10)

    print("\n🧬 IMMORTAL AGENT — DASHBOARD")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

    print("┌─ WRAPPER STATUS " + "─" * 40)
    max_fails = max((s["fail_count"] for s in stats), default=1)
    for s in stats:
        status_icon = "✅" if s["status"] == "alive" else "💀"
        fail_bar = bar(s["fail_count"], max_fails, 10)
        last = s.get("last_success") or s.get("last_failure") or "never"
        last = last[:19] if last != "never" else last
        print(f"│ {status_icon} {s['name']:<14} fails: {s['fail_count']:<3} {fail_bar}  last: {last}")

    if not stats:
        print("│  No data yet. Run agent.py first.")

    print("└" + "─" * 56)

    print("\n┌─ RECENT EVENTS " + "─" * 41)
    for e in events:
        ts = e["timestamp"][:19]
        icon = {"alive": "💚", "all_dead": "💀", "ping_failed": "🔴",
                "ping_success": "💚", "repair_failed": "🔧",
                "wrapper_installed": "✨"}.get(e["event_type"], "•")
        print(f"│ {icon} [{ts}] {e['event_type']:<20} {e['wrapper_name']}")

    if not events:
        print("│  No events yet.")

    print("└" + "─" * 56)
    print()


if __name__ == "__main__":
    asyncio.run(render())
