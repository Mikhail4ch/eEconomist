import requests
from fake_useragent import FakeUserAgent
import json

headers = {
    'user-agent': FakeUserAgent().random
}

TOKEN_ADDRESS = {
    'ETH':  'So11111111111111111111111111111111111111112',
    'SOL':  'BeRUj3h7BqkbdfFU7FBNYbodgf8GCHodzKvF9aVjNNfL',
    'USDT': 'CEBP3CqAbW4zdZA57H2wfaSG1QNdzQ72GiQEbQXyW9Tm',
    'USDC': 'AKEWE7Bgh87GPp171b4cJPSSZfmZwQ3KaqYqXoKLNAEE',
    'BITZ': '64mggk2nXg6vHC1qCdsZdEFzd5QGN4id54Vbho4PswCF',
    'tETH': 'GU7NS9xCwgNPiAdJ69iusFrRfawjDDPjeMBovhV1d4kn',
    'TUSD': '27Kkn8PWJbKJsRZrxbsYDdedpUQKnJ5vNfserCxNEJ3R',
    'LAIKA': 'LaihKXA47apnS599tyEyasY2REfEzBNe4heunANhsMx'
}

class ORCA:
    """Class to fetch and process Orca pool data for a specific asset."""
    def __init__(self, symbol):
        self._SYMBOL = symbol.upper()

    def fetch_data(self):
        url = (
            'https://api.orca.so/v2/eclipse/pools'
            '?limit=50&stats=5m,15m,30m,1H,2H,4H,8H,24H,7D,30D'
        )
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        self._DATA = data['data']
        self._top_pool_keys = []
        self._poolActivity = {}
        self._tvlData = {}
    
    def bestYield24(self):
        results = []
        url_dict = {}
        activity_dict = {}
        tvl_dict = {}

        for asset in self._DATA:
            try:
                tvl = float(asset.get('tvlUsdc', 0))
                if tvl <= 0:
                    continue  # skip zero TVL pools

                yld = float(asset['stats']['24h']['yieldOverTvl']) * 100
                yld_rounded = round(yld, 3)
                tokenA = asset['tokenA']
                tokenB = asset['tokenB']
                symbolA = tokenA['symbol'].upper()
                symbolB = tokenB['symbol'].upper()
                addressA = tokenA['address']
                addressB = tokenB['address']

                if symbolA == self._SYMBOL:
                    pair_str = f"{symbolA}/{symbolB} (Orca)"
                    pool_url = (
                        f"https://www.orca.so/pools?chainId=eclipse"
                        f"&tokens={addressA}&tokens={addressB}"
                    )
                elif symbolB == self._SYMBOL:
                    pair_str = f"{symbolB}/{symbolA} (Orca)"
                    pool_url = (
                        f"https://www.orca.so/pools?chainId=eclipse"
                        f"&tokens={addressB}&tokens={addressA}"
                    )
                else:
                    continue

                key = f"{pair_str} | {yld_rounded}％"
                results.append((key, yld_rounded, pair_str))
                url_dict[key] = pool_url

                # Prepare activity for later
                volume = float(asset['stats']['24h'].get('volume', 0))
                activity = round(volume / tvl, 3) if tvl else None
                activity_dict[key] = activity
                tvl_dict[key] = int(round(tvl,0))

            except Exception:
                continue

        # Top 3 by yield
        results = sorted(results, key=lambda x: x[1], reverse=True)[:3]
        self._top_pool_keys = [key for key, _, _ in results]

        # Output with URLs
        output = {key: url_dict[key] for key, _, _ in results}

        self._poolActivity = {key: activity_dict[key] for key in self._top_pool_keys}
        self._tvlData = {key: tvl_dict[key] for key in self._top_pool_keys}

        if not output:
            return {}
        return output

    def poolActivities(self):
        return self._poolActivity
    def tvlData(self):
        return self._tvlData









