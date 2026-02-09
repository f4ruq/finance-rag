import requests
import pandas as pd
import config

class FredClient:
    def __init__(self, api_key: str = config.FRED_API_KEY):
        self.api_key = api_key
        self.base_url = config.BASE_URL

    def fetch_series(self, series_id: str, start_date: str = config.START_DATE) -> pd.DataFrame:
        """
        Fetches a specific series from FRED API and returns a DataFrame.
        """
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])

            df = pd.DataFrame(observations)
            if df.empty:
                 return pd.DataFrame(columns=["date", "value"])

            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"]).sort_values("date")
            
            return df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching series {series_id}: {e}")
            return pd.DataFrame()
