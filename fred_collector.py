import os
import json
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

import config
from fred_client import FredClient

class FredCollector:
    def __init__(self, use_blob: bool = False):
        self.client = FredClient()
        self.stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.use_blob = use_blob
        if not use_blob:
            self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(config.RAW_DIR, exist_ok=True)
        os.makedirs(config.SUMMARY_DIR, exist_ok=True)

    def save_json(self, path_or_blob: str, payload: dict, blob_container: Optional[str] = None):
        """Yerel diske veya Blob Storage'a JSON kaydeder."""
        if self.use_blob:
            import sys, os as _os
            sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "azure"))
            from blob_helper import upload_json
            upload_json(blob_container, path_or_blob, payload)
        else:
            with open(path_or_blob, "w", encoding="utf-8") as f:
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
        from config_cloud import CONTAINER_RAW, CONTAINER_CLEAN, BLOB_PATHS  # noqa (cloud only)
        dataframes = {}
        summaries = []

        for sid in config.FRED_SERIES_LIST:
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

            filename = f"{sid}_{self.stamp}.json"
            if self.use_blob:
                blob_name = BLOB_PATHS["fred_raw"].format(filename=filename)
                self.save_json(blob_name, raw_payload, blob_container=CONTAINER_RAW)
            else:
                raw_path = os.path.join(config.RAW_DIR, filename)
                self.save_json(raw_path, raw_payload)

            summary = self.summarize_last_12(df, sid)
            summaries.append(summary)
            print(f"{sid} -> saved {len(df)} observations")

        # Yield curve calculation
        yield_curve_info = self.calculate_yield_curve(dataframes)

        # Save summary report
        report = {
            "source": "FRED",
            "fetched_at_utc": self.stamp,
            "start_date": config.FRED_START_DATE,
            "series_included": config.FRED_SERIES_LIST,
            "summaries_last_12": summaries,
            "yield_curve": yield_curve_info
        }

        report_filename = f"macro_report_{self.stamp}.json"
        if self.use_blob:
            blob_name = BLOB_PATHS["fred_summary"].format(filename=report_filename)
            self.save_json(blob_name, report, blob_container=CONTAINER_RAW)
        else:
            report_path = os.path.join(config.SUMMARY_DIR, report_filename)
            self.save_json(report_path, report)
            print("\n--- Saved Macro Report ---")
            print(report_path)


def run(use_blob: bool = False):
    """Pipeline ve Azure Functions tarafından çağrılacak ana fonksiyon."""
    collector = FredCollector(use_blob=use_blob)
    collector.run()


if __name__ == "__main__":
    run(use_blob=False)
