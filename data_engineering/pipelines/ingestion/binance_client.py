import time
import requests
from typing import Dict, Any, Optional
from app.utils.logger import logger

class BinanceAPIClient:
    """
    Production-grade exchange API client equipped with exponential backoff retries,
    network fault tolerances, and robust logging metrics.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.binance.com"):
        self.base_url = base_url
        self.headers = {"X-MBX-APIKEY": api_key} if api_key else {}

    def get_ticker_24h(self, symbol: str, retries: int = 3, backoff_factor: float = 1.5) -> Dict[str, Any]:
        """
        Queries exchange statistics for a crypto pair.
        Implements exponential backoff to handle transient network issues or rate limits safely.
        """
        url = f"{self.base_url}/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        
        delay = 1.0
        for attempt in range(retries):
            try:
                logger.info(f"Querying Binance ticker stats for {symbol} (Attempt {attempt + 1}/{retries})")
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                
                # Check for rate-limiting status codes (429/418)
                if response.status_code in [429, 418]:
                    retry_after = int(response.headers.get("Retry-After", delay))
                    logger.warning(f"IP Rate limit hit. Backing off for {retry_after} seconds.")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network exception calling Binance on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to ingest Binance tickers after {retries} attempts.") from e
                
                time.sleep(delay)
                delay *= backoff_factor
                
        raise RuntimeError("Binance client failed during request ingestion loops.")
