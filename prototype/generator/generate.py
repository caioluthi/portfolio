"""Generate Second Avenue's simulated book of Risk contracts.

Writes four source tables as CSV, shaped like the three source systems in the
PRD (ConsignTrack for consignors, contracts and assets; Listings; Sales):

    consignors.csv  contracts.csv  assets.csv  listings.csv  sales.csv

Usage:
    python generate.py --out ../data            # write the CSVs
    python generate.py --out ../data --report   # also print calibration vs Phase 2

All randomness comes from the seed in config.yaml, so the same config always
produces the same book.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).parent
CHANNELS = ["app", "website", "live"]


def load_config(path: Path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["today"] = pd.Timestamp(cfg["today"]).date()
    return cfg


def tier_schedule(rng: np.random.Generator) -> str:
    """Default upside tiers, occasionally negotiated (Phase 1 appendix A)."""
    if rng.random() < 0.8:
        tiers = [[0, 10000, 0.20], [10000, 20000, 0.30], [20000, None, 0.70]]
    else:
        a, b = sorted(rng.choice([5000, 10000, 15000, 25000], 2, replace=False))
        tiers = [[0, int(a), 0.15], [int(a), int(b), 0.30], [int(b), None, 0.60]]
    return json.dumps([{"from": f, "to": t, "share": s} for f, t, s in tiers])


def generate(cfg: dict) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(cfg["seed"])
    # Estimates draw from their own stream, so adding them leaves the rest of the book unchanged.
    rng_est = np.random.default_rng(cfg["seed"] + 1)
    book, pricing, timing = cfg["book"], cfg["pricing"], cfg["timing"]
    today: date = cfg["today"]
    L = book["lifecycle_days"]
    regions = cfg["regions"]
    types = cfg["asset_types"]

    # Consignors
    n_cons = book["consignors"]
    consignors = pd.DataFrame({
        "consignor_id": [f"CN-{i:05d}" for i in range(1, n_cons + 1)],
        "home_region": rng.choice(regions, n_cons),
    })
    # A few consignors bring many contracts; most bring one or two.
    cons_weight = rng.pareto(1.5, n_cons) + 1
    cons_weight /= cons_weight.sum()

    # Contracts: start dates spread evenly over the history window
    first_start = today - timedelta(days=cfg["history_days"])
    n_days = (today - first_start).days
    n_contracts = int(round(book["contracts_per_year"] * n_days / 365))
    starts = sorted(first_start + timedelta(days=int(d)) for d in rng.integers(0, n_days, n_contracts))

    contracts, assets, listings, sales = [], [], [], []
    asset_seq = sale_seq = listing_seq = 0
    recent_cutoff = today - timedelta(days=182)

    for ci, start in enumerate(starts, start=1):
        cid = f"CT-{ci:05d}"
        cons_idx = rng.choice(n_cons, p=cons_weight)
        region = consignors.home_region[cons_idx]
        expiry = start + timedelta(days=L)
        target = float(round(rng.lognormal(np.log(book["target_median_usd"]), book["target_sigma"]), -2))
        cancelled = rng.random() < book["cancelled_share"]
        status = "cancelled" if cancelled else ("closed" if expiry <= today else "active")
        single = rng.random() < book["single_asset_share"]

        contracts.append({
            "contract_id": cid,
            "consignor_id": consignors.consignor_id[cons_idx],
            "start_date": start,
            "lifecycle_days": L,
            "expiry_date": expiry,
            "target_price": target,
            "tier_schedule": tier_schedule(rng),
            "status": status,
            "region": region,
        })
        if cancelled:
            continue

        # Demand for this contract's items: shared shock, regional demand, recent softening
        drift = pricing["recent_drift"] if expiry > recent_cutoff else 0.0
        shock = rng.lognormal(0, pricing["contract_shock_sigma"]) * cfg["region_demand"][region] * (1 + drift)

        # Assets and their expected values
        if single:
            n_assets = 1
        else:
            a = book["assets_per_contract"]
            n_assets = int(np.clip(rng.poisson(a["mean"]), a["min"], a["max"]))
        main_type = rng.choice(types)
        a_types = [main_type if rng.random() < 0.7 else rng.choice(types) for _ in range(n_assets)]
        weights = rng.dirichlet(np.ones(n_assets) * 2) if n_assets > 1 else np.array([1.0])
        expected = weights * target * pricing["expected_over_target"]

        auction_day = int(rng.integers(timing["live_auction_day"]["min"], timing["live_auction_day"]["max"] + 1))

        for k in range(n_assets):
            asset_seq += 1
            aid = f"AS-{asset_seq:06d}"
            atype = a_types[k]
            p = cfg["placement"][atype]
            channel = rng.choice(CHANNELS, p=[p[c] for c in CHANNELS])
            fit = cfg["channel_fit"][atype][channel]
            # Appraised value at intake: channel-agnostic, blind to this contract's demand, with appraisal error
            estimate = round(float(expected[k] * rng_est.lognormal(0, cfg["estimates"]["sigma"])), -1)
            assets.append({"asset_id": aid, "contract_id": cid, "asset_type": atype, "estimate_usd": estimate})

            # Listing
            listing_seq += 1
            list_day = int(rng.integers(0, 8)) if channel != "live" else max(0, auction_day - 14)
            listed = start + timedelta(days=list_day)

            # Does it sell, when, and for how much?
            p_unsold = min(0.9, pricing["unsold_base"] / max(shock * fit, 0.2) ** 2)
            sells = rng.random() >= p_unsold
            if channel == "live":
                sale_day = auction_day
            else:
                t = timing[channel]
                b = t["b"] / max(shock, 0.2) ** timing["slowdown_k"]
                sale_day = int(rng.beta(t["a"], b) * L)
            sale_day = min(sale_day, L - 1)
            sale_date = start + timedelta(days=sale_day)
            sold = sells and sale_date <= today and sale_date >= listed
            # A live item that was never going to sell still goes to auction; it just doesn't clear.

            listing_end = sale_date if sold else min(expiry, today)
            listings.append({
                "listing_id": f"LS-{listing_seq:06d}",
                "asset_id": aid,
                "listing_channel": channel,
                "listed_date": listed,
                "ended_date": listing_end if (sold or expiry <= today) else None,
                "listing_status": "sold" if sold else ("expired" if expiry <= today else "live"),
            })
            if sold:
                sale_seq += 1
                price = expected[k] * fit * shock * rng.lognormal(0, pricing["asset_noise_sigma"])
                sales.append({
                    "sale_id": f"SL-{sale_seq:06d}",
                    "asset_id": aid,
                    "sale_date": sale_date,
                    "gross_amount": round(float(price), 2),
                    "channel": channel,
                    "region": region,
                })

    out = {
        "consignors": consignors,
        "contracts": pd.DataFrame(contracts),
        "assets": pd.DataFrame(assets),
        "listings": pd.DataFrame(listings),
        "sales": pd.DataFrame(sales),
    }
    add_worked_example(out, today)
    return out


def add_worked_example(t: dict[str, pd.DataFrame], today: date) -> None:
    """The PRD's worked example as a fixed contract, so the metrics can be checked against it.

    $50,000 target, 90 days: $6,500 sold by day 15, $11,000 by day 30, closes at $36,000.
    """
    start = today - timedelta(days=200)
    cid, cons = "CT-EXAMPLE", t["consignors"].consignor_id.iloc[0]
    t["contracts"] = pd.concat([t["contracts"], pd.DataFrame([{
        "contract_id": cid, "consignor_id": cons, "start_date": start, "lifecycle_days": 90,
        "expiry_date": start + timedelta(days=90), "target_price": 50000.0,
        "tier_schedule": tier_schedule(np.random.default_rng(0)), "status": "closed", "region": "Northeast",
    }])], ignore_index=True)
    path = [(5, 3000), (12, 3500), (22, 2000), (28, 2500), (44, 5000), (58, 6000), (74, 6000), (88, 8000)]
    a, l, s = [], [], []
    for i, (day, amount) in enumerate(path, start=1):
        aid = f"AS-EX{i:03d}"
        d = start + timedelta(days=day)
        a.append({"asset_id": aid, "contract_id": cid, "asset_type": "furniture", "estimate_usd": float(amount)})
        l.append({"listing_id": f"LS-EX{i:03d}", "asset_id": aid, "listing_channel": "website",
                  "listed_date": start, "ended_date": d, "listing_status": "sold"})
        s.append({"sale_id": f"SL-EX{i:03d}", "asset_id": aid, "sale_date": d, "gross_amount": float(amount),
                  "channel": "website", "region": "Northeast"})
    t["assets"] = pd.concat([t["assets"], pd.DataFrame(a)], ignore_index=True)
    t["listings"] = pd.concat([t["listings"], pd.DataFrame(l)], ignore_index=True)
    t["sales"] = pd.concat([t["sales"], pd.DataFrame(s)], ignore_index=True)


def report(t: dict[str, pd.DataFrame], cfg: dict) -> None:
    """Compare the generated book with the Phase 2 calibration targets."""
    today = cfg["today"]
    c = t["contracts"]
    c = c[c.contract_id != "CT-EXAMPLE"]
    realized = (t["sales"].merge(t["assets"], on="asset_id").groupby("contract_id").gross_amount.sum())
    c = c.assign(realized=c.contract_id.map(realized).fillna(0.0))
    closed = c[c.status == "closed"]
    def window(days):
        w = closed[closed.expiry_date > today - timedelta(days=days)]
        under = w[w.realized < w.target_price]
        return len(w), len(under) / len(w), ((under.target_price - under.realized) / under.target_price).mean(), (under.target_price - under.realized).sum()
    n12, r12, sh12, usd12 = window(365)
    n6, r6, _, _ = window(182)
    active = c[c.status == "active"]
    tg = cfg["calibration_targets"]
    print(f"contracts              {len(c):>8,}   (active {len(active):,}, cancelled {(c.status=='cancelled').sum():,})")
    print(f"avg target             ${c.target_price.mean():>9,.0f}   Phase 2: ~$50,000")
    print(f"active book            ${active.target_price.sum()/1e6:>8.1f}M   Phase 2: ~$25M")
    print(f"closed, last 12 months {n12:>8,}")
    print(f"underperformed 12m     {r12:>8.1%}   target {tg['underperformance_rate_12m']:.0%}")
    print(f"underperformed 6m      {r6:>8.1%}   target {tg['underperformance_rate_6m']:.0%}")
    print(f"avg shortfall share    {sh12:>8.1%}   target {tg['avg_shortfall_share']:.0%}")
    print(f"shortfall paid, 12m    ${usd12/1e6:>8.2f}M   Phase 2: ~$3.6M")
    print(f"assets {len(t['assets']):,}  listings {len(t['listings']):,}  sales {len(t['sales']):,}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=HERE / "config.yaml")
    ap.add_argument("--out", type=Path, default=HERE.parent / "data")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    tables = generate(cfg)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(args.out / f"{name}.csv", index=False)
    if args.report:
        report(tables, cfg)


if __name__ == "__main__":
    main()
