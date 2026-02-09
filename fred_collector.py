import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

import config
from fred_client import FredClient

class FredCollector:
    def __init__(self):
        self.client = FredClient()
        self.stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(config.RAW_DIR, exist_ok=True)
        os.makedirs(config.SUMMARY_DIR, exist_ok=True)

    def save_json(self, path: str, payload: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def summarize_last_12(self, df: pd.DataFrame, series_id: str) -> Dict:
        if df.empty:
            return {}

        last_12 = df.tail(12)
        start_val = last_12.iloc[0]["value"]
        end_val = last_12.iloc[-1]["value"]

        change = end_val - start_val
        pct_change = (change / start_val) * 100 if start_val != 0 else None

        if change > 0:
            trend = "increasing"
        elif change < 0:
            trend = "decreasing"
        else:
            trend = "flat"

        return {
            "series": series_id,
            "start_date": str(last_12.iloc[0]["date"].date()),
            "end_date": str(last_12.iloc[-1]["date"].date()),
            "start_value": float(start_val),
            "end_value": float(end_val),
            "change": float(change),
            "pct_change": float(pct_change) if pct_change is not None else None,
            "trend": trend
        }

    def calculate_yield_curve(self, dataframes: Dict[str, pd.DataFrame]) -> Optional[Dict]:
        if "DGS10" in dataframes and "DGS2" in dataframes:
            d10 = dataframes["DGS10"][["date", "value"]].rename(columns={"value": "DGS10"})
            d2 = dataframes["DGS2"][["date", "value"]].rename(columns={"value": "DGS2"})

            merged = pd.merge(d10, d2, on="date", how="inner")
            if merged.empty:
                return None
                
            merged["spread_10y_2y"] = merged["DGS10"] - merged["DGS2"]
            latest = merged.iloc[-1]

            return {
                "date": str(latest["date"].date()),
                "dgs10": float(latest["DGS10"]),
                "dgs2": float(latest["DGS2"]),
                "spread_10y_2y": float(latest["spread_10y_2y"]),
                "status": "INVERTED" if latest["spread_10y_2y"] < 0 else "NORMAL"
            }
        return None

    def run(self):
        print("Fetching FRED series...\n")
        dataframes = {}
        summaries = []

        for sid in config.SERIES_LIST:
            df = self.client.fetch_series(sid)
            if df.empty:
                print(f"Skipping {sid} due to empty data.")
                continue

            dataframes[sid] = df

            # Save raw observations
            raw_payload = {
                "series_id": sid,
                "source": "FRED",
                "fetched_at_utc": self.stamp,
                "observations": [
                    {"date": str(row["date"].date()), "value": float(row["value"])}
                    for _, row in df.iterrows()
                ]
            }

            raw_path = os.path.join(config.RAW_DIR, f"{sid}_{self.stamp}.json")
            self.save_json(raw_path, raw_payload)

            summary = self.summarize_last_12(df, sid)
            summaries.append(summary)

            print(f"{sid} -> saved {len(df)} observations to {raw_path}")

        # Yield curve calculation
        yield_curve_info = self.calculate_yield_curve(dataframes)

        # Save summary report
        report = {
            "source": "FRED",
            "fetched_at_utc": self.stamp,
            "start_date": config.START_DATE,
            "series_included": config.SERIES_LIST,
            "summaries_last_12": summaries,
            "yield_curve": yield_curve_info
        }

        report_path = os.path.join(config.SUMMARY_DIR, f"macro_report_{self.stamp}.json")
        self.save_json(report_path, report)

        print("\n--- Saved Macro Report ---")
        print(report_path)

if __name__ == "__main__":
    collector = FredCollector()
    collector.run()
