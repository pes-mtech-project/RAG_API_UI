import csv
import datetime
import json
import random
import time
from pathlib import Path
from typing import Dict, Any, List

import requests

# --------- CONFIG ---------
SECTOR_TICKERS = {
    "NIFTY IT": "^CNXIT",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY FIN SERVICE": "^CNXFIN",
    "NIFTY PSU BANK": "^CNXPSUBANK"
}

YF_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
ARCHIVE_DIR = Path(__file__).resolve().parent
DEFAULT_TICKER_CSV = ARCHIVE_DIR / "ticker_universe_5sectors_45.csv"
TICKER_OUTPUT_PATH = ARCHIVE_DIR / "ticker_universe_last_70d.json"
SECTOR_OUTPUT_PATH = ARCHIVE_DIR / "sector_performance_last_70d.json"

# --------- CORE LOGIC ---------

def build_yahoo_symbol(ticker: str, suffix: str = ".NS") -> str:
    """
    Append exchange suffix for Yahoo Finance unless a suffix/prefix already exists.
    """
    if ticker.startswith("^") or "." in ticker:
        return ticker
    return f"{ticker}{suffix}" if suffix else ticker


def fetch_yahoo_history(
    ticker: str,
    range_days: str = "1mo",
    interval: str = "1d",
    max_retries: int = 5,
    backoff_base: float = 2.0
) -> Dict[str, Any]:
    """
    Calls Yahoo Finance chart API for a given ticker.
    Example: range_days = '15d' or '1mo', interval = '1d'
    """
    params = {
        "range": range_days,   # Yahoo accepts 15d / 1mo / 3mo etc.
        "interval": interval
    }
    headers = {
        # Yahoo is sensitive to default clients; randomize UA slightly to avoid easy 429s.
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.{random.randint(0,99)}.0.0 Safari/537.36",
        "Accept": "application/json,text/*;q=0.9",
    }

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                YF_CHART_URL.format(ticker=ticker),
                params=params,
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 429:
                # Too many requests: exponential backoff with jitter
                sleep_for = backoff_base ** attempt + random.random()
                time.sleep(sleep_for)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            sleep_for = backoff_base ** attempt + random.random()
            time.sleep(sleep_for)
    # After retries, raise last seen error
    if last_exc:
        raise last_exc
    raise RuntimeError("Failed to fetch Yahoo Finance data")


def extract_ohlc_from_chart(chart_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses Yahoo chart API JSON into a list of
    { date, close, open, high, low, volume } records.
    """
    result = chart_json.get("chart", {}).get("result", [])
    if not result:
        return []

    chart = result[0]
    timestamps = chart.get("timestamp", [])
    indicators = chart.get("indicators", {})
    quote = indicators.get("quote", [{}])[0]

    closes = quote.get("close", [])
    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    volumes = quote.get("volume", [])

    records = []
    for i, ts in enumerate(timestamps):
        # ts is in seconds since epoch (UTC)
        dt = datetime.datetime.utcfromtimestamp(ts).date().isoformat()

        # Some days might have null close (holidays, partial data)
        close = closes[i] if i < len(closes) else None
        open_ = opens[i] if i < len(opens) else None
        high = highs[i] if i < len(highs) else None
        low = lows[i] if i < len(lows) else None
        vol = volumes[i] if i < len(volumes) else None

        # skip rows where close is None
        if close is None:
            continue

        records.append(
            {
                "date": dt,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": vol,
            }
        )
    return records


def compute_window_performance(records: List[Dict[str, Any]], window_days: int = 70) -> Dict[str, Any]:
    """
    Given list of daily records sorted by date,
    take last N *trading* days and compute % change.
    """
    if not records:
        return {
            "start_date": None,
            "end_date": None,
            "start_close": None,
            "end_close": None,
            "change_pct": None,
            "last_window_data": []
        }

    # ensure sorted by date
    records_sorted = sorted(records, key=lambda r: r["date"])
    last_window = records_sorted[-window_days:] if len(records_sorted) > window_days else records_sorted

    start = last_window[0]
    end = last_window[-1]

    start_close = start["close"]
    end_close = end["close"]

    if start_close is None or end_close is None:
        change_pct = None
    else:
        change_pct = ((end_close - start_close) / start_close) * 100.0

    return {
        "start_date": start["date"],
        "end_date": end["date"],
        "start_close": start_close,
        "end_close": end_close,
        "change_pct": round(change_pct, 2) if change_pct is not None else None,
        "last_window_data": last_window
    }


def get_sector_performance_last_70d() -> Dict[str, Any]:
    """
    For each sector index, fetch Yahoo data and compute
    70-day performance.
    """
    output = {}
    for sector_name, ticker in SECTOR_TICKERS.items():
        try:
            chart_json = fetch_yahoo_history(ticker, range_days="3mo", interval="1d")
            records = extract_ohlc_from_chart(chart_json)
            perf = compute_window_performance(records, window_days=70)

            output[sector_name] = {
                "ticker": ticker,
                **perf
            }
        except Exception as e:
            output[sector_name] = {
                "ticker": ticker,
                "error": str(e)
            }
    return output


def load_tickers_from_csv(csv_path: Path) -> List[Dict[str, str]]:
    """
    Load ticker universe rows from CSV.
    """
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if row.get("ticker")]


def get_ticker_universe_last_70d(
    csv_path: Path = DEFAULT_TICKER_CSV,
    yahoo_suffix: str = ".NS"
) -> Dict[str, Any]:
    """
    Fetch last 70-day history for each ticker in the CSV and compute performance.
    """
    tickers = load_tickers_from_csv(csv_path)
    output: Dict[str, Any] = {}

    for row in tickers:
        raw_ticker = row.get("ticker", "").strip()
        yahoo_symbol = build_yahoo_symbol(raw_ticker, yahoo_suffix)
        try:
            chart_json = fetch_yahoo_history(yahoo_symbol, range_days="3mo", interval="1d")
            records = extract_ohlc_from_chart(chart_json)
            perf = compute_window_performance(records, window_days=70)
            output[raw_ticker] = {
                "sector": row.get("sector"),
                "cap_bucket": row.get("cap_bucket"),
                "company_name": row.get("company_name"),
                "ticker": raw_ticker,
                "yahoo_symbol": yahoo_symbol,
                **perf
            }
        except Exception as e:
            output[raw_ticker] = {
                "sector": row.get("sector"),
                "cap_bucket": row.get("cap_bucket"),
                "company_name": row.get("company_name"),
                "ticker": raw_ticker,
                "yahoo_symbol": yahoo_symbol,
                "error": str(e)
            }
    return output


if __name__ == "__main__":
    sector_perf = get_sector_performance_last_70d()
    print(json.dumps(sector_perf, indent=2))
    # write this sector_perf to a JSON file if needed   
    with SECTOR_OUTPUT_PATH.open("w") as f:
        json.dump(sector_perf, f, indent=2)

    # Also generate ticker-level market data from the universe CSV
    ticker_perf = get_ticker_universe_last_70d()
    with TICKER_OUTPUT_PATH.open("w") as f:
        json.dump(ticker_perf, f, indent=2)
