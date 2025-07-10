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
    'TETH': 'GU7NS9xCwgNPiAdJ69iusFrRfawjDDPjeMBovhV1d4kn',
    'TUSD': '27Kkn8PWJbKJsRZrxbsYDdedpUQKnJ5vNfserCxNEJ3R',
    'LAIKA': 'LaihKXA47apnS599tyEyasY2REfEzBNe4heunANhsMx',
    'SBITZ': 'sBTZcSwRZhRq3JcjFh1xwxgCxmsN7MreyU3Zx8dA8uF',
    'MCT': '82kkga2kBcQNyV4VKJhGvE7Z58fFavVyuh5NapMVo7Qs'
}

POOLS_WITH_POINTS = {
    'ETH/USDC': 'HRgVv1pyBLXdsAddq4ubSqo8xdQWRrYbvmXqEDtectce',
    'BITZ/ETH': 'HG7iQMk29cgs74ZhSwrnye3C6SLQwKnfsbXqJVRi1x8H',
    'sBITZ/ETH': '9RkzLPufg9RVxRLXZx1drZvf1gXLwgffnhW9oFJSstad',
    'SOL/ETH': '86vPh8ctgeQnnn8qPADy5BkzrqoH5XjMCWvkd4tYhhmM',
    'SOL/USDC': 'E2B7KUFwjxrsy9cC17hmadPsxWHD1NufZXTyrtuz8YxC',
    'tETH/ETH': 'FvVsbwsbGVo6PVfimkkPhpcRfBrRitiV946nMNNuz7f9',
    'tUSD/USDC': '1Zxv7bYYzMuK8eey85ZSowa24S8B7QNfDx3GQpKQ4Bf',
}

ADDRESS_TO_SYMBOL = {v: k for k, v in TOKEN_ADDRESS.items()}

class INVARIANT:
    def __init__(self, symbol):
        self._SYMBOL = symbol.upper()
    
    def fetch_data(self):
        url = 'https://stats.invariant.app/eclipse/intervals/eclipse-mainnet?interval=daily'
        response = requests.get(url, headers=headers)
        self._DATA = json.loads(response.text)
        self._poolActivity = {}
        self._tvlData = {}
        self._poolWithPoActivity = {}
        self._poolWithPotvlData = {}

    def bestYield24(self):
        token_addr = TOKEN_ADDRESS.get(self._SYMBOL)
        if not token_addr:
            return f"Unknown symbol: {self._SYMBOL}"
        pools = self._DATA.get('poolsData', [])
        best_per_pair = {}
        best_per_activity = {}
        best_per_tvl = {}

        for pool in pools:
            try:
                tvl = float(pool.get('tvl', 0))
                if tvl <= 0:
                    continue  # skip zero TVL pools

                apy = float(pool.get('apy', 0))
                daily_yield = round(apy / 365, 3)
                symbolX = ADDRESS_TO_SYMBOL.get(pool.get('tokenX'), pool.get('tokenX'))
                symbolY = ADDRESS_TO_SYMBOL.get(pool.get('tokenY'), pool.get('tokenY'))
                fee = float(pool.get('fee'))
                fee_str = f"{fee:.2f}".replace('.', '_')
                volume = float(pool.get('volume', 0))
                activity = round(volume / tvl, 4) if tvl else 0

                if pool.get('tokenX') == token_addr or pool.get('tokenY') == token_addr:
                    if pool.get('tokenX') == token_addr:
                        pair = f"{symbolX}/{symbolY} (Invariant)"
                        url = f"https://eclipse.invariant.app/newPosition/{symbolX}/{symbolY}/{fee_str}"
                    else:
                        pair = f"{symbolY}/{symbolX} (Invariant)"
                        url = f"https://eclipse.invariant.app/newPosition/{symbolY}/{symbolX}/{fee_str}"

                    if pair not in best_per_pair or daily_yield > best_per_pair[pair][0]:
                        best_per_pair[pair] = (daily_yield, url)
                        best_per_activity[pair] = activity
                        best_per_tvl[pair] = int(round(tvl,0))
            except Exception:
                continue

        # Sort and get top 3 by daily yield
        sorted_pairs = sorted(best_per_pair.items(), key=lambda x: x[1][0], reverse=True)[:3]

        output = {
            f"{pair} | {yield_}％": url
            for pair, (yield_, url) in sorted_pairs
        }
        self._poolActivity = {
            f"{pair} | {yield_}％": best_per_activity[pair]
            for pair, (yield_, url) in sorted_pairs
        }
        self._tvlData ={
            f"{pair} | {yield_}％": best_per_tvl[pair]
            for pair, (yield_, url) in sorted_pairs
        }

        if not output:
            return {}
        return output

    def poolActivities(self):
        return self._poolActivity
    def tvlData(self):
        return self._tvlData
    def topPoolsWithPoints(self):
        result = {}
        pools = self._DATA.get('poolsData', [])

        addr_to_pool = {v: k for k, v in POOLS_WITH_POINTS.items()}

        for pool in pools:
            pool_addr = pool.get('poolAddress')
            pool_name = addr_to_pool.get(pool_addr)
            if not pool_name:
                continue

            apy = float(pool.get('apy', 0))
            daily_apr = round(apy / 365, 3)
            fee = float(pool.get('fee'))
            fee_str = f"{fee:.2f}".replace('.', '_')
            volume = float(pool.get('volume', 0))
            tvl = float(pool.get('tvl', 0))
            activity = round(volume / tvl, 4) if tvl else 0
            tokenX = ADDRESS_TO_SYMBOL.get(pool.get('tokenX'), pool.get('tokenX'))
            tokenY = ADDRESS_TO_SYMBOL.get(pool.get('tokenY'), pool.get('tokenY'))

            url = f"https://eclipse.invariant.app/newPosition/{tokenX}/{tokenY}/{fee_str}"

            key = f"{pool_name} | {daily_apr}％"
            result[key] = url
            self._poolWithPoActivity[key] = activity
            self._poolWithPotvlData[key] = int(round(tvl,0))
        return result
    def poolsWithPointsActivity(self):
        return self._poolWithPoActivity 
    def poolsWithPointsTVL(self):
        return self._poolWithPotvlData








    




