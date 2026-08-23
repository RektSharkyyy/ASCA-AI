"""
ASCA AI — Market Price Scraper / Supabase Sync CLI.

Implements the manual verification plan for the scraper pipeline:

    # 1. Seed 30 days of historical baseline into market_data
    python scripts/sync_market_prices.py seed --days 30

    # 2. Sync today's prices for both economic centres
    python scripts/sync_market_prices.py sync

    # 3. Read the HARTI bulletin without touching the DB
    python scripts/sync_market_prices.py fetch --centre DAMBULLA

    # 4. Inspect what is actually stored in market_data
    python scripts/sync_market_prices.py show --centre DAMBULLA --crop tomato

    # 5. Prove Prophet fits on real DB rows (no synthetic fallback)
    python scripts/sync_market_prices.py verify --centre DAMBULLA --crop tomato

    # 6. Run the whole verification plan end-to-end
    python scripts/sync_market_prices.py all
"""

import argparse
import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Allow `python scripts/sync_market_prices.py` from the backend root.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import func, select  # noqa: E402

from src.infrastructure.db import AsyncSessionLocal, init_db  # noqa: E402
from src.infrastructure.models import MarketDataModel  # noqa: E402
from src.services.scraper_service import SUPPORTED_CENTRES, market_scraper  # noqa: E402


def _hr(title: str) -> None:
    print(f"\n{'=' * 74}\n  {title}\n{'=' * 74}")


# --------------------------------------------------------------------------- #
# 1. Seed historical baseline
# --------------------------------------------------------------------------- #
async def cmd_seed(days: int) -> None:
    _hr(f"SEED — {days}-day historical baseline → market_data")
    result = await market_scraper.seed_historical_baseline(days=days)
    print(f"  days seeded      : {result['days_seeded']}")
    print(f"  centres          : {', '.join(result['centres'])}")
    print(f"  crops            : {', '.join(result['crops'])}")
    print(f"  rows inserted    : {result['total_inserted']}")
    print(f"  rows preserved   : {result['total_updated']}  (already existed — untouched)")


# --------------------------------------------------------------------------- #
# 2. Sync today's prices
# --------------------------------------------------------------------------- #
async def cmd_sync(centre: str | None) -> None:
    _hr(f"SYNC — today's prices for {centre or 'ALL CENTRES'}")
    if centre:
        results = [await market_scraper.sync_center_prices(centre.upper())]
    else:
        results = await market_scraper.sync_all_centers()

    for r in results:
        print(
            f"  {r['centre_id']:<18} {r['date']}  "
            f"crops={r['crops_synced']}  inserted={r['inserted']}  "
            f"updated={r['updated']}  live_harti={r['live_prices_found']}"
        )


# --------------------------------------------------------------------------- #
# 3. Read-only bulletin fetch
# --------------------------------------------------------------------------- #
async def cmd_fetch(centre: str) -> None:
    _hr(f"FETCH — HARTI bulletin for {centre.upper()} (no DB write)")
    quotes = await market_scraper.fetch_daily_market_prices(centre.upper())
    print(f"  {'CROP':<16}{'PRICE LKR/kg':>14}{'SUPPLY T':>12}   SOURCE")
    print(f"  {'-' * 56}")
    for crop, q in quotes.items():
        print(
            f"  {q['crop_label']:<16}{q['price_lkr']:>14.2f}"
            f"{q['supply_tons']:>12.2f}   {q['source']}"
        )


# --------------------------------------------------------------------------- #
# 4. Inspect market_data contents
# --------------------------------------------------------------------------- #
async def cmd_show(centre: str, crop: str, limit: int = 10) -> None:
    _hr(f"SHOW — market_data rows for {centre.upper()}/{crop}")
    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(select(func.count()).select_from(MarketDataModel))
        ).scalar_one()

        per_centre = (
            await session.execute(
                select(MarketDataModel.center_id, func.count(MarketDataModel.id))
                .group_by(MarketDataModel.center_id)
            )
        ).all()

        rows = (
            await session.execute(
                select(MarketDataModel)
                .where(
                    MarketDataModel.center_id == centre.upper(),
                    MarketDataModel.crop_name == crop,
                )
                .order_by(MarketDataModel.date.desc())
                .limit(limit)
            )
        ).scalars().all()

    print(f"  total rows in market_data : {total}")
    for cid, count in per_centre:
        print(f"    - {cid:<18} {count} rows")

    print(f"\n  latest {len(rows)} rows for {centre.upper()}/{crop} (newest first):")
    print(f"    {'DATE':<14}{'PRICE LKR/kg':>14}{'SUPPLY T':>12}")
    print(f"    {'-' * 40}")
    for r in rows:
        print(
            f"    {r.date.date().isoformat():<14}"
            f"{r.wholesale_price_lkr:>14.2f}{r.supply_volume_tons:>12.2f}"
        )


