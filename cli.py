"""
cli.py — Command-line interface for ImmortalAgent.

Subcommands:
  run         Start the immortal agent survival loop
  multi       Start multi-shard coordinator
  status      Show current wrapper health (one-shot)
  health      Show health JSON
  tail        Tail recent events
  trend       Show hourly trend for a wrapper
  budget      Show rate budget stats
  ask         Send a one-shot prompt
  dashboard   Launch live terminal dashboard
  server      Start REST API server
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from loguru import logger


def _run(_: argparse.Namespace) -> None:
    from agent import ImmortalAgent
    agent = ImmortalAgent()
    asyncio.run(agent.survive())


def _multi(args: argparse.Namespace) -> None:
    from multi_agent import _main
    asyncio.run(_main(n_shards=args.shards))


def _status(_: argparse.Namespace) -> None:
    from memory import init_db, get_wrapper_stats

    async def _go():
        await init_db()
        stats = await get_wrapper_stats()
        if not stats:
            print("No wrapper data yet. Run the agent first.")
            return
        print(f"{'Name':<20} {'Status':<8} {'Health':>7} {'Succ':>6} {'Fail':>6}")
        print("-" * 55)
        for s in stats:
            print(
                f"{s['name']:<20} {s.get('status','?'):<8} "
                f"{float(s.get('health_score') or 0):>7.2f} "
                f"{s.get('success_count',0):>6} "
                f"{s.get('fail_count',0):>6}"
            )

    asyncio.run(_go())


def _health(_: argparse.Namespace) -> None:
    from memory import init_db, get_wrapper_stats

    async def _go():
        await init_db()
        stats = await get_wrapper_stats()
        print(json.dumps(stats, indent=2))

    asyncio.run(_go())


def _tail(args: argparse.Namespace) -> None:
    from memory import init_db, get_recent_events

    async def _go():
        await init_db()
        events = await get_recent_events(args.n)
        for e in reversed(events):
            ts = e.get("timestamp", "")[:19]
            print(f"{ts}  {e.get('event_type',''):<25} {e.get('wrapper_name','')}")

    asyncio.run(_go())


def _trend(args: argparse.Namespace) -> None:
    from memory import init_db, get_hourly_trend

    async def _go():
        await init_db()
        rows = await get_hourly_trend(args.wrapper, args.hours)
        print(f"{'Hour':<17} {'Succ':>5} {'Fail':>5} {'AvgLat':>8} {'Health':>7}")
        print("-" * 50)
        for r in reversed(rows):
            print(
                f"{r['hour']:<17} {r['success_count']:>5} {r['fail_count']:>5} "
                f"{r['avg_latency']:>8.0f} {r['health_score']:>7.3f}"
            )

    asyncio.run(_go())


def _budget(_: argparse.Namespace) -> None:
    from rate_budget import BUDGET
    print(json.dumps(BUDGET.stats(), indent=2))


def _ask(args: argparse.Namespace) -> None:
    from memory import init_db
    from wrapper_pool import WrapperPool
    from rate_budget import BUDGET

    async def _go():
        await init_db()
        pool = WrapperPool()
        await BUDGET.acquire()
        response, source = await pool.send_with_fallback(args.prompt)
        if response:
            print(f"[{source}] {response}")
        else:
            print("All wrappers failed.", file=sys.stderr)
            sys.exit(1)

    asyncio.run(_go())


def _dashboard(_: argparse.Namespace) -> None:
    from dashboard import run_dashboard
    asyncio.run(run_dashboard())


def _server(args: argparse.Namespace) -> None:
    try:
        import uvicorn
    except ImportError:
        print("pip install uvicorn fastapi")
        sys.exit(1)
    uvicorn.run("rest_api:app", host=args.host, port=args.port, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="immortal", description="ImmortalAgent CLI v3.0"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run", help="Start survival loop")

    mp = sub.add_parser("multi", help="Start multi-shard coordinator")
    mp.add_argument("--shards", type=int, default=3)

    sub.add_parser("status", help="Show wrapper table")
    sub.add_parser("health", help="Show health JSON")

    tp = sub.add_parser("tail", help="Tail recent events")
    tp.add_argument("-n", type=int, default=20)

    trp = sub.add_parser("trend", help="Show hourly trend")
    trp.add_argument("wrapper", help="Wrapper name")
    trp.add_argument("--hours", type=int, default=24)

    sub.add_parser("budget", help="Show rate budget")

    ap = sub.add_parser("ask", help="One-shot prompt")
    ap.add_argument("prompt")

    sub.add_parser("dashboard", help="Live terminal dashboard")

    sp = sub.add_parser("server", help="Start REST API server")
    sp.add_argument("--host", default="0.0.0.0")
    sp.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    dispatch = {
        "run": _run,
        "multi": _multi,
        "status": _status,
        "health": _health,
        "tail": _tail,
        "trend": _trend,
        "budget": _budget,
        "ask": _ask,
        "dashboard": _dashboard,
        "server": _server,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
