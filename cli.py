"""CLI utility for Immortal Agent."""
import asyncio
import argparse
from memory import init_db, get_wrapper_stats, get_recent_events
from wrapper_pool import WrapperPool


async def cmd_status():
    await init_db()
    stats = await get_wrapper_stats()
    if not stats:
        print("No data yet. Run 'python agent.py' first.")
        return
    print(f"{'Wrapper':<16} {'Status':<8} {'Fails':<7} {'Last Success'}")
    print("-" * 55)
    for s in stats:
        print(f"{s['name']:<16} {s['status']:<8} {s['fail_count']:<7} {s.get('last_success') or 'never'}")


async def cmd_ping(wrapper_name: str = None):
    pool = WrapperPool()
    if wrapper_name:
        targets = [w for w in pool.wrappers if w.name == wrapper_name]
        if not targets:
            print(f"Unknown wrapper: {wrapper_name}")
            return
    else:
        targets = pool.wrappers

    for w in targets:
        alive = await w.is_alive()
        icon = "✅" if alive else "💀"
        print(f"{icon} {w.name}")


async def cmd_ask(prompt: str):
    pool = WrapperPool()
    response, source = await pool.send_with_fallback(prompt)
    if response:
        print(f"[{source}] {response}")
    else:
        print("All wrappers dead. No response.")


async def cmd_events(n: int = 20):
    await init_db()
    events = await get_recent_events(limit=n)
    for e in events:
        print(f"[{e['timestamp'][:19]}] {e['event_type']:<22} {e['wrapper_name']}")


def main():
    parser = argparse.ArgumentParser(description="Immortal Agent CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="Show wrapper status")

    ping_p = sub.add_parser("ping", help="Ping one or all wrappers")
    ping_p.add_argument("wrapper", nargs="?", help="Wrapper name (optional)")

    ask_p = sub.add_parser("ask", help="Send a prompt through the pool")
    ask_p.add_argument("prompt", help="Prompt to send")

    events_p = sub.add_parser("events", help="Show recent events")
    events_p.add_argument("-n", type=int, default=20, help="Number of events")

    args = parser.parse_args()

    if args.cmd == "status":
        asyncio.run(cmd_status())
    elif args.cmd == "ping":
        asyncio.run(cmd_ping(getattr(args, "wrapper", None)))
    elif args.cmd == "ask":
        asyncio.run(cmd_ask(args.prompt))
    elif args.cmd == "events":
        asyncio.run(cmd_events(args.n))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