# --------------------------------------------------------------------------- #
# 5. Prophet fit verification
# --------------------------------------------------------------------------- #
async def cmd_verify(centre: str, crop: str) -> None:
    _hr(f"VERIFY — Prophet fit from market_data for {centre.upper()}/{crop}")

    from src.agents.market_scout import market_scout_agent
    from src.services.market_service import market_service

    df = await market_scout_agent.fetch_historical_data_async(centre.upper(), crop)
    source = df.attrs.get("source", "unknown")

    print(f"  history rows        : {len(df)}")
    print(f"  data source         : {source}")
    print(f"  date range          : {df['ds'].min().date()} → {df['ds'].max().date()}")
    print(f"  NaN price values    : {int(df['y'].isna().sum())}")
    missing_days = (
        (df["ds"].max() - df["ds"].min()).days + 1 - len(df["ds"].drop_duplicates())
    )
    print(f"  missing daily gaps  : {missing_days}")

    forecast = await market_service.get_forecast(centre.upper(), crop)
    print("\n  --- Prophet forecast ---")
    print(f"  model used          : {forecast.model_used}")
    print(f"  current price       : LKR {forecast.current_price_lkr}/kg")
    print(f"  day 7 forecast      : LKR {forecast.day7_price_lkr}/kg")
    print(f"  day 14 forecast     : LKR {forecast.day14_price_lkr}/kg")
    print(f"  14-day change       : {forecast.price_change_pct}%")
    print(f"  supply volume       : {forecast.supply_volume_tons} T")
    print(f"  risk level          : {forecast.risk_level}")
    print(f"  chart series points : {len(forecast.series)}")

    ok = source == "supabase" and forecast.model_used == "prophet" and missing_days == 0
    print(
        f"\n  RESULT: {'✅ PASS' if ok else '❌ FAIL'} — "
        f"source={source}, model={forecast.model_used}, gaps={missing_days}"
    )


# --------------------------------------------------------------------------- #
# 6. Manual override check
# --------------------------------------------------------------------------- #
async def cmd_manual(centre: str, crop: str, price: float, supply: float) -> None:
    _hr(f"MANUAL UPDATE — {centre.upper()}/{crop} → LKR {price}/kg")
    result = await market_scraper.manual_update_price(centre.upper(), crop, price, supply)
    for k, v in result.items():
        print(f"  {k:<14}: {v}")


# --------------------------------------------------------------------------- #
# Full plan
# --------------------------------------------------------------------------- #
async def cmd_all(days: int, centre: str, crop: str) -> None:
    await cmd_seed(days)
    await cmd_sync(None)
    await cmd_fetch(centre)
    await cmd_show(centre, crop)
    await cmd_verify(centre, crop)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
async def main() -> None:
    parser = argparse.ArgumentParser(description="ASCA AI market price scraper CLI")
    parser.add_argument(
        "command",
        choices=["seed", "sync", "fetch", "show", "verify", "manual", "all"],
    )
    parser.add_argument("--days", type=int, default=30, help="Days of history to seed")
    parser.add_argument("--centre", default="DAMBULLA", help=f"One of {SUPPORTED_CENTRES}")
    parser.add_argument("--crop", default="tomato", help="Crop key, e.g. tomato")
    parser.add_argument("--all-centres", action="store_true", help="Sync every centre")
    parser.add_argument("--price", type=float, default=195.0, help="Manual price LKR/kg")
    parser.add_argument("--supply", type=float, default=40.0, help="Manual supply tons")
    args = parser.parse_args()

    await init_db()

    if args.command == "seed":
        await cmd_seed(args.days)
    elif args.command == "sync":
        await cmd_sync(None if args.all_centres else args.centre)
    elif args.command == "fetch":
        await cmd_fetch(args.centre)
    elif args.command == "show":
        await cmd_show(args.centre, args.crop)
    elif args.command == "verify":
        await cmd_verify(args.centre, args.crop)
    elif args.command == "manual":
        await cmd_manual(args.centre, args.crop, args.price, args.supply)
    elif args.command == "all":
        await cmd_all(args.days, args.centre, args.crop)

    print()


if __name__ == "__main__":
    asyncio.run(main())
